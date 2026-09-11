#!/usr/bin/env python3
"""Executable heterogeneous-runtime evaluation for First Loss Methodology."""

from __future__ import annotations

import argparse
import copy
import csv
import json
import random
from collections import Counter, defaultdict
from pathlib import Path


VERSION = "flm-runtime-benchmark-1.1.0"
MASTER_SEED = 20260911
PROFILES = ("local", "direct", "partial", "noisy", "nonlocal", "reacquired")
METHODS = (
    "final_symptom",
    "component_heuristic",
    "flm_no_intervention",
    "flm_no_replay",
    "flm_full",
)


def observation(
    stage: str,
    present: bool,
    violations: list[str] | None = None,
    reason: str | None = None,
    error_count: int = 0,
    nonlocal_effect: bool = False,
) -> dict[str, object]:
    return {
        "stage": stage,
        "observed": True,
        "present": present,
        "violations": violations or [],
        "reason": reason,
        "error_count": error_count,
        "nonlocal_effect": nonlocal_effect,
    }


class RagRuntime:
    name = "rag"
    stages = ("store", "retrieve", "enrich", "fallback", "cap", "answer")

    def execute(self, profile: str, seed: int) -> dict[str, object]:
        documents = [
            {"id": "target", "rank": 1, "text": "first-loss evidence"},
            {"id": "other-a", "rank": 2, "text": "distractor"},
            {"id": "other-b", "rank": 3, "text": "distractor"},
        ]
        trace = [observation("store", True)]
        retrieved = list(documents)
        if profile == "reacquired":
            retrieved = [item for item in retrieved if item["id"] != "target"]
        trace.append(observation("retrieve", any(item["id"] == "target" for item in retrieved)))

        enriched = [dict(item, source="corpus") for item in retrieved]
        if profile in {"local", "partial", "noisy"}:
            enriched = list(reversed(enriched))
            trace.append(observation("enrich", True, ["order"], error_count=2))
        elif profile == "nonlocal":
            trace.append(observation("enrich", True, nonlocal_effect=True, error_count=1))
        else:
            trace.append(observation("enrich", any(item["id"] == "target" for item in enriched)))

        if profile == "reacquired":
            enriched.append(dict(documents[0], source="fallback"))
        trace.append(observation("fallback", any(item["id"] == "target" for item in enriched)))

        capped = enriched[:2]
        if profile == "direct":
            capped = [item for item in capped if item["id"] != "target"]
        cap_present = any(item["id"] == "target" for item in capped)
        trace.append(observation("cap", cap_present, reason=None if cap_present else "target outside cap", error_count=1))

        answer_present = cap_present and profile != "nonlocal"
        trace.append(
            observation(
                "answer",
                answer_present,
                reason=None if answer_present else "required context unavailable",
                error_count=3,
            )
        )
        truth = {
            "local": ("cap", "enrich", "enrich", "exact"),
            "direct": ("cap", None, "cap", "exact"),
            "partial": ("cap", "enrich", "enrich", "bounded"),
            "noisy": ("cap", "enrich", "enrich", "exact"),
            "nonlocal": ("answer", None, "enrich", "exception"),
            "reacquired": ("retrieve", None, None, "reacquired"),
        }[profile]
        return make_case(self.name, profile, seed, trace, truth)


class EtlRuntime:
    name = "etl"
    stages = ("source", "parse", "map", "dead_letter", "join", "sink")

    def execute(self, profile: str, seed: int) -> dict[str, object]:
        event = {"id": "target", "account": "A-17", "event_time": 100}
        trace = [observation("source", True), observation("parse", True)]
        mapped = dict(event)
        if profile in {"local", "partial", "noisy"}:
            mapped["account"] = "A17"
            trace.append(observation("map", True, ["key"], error_count=2))
        elif profile == "nonlocal":
            trace.append(observation("map", True, nonlocal_effect=True, error_count=1))
        else:
            trace.append(observation("map", profile != "reacquired"))

        dead_letter_present = profile == "reacquired"
        trace.append(observation("dead_letter", dead_letter_present or profile != "reacquired"))
        if dead_letter_present:
            mapped = dict(event)

        joined = mapped.get("account") == "A-17"
        if profile == "direct":
            joined = False
        trace.append(observation("join", joined, reason=None if joined else "dimension key not found", error_count=1))
        sink_present = joined and profile != "nonlocal"
        trace.append(
            observation(
                "sink",
                sink_present,
                reason=None if sink_present else "record absent from committed window",
                error_count=3,
            )
        )
        truth = {
            "local": ("join", "map", "map", "exact"),
            "direct": ("join", None, "join", "exact"),
            "partial": ("join", "map", "map", "bounded"),
            "noisy": ("join", "map", "map", "exact"),
            "nonlocal": ("sink", None, "map", "exception"),
            "reacquired": ("map", None, None, "reacquired"),
        }[profile]
        return make_case(self.name, profile, seed, trace, truth)


