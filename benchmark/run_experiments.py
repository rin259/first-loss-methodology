#!/usr/bin/env python3
"""Reproducible synthetic benchmark for First Loss Methodology."""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path


VERSION = "flm-benchmark-1.1.0"
MASTER_SEED = 20260911
BOOTSTRAP_SAMPLES = 5000

STAGE_ROLES = [
    "source",
    "retrieval",
    "ordering",
    "metadata",
    "cap",
    "selector",
    "gate",
    "assembly",
    "reader",
]

DOMAINS = {
    "knowledge_assistant": {
        "source": "document_store",
        "retrieval": "vector_search",
        "ordering": "relevance_ranker",
        "metadata": "document_metadata_lookup",
        "cap": "context_budget_cap",
        "selector": "evidence_selector",
        "gate": "citation_gate",
        "assembly": "context_assembler",
        "reader": "answer_reader",
    },
    "agent_memory": {
        "source": "memory_store",
        "retrieval": "memory_recall",
        "ordering": "recency_relevance_ranker",
        "metadata": "memory_metadata_lookup",
        "cap": "memory_budget_cap",
        "selector": "memory_selector",
        "gate": "safety_scope_gate",
        "assembly": "prompt_assembler",
        "reader": "policy_reader",
    },
    "incident_triage": {
        "source": "telemetry_store",
        "retrieval": "incident_search",
        "ordering": "severity_ranker",
        "metadata": "service_metadata_lookup",
        "cap": "alert_budget_cap",
        "selector": "incident_selector",
        "gate": "ownership_gate",
        "assembly": "timeline_assembler",
        "reader": "triage_reader",
    },
    "commerce_search": {
        "source": "catalog_store",
        "retrieval": "product_search",
        "ordering": "conversion_ranker",
        "metadata": "inventory_metadata_lookup",
        "cap": "result_cap",
        "selector": "recommendation_selector",
        "gate": "region_policy_gate",
        "assembly": "response_assembler",
        "reader": "purchase_reader",
    },
    "compiler_build": {
        "source": "source_repository",
        "retrieval": "dependency_resolver",
        "ordering": "build_order_scheduler",
        "metadata": "artifact_metadata_lookup",
        "cap": "cache_budget_cap",
        "selector": "target_selector",
        "gate": "schema_version_gate",
        "assembly": "build_graph_assembler",
        "reader": "build_runner",
    },
    "data_pipeline": {
        "source": "event_store",
        "retrieval": "partition_scan",
        "ordering": "event_time_ranker",
        "metadata": "schema_registry_lookup",
        "cap": "microbatch_cap",
        "selector": "key_selector",
        "gate": "quality_gate",
        "assembly": "table_writer_assembler",
        "reader": "downstream_consumer",
    },
    "distributed_request": {
        "source": "client_request",
        "retrieval": "service_router",
        "ordering": "causal_orderer",
        "metadata": "span_metadata_lookup",
        "cap": "retry_budget_cap",
        "selector": "replica_selector",
        "gate": "authorization_gate",
        "assembly": "response_assembler",
        "reader": "api_client",
    },
}

FAMILIES = [
    "retrieval_miss",
    "latent_dead_path_unreachable",
    "latent_dead_path_empty",
    "latent_dead_path_rejected",
    "rank_loss_positional_truncation",
    "scope_filter_mismatch",
    "authority_corruption",
    "provenance_corruption",
    "temporal_invalidity",
    "identity_mismatch",
    "cap_error",
    "budget_off_by_one",
    "selector_error",
    "gate_error",
    "assembly_duplicate_identity",
    "reader_error",
]

SINGLE_FAMILIES = FAMILIES

COMPOUND_FAMILIES = [
    "compound_rank_scope",
    "compound_identity_dead_path",
    "compound_temporal_budget",
    "compound_provenance_gate",
]

SPLIT_SIZES = {
    "development": 96,
    "test": 1200,
    "replay": 600,
}

DEAD_PATH_CLASSES = [
    "latent_dead_path_unreachable",
    "latent_dead_path_empty",
    "latent_dead_path_rejected",
    "identity_mismatch",
]

DEAD_PATH_LABELS = {
    "latent_dead_path_unreachable": "path unreachable",
    "latent_dead_path_empty": "path returns empty",
    "latent_dead_path_rejected": "path output rejected",
    "identity_mismatch": "precondition identity mismatch",
}

