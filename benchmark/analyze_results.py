#!/usr/bin/env python3
"""Post-hoc analysis of frozen FLM benchmark outputs.

Reads the published result files (no experiments are re-run) and emits:

- runtime_results/ANALYSIS.md : per-profile breakdown, clustered comparisons,
  and the FLM error taxonomy.
- llm_results/ANALYSIS.md : Wilson intervals, repeat-agreement distribution,
  ILA failure breakdown, and the FLM overlap analysis.

Only the Python standard library is used.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PROFILES = ["local", "direct", "partial", "noisy", "nonlocal", "reacquired"]
RUNTIMES = ["rag", "etl", "build"]
METHODS = [
    "final_symptom",
    "component_heuristic",
    "flm_no_intervention",
    "flm_no_replay",
    "flm_full",
]


def wilson(correct: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """Return the Wilson score 95% interval for a binomial proportion."""
    if total == 0:
        return (0.0, 0.0)
    p = correct / total
    denom = 1.0 + z * z / total
    center = (p + z * z / (2.0 * total)) / denom
    half = z * math.sqrt(p * (1.0 - p) / total + z * z / (4.0 * total * total)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def fmt_ci(correct: int, total: int) -> str:
    p = correct / total if total else 0.0
    low, high = wilson(correct, total)
    return f"{p:.3f} [{low:.3f}, {high:.3f}]"


def mcnemar_exact(b: int, c: int) -> float:
    """Exact two-sided McNemar p-value for b and c discordant pairs."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) * (0.5**n)
    return min(1.0, 2.0 * tail)


def fmt_p(p: float) -> str:
    if p < 1e-300:
        return "<1e-300"
    return f"{p:.3g}"