class BuildRuntime:
    name = "build"
    stages = ("repository", "resolve", "cache", "vendor", "link", "test")

    def execute(self, profile: str, seed: int) -> dict[str, object]:
        artifact = {"id": "target", "version": "2.0", "abi": "v2"}
        trace = [observation("repository", True)]
        resolved = dict(artifact)
        if profile in {"local", "partial", "noisy"}:
            resolved["version"] = "1.0"
            trace.append(observation("resolve", True, ["version"], error_count=2))
        elif profile == "reacquired":
            resolved = {}
            trace.append(observation("resolve", False, reason="registry miss"))
        elif profile == "nonlocal":
            trace.append(observation("resolve", True, nonlocal_effect=True, error_count=1))
        else:
            trace.append(observation("resolve", True))

        trace.append(observation("cache", bool(resolved)))
        if profile == "reacquired":
            resolved = dict(artifact)
        trace.append(observation("vendor", bool(resolved)))

        linked = resolved.get("version") == "2.0"
        if profile == "direct":
            linked = False
        trace.append(observation("link", linked, reason=None if linked else "required symbol unavailable", error_count=1))
        test_present = linked and profile != "nonlocal"
        trace.append(
            observation(
                "test",
                test_present,
                reason=None if test_present else "binary failed to load",
                error_count=3,
            )
        )
        truth = {
            "local": ("link", "resolve", "resolve", "exact"),
            "direct": ("link", None, "link", "exact"),
            "partial": ("link", "resolve", "resolve", "bounded"),
            "noisy": ("link", "resolve", "resolve", "exact"),
            "nonlocal": ("test", None, "resolve", "exception"),
            "reacquired": ("resolve", None, None, "reacquired"),
        }[profile]
        return make_case(self.name, profile, seed, trace, truth)


def make_case(
    runtime: str,
    profile: str,
    seed: int,
    trace: list[dict[str, object]],
    truth: tuple[str, str | None, str | None, str],
) -> dict[str, object]:
    fl_stage, il_stage, root_stage, expected_status = truth
    if profile == "partial":
        for item in trace:
            if item["stage"] == fl_stage:
                item["observed"] = False
                item["present"] = None
                item["violations"] = []
                item["reason"] = None
    traces = [trace]
    if profile == "noisy":
        traces = []
        for replay in range(5):
            replay_trace = copy.deepcopy(trace)
            rng = random.Random(seed + replay * 997)
            if rng.random() < 0.28:
                fl_index = next(index for index, item in enumerate(replay_trace) if item["stage"] == fl_stage)
                replay_trace[fl_index]["present"] = True
                replay_trace[fl_index]["reason"] = None
                il_item = next(item for item in replay_trace if item["stage"] == il_stage)
                il_item["violations"] = []
            traces.append(replay_trace)
    return {
        "case_id": f"{runtime}-{profile}-{seed}",
        "version": VERSION,
        "runtime": runtime,
        "profile": profile,
        "seed": seed,
        "traces": traces,
        "ground_truth": {
            "fl": fl_stage,
            "il": il_stage,
            "rc": root_stage,
            "status": expected_status,
        },
        "intervention": {
            "target": root_stage,
            "fail_before": expected_status not in {"reacquired"},
            "pass_after": expected_status in {"exact"},
        },
    }


def first_loss(trace: list[dict[str, object]]) -> str | None:
    previous_present = True
    for item in trace:
        if not item["observed"]:
            continue
        present = bool(item["present"])
        if previous_present and not present:
            return str(item["stage"])
        previous_present = present
    return None