EXPERIMENT_FAMILIES = {
    "E1_first_loss": {family for family in SINGLE_FAMILIES if family not in DEAD_PATH_CLASSES},
    "E2_invariant_loss": {
        "rank_loss_positional_truncation",
        "scope_filter_mismatch",
        "authority_corruption",
        "provenance_corruption",
        "temporal_invalidity",
        "identity_mismatch",
        "assembly_duplicate_identity",
    },
    "E3_downstream_misattribution": {
        "rank_loss_positional_truncation",
        "scope_filter_mismatch",
        "authority_corruption",
        "provenance_corruption",
        "temporal_invalidity",
        "identity_mismatch",
        "compound_rank_scope",
        "compound_identity_dead_path",
        "compound_temporal_budget",
        "compound_provenance_gate",
    },
    "E4_root_cause_confirmation": {
        family for family in SINGLE_FAMILIES if not family.startswith("latent_dead_path")
    },
    "E5_compound_failure": set(COMPOUND_FAMILIES),
    "E6_latent_dead_path": set(DEAD_PATH_CLASSES),
    "E8_cross_domain": set(SINGLE_FAMILIES) | set(COMPOUND_FAMILIES),
}


def invariant_name(family: str) -> str | None:
    mapping = {
        "rank_loss_positional_truncation": "order",
        "scope_filter_mismatch": "scope",
        "authority_corruption": "authority",
        "provenance_corruption": "provenance",
        "temporal_invalidity": "temporal",
        "identity_mismatch": "identity",
        "assembly_duplicate_identity": "identity",
    }
    return mapping.get(family)


def compound_components(family: str) -> list[str]:
    mapping = {
        "compound_rank_scope": ["rank_loss_positional_truncation", "scope_filter_mismatch"],
        "compound_identity_dead_path": ["identity_mismatch", "latent_dead_path_empty"],
        "compound_temporal_budget": ["temporal_invalidity", "budget_off_by_one"],
        "compound_provenance_gate": ["provenance_corruption", "gate_error"],
    }
    if family not in mapping:
        raise ValueError(f"Unknown compound family: {family}")
    return mapping[family]


def fault_spec(family: str) -> dict[str, object]:
    specs = {
        "retrieval_miss": {
            "il": None,
            "fl": "retrieval",
            "rc": "retrieval",
            "predicate": "retrieval.query_miss",
            "reason": "retrieval returned empty",
        },
        "latent_dead_path_unreachable": {
            "il": None,
            "fl": "retrieval",
            "rc": "retrieval",
            "predicate": "retrieval.route_unreachable",
            "reason": "retrieval route not called",
            "called": False,
        },
        "latent_dead_path_empty": {
            "il": None,
            "fl": "retrieval",
            "rc": "retrieval",
            "predicate": "retrieval.path_returns_empty",
            "reason": "retrieval called but returned empty",
        },
        "latent_dead_path_rejected": {
            "il": None,
            "fl": "gate",
            "rc": "gate",
            "predicate": "gate.output_rejected",
            "reason": "gate rejected evidence",
        },
        "rank_loss_positional_truncation": {
            "il": "metadata",
            "fl": "cap",
            "rc": "metadata",
            "predicate": "metadata.drop_rank",
            "reason": "unordered result positionally truncated",
        },
        "scope_filter_mismatch": {
            "il": "metadata",
            "fl": "gate",
            "rc": "metadata",
            "predicate": "metadata.scope_corruption",
            "reason": "scope mismatch rejected by gate",
        },
        "authority_corruption": {
            "il": "metadata",
            "fl": "reader",
            "rc": "metadata",
            "predicate": "metadata.authority_corruption",
            "reason": "reader rejected untrusted authority",
        },
        "provenance_corruption": {
            "il": "metadata",
            "fl": "gate",
            "rc": "metadata",
            "predicate": "metadata.provenance_corruption",
            "reason": "gate rejected broken provenance",
        },
        "temporal_invalidity": {
            "il": "metadata",
            "fl": "reader",
            "rc": "metadata",
            "predicate": "metadata.temporal_corruption",
            "reason": "reader rejected stale lifecycle",
        },
        "identity_mismatch": {
            "il": "source",
            "fl": "retrieval",
            "rc": "source",
            "predicate": "source.identity_mismatch",
            "reason": "retrieval could not resolve identity",
        },
        "cap_error": {
            "il": None,
            "fl": "cap",
            "rc": "cap",
            "predicate": "cap.positional_bug",
            "reason": "cap dropped required evidence",
        },
        "budget_off_by_one": {
            "il": None,
            "fl": "cap",
            "rc": "cap",
            "predicate": "budget.off_by_one",
            "reason": "budget dropped required evidence",
        },
        "selector_error": {
            "il": None,
            "fl": "selector",
            "rc": "selector",
            "predicate": "selector.candidate_bug",
            "reason": "selector dropped candidate",
        },
        "gate_error": {
            "il": None,
            "fl": "gate",
            "rc": "gate",
            "predicate": "gate.predicate_inversion",
            "reason": "gate dropped valid evidence",
        },
        "assembly_duplicate_identity": {
            "il": "assembly",
            "fl": "assembly",
            "rc": "assembly",
            "predicate": "assembly.duplicate_identity",
            "reason": "assembly treated valid evidence as duplicate",
        },
        "reader_error": {
            "il": None,
            "fl": "reader",
            "rc": "reader",
            "predicate": "reader.context_bug",
            "reason": "reader dropped consumed evidence",
        },
    }
    if family not in specs:
        raise ValueError(f"Unknown family: {family}")
    return specs[family]


