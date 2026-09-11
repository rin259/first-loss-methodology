#!/usr/bin/env python3
"""Validate the FLM evidence-conservation contract for replay cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_OBSERVATION_FIELDS = {
    "stage_role",
    "stage_name",
    "called",
    "present",
    "invariant_violations",
    "rejection_reason",
}

REQUIRED_CASE_FIELDS = {
    "case_id",
    "split",
    "seed",
    "benchmark_version",
    "domain",
    "family",
    "pipeline_roles",
    "trace",
    "ground_truth",
}

REQUIRED_GROUND_TRUTH_FIELDS = {"fl", "il", "rc", "predicate"}


def validate_case(case: dict[str, object], strict: bool = True) -> list[str]:
    errors: list[str] = []
    missing_case = REQUIRED_CASE_FIELDS - set(case)
    if missing_case:
        errors.append(f"case missing fields: {sorted(missing_case)}")

    trace = case.get("trace", [])
    if not isinstance(trace, list):
        errors.append("trace is not a list")
        return errors

    seen_roles: set[str] = set()
    for observation in trace:
        if not isinstance(observation, dict):
            errors.append("trace observation is not an object")
            continue
        role = observation.get("stage_role")
        if not isinstance(role, str):
            errors.append("stage_role is not a string")
        elif role in seen_roles:
            errors.append(f"duplicate stage_role: {role}")
        else:
            seen_roles.add(role)

        missing = REQUIRED_OBSERVATION_FIELDS - set(observation)
        if missing:
            errors.append(f"{role or 'unknown'} missing fields: {sorted(missing)}")

        if strict and not observation.get("called") and observation.get("present"):
            errors.append(f"{role}: uncalled stage cannot be present")

        if observation.get("present") is False and not observation.get("rejection_reason"):
            errors.append(f"{role}: absent evidence lacks rejection_reason")

    truth = case.get("ground_truth", {})
    if isinstance(truth, dict):
        missing_truth = REQUIRED_GROUND_TRUTH_FIELDS - set(truth)
        if missing_truth:
            errors.append(f"ground_truth missing fields: {sorted(missing_truth)}")
        elif truth.get("il") is not None and truth.get("il") not in seen_roles:
            errors.append("invariant loss stage is not in trace")

    return errors


def conservation_completeness(case: dict[str, object]) -> float:
    observations = case.get("trace", [])
    if not observations:
        return 0.0
    total = len(observations) * len(REQUIRED_OBSERVATION_FIELDS)
    recorded = sum(
        len(REQUIRED_OBSERVATION_FIELDS & set(observation))
        for observation in observations
        if isinstance(observation, dict)
    )
    return recorded / total


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="JSONL file containing FLM cases")
    parser.add_argument("--split", help="Validate only one split")
    parser.add_argument("--non-strict", action="store_true")
    args = parser.parse_args()

    total = 0
    errors = 0
    completeness = 0.0
    with Path(args.input).open(encoding="utf-8") as file_handle:
        for line in file_handle:
            case = json.loads(line)
            if args.split and case.get("split") != args.split:
                continue
            total += 1
            completeness += conservation_completeness(case)
            case_errors = validate_case(case, strict=not args.non_strict)
            if case_errors:
                errors += 1
                print(f"{case.get('case_id', 'unknown')}: {case_errors}")

    average_cc = completeness / total if total else 0.0
    print(
        json.dumps(
            {
                "cases": total,
                "invalid_cases": errors,
                "average_conservation_completeness": average_cc,
            },
            sort_keys=True,
        )
    )
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