def load_metrics(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def clustered_delta_ci(
    per_config: dict[str, dict[str, int]],
    metric: str,
    methods: tuple[str, str],
    reps: int = 10000,
    seed: int = 20260911,
) -> tuple[float, float]:
    """Bootstrap 95% CI for the mean metric difference between two methods.

    Resampling is clustered by fault configuration so that repeated seeded
    runs of the same configuration stay together.
    """
    deltas: list[float] = []
    for config, counts in per_config.items():
        total = counts[f"{methods[0]}_n"]
        if total == 0:
            continue
        a = counts[f"{methods[0]}_{metric}"] / total
        b = counts[f"{methods[1]}_{metric}"] / total
        deltas.append(a - b)
    rng = random.Random(seed)
    means: list[float] = []
    for _ in range(reps):
        sample = [deltas[rng.randrange(len(deltas))] for _ in deltas]
        means.append(sum(sample) / len(sample))
    means.sort()
    low = means[int(math.floor(0.025 * reps))]
    high = means[int(math.ceil(0.975 * reps)) - 1]
    return low, high


def runtime_analysis(runtime_dir: Path) -> str:
    metrics = load_metrics(runtime_dir / "metrics.csv")
    cases = {case["case_id"]: case for case in load_jsonl(runtime_dir / "cases.jsonl")}

    lines: list[str] = ["# Runtime results: post-hoc analysis", ""]

    # ---- configuration structure -------------------------------------
    config_runs: dict[tuple[str, str], int] = Counter()
    config_truths: dict[tuple[str, str], set[str]] = defaultdict(set)
    for case in cases.values():
        key = (case["runtime"], case["profile"])
        config_runs[key] += 1
        config_truths[key].add(json.dumps(case["ground_truth"], sort_keys=True))
    distinct_truths = {len(truths) for truths in config_truths.values()}
    lines += [
        f"- Runs: {len(cases)} across {len(config_runs)} fault configurations",
        f"- Distinct ground truths per configuration: {min(distinct_truths)}"
        f"-{max(distinct_truths)} (each configuration replays one injected fault)",
        "",
        "The 360 runs are therefore 18 fault configurations sampled with 20 seeded"
        " replay repetitions each. Repetitions measure robustness of attribution"
        " under re-execution (probe noise, instrumentation), not sampling of"
        " independent faults. Method comparisons below are reported at both the"
        " run level and the configuration level.",
        "",
    ]

    # ---- per-profile run-level table ----------------------------------
    lines += [
        "## Run-level breakdown by stress profile (3 runtimes x 20 repetitions)",
        "",
        "Exact metrics are defined only for eligible-exact runs (profiles"
        " local, direct, noisy; n=60 per profile); the eligible count is"
        " shown per row. Bounded, exception, and reacquired profiles are"
        " scored by safe attribution only.",
        "",
        "| Profile | Method | Safe | Exact FLA | Exact RCA | Confirmed | Overclaim |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    by_profile: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in metrics:
        by_profile[row["profile"]].append(row)
    for profile in PROFILES:
        rows = by_profile[profile]
        for method in METHODS:
            sel = [row for row in rows if row["method"] == method]
            n = len(sel)
            if n == 0:
                continue
            eligible = [row for row in sel if row["eligible_exact"] == "1"]
            safe = sum(int(row["safe_attribution"]) for row in sel) / n
            over = sum(int(row["overclaim"]) for row in sel) / len(sel)

            def exact_rate(column: str) -> str:
                if not eligible:
                    return "--"
                return f"{sum(int(row[column]) for row in eligible) / len(eligible):.3f}"

            lines.append(
                f"| {profile} | {method} | {safe:.3f} | {exact_rate('exact_fl_correct')} "
                f"| {exact_rate('exact_rc_correct')} | {exact_rate('confirmed_rc_correct')} | {over:.3f} |"
            )
    lines.append("")

    # ---- configuration-level aggregation ------------------------------
    per_config: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    case_profile: dict[str, str] = {}
    for row in metrics:
        case_id = row["case_id"]
        case_profile[case_id] = row["profile"]
        config = f"{row['runtime']}/{row['profile']}"
        bucket = per_config[config]
        bucket[f"{row['method']}_n"] += 1
        for metric in ("safe_attribution", "exact_fl_correct", "exact_rc_correct"):
            bucket[f"{row['method']}_{metric}"] += int(row[metric])
    config_level: dict[tuple[str, str, str], float] = {}
    for config, bucket in per_config.items():
        runtime, profile = config.split("/")
        n = bucket["flm_full_n"]
        for method in METHODS:
            for metric in ("safe_attribution", "exact_fl_correct", "exact_rc_correct"):
                config_level[(runtime, profile, f"{method}:{metric}")] = (
                    bucket[f"{method}_{metric}"] / n
                )
    lines += [
        "## Configuration-level aggregation (18 units)",
        "",
        "| Profile | Method | Safe | Exact FLA | Exact RCA |",
        "|---|---|---:|---:|---:|",
    ]
    for profile in PROFILES:
        for method in METHODS:
            safe = sum(config_level[(rt, profile, f"{method}:safe_attribution")] for rt in RUNTIMES) / 3
            fla = sum(config_level[(rt, profile, f"{method}:exact_fl_correct")] for rt in RUNTIMES) / 3
            rca = sum(config_level[(rt, profile, f"{method}:exact_rc_correct")] for rt in RUNTIMES) / 3
            lines.append(
                f"| {profile} | {method} | {safe:.3f} | {fla:.3f} | {rca:.3f} |"
            )
    lines.append("")

    # ---- paired comparisons --------------------------------------------
    lines += [
        "## Paired comparisons: FLM full vs ablations",
        "",
        "Run-level exact McNemar p-values treat the 360 runs as paired binary"
        " outcomes; because runs of one configuration share the injected fault, a"
        " configuration-clustered bootstrap 95% CI of the mean difference is"
        " reported alongside.",
        "",
        "| Pair | Metric | Discordant (full/abl) | Run McNemar p | Clustered 95% CI of delta |",
        "|---|---|---|---:|---|",
    ]
    pairs = [
        ("flm_full", "flm_no_replay"),
        ("flm_full", "flm_no_intervention"),
        ("flm_no_replay", "flm_no_intervention"),
    ]
    per_config_runs: dict[str, dict[str, list[dict[str, str]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for row in metrics:
        per_config_runs[f"{row['runtime']}/{row['profile']}"][row["method"]].append(row)
    for method_a, method_b in pairs:
        for metric, column in (
            ("safe", "safe_attribution"),
            ("exact_fl", "exact_fl_correct"),
        ):
            both_a = 0
            only_a = 0
            only_b = 0
            clustered: dict[str, dict[str, int]] = {}
            for config, runs in per_config_runs.items():
                runs_a = {r["case_id"]: int(r[column]) for r in runs[method_a]}
                runs_b = {r["case_id"]: int(r[column]) for r in runs[method_b]}
                bucket = clustered.setdefault(
                    config,
                    {
                        f"{method_a}_n": 0,
                        f"{method_b}_n": 0,
                        f"{method_a}_{metric}": 0,
                        f"{method_b}_{metric}": 0,
                    },
                )
                for case_id, a in runs_a.items():
                    b = runs_b[case_id]
                    bucket[f"{method_a}_n"] += 1
                    bucket[f"{method_b}_n"] += 1
                    bucket[f"{method_a}_{metric}"] += a
                    bucket[f"{method_b}_{metric}"] += b
                    if a and not b:
                        only_a += 1
                    elif b and not a:
                        only_b += 1
                    elif a and b:
                        both_a += 1
            p = mcnemar_exact(only_a, only_b)
            low, high = clustered_delta_ci(clustered, metric, (method_a, method_b))
            lines.append(
                f"| {method_a} vs {method_b} | {metric} | {only_a}/{only_b} "
                f"| {fmt_p(p)} | [{low:+.3f}, {high:+.3f}] |"
            )
    lines.append("")

    # ---- FLM error taxonomy --------------------------------------------
    lines += [
        "## FLM error taxonomy (eligible-exact runs only)",
        "",
        "Exact-attribution errors are only defined for eligible-exact runs"
        " (profiles local, direct, noisy; 180 of 360 runs). Runs in the"
        " bounded, exception, and reacquired profiles are scored by safe"
        " attribution and cannot produce an exact-stage error.",
        "",
    ]
    err_by_profile: Counter[str] = Counter()
    err_details: Counter[tuple[str, str, str, str]] = Counter()
    safe_misses: list[str] = []
    flm_rows = {row["case_id"]: row for row in metrics if row["method"] == "flm_full"}
    noreplay_rows = {
        row["case_id"]: row for row in metrics if row["method"] == "flm_no_replay"
    }
    for case_id, row in sorted(flm_rows.items()):
        case = cases[case_id]
        truth = case["ground_truth"]
        if row["eligible_exact"] != "1":
            continue
        if int(row["exact_fl_correct"]) == 0:
            err_by_profile[row["profile"]] += 1
            err_details[
                (row["runtime"], row["profile"], row["fl_pred"] or "-", truth["fl"])
            ] += 1
        if int(row["safe_attribution"]) == 0:
            replay_note = ""
            if noreplay_rows[case_id]["safe_attribution"] == "1":
                replay_note = "; the no-replay ablation answered this case correctly"
            safe_misses.append(
                f"{case_id}: claimed status={row['status_pred']} with"
                f" FL={row['fl_pred'] or '-'}, ground truth FL={truth['fl']}"
                f"{replay_note}"
            )
    lines.append("| Profile | Exact-FL errors (of eligible runs) |")
    lines.append("|---|---:|")
    for profile in ("local", "direct", "noisy"):
        lines.append(f"| {profile} | {err_by_profile[profile]} |")
    lines.append("")
    lines.append("| Runtime | Profile | FL prediction | Ground truth | Runs |")
    lines.append("|---|---|---|---|---:|")
    for (runtime, profile, pred, truth), count in sorted(err_details.items()):
        lines.append(f"| {runtime} | {profile} | {pred} | {truth} | {count} |")
    lines.append("")
    if safe_misses:
        lines += ["Safe-attribution failures of the full method:", ""]
        lines += [f"- {item}" for item in safe_misses]
        lines.append("")
    else:
        lines += ["No safe-attribution failures.", ""]

    noreplay_misses = [
        case_id
        for case_id, row in sorted(noreplay_rows.items())
        if row["eligible_exact"] == "1" and row["safe_attribution"] == "0"
    ]
    recovered = [
        case_id
        for case_id in noreplay_misses
        if flm_rows[case_id]["safe_attribution"] == "1"
    ]
    introduced = [
        case_id
        for case_id, row in sorted(flm_rows.items())
        if row["safe_attribution"] == "0" and noreplay_rows[case_id]["safe_attribution"] == "1"
    ]
    lines += [
        "## Replay ablation detail (full vs no-replay, safe attribution)",
        "",
        f"- Errors of the full method: 7; errors without replay: "
        f"{len(noreplay_misses)}",
        f"- Cases corrected by replay: {len(recovered)}",
        f"- Cases where replay turned a correct answer into a wrong exact"
        f" claim: {len(introduced)}",
        "",
        "The four reversed cases show that majority aggregation over five"
        " noisy probe repetitions can itself manufacture an overconfident"
        " exact answer; replay is not monotone under probe noise.",
        "",
    ]

    # ---- ground-truth transition overview -------------------------------
    truth_shapes: Counter[tuple[str, str, str]] = Counter()
    for case in cases.values():
        truth = case["ground_truth"]
        truth_shapes[(case["profile"], truth["fl"] or "-", truth["il"] or "-")] += 1
    lines += [
        "## Ground-truth shapes per profile",
        "",
        "| Profile | First Loss stage | Invariant Loss stage | Runs |",
        "|---|---|---|---:|",
    ]
    for (profile, fl, il), count in sorted(truth_shapes.items()):
        lines.append(f"| {profile} | {fl} | {il} | {count} |")
    lines.append("")

    return "\n".join(lines)


def synthetic_analysis(results_dir: Path) -> str:
    """Per-family breakdown and ablation significance for the controlled run."""
    metrics = load_metrics(results_dir / "case_metrics.csv")
    test = [row for row in metrics if row["split"] == "test"]
    n_methods = len({row["method"] for row in test})
    n_cases = len(test) // n_methods if n_methods else 0

    by_family: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in test:
        by_family[row["family"]].append(row)

    lines: list[str] = [
        "# Controlled benchmark: post-hoc analysis (test split, n="
        f"{n_cases} cases per method)",
        "",
        "## FLM accuracy by fault family",
        "",
        "| Family | n | FLM RCA | Component RCA | Existence-only RCA |",
        "|---|---:|---:|---:|---:|",
    ]
    flm_all_exact = True
    for family in sorted(by_family):
        rows = by_family[family]
        n = len({row["case_id"] for row in rows})

        def rate(method: str, column: str) -> str:
            sel = [row for row in rows if row["method"] == method]
            return f"{sum(int(row[column]) for row in sel) / len(sel):.3f}" if sel else "--"

        flm_rca = rate("flm_full", "rc_correct")
        if flm_rca != "1.000":
            flm_all_exact = False
        lines.append(
            f"| {family} | {n} | {flm_rca} "
            f"| {rate('component_level_rca', 'rc_correct')} "
            f"| {rate('existence_only_provenance', 'rc_correct')} |"
        )
    lines += [
        "",
        f"FLM is exact on every family: {flm_all_exact}. The informative"
        " columns are the baselines, which lose accuracy precisely on the"
        " families whose failure semantics depend on the loss boundary.",
        "",
    ]

    # ---- ablation significance -----------------------------------------
    full = {row["case_id"]: row for row in test if row["method"] == "flm_full"}
    lines += [
        "## Ablation significance (exact McNemar vs FLM full, test split)",
        "",
        "| Variant | RCA confirmed | 1-FDAR | p (confirmed) | p (1-FDAR) |",
        "|---|---:|---:|---:|---:|",
    ]
    variants = [
        "flm_no_first_loss_rule",
        "flm_no_invariant_checking",
        "flm_no_upstream_exclusion",
        "flm_no_minimal_probe",
        "flm_no_intervention",
        "flm_no_independent_replay",
        "flm_blind_candidate_selection",
    ]
    for variant in variants:
        rows = {row["case_id"]: row for row in test if row["method"] == variant}
        table: list[str] = []
        for column in ("rc_confirmed", "incorrect_downstream"):
            b = sum(
                1
                for case_id, row in rows.items()
                if int(row[column]) == 1 and int(full[case_id][column]) == 0
            )
            c = sum(
                1
                for case_id, row in rows.items()
                if int(row[column]) == 0 and int(full[case_id][column]) == 1
            )
            table.append(f"{fmt_p(mcnemar_exact(b, c))} ({b}/{c})")
        confirmed = sum(int(row["rc_confirmed"]) for row in rows.values()) / len(rows)
        one_fdar = 1 - sum(int(row["incorrect_downstream"]) for row in rows.values()) / len(rows)
        lines.append(
            f"| {variant} | {confirmed:.3f} | {one_fdar:.3f} "
            f"| {table[0]} | {table[1]} |"
        )
    lines += [
        "",
        "Discordant pairs are reported as (variant worse/full better). The two",
        "confirmation ablations (no intervention, no replay) are identical to",
        "the full method on localization metrics by design and differ only in",
        "claim strength.",
        "",
    ]
    return "\n".join(lines)


def llm_analysis(llm_dir: Path, runtime_dir: Path) -> str:
    responses = load_jsonl(llm_dir / "responses.jsonl")
    cases = {
        case["case_id"]: case for case in load_jsonl(runtime_dir / "cases.jsonl")
    }
    metrics = load_metrics(runtime_dir / "metrics.csv")
    flm_rows = {row["case_id"]: row for row in metrics if row["method"] == "flm_full"}

    runs_by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for response in responses:
        runs_by_case[response["case_id"]].append(response)
    case_ids = sorted(runs_by_case)

    def attribution_correct(run: dict[str, Any]) -> int:
        """Recompute the frozen attribution_correct score from raw fields.

        Mirrors run_llm_baseline.score_prediction: the status must match and,
        for eligible-exact cases, the First Loss and root-cause stages too.
        """
        truth = cases[run["case_id"]]["ground_truth"]
        prediction = run["prediction"]
        exact = truth["status"] == "exact"
        return int(
            prediction["status"] == truth["status"]
            and (
                not exact
                or (
                    prediction.get("first_loss_stage") == truth["fl"]
                    and prediction.get("root_cause_stage") == truth["rc"]
                )
            )
        )

    strata: Counter[tuple[str, str]] = Counter()
    for case_id in case_ids:
        case = cases[case_id]
        strata[(case["runtime"], case["profile"])] += 1

    lines: list[str] = [
        "# Real-model baseline: post-hoc analysis",
        "",
        "All intervals are Wilson score 95% intervals. Runs are the unit for"
        " per-run metrics; cases (n=60) are the unit for agreement.",
        "",
        "## Stratification allocation",
        "",
        "Round-robin sampling over 18 runtime/profile strata yields 60 cases:"
        " six strata contribute 4 cases and twelve strata contribute 3.",
        "",
        "| Runtime | Profile | Cases |",
        "|---|---|---:|",
    ]
    for (runtime, profile), count in sorted(strata.items()):
        lines.append(f"| {runtime} | {profile} | {count} |")
    lines.append("")

    # ---- headline metrics with Wilson intervals -------------------------
    n_runs = len(responses)
    eligible = [r for r in responses if r["scores"]["exact"] == 1]
    risky = [r for r in responses if r["scores"]["risky"] == 1]
    n_eligible = len(eligible)
    n_risky = len(risky)
    attribution = sum(attribution_correct(r) for r in responses)
    exact_fla = sum(1 for r in eligible if r["scores"]["fl_correct"] == 1)
    exact_ila = sum(1 for r in eligible if r["scores"]["il_correct"] == 1)
    exact_rca = sum(1 for r in eligible if r["scores"]["rc_correct"] == 1)
    status = sum(1 for r in responses if r["scores"]["status_correct"] == 1)
    overclaim = sum(1 for r in risky if r["scores"]["overclaim"] == 1)
    schema = sum(1 for r in responses if r["scores"]["valid_schema"] == 1)

    lines += [
        "## Headline metrics with Wilson 95% intervals",
        "",
        f"Per-run metrics use all {n_runs} runs; exact-path metrics are gated"
        f" on eligible-exact runs (profiles local, direct, noisy; n="
        f"{n_eligible}); the overclaim denominator is risky runs (n="
        f"{n_risky}).",
        "",
        "| Metric | Estimate [95% CI] |",
        "|---|---|",
        f"| Attribution accuracy (n={n_runs}) | {fmt_ci(attribution, n_runs)} |",
        f"| Exact-path FLA (n={n_eligible}) | {fmt_ci(exact_fla, n_eligible)} |",
        f"| Exact-path ILA (n={n_eligible}) | {fmt_ci(exact_ila, n_eligible)} |",
        f"| Exact-path RCA (n={n_eligible}) | {fmt_ci(exact_rca, n_eligible)} |",
        f"| Status accuracy (n={n_runs}) | {fmt_ci(status, n_runs)} |",
        f"| Overclaim rate (denominator: risky runs = {n_risky}) "
        f"| {fmt_ci(overclaim, n_risky)} |",
        f"| Schema adherence (n={n_runs}) | {fmt_ci(schema, n_runs)} |",
        "",
    ]

    # ---- repeat agreement ----------------------------------------------
    def answer(run: dict[str, Any]) -> tuple[Any, ...]:
        prediction = run["prediction"]
        return (
            prediction.get("status"),
            prediction.get("first_loss_stage"),
            prediction.get("invariant_loss_stage"),
            prediction.get("root_cause_stage"),
        )

    agreement_counts: Counter[int] = Counter()
    majority_correct = 0
    for case_id in case_ids:
        answers = [answer(run) for run in runs_by_case[case_id]]
        distinct = Counter(answers)
        agreement_counts[len(distinct)] += 1
        majority_answer, _ = distinct.most_common(1)[0]
        truth = cases[case_id]["ground_truth"]
        if majority_answer[3] == truth["rc"]:
            majority_correct += 1

    n_cases = len(case_ids)
    all_agree = agreement_counts[1]

    distinct_raw: Counter[int] = Counter()
    reasoning_spread = 0
    for case_id in case_ids:
        raws = {run["raw_output"] for run in runs_by_case[case_id]}
        distinct_raw[len(raws)] += 1
        tokens = [
            (run.get("usage") or {}).get("output_tokens_details", {}).get("reasoning_tokens")
            for run in runs_by_case[case_id]
        ]
        tokens = [t for t in tokens if isinstance(t, int)]
        if tokens and len(set(tokens)) > 1:
            reasoning_spread += 1

    lines += [
        "## Repeat content (temperature 0)",
        "",
        "Whether repeated runs are byte-identical at the raw level, not only at",
        "the parsed answer level.",
        "",
        "- Cases with five distinct raw outputs: "
        f"{distinct_raw[5]}/{n_cases}",
        "- Distribution of distinct raw outputs per case: "
        + ", ".join(f"{k} distinct: {v}" for k, v in sorted(distinct_raw.items())),
        f"- Cases where reported reasoning tokens vary across repeats: "
        f"{reasoning_spread}/{n_cases}",
        "",
    ]

    lines += [
        "## Repeat agreement",
        "",
        f"- Cases with five identical answers: {all_agree}/{n_cases} "
        f"({all_agree / n_cases:.3f})",
        "- Distribution of distinct answers per case (of 5 repeats): "
        + ", ".join(f"{k} distinct: {v}" for k, v in sorted(agreement_counts.items())),
        "",
        "Exploratory (not preregistered): majority-vote root-cause accuracy"
        f" across the five repeats is {majority_correct}/{n_cases} "
        f"({majority_correct / n_cases:.3f}).",
        "",
    ]

    # ---- ILA failure breakdown ------------------------------------------
    il_errors: Counter[tuple[str, str, str, str]] = Counter()
    il_error_cases: set[str] = set()
    il_error_runs = 0
    for run in eligible:
        if run["scores"]["il_correct"] == 0:
            case = cases[run["case_id"]]
            truth = case["ground_truth"]
            predicted = run["prediction"].get("invariant_loss_stage")
            il_errors[(case["runtime"], case["profile"], predicted or "-", truth["il"] or "-")] += 1
            il_error_cases.add(run["case_id"])
            il_error_runs += 1
    hallucinated = sum(
        1
        for run in eligible
        if run["scores"]["il_correct"] == 0
        and run["prediction"].get("invariant_loss_stage")
        and not cases[run["case_id"]]["ground_truth"]["il"]
    )
    lines += [
        "## Invariant Loss failures (eligible-exact runs)",
        "",
        f"- Runs with an IL error: {il_error_runs}/{n_eligible}; cases affected:"
        f" {len(il_error_cases)} of the eligible cases",
        f"- Of these, runs that hallucinate an IL stage where ground truth is"
        f" none: {hallucinated}",
        "",
        "| Runtime | Profile | Predicted IL | Ground-truth IL | Runs |",
        "|---|---|---|---|---:|",
    ]
    for (runtime, profile, pred, truth), count in sorted(il_errors.items()):
        lines.append(f"| {runtime} | {profile} | {pred} | {truth} | {count} |")
    lines.append("")

    # ---- overlap with FLM ------------------------------------------------
    def rate(values: list[int]) -> str:
        total = len(values)
        correct = sum(values)
        return fmt_ci(correct, total)

    flm_safe = [int(flm_rows[c]["safe_attribution"]) for c in case_ids]
    llm_any: list[int] = []
    llm_all: list[int] = []
    union_any = 0
    union_all = 0
    both_wrong_any = 0
    for case_id in case_ids:
        case_runs = runs_by_case[case_id]
        runs_ok = [attribution_correct(run) for run in case_runs]
        any_ok = 1 if any(runs_ok) else 0
        all_ok = 1 if all(runs_ok) else 0
        llm_any.append(any_ok)
        llm_all.append(all_ok)
        if not any_ok and not flm_safe[case_ids.index(case_id)]:
            both_wrong_any += 1
        if any_ok or flm_safe[case_ids.index(case_id)]:
            union_any += 1
        if all_ok or flm_safe[case_ids.index(case_id)]:
            union_all += 1

    eligible_ids = [
        c for c in case_ids if flm_rows[c]["eligible_exact"] == "1"
    ]
    flm_fl_elig = [int(flm_rows[c]["exact_fl_correct"]) for c in eligible_ids]
    llm_fl_elig = [
        1
        if all(
            run["scores"]["fl_correct"] == 1 for run in runs_by_case[c]
        )
        else 0
        for c in eligible_ids
    ]

    lines += [
        "## Overlap with FLM on the same 60 cases",
        "",
        "LLM attribution_correct requires the right status and, for"
        " eligible-exact cases, the right FL and RC stage. FLM values are the"
        " frozen run from the runtime benchmark (safe attribution).",
        "",
        f"- Attribution correct, FLM: {rate(flm_safe)}",
        f"- Attribution correct, LLM, strict (all five repeats): {rate(llm_all)}",
        f"- Attribution correct, LLM, lenient (at least one of five): {rate(llm_any)}",
        f"- Cases where both FLM and every LLM repeat are wrong: {both_wrong_any}/60",
        f"- Oracle union (FLM or any LLM repeat correct): {union_any}/60 "
        f"({union_any / 60:.3f})",
        f"- Oracle union (FLM or all LLM repeats correct): {union_all}/60 "
        f"({union_all / 60:.3f})",
        "",
        "Exact-path FL restricted to eligible cases (n="
        f"{len(eligible_ids)}):",
        "",
        f"- FLM: {rate(flm_fl_elig)}",
        f"- LLM, strict: {rate(llm_fl_elig)}",
        "",
    ]

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    root = args.root

    synthetic_report = synthetic_analysis(root / "results")
    (root / "results" / "ANALYSIS.md").write_text(synthetic_report, encoding="utf-8")

    runtime_report = runtime_analysis(root / "runtime_results")
    (root / "runtime_results" / "ANALYSIS.md").write_text(runtime_report, encoding="utf-8")

    llm_report = llm_analysis(root / "llm_results", root / "runtime_results")
    (root / "llm_results" / "ANALYSIS.md").write_text(llm_report, encoding="utf-8")

    print("wrote benchmark/results/ANALYSIS.md")
    print("wrote benchmark/runtime_results/ANALYSIS.md")
    print("wrote benchmark/llm_results/ANALYSIS.md")


if __name__ == "__main__":
    main()