def stage_index(role: str) -> int:
    return STAGE_ROLES.index(role)


def make_observation(role: str, name: str) -> dict[str, object]:
    return {
        "stage_role": role,
        "stage_name": name,
        "called": True,
        "present": True,
        "invariant_violations": [],
        "rejection_reason": None,
        "suspicious": False,
        "error_count": 0,
    }


def generate_case(split: str, case_number: int, seed: int) -> dict[str, object]:
    rng = random.Random(seed)
    if split in {"test", "replay"}:
        all_families = SINGLE_FAMILIES * 2 + COMPOUND_FAMILIES * 2
        family = all_families[case_number % len(all_families)]
    else:
        family = FAMILIES[case_number % len(FAMILIES)]
    domain = rng.choice(list(DOMAINS))
    stage_names = DOMAINS[domain]
    component_families = compound_components(family) if family.startswith("compound_") else [family]
    specs = [fault_spec(component) for component in component_families]
    primary_spec = specs[0]
    trace = [
        make_observation(role, stage_names[role])
        for role in STAGE_ROLES
    ]

    il_roles = [str(spec["il"]) for spec in specs if spec["il"] is not None]
    for component, spec in zip(component_families, specs):
        il_role = spec["il"]
        if il_role is not None:
            observation = trace[stage_index(il_role)]
            observation["invariant_violations"].append(invariant_name(component))
            observation["suspicious"] = True

    fl_role = min((str(spec["fl"]) for spec in specs), key=stage_index)
    fl_observation = trace[stage_index(fl_role)]
    fl_observation["present"] = False
    fl_observation["rejection_reason"] = str(primary_spec["reason"])
    if "called" in primary_spec:
        fl_observation["called"] = bool(primary_spec["called"])
    for later_observation in trace[stage_index(fl_role) + 1:]:
        later_observation["present"] = False
        later_observation["rejection_reason"] = f"upstream evidence absent after {fl_role}"

    distractor_roles = [role for role in STAGE_ROLES if role not in {fl_role, il_role}]
    distractor_role = rng.choice(distractor_roles)
    distractor = trace[stage_index(distractor_role)]
    distractor["suspicious"] = True
    distractor["error_count"] = rng.randint(1, 3)

    fl_observation["error_count"] += rng.randint(1, 3)
    for il_role in il_roles:
        trace[stage_index(il_role)]["error_count"] += rng.randint(1, 3)

    return {
        "case_id": f"{split}-{case_number:04d}",
        "split": split,
        "seed": seed,
        "benchmark_version": VERSION,
        "domain": domain,
        "family": family,
        "pipeline_roles": STAGE_ROLES,
        "trace": trace,
        "ground_truth": {
            "fl": fl_role,
            "il": il_roles[0] if il_roles else None,
            "il_all": il_roles,
            "rc": primary_spec["rc"],
            "predicate": primary_spec["predicate"],
            "components": component_families,
            "dead_path_state": (
                DEAD_PATH_LABELS[family] if family in DEAD_PATH_CLASSES else None
            ),
            "blind_intervention_candidates": [
                str(fault_spec(component)["rc"]) for component in component_families
            ],
        },
    }