def invariant_loss(trace: list[dict[str, object]]) -> str | None:
    for item in trace:
        if item["observed"] and item["violations"]:
            return str(item["stage"])
    return None


def has_reacquisition(trace: list[dict[str, object]]) -> bool:
    seen_absent = False
    for item in trace:
        if not item["observed"]:
            continue
        if item["present"] is False:
            seen_absent = True
        elif seen_absent and item["present"] is True:
            return True
    return False


def bounded_interval(trace: list[dict[str, object]]) -> tuple[str, str] | None:
    for index, item in enumerate(trace):
        if item["observed"]:
            continue
        left = next((trace[pos]["stage"] for pos in range(index - 1, -1, -1) if trace[pos]["observed"]), None)
        right = next((trace[pos]["stage"] for pos in range(index + 1, len(trace)) if trace[pos]["observed"]), None)
        if left is not None and right is not None:
            return str(left), str(right)
    return None


def majority(values: list[str | None]) -> str | None:
    return Counter(values).most_common(1)[0][0]


def flm_diagnosis(case: dict[str, object], replay: bool, intervention: bool) -> dict[str, object]:
    traces = case["traces"] if replay else case["traces"][:1]
    primary_trace = traces[0]
    if any(item["nonlocal_effect"] for item in primary_trace if item["observed"]):
        return {"status": "exception", "fl": first_loss(primary_trace), "il": None, "rc": None, "confirmed": False}
    if has_reacquisition(primary_trace):
        return {"status": "reacquired", "fl": first_loss(primary_trace), "il": None, "rc": None, "confirmed": False}
    interval = bounded_interval(primary_trace)
    if interval is not None:
        return {"status": "bounded", "bounds": interval, "fl": None, "il": invariant_loss(primary_trace), "rc": None, "confirmed": False}

    fl_stage = majority([first_loss(trace) for trace in traces])
    il_stage = majority([invariant_loss(trace) for trace in traces])
    candidate = il_stage or fl_stage
    confirmed = bool(
        intervention
        and case["intervention"]["fail_before"]
        and case["intervention"]["pass_after"]
        and case["intervention"]["target"] == candidate
    )
    return {
        "status": "exact",
        "fl": fl_stage,
        "il": il_stage,
        "rc": candidate,
        "confirmed": confirmed,
    }


def predict(method: str, case: dict[str, object]) -> dict[str, object]:
    trace = case["traces"][0]
    if method == "flm_full":
        return flm_diagnosis(case, replay=True, intervention=True)
    if method == "flm_no_intervention":
        return flm_diagnosis(case, replay=True, intervention=False)
    if method == "flm_no_replay":
        return flm_diagnosis(case, replay=False, intervention=True)
    if method == "final_symptom":
        absent = [str(item["stage"]) for item in trace if item["observed"] and item["present"] is False]
        stage = absent[-1] if absent else str(trace[-1]["stage"])
        return {"status": "exact", "fl": stage, "il": None, "rc": stage, "confirmed": False}
    if method == "component_heuristic":
        candidates = [item for item in trace if item["observed"]]
        stage = str(max(candidates, key=lambda item: (int(item["error_count"]), trace.index(item)))["stage"])
        return {"status": "exact", "fl": first_loss(trace), "il": invariant_loss(trace), "rc": stage, "confirmed": False}
    raise ValueError(f"Unknown method: {method}")


def stage_between(stage: str, bounds: tuple[str, str], trace: list[dict[str, object]]) -> bool:
    order = [str(item["stage"]) for item in trace]
    return order.index(bounds[0]) < order.index(stage) < order.index(bounds[1])


