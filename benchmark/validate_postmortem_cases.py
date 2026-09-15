#!/usr/bin/env python3
"""Validate the public postmortem encoding corpus.

Checks structural well-formedness of benchmark/public_postmortem_cases.jsonl:
required fields, status vocabulary, stage references, boundary citations, and
non-empty candidate sets. These encodings carry no ground truth, so the
validator enforces form, not outcomes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED_FIELDS = [
    "case_id",
    "operator",
    "incident_date",
    "source_url",
    "evidence_item",
    "stages",
    "boundaries",
    "flm_output",
    "postmortem_reference",
    "notes",
]

STATUS_VOCABULARY = {"exact", "bounded", "exception", "reacquisition", "acquisition"}
P_VOCABULARY = {"0", "1", "?"}


def validate_case(record: dict[str, object], errors: list[str]) -> None:
    case_id = str(record.get("case_id", f"<record {errors and len(errors)}>"))
    for field in REQUIRED_FIELDS:
        if field not in record:
            errors.append(f"{case_id}: missing required field '{field}'")

    stages = record.get("stages")
    if not isinstance(stages, list) or len(stages) < 3:
        errors.append(f"{case_id}: 'stages' must list at least three transformations")
        stages = []

    boundaries = record.get("boundaries")
    if not isinstance(boundaries, list) or not boundaries:
        errors.append(f"{case_id}: 'boundaries' must be a non-empty list")
        boundaries = []
    for index, boundary in enumerate(boundaries):
        if not isinstance(boundary, dict):
            errors.append(f"{case_id}: boundary {index} is not an object")
            continue
        for field in ("stage", "P", "citation", "note"):
            if not boundary.get(field):
                errors.append(f"{case_id}: boundary {index} missing '{field}'")
        p_value = str(boundary.get("P", ""))
        if p_value not in P_VOCABULARY:
            errors.append(f"{case_id}: boundary {index} has invalid P value {p_value!r}")
        stage = str(boundary.get("stage", ""))
        if stages and stage not in stages:
            errors.append(f"{case_id}: boundary {index} references unknown stage {stage!r}")

    source_url = str(record.get("source_url", ""))
    if not source_url.startswith(("http://", "https://")):
        errors.append(f"{case_id}: 'source_url' must be an absolute URL")

    flm = record.get("flm_output")
    if not isinstance(flm, dict):
        errors.append(f"{case_id}: 'flm_output' must be an object")
        return
    status = flm.get("status")
    if status not in STATUS_VOCABULARY:
        errors.append(f"{case_id}: status {status!r} not in {sorted(STATUS_VOCABULARY)}")

    for key in ("invariant_loss", "first_loss"):
        value = flm.get(key)
        if value is not None and stages and value not in stages:
            errors.append(f"{case_id}: {key} {value!r} is not a declared stage")

    bounded = flm.get("bounded_interval")
    if bounded is not None and not isinstance(bounded, list):
        errors.append(f"{case_id}: 'bounded_interval' must be a list of two stages or null")

    candidates = flm.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        errors.append(f"{case_id}: candidate set must be non-empty (bounded attribution)")

    for key in ("nonlocal", "reacquisition"):
        if not isinstance(flm.get(key), bool):
            errors.append(f"{case_id}: '{key}' must be a boolean")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <cases.jsonl>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"error: {path} does not exist", file=sys.stderr)
        return 2

    errors: list[str] = []
    count = 0
    seen_ids: set[str] = set()
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            count += 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_number}: invalid JSON ({exc})")
                continue
            case_id = str(record.get("case_id", f"line {line_number}"))
            if case_id in seen_ids:
                errors.append(f"{case_id}: duplicate case_id")
            seen_ids.add(case_id)
            validate_case(record, errors)

    if count == 0:
        errors.append("corpus is empty")

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"OK: {count} public postmortem encodings validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