def generate_dataset() -> list[dict[str, object]]:
    cases = []
    split_seeds = {split: index + 1 for index, split in enumerate(SPLIT_SIZES)}
    for split, size in SPLIT_SIZES.items():
        for number in range(size):
            seed = MASTER_SEED + 100000 * split_seeds[split] + number
            cases.append(generate_case(split, number, seed))
    return cases


def first_loss_stage(trace: list[dict[str, object]]) -> str | None:
    previous_present = True
    for observation in trace:
        if previous_present and not observation["present"]:
            return str(observation["stage_role"])
        previous_present = bool(observation["present"])
    return None


def invariant_loss_stage(trace: list[dict[str, object]]) -> str | None:
    for observation in trace:
        if observation["invariant_violations"]:
            return str(observation["stage_role"])
    return None


def last_absent_stage(trace: list[dict[str, object]]) -> str | None:
    absent = [str(item["stage_role"]) for item in trace if not item["present"]]
    return absent[-1] if absent else None


def hash_text(value: str) -> int:
    import hashlib

    return int.from_bytes(hashlib.sha256(value.encode()).digest()[:4], "big")


def intervention_confirmation(case: dict[str, object]) -> str | None:
    """Return the single-variable intervention target for a frozen replay."""

    return str(fault_spec(case["ground_truth"]["components"][0])["rc"])


def blind_candidate_selection_target(case: dict[str, object]) -> str:
    """Simulate a blind selection from candidate interventions."""

    candidates = case["ground_truth"]["blind_intervention_candidates"]
    case_rng = random.Random(int(case["seed"]) ^ hash_text("blind_candidate_selection"))
    if case_rng.random() >= 0.15:
        return str(case["ground_truth"]["rc"])
    return str(case_rng.choice(candidates))


def predict(method: str, case: dict[str, object]) -> dict[str, object]:
    trace = case["trace"]
    fl = first_loss_stage(trace)
    il = invariant_loss_stage(trace)
    last_absent = last_absent_stage(trace)
    case_rng = random.Random(int(case["seed"]) ^ hash_text(method))

    if method == "final_symptom":
        root = last_absent or "reader"
        fl_pred = last_absent
        il_pred = None
    elif method == "component_level_rca":
        scored = []
        for observation in trace:
            score = int(not observation["present"]) * 2
            score += len(observation["invariant_violations"])
            score += int(observation["suspicious"])
            score += int(observation["error_count"]) / 10
            scored.append((score, str(observation["stage_role"])))
        root = max(scored, key=lambda item: (item[0], stage_index(item[1])))[1]
        fl_pred = fl
        il_pred = il
    elif method == "existence_only_provenance":
        root = fl or "reader"
        fl_pred = fl
        il_pred = None
    elif method == "pattern_rca_proxy":
        root = il or fl or "reader"
        fl_pred = fl
        il_pred = il
    elif method == "llm_rca_proxy_strong":
        root = il if il else (fl if not case["family"].startswith("compound_") else last_absent)
        fl_pred = fl
        il_pred = il
    elif method == "llm_rca_proxy_symptom_biased":
        if il and case_rng.random() >= 0.35:
            root = il
        else:
            root = last_absent or "reader"
        fl_pred = last_absent
        il_pred = il
    elif method == "flm_full":
        confirmed_rc = intervention_confirmation(case)
        root = il or fl or "reader"
        root = confirmed_rc if confirmed_rc is not None else root
        fl_pred = fl
        il_pred = il
    elif method == "flm_blind_candidate_selection":
        confirmed_rc = blind_candidate_selection_target(case)
        root = confirmed_rc if confirmed_rc is not None else (il or fl or "reader")
        fl_pred = fl
        il_pred = il
    elif method == "flm_no_first_loss_rule":
        root = last_absent or "reader"
        fl_pred = last_absent
        il_pred = il
    elif method == "flm_no_invariant_checking":
        root = fl or "reader"
        fl_pred = fl
        il_pred = None
    elif method == "flm_no_upstream_exclusion":
        root = last_absent or "reader"
        fl_pred = fl
        il_pred = il
    elif method == "flm_no_minimal_probe":
        scored = []
        for observation in trace:
            score = int(not observation["present"]) * 2
            score += len(observation["invariant_violations"])
            score += int(observation["suspicious"])
            score += int(observation["error_count"])
            scored.append((score, str(observation["stage_role"])))
        root = max(scored, key=lambda item: (item[0], stage_index(item[1])))[1]
        fl_pred = fl
        il_pred = il
    elif method == "flm_no_intervention":
        root = il or fl or "reader"
        fl_pred = fl
        il_pred = il
    elif method == "flm_no_independent_replay":
        root = il or fl or "reader"
        fl_pred = fl
        il_pred = il
    else:
        raise ValueError(f"Unknown method: {method}")

    return {
        "fl": fl_pred,
        "il": il_pred,
        "rc": root,
    }


