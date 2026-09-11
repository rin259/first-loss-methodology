#!/usr/bin/env python3
"""Regression tests for FLM benchmark statistics and attribution metrics."""

from __future__ import annotations

import unittest
from unittest.mock import patch

import run_experiments
import run_llm_baseline
import runtime_experiments


class FixedRandom:
    def __init__(self, seed: int) -> None:
        self.seed = seed

    def randrange(self, size: int) -> int:
        return 0

    def choices(self, population: list[float], k: int) -> list[float]:
        return [population[0]] * k


class BenchmarkTests(unittest.TestCase):
    def test_paired_bootstrap_uses_shared_indices(self) -> None:
        with patch.object(run_experiments.random, "Random", FixedRandom):
            observed, lower, upper = run_experiments.paired_bootstrap_difference(
                [1, 0], [0, 1], rng_seed=7, samples=4
            )

        self.assertEqual(observed, 0.0)
        self.assertEqual(lower, 1.0)
        self.assertEqual(upper, 1.0)

    def test_underflowed_p_value_is_reported_as_bound(self) -> None:
        self.assertEqual(run_experiments.format_p_value(0.0), "<1e-300")

    def test_full_method_has_no_downstream_attribution(self) -> None:
        case = run_experiments.generate_case("test", 4, run_experiments.MASTER_SEED)
        rows, _ = run_experiments.evaluate_cases([case])
        full_row = next(row for row in rows if row["method"] == "flm_full")

        self.assertEqual(full_row["incorrect_downstream"], 0)

    def test_runtime_benchmark_handles_bounded_and_exception_cases(self) -> None:
        partial = runtime_experiments.RagRuntime().execute("partial", 11)
        nonlocal_case = runtime_experiments.EtlRuntime().execute("nonlocal", 12)

        self.assertEqual(runtime_experiments.predict("flm_full", partial)["status"], "bounded")
        self.assertEqual(runtime_experiments.predict("flm_full", nonlocal_case)["status"], "exception")

    def test_intervention_is_required_for_confirmation(self) -> None:
        case = runtime_experiments.BuildRuntime().execute("local", 13)

        full = runtime_experiments.predict("flm_full", case)
        ablated = runtime_experiments.predict("flm_no_intervention", case)

        self.assertTrue(full["confirmed"])
        self.assertFalse(ablated["confirmed"])

    def test_llm_prompt_hides_ground_truth_and_profile(self) -> None:
        case = runtime_experiments.RagRuntime().execute("local", 14)
        prompt = run_llm_baseline.make_prompt(case)

        self.assertNotIn("ground_truth", prompt)
        self.assertNotIn('"profile": "local"', prompt)
        self.assertIn('"profile_label": "withheld"', prompt)

    def test_llm_parser_rejects_unfrozen_status_values(self) -> None:
        prediction, valid = run_llm_baseline.parse_prediction(
            '```json {"case_id":"x","status":"diagnosable","first_loss_stage":null,'
            '"invariant_loss_stage":null,"root_cause_stage":null,"rationale":"x"} ```'
        )

        self.assertFalse(valid)
        self.assertEqual(prediction["status"], "diagnosable")

    def test_llm_repeat_consistency_ignores_rationale_wording(self) -> None:
        common = {
            "case_id": "x",
            "prediction": {
                "status": "exact",
                "first_loss_stage": "cap",
                "invariant_loss_stage": "metadata",
                "root_cause_stage": "metadata",
                "rationale": "first wording",
            },
            "scores": {
                "exact": 1,
                "risky": 0,
                "status_correct": 1,
                "fl_correct": 1,
                "il_correct": 1,
                "rc_correct": 1,
                "overclaim": 0,
                "valid_schema": 1,
                "attribution_correct": 1,
            },
        }
        second = {**common, "prediction": {**common["prediction"], "rationale": "second wording"}}

        self.assertEqual(run_llm_baseline.summarize([common, second])["repeat_consistency"], 1.0)


if __name__ == "__main__":
    unittest.main()
