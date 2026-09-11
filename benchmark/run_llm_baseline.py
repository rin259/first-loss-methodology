#!/usr/bin/env python3
"""Run an auditable, repeated LLM-RCA baseline with the OpenAI Responses API."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import time
import socket
import urllib.error
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


PROMPT_VERSION = "llm-rca-v1.1.1"
SYSTEM_PROMPT = """You are evaluating a software incident from an execution trace.
Use only the supplied stage order and observations. Diagnose where the relevant evidence
first became unavailable, where its first recorded invariant violation occurred, and the
most likely root-cause stage. Choose the status that best describes the evidence available
in the trace. Keep the rationale to one sentence."""

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "case_id": {"type": "string"},
        "status": {
            "type": "string",
            "enum": ["exact", "bounded", "exception", "reacquired", "unknown"],
        },
        "first_loss_stage": {"type": ["string", "null"]},
        "invariant_loss_stage": {"type": ["string", "null"]},
        "root_cause_stage": {"type": ["string", "null"]},
        "rationale": {"type": "string"},
    },
    "required": [
        "case_id",
        "status",
        "first_loss_stage",
        "invariant_loss_stage",
        "root_cause_stage",
        "rationale",
    ],
    "additionalProperties": False,
}


def load_cases(path: Path) -> list[dict[str, object]]:
    with path.open(encoding="utf-8") as file_handle:
        return [json.loads(line) for line in file_handle if line.strip()]


def stratified_sample(cases: list[dict[str, object]], count: int, seed: int) -> list[dict[str, object]]:
    groups = defaultdict(list)
    for case in cases:
        groups[(case["runtime"], case["profile"])].append(case)
    rng = random.Random(seed)
    selected = []
    keys = sorted(groups)
    while len(selected) < min(count, len(cases)):
        progressed = False
        for key in keys:
            if len(selected) >= count:
                break
            if groups[key]:
                selected.append(groups[key].pop(rng.randrange(len(groups[key]))))
                progressed = True
        if not progressed:
            break
    return selected


def visible_case(case: dict[str, object]) -> dict[str, object]:
    return {
        "case_id": case["case_id"],
        "runtime": case["runtime"],
        "profile_label": "withheld",
        "stage_order": [item["stage"] for item in case["traces"][0]],
        "replays": case["traces"],
    }


def make_prompt(case: dict[str, object]) -> str:
    return (
        "Diagnose this case and return only one JSON object using exactly these six keys: "
        "case_id, status, first_loss_stage, invariant_loss_stage, root_cause_stage, rationale. "
        "Do not rename, add, or omit keys. Status meanings: exact means the trace supports exact "
        "stage localization; bounded means an unobserved interval prevents exact localization; "
        "exception means a nonlocal effect prevents direct-path attribution; reacquired means "
        "evidence becomes absent and later present; unknown means none of the other labels is "
        "supported. Use null for an unidentified stage. Do not use Markdown fences. The required "
        "shape is: {\"case_id\":\"...\",\"status\":\"exact\",\"first_loss_stage\":null,"
        "\"invariant_loss_stage\":null,\"root_cause_stage\":null,\"rationale\":\"...\"}.\n"
        + json.dumps(visible_case(case), sort_keys=True)
    )


def prompt_hash(prompt: str) -> str:
    material = PROMPT_VERSION + "\n" + SYSTEM_PROMPT + "\n" + prompt
    return hashlib.sha256(material.encode()).hexdigest()


def response_text(response: dict[str, object]) -> str:
    for item in response.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                return str(content["text"])
    raise ValueError("Responses API result did not contain output_text")


def call_openai(
    model: str,
    prompt: str,
    temperature: float,
    timeout: int,
    max_output_tokens: int,
    base_url: str,
    response_format: str,
) -> dict[str, object]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    payload = {
        "model": model,
        "input": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_output_tokens": max_output_tokens,
        "text": {"format": {"type": response_format}},
    }
    if response_format == "json_schema":
        payload["text"]["format"] = {
            "type": "json_schema",
            "name": "flm_rca_baseline",
            "strict": True,
            "schema": OUTPUT_SCHEMA,
        }
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/responses",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    last_error = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as result:
                return json.load(result)
        except urllib.error.HTTPError as error:
            details = error.read().decode(errors="replace")
            if error.code not in {408, 425, 429, 500, 502, 503, 504}:
                raise RuntimeError(f"OpenAI API returned HTTP {error.code}: {details}") from error
            last_error = RuntimeError(f"OpenAI API returned HTTP {error.code}: {details}")
        except (urllib.error.URLError, TimeoutError, socket.timeout) as error:
            last_error = error
        time.sleep(min(30, 2**attempt))
    raise RuntimeError(f"OpenAI API request failed after retries: {last_error}")


def score_prediction(
    case: dict[str, object],
    prediction: dict[str, object],
    parse_valid: bool,
) -> dict[str, int]:
    truth = case["ground_truth"]
    exact = truth["status"] == "exact"
    risky = truth["status"] in {"bounded", "exception", "reacquired"}
    valid_status = prediction.get("status") in {"exact", "bounded", "exception", "reacquired", "unknown"}
    return {
        "status_correct": int(parse_valid and prediction["status"] == truth["status"]),
        "fl_correct": int(exact and prediction["first_loss_stage"] == truth["fl"]),
        "il_correct": int(exact and prediction["invariant_loss_stage"] == truth["il"]),
        "rc_correct": int(exact and prediction["root_cause_stage"] == truth["rc"]),
        "overclaim": int(risky and prediction["status"] == "exact"),
        "exact": int(exact),
        "risky": int(risky),
        "valid_schema": int(parse_valid and valid_status and set(prediction) == set(OUTPUT_SCHEMA["properties"])),
        "attribution_correct": int(
            prediction["status"] == truth["status"]
            and (
                not exact
                or (
                    prediction["first_loss_stage"] == truth["fl"]
                    and prediction["root_cause_stage"] == truth["rc"]
                )
            )
        ),
    }


def parse_prediction(text: str) -> tuple[dict[str, object], bool]:
    candidate = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", candidate, re.DOTALL)
    if fenced:
        candidate = fenced.group(1)
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError:
        return {
            "case_id": "",
            "status": "unknown",
            "first_loss_stage": None,
            "invariant_loss_stage": None,
            "root_cause_stage": None,
            "rationale": "invalid JSON response",
        }, False
    valid = (
        isinstance(value, dict)
        and set(value) == set(OUTPUT_SCHEMA["properties"])
        and value.get("status") in {"exact", "bounded", "exception", "reacquired", "unknown"}
    )
    if not isinstance(value, dict) or set(value) != set(OUTPUT_SCHEMA["properties"]):
        return {
            "case_id": str(value.get("case_id", "")) if isinstance(value, dict) else "",
            "status": "unknown",
            "first_loss_stage": None,
            "invariant_loss_stage": None,
            "root_cause_stage": None,
            "rationale": "response did not match the frozen output schema",
        }, False
    if not valid:
        return value, False
    return value, valid


def export_prompts(cases: list[dict[str, object]], path: Path, repeats: int) -> None:
    with path.open("w", encoding="utf-8") as file_handle:
        for case in cases:
            prompt = make_prompt(case)
            for repeat in range(repeats):
                file_handle.write(
                    json.dumps(
                        {
                            "case_id": case["case_id"],
                            "repeat": repeat,
                            "prompt_version": PROMPT_VERSION,
                            "prompt_hash": prompt_hash(prompt),
                            "system": SYSTEM_PROMPT,
                            "input": prompt,
                            "schema": OUTPUT_SCHEMA,
                        },
                        sort_keys=True,
                    )
                    + "\n"
                )


def summarize(records: list[dict[str, object]]) -> dict[str, object]:
    exact = [record for record in records if record["scores"]["exact"]]
    risky = [record for record in records if record["scores"]["risky"]]
    by_case = defaultdict(list)
    for record in records:
        prediction = record["prediction"]
        by_case[record["case_id"]].append(
            (
                prediction["status"],
                prediction["first_loss_stage"],
                prediction["invariant_loss_stage"],
                prediction["root_cause_stage"],
            )
        )
    return {
        "runs": len(records),
        "cases": len(by_case),
        "status_accuracy": sum(record["scores"]["status_correct"] for record in records) / len(records),
        "exact_fla": sum(record["scores"]["fl_correct"] for record in exact) / len(exact),
        "exact_ila": sum(record["scores"]["il_correct"] for record in exact) / len(exact),
        "exact_rca": sum(record["scores"]["rc_correct"] for record in exact) / len(exact),
        "overclaim_rate": (
            sum(record["scores"]["overclaim"] for record in risky) / len(risky)
            if risky
            else 0.0
        ),
        "attribution_accuracy": sum(record["scores"]["attribution_correct"] for record in records) / len(records),
        "repeat_consistency": sum(len(set(values)) == 1 for values in by_case.values()) / len(by_case),
        "schema_adherence": sum(record["scores"]["valid_schema"] for record in records) / len(records),
    }


def render_report(summary: dict[str, object], manifest: dict[str, object]) -> str:
    return "\n".join(
        [
            "# Real-model RCA baseline",
            "",
            f"- Prompt version: `{manifest['prompt_version']}`",
            f"- Requested model: `{manifest['model']}`",
            f"- Provider-reported model: `{manifest.get('provider_reported_model', 'see manifest verification')}`",
            f"- Cases / repeated runs: `{summary['cases']}` / `{summary['runs']}`",
            f"- Response format: `{manifest['response_format']}` with exact field validation",
            "",
            "| Metric | Result |",
            "|---|---:|",
            f"| Attribution accuracy | {summary['attribution_accuracy']:.3f} |",
            f"| Exact-path FLA | {summary['exact_fla']:.3f} |",
            f"| Exact-path ILA | {summary['exact_ila']:.3f} |",
            f"| Exact-path RCA | {summary['exact_rca']:.3f} |",
            f"| Status accuracy | {summary['status_accuracy']:.3f} |",
            f"| Risky-case overclaim rate | {summary['overclaim_rate']:.3f} |",
            f"| Five-run exact agreement | {summary['repeat_consistency']:.3f} |",
            f"| Schema adherence | {summary['schema_adherence']:.3f} |",
            "",
            "Two compatibility pilots are excluded. The final prompt was frozen only after those pilots, so this is not a preregistered model comparison. The endpoint is OpenAI-compatible; it is not evidence that the model was served by OpenAI.",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="benchmark/runtime_results/cases.jsonl")
    parser.add_argument("--output-dir", default="benchmark/llm_results")
    parser.add_argument("--model")
    parser.add_argument("--base-url", default="https://api.openai.com/v1")
    parser.add_argument("--response-format", choices=("json_schema", "json_object"), default="json_schema")
    parser.add_argument("--cases", type=int, default=60)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=20260911)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--max-output-tokens", type=int, default=300)
    parser.add_argument("--delay", type=float, default=0.0)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.json"
    existing_manifest = (
        json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest_path.exists()
        else {}
    )
    cases = stratified_sample(load_cases(Path(args.input)), args.cases, args.seed)
    cases_by_id = {case["case_id"]: case for case in cases}
    export_prompts(cases, output_dir / "prompts.jsonl", args.repeats)
    manifest = {
        "prompt_version": PROMPT_VERSION,
        "model": args.model,
        "temperature": args.temperature,
        "seed": args.seed,
        "cases": len(cases),
        "repeats": args.repeats,
        "api": "OpenAI Responses API",
        "base_url": args.base_url,
        "documentation": "https://developers.openai.com/api/docs/guides/structured-outputs",
        "max_output_tokens": args.max_output_tokens,
        "response_format": args.response_format,
        "workers": args.workers,
        "provider_reported_model": existing_manifest.get("provider_reported_model"),
        "pilot_runs_excluded": existing_manifest.get("pilot_runs_excluded", 0),
        "pilot_exclusion_reason": existing_manifest.get("pilot_exclusion_reason"),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    if not args.run:
        print(f"Exported {len(cases) * args.repeats} frozen prompts; pass --run and --model to call the API.")
        return
    if not args.model:
        raise SystemExit("--model is required with --run")

    responses_path = output_dir / "responses.jsonl"
    records = []
    completed = set()
    if responses_path.exists():
        with responses_path.open(encoding="utf-8") as file_handle:
            existing_records = [json.loads(line) for line in file_handle if line.strip()]
        deduplicated = {}
        for record in existing_records:
            deduplicated.setdefault((record["case_id"], record["repeat"]), record)
        records = list(deduplicated.values())
        for record in records:
            record["scores"] = score_prediction(
                cases_by_id[record["case_id"]],
                record["prediction"],
                bool(record["parse_valid"]),
            )
        if len(records) != len(existing_records):
            temporary_path = responses_path.with_suffix(".jsonl.tmp")
            with temporary_path.open("w", encoding="utf-8") as file_handle:
                for record in records:
                    file_handle.write(json.dumps(record, sort_keys=True) + "\n")
            temporary_path.replace(responses_path)
        completed = {(record["case_id"], record["repeat"]) for record in records}
    pending = [
        (case, repeat)
        for case in cases
        for repeat in range(args.repeats)
        if (case["case_id"], repeat) not in completed
    ]

    def execute(task: tuple[dict[str, object], int]) -> dict[str, object]:
        case, repeat = task
        prompt = make_prompt(case)
        started = time.time()
        response = call_openai(
            args.model,
            prompt,
            args.temperature,
            args.timeout,
            args.max_output_tokens,
            args.base_url,
            args.response_format,
        )
        raw_output = response_text(response)
        prediction, parse_valid = parse_prediction(raw_output)
        if args.delay:
            time.sleep(args.delay)
        return {
            "case_id": case["case_id"],
            "repeat": repeat,
            "model": args.model,
            "temperature": args.temperature,
            "prompt_version": PROMPT_VERSION,
            "prompt_hash": prompt_hash(prompt),
            "response_id": response.get("id"),
            "usage": response.get("usage"),
            "elapsed_seconds": time.time() - started,
            "prediction": prediction,
            "parse_valid": parse_valid,
            "raw_output": raw_output,
            "scores": score_prediction(case, prediction, parse_valid),
        }

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(execute, task) for task in pending]
        for future in as_completed(futures):
            record = future.result()
            records.append(record)
            with responses_path.open("a", encoding="utf-8") as file_handle:
                file_handle.write(json.dumps(record, sort_keys=True) + "\n")
    summary = summarize(records)
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "REPORT.md").write_text(render_report(summary, manifest), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