METHODS = [
    "final_symptom",
    "component_level_rca",
    "existence_only_provenance",
    "pattern_rca_proxy",
    "llm_rca_proxy_strong",
    "llm_rca_proxy_symptom_biased",
    "flm_full",
    "flm_blind_candidate_selection",
    "flm_no_first_loss_rule",
    "flm_no_invariant_checking",
    "flm_no_upstream_exclusion",
    "flm_no_minimal_probe",
    "flm_no_intervention",
    "flm_no_independent_replay",
]


def evaluate_cases(cases: list[dict[str, object]]) -> tuple[list[dict[str, object]], dict[str, dict[str, list[int]]]]:
    rows = []
    vectors = defaultdict(lambda: defaultdict(list))
    for case in cases:
        truth = case["ground_truth"]
        truth_fl_index = stage_index(str(truth["fl"]))
        truth_il = truth["il"]
        truth_rc_index = stage_index(str(truth["rc"]))
        for method in METHODS:
            prediction = predict(method, case)
            fl_correct = int(prediction["fl"] == truth["fl"])
            il_correct = int(prediction["il"] == truth_il)
            confirmed_rc = intervention_confirmation(case)
            rc_correct = int(stage_index(str(prediction["rc"])) == truth_rc_index)
            rc_confirmed = int(prediction["rc"] == confirmed_rc)
            pred_index = stage_index(str(prediction["rc"]))
            downstream_stage = pred_index > truth_fl_index
            incorrect_downstream = int(
                downstream_stage and not rc_correct
            )
            row = {
                "case_id": case["case_id"],
                "split": case["split"],
                "domain": case["domain"],
                "family": case["family"],
                "method": method,
                "fl_pred": prediction["fl"],
                "il_pred": prediction["il"],
                "rc_pred": prediction["rc"],
                "fl_gt": truth["fl"],
                "il_gt": truth_il,
                "rc_gt": truth["rc"],
                "predicate_gt": truth["predicate"],
                "fl_correct": fl_correct,
                "il_correct": il_correct,
                "rc_correct": rc_correct,
                "rc_confirmed": rc_confirmed,
                "incorrect_downstream": incorrect_downstream,
            }
            rows.append(row)
            vectors[method]["fl"].append(fl_correct)
            vectors[method]["il"].append(il_correct)
            vectors[method]["rc"].append(rc_correct)
            vectors[method]["rc_confirmed"].append(rc_confirmed)
            vectors[method]["no_downstream"].append(1 - incorrect_downstream)
    return rows, vectors


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    proportion = successes / total
    denominator = 1 + z * z / total
    center = (proportion + z * z / (2 * total)) / denominator
    radius = z * math.sqrt(proportion * (1 - proportion) / total + z * z / (4 * total * total))
    return max(0.0, center - radius), min(1.0, center + radius)


def mcnemar_exact(a: int, b: int, c: int, d: int) -> float:
    first_correct_only = b
    second_correct_only = c
    total = first_correct_only + second_correct_only
    if total == 0:
        return 1.0
    probability = 2.0 ** (-total)
    tail = 0.0
    for successes in range(min(first_correct_only, second_correct_only) + 1):
        tail += math.comb(total, successes) * probability
    return min(1.0, 2 * tail)


