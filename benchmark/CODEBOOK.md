# FLM benchmark codebook

## Files

- `run_experiments.py`: deterministic case generator, method runner, statistics, and report writer.
- `runtime_experiments.py`: three executable reference runtimes plus missing-observation, noisy-probe, nonlocal, and reacquisition profiles.
- `run_llm_baseline.py`: frozen real-model protocol and Responses API runner.
- `conservation_schema.py`: validates the evidence-conservation contract.
- `EXPERIMENT_MATRIX.md`: E1-E8 family sets and interpretation.
- `INCIDENT_REPLAY.md`: structured real-incident replay.
- `results/cases.jsonl`: all generated cases and frozen ground truth.
- `results/case_metrics.csv`: one row per case-method pair.
- `results/summary.json`: overall, split-level, family, domain, and statistical summaries.
- `results/REPORT.md`: human-readable report.
- `runtime_results/REPORT.md`: heterogeneous executable-runtime report.
- `llm_results/prompts.jsonl`: frozen, ground-truth-free model requests.

## Case schema

Required case fields: `case_id`, `split`, `seed`, `benchmark_version`, `domain`, `family`, `pipeline_roles`, `trace`, `ground_truth`.

Required observation fields per stage: `stage_role`, `stage_name`, `called`, `present`, `invariant_violations`, `rejection_reason`.

Required ground-truth fields: `fl`, `il`, `il_all`, `rc`, `predicate`, `components`, `blind_intervention_candidates`.

## Methods

- `final_symptom`: blames the last absent stage.
- `component_level_rca`: heuristic component scoring without the First Loss boundary.
- `existence_only_provenance`: tracks presence but ignores invariant loss.
- `pattern_rca_proxy`: deterministic trace-pattern baseline.
- `llm_rca_proxy_strong` / `llm_rca_proxy_symptom_biased`: trace-only LLM behavior proxies, not real model runs.
- `flm_full`: FLM with invariant checking, boundary, minimal probe, and intervention.
- `flm_blind_candidate_selection`: FLM when intervention targets are drawn blind from the candidate list; a synthetic candidate-selection control, not a human-subject study.
- `flm_no_*`: ablations.

## Reproduce

```bash
python3 benchmark/run_experiments.py --output-dir benchmark/results --samples 5000
python3 benchmark/conservation_schema.py benchmark/results/cases.jsonl --split test
python3 benchmark/conservation_schema.py benchmark/results/cases.jsonl --split replay
python3 benchmark/runtime_experiments.py --output-dir benchmark/runtime_results --repetitions 20
python3 -m unittest discover -s benchmark -p 'test_*.py'
```

The legacy controlled benchmark uses a paired bootstrap with one shared resampled case index for both methods. Versions before `v1.1.0` accidentally drew the two methods independently; point estimates were unaffected, but the corrected confidence intervals are the ones in the current report.

## Release boundaries

- The benchmark is synthetic and fully traceable, so its ground truth is exact but its domain realism is limited.
- LLM proxies are not proprietary or public model runs.
- Blind intervention is a simulated draw, not a human-subject study.
- Cross-domain transfer is by abstract stage roles and domain-specific names, not heterogeneous production runtimes.
- The executable runtimes are small authored systems, not production deployments.
- `llm_results/` contains the completed 300-response `glm-5-3-flash` run, including prompts, raw outputs, usage, response IDs, per-run scores, and the manifest. The API key is never persisted.