def score(method: str, case: dict[str, object]) -> dict[str, object]:
    prediction = predict(method, case)
    truth = case["ground_truth"]
    expected_status = truth["status"]
    if expected_status == "bounded":
        safe = prediction["status"] == "bounded" and stage_between(
            str(truth["fl"]), tuple(prediction.get("bounds", ("", ""))), case["traces"][0]
        )
    else:
        safe = prediction["status"] == expected_status
        if expected_status == "exact":
            safe = safe and prediction.get("fl") == truth["fl"] and prediction.get("rc") == truth["rc"]
    risky = expected_status in {"bounded", "exception", "reacquired"}
    overclaim = risky and prediction["status"] == "exact"
    eligible_exact = expected_status == "exact"
    return {
        "case_id": case["case_id"],
        "runtime": case["runtime"],
        "profile": case["profile"],
        "method": method,
        "status_pred": prediction["status"],
        "fl_pred": prediction.get("fl"),
        "il_pred": prediction.get("il"),
        "rc_pred": prediction.get("rc"),
        "safe_attribution": int(safe),
        "exact_fl_correct": int(eligible_exact and prediction.get("fl") == truth["fl"]),
        "exact_rc_correct": int(eligible_exact and prediction.get("rc") == truth["rc"]),
        "confirmed_rc_correct": int(eligible_exact and prediction.get("confirmed") and prediction.get("rc") == truth["rc"]),
        "eligible_exact": int(eligible_exact),
        "overclaim": int(overclaim),
        "risky": int(risky),
    }


def generate_cases(repetitions: int) -> list[dict[str, object]]:
    cases = []
    runtimes = (RagRuntime(), EtlRuntime(), BuildRuntime())
    for runtime_index, runtime in enumerate(runtimes):
        for profile_index, profile in enumerate(PROFILES):
            for repetition in range(repetitions):
                seed = MASTER_SEED + runtime_index * 10000 + profile_index * 1000 + repetition
                cases.append(runtime.execute(profile, seed))
    return cases


def summarize(rows: list[dict[str, object]]) -> dict[str, object]:
    result = {}
    for method in METHODS:
        method_rows = [row for row in rows if row["method"] == method]
        exact_rows = [row for row in method_rows if row["eligible_exact"]]
        risky_rows = [row for row in method_rows if row["risky"]]
        result[method] = {
            "safe_attribution": sum(row["safe_attribution"] for row in method_rows) / len(method_rows),
            "exact_fla": sum(row["exact_fl_correct"] for row in exact_rows) / len(exact_rows),
            "exact_rca": sum(row["exact_rc_correct"] for row in exact_rows) / len(exact_rows),
            "confirmed_rca": sum(row["confirmed_rc_correct"] for row in exact_rows) / len(exact_rows),
            "overclaim_rate": sum(row["overclaim"] for row in risky_rows) / len(risky_rows),
            "n": len(method_rows),
        }
    return result


def render_report(summary: dict[str, object], cases: list[dict[str, object]], repetitions: int) -> str:
    lines = [
        "# Heterogeneous executable-runtime report",
        "",
        f"- Version: `{VERSION}`",
        f"- Cases: `{len(cases)}` ({repetitions} repetitions per runtime/profile)",
        "- Runtimes: executable RAG, ETL, and build-system reference implementations",
        "- Stress profiles: local fault, direct loss, partial observability, noisy probes, nonlocal side effect, and reacquisition",
        "",
        "| Method | Safe attribution | Exact FLA | Exact RCA | Confirmed RCA | Overclaim rate |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for method in METHODS:
        metrics = summary[method]
        lines.append(
            f"| `{method}` | {metrics['safe_attribution']:.3f} | {metrics['exact_fla']:.3f} | "
            f"{metrics['exact_rca']:.3f} | {metrics['confirmed_rca']:.3f} | {metrics['overclaim_rate']:.3f} |"
        )
    lines.extend(
        [
            "",
            "Safe attribution requires an exact answer on fully observed local paths, a containing interval when the loss stage is hidden, an explicit exception for nonlocal causality, and segment-aware handling when evidence is reacquired. Confirmed RCA additionally requires fail-before/pass-after intervention evidence.",
            "",
            "These are small executable reference runtimes, not production deployments. They reduce the role-label transfer problem in the original synthetic benchmark but do not establish population-level generality.",
            "",
        ]
    )
    return "\n".join(lines)


def write_csv(rows: list[dict[str, object]], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="benchmark/runtime_results")
    parser.add_argument("--repetitions", type=int, default=20)
    args = parser.parse_args()

    cases = generate_cases(args.repetitions)
    rows = [score(method, case) for case in cases for method in METHODS]
    summary = summarize(rows)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "cases.jsonl").open("w", encoding="utf-8") as file_handle:
        for case in cases:
            file_handle.write(json.dumps(case, sort_keys=True) + "\n")
    write_csv(rows, output_dir / "metrics.csv")
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = render_report(summary, cases, args.repetitions)
    (output_dir / "REPORT.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