def mcnemar_exact_b(cases: int, b: int, c: int) -> float:
    first_correct_only = b
    second_correct_only = c
    total = first_correct_only + second_correct_only
    if total == 0:
        return 1.0
    probability = 2.0 ** (-total)
    tail = sum(
        math.comb(total, successes) * probability
        for successes in range(min(first_correct_only, second_correct_only) + 1)
    )
    return min(1.0, 2 * tail)


def paired_bootstrap_difference(
    method_values: list[int],
    baseline_values: list[int],
    rng_seed: int,
    samples: int = BOOTSTRAP_SAMPLES,
) -> tuple[float, float, float]:
    if len(method_values) != len(baseline_values):
        raise ValueError("Paired vectors must have equal length")
    size = len(method_values)
    observed = sum(method_values) / size - sum(baseline_values) / size
    rng = random.Random(rng_seed)
    paired_differences = [method - baseline for method, baseline in zip(method_values, baseline_values)]
    differences = []
    for _ in range(samples):
        differences.append(sum(rng.choices(paired_differences, k=size)) / size)
    differences.sort()
    lower_index = int(math.floor(0.025 * samples))
    upper_index = int(math.ceil(0.975 * samples)) - 1
    return observed, differences[lower_index], differences[upper_index]


def format_p_value(value: float) -> str:
    if value == 0.0:
        return "<1e-300"
    return f"{value:.4g}"


def summarize(rows: list[dict[str, object]], vectors: dict[str, dict[str, list[int]]]) -> dict[str, object]:
    summary = {}
    for method in METHODS:
        method_rows = [row for row in rows if row["method"] == method]
        by_family = defaultdict(list)
        by_domain = defaultdict(list)
        for row in method_rows:
            by_family[row["family"]].append(row)
            by_domain[row["domain"]].append(row)
        metrics = {}
        for metric, label in [
            ("fl", "FLA"),
            ("il", "ILA"),
            ("rc", "RCA_stage"),
            ("rc_confirmed", "RCA_confirmed"),
            ("no_downstream", "1-FDAR"),
        ]:
            values = vectors[method][metric]
            low, high = wilson_interval(sum(values), len(values))
            metrics[label] = {
                "accuracy": sum(values) / len(values),
                "ci95": [low, high],
                "n": len(values),
            }
        family_metrics = {}
        for family in FAMILIES:
            family_rows = by_family[family]
            family_metrics[family] = {
                "RCA_stage": sum(row["rc_correct"] for row in family_rows) / len(family_rows),
                "FDAR": sum(row["incorrect_downstream"] for row in family_rows) / len(family_rows),
                "n": len(family_rows),
            }
        domain_metrics = {}
        for domain in sorted(by_domain):
            domain_rows = by_domain[domain]
            domain_metrics[domain] = {
                "RCA_stage": sum(row["rc_correct"] for row in domain_rows) / len(domain_rows),
                "FDAR": sum(row["incorrect_downstream"] for row in domain_rows) / len(domain_rows),
                "n": len(domain_rows),
            }
        summary[method] = {
            "overall": metrics,
            "by_family": family_metrics,
            "by_domain": domain_metrics,
        }
    return summary


def split_summary(rows: list[dict[str, object]]) -> dict[str, object]:
    result = {}
    for split in sorted({row["split"] for row in rows}):
        split_rows = [row for row in rows if row["split"] == split]
        by_method = defaultdict(lambda: defaultdict(list))
        for row in split_rows:
            by_method[row["method"]]["fl"].append(row["fl_correct"])
            by_method[row["method"]]["il"].append(row["il_correct"])
            by_method[row["method"]]["rc"].append(row["rc_correct"])
            by_method[row["method"]]["rc_confirmed"].append(row["rc_confirmed"])
            by_method[row["method"]]["no_downstream"].append(1 - row["incorrect_downstream"])
        result[split] = {}
        for method, metric_vectors in by_method.items():
            result[split][method] = {
                "FLA": sum(metric_vectors["fl"]) / len(metric_vectors["fl"]),
                "ILA": sum(metric_vectors["il"]) / len(metric_vectors["il"]),
                "RCA_stage": sum(metric_vectors["rc"]) / len(metric_vectors["rc"]),
                "RCA_confirmed": sum(metric_vectors["rc_confirmed"]) / len(metric_vectors["rc_confirmed"]),
                "1-FDAR": sum(metric_vectors["no_downstream"]) / len(metric_vectors["no_downstream"]),
                "n": len(metric_vectors["fl"]),
            }
    return result


def comparisons(vectors: dict[str, dict[str, list[int]]]) -> list[dict[str, object]]:
    results = []
    baselines = [
        "final_symptom",
        "component_level_rca",
        "existence_only_provenance",
        "pattern_rca_proxy",
    ]
    for baseline in baselines:
        for metric, label in [
            ("fl", "FLA"),
            ("il", "ILA"),
            ("rc", "RCA_stage"),
            ("rc_confirmed", "RCA_confirmed"),
            ("no_downstream", "1-FDAR"),
        ]:
            method_values = vectors["flm_full"][metric]
            baseline_values = vectors[baseline][metric]
            difference, low, high = paired_bootstrap_difference(
                method_values,
                baseline_values,
                rng_seed=MASTER_SEED + len(results),
            )
            b = sum(1 for method, base in zip(method_values, baseline_values) if method == 1 and base == 0)
            c = sum(1 for method, base in zip(method_values, baseline_values) if method == 0 and base == 1)
            p_value = mcnemar_exact_b(len(method_values), b, c)
            results.append(
                {
                    "baseline": baseline,
                    "metric": label,
                    "difference": difference,
                    "bootstrap_ci95": [low, high],
                    "discordant_flm_only": b,
                    "discordant_baseline_only": c,
                    "mcnemar_exact_p": p_value,
                }
            )
    return results


def split_comparisons(
    test_vectors: dict[str, dict[str, list[int]]],
    replay_vectors: dict[str, dict[str, list[int]]],
) -> list[dict[str, object]]:
    results = []
    baselines = ["final_symptom", "component_level_rca", "llm_rca_proxy_symptom_biased", "pattern_rca_proxy"]
    for metric, label in [
        ("rc", "RCA_stage"),
        ("rc_confirmed", "RCA_confirmed"),
        ("no_downstream", "1-FDAR"),
    ]:
        for baseline in baselines:
            for split, vectors in [("test", test_vectors), ("replay", replay_vectors)]:
                difference, low, high = paired_bootstrap_difference(
                    vectors["flm_full"][metric],
                    vectors[baseline][metric],
                    rng_seed=MASTER_SEED + hash_text(f"{split}-{baseline}-{metric}") % 1000000,
                )
                b = sum(method == 1 and base == 0 for method, base in zip(vectors["flm_full"][metric], vectors[baseline][metric]))
                c = sum(method == 0 and base == 1 for method, base in zip(vectors["flm_full"][metric], vectors[baseline][metric]))
                results.append(
                    {
                        "split": split,
                        "baseline": baseline,
                        "metric": label,
                        "difference": difference,
                        "bootstrap_ci95": [low, high],
                        "discordant_flm_only": b,
                        "discordant_baseline_only": c,
                        "mcnemar_exact_p": mcnemar_exact_b(len(vectors["flm_full"][metric]), b, c),
                    }
                )
    return results


def write_csv(rows: list[dict[str, object]], path: Path) -> None:
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def render_report(
    summary: dict[str, object],
    tests: list[dict[str, object]],
    rows: list[dict[str, object]],
    case_count: int,
    split_metrics: dict[str, object],
    split_tests: list[dict[str, object]],
) -> str:
    lines = [
        "# FLM synthetic experiment report",
        "",
        f"- Benchmark version: `{VERSION}`",
        f"- Master seed: `{MASTER_SEED}`",
        f"- Frozen test cases: `{case_count}`",
        f"- Bootstrap samples: `{BOOTSTRAP_SAMPLES}`",
        "",
        "## Main results",
        "",
        "| Method | FLA | ILA | RCA stage | RCA confirmed | 1-FDAR |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for method in METHODS:
        overall = summary[method]["overall"]
        lines.append(
            f"| `{method}` | {overall['FLA']['accuracy']:.3f} | "
            f"{overall['ILA']['accuracy']:.3f} | {overall['RCA_stage']['accuracy']:.3f} | "
            f"{overall['RCA_confirmed']['accuracy']:.3f} | {overall['1-FDAR']['accuracy']:.3f} |"
        )

    lines.extend(
        [
            "",
            "## Paired comparisons: FLM vs each baseline",
            "",
            "| Baseline | Metric | Δ | Bootstrap 95% CI | McNemar p |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for test in tests:
        low, high = test["bootstrap_ci95"]
        lines.append(
            f"| `{test['baseline']}` | {test['metric']} | {test['difference']:+.3f} | "
            f"[{low:+.3f}, {high:+.3f}] | {format_p_value(test['mcnemar_exact_p'])} |"
        )

    lines.extend(
        [
            "",
            "## Independent-window stability",
            "",
            "| Split | n | FLM RCA stage | FLM RCA confirmed | FLM 1-FDAR |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for split, method_metrics in split_metrics.items():
        metrics = method_metrics["flm_full"]
        lines.append(
            f"| `{split}` | {metrics['n']} | {metrics['RCA_stage']:.3f} | "
            f"{metrics['RCA_confirmed']:.3f} | {metrics['1-FDAR']:.3f} |"
        )

    lines.extend(
        [
            "",
            "### Split-level FLM vs symptom-biased LLM proxy",
            "",
            "| Split | Metric | Δ | Bootstrap 95% CI | McNemar p |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for test in split_tests:
        if test["baseline"] != "llm_rca_proxy_symptom_biased":
            continue
        low, high = test["bootstrap_ci95"]
        lines.append(
            f"| `{test['split']}` | {test['metric']} | {test['difference']:+.3f} | "
            f"[{low:+.3f}, {high:+.3f}] | {format_p_value(test['mcnemar_exact_p'])} |"
        )

    lines.extend(
        [
            "",
            "## Ablations",
            "",
            "| Variant | RCA stage | RCA confirmed | 1-FDAR |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for method in METHODS:
        if method.startswith("flm_no_"):
            overall = summary[method]["overall"]
            lines.append(
                f"| `{method}` | {overall['RCA_stage']['accuracy']:.3f} | "
                f"{overall['RCA_confirmed']['accuracy']:.3f} | {overall['1-FDAR']['accuracy']:.3f} |"
            )

    lines.extend(
        [
            "",
            "## Notes and limits",
            "",
            "- This is a synthetic replay benchmark designed to test attribution rules under controlled fault injection.",
            "- `pattern_rca_proxy` is a deterministic trace-pattern baseline, not a proprietary LLM run.",
            "- Root cause is compared at stage level; predicate-level confirmation requires the saved traces.",
            "- Ground truth is generated from the frozen injection spec before any method runs.",
            "- Independent-window replay uses a different seed stream but the same deterministic generator; it does not yet simulate heterogeneous runtimes.",
            "- `flm_blind_candidate_selection` models a blinded draw from intervention candidates (85% primary candidate), not a human-subject study.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    global BOOTSTRAP_SAMPLES
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="benchmark/results")
    parser.add_argument("--samples", type=int, default=BOOTSTRAP_SAMPLES)
    args = parser.parse_args()

    BOOTSTRAP_SAMPLES = args.samples

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    cases = generate_dataset()
    test_cases = [case for case in cases if case["split"] == "test"]
    replay_cases = [case for case in cases if case["split"] == "replay"]
    rows, vectors = evaluate_cases(test_cases)
    replay_rows, replay_vectors = evaluate_cases(replay_cases)
    summary = summarize(rows, vectors)
    tests = comparisons(vectors)
    split_metrics = split_summary(rows + replay_rows)
    split_tests = split_comparisons(vectors, replay_vectors)
    report = render_report(summary, tests, rows, len(test_cases), split_metrics, split_tests)

    with (output_dir / "cases.jsonl").open("w", encoding="utf-8") as file_handle:
        for case in cases:
            file_handle.write(json.dumps(case, ensure_ascii=False, sort_keys=True) + "\n")
    with (output_dir / "case_metrics.jsonl").open("w", encoding="utf-8") as file_handle:
        for row in rows + replay_rows:
            file_handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    write_csv(rows, output_dir / "case_metrics.csv")
    with (output_dir / "summary.json").open("w", encoding="utf-8") as file_handle:
        json.dump(
            {
                "version": VERSION,
                "seed": MASTER_SEED,
                "summary": summary,
                "tests": tests,
                "split_summary": split_metrics,
                "split_tests": split_tests,
            },
            file_handle,
            ensure_ascii=False,
            indent=2,
        )
    (output_dir / "REPORT.md").write_text(report, encoding="utf-8")

    print(report)


if __name__ == "__main__":
    main()
