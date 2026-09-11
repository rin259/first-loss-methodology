# FLM synthetic experiment report

- Benchmark version: `flm-benchmark-1.1.0`
- Master seed: `20260911`
- Frozen test cases: `1200`
- Bootstrap samples: `5000`

## Main results

| Method | FLA | ILA | RCA stage | RCA confirmed | 1-FDAR |
|---|---:|---:|---:|---:|---:|
| `final_symptom` | 0.150 | 0.450 | 0.050 | 0.050 | 0.150 |
| `component_level_rca` | 1.000 | 1.000 | 0.420 | 0.420 | 0.578 |
| `existence_only_provenance` | 1.000 | 0.450 | 0.500 | 0.500 | 1.000 |
| `pattern_rca_proxy` | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| `llm_rca_proxy_strong` | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| `llm_rca_proxy_symptom_biased` | 0.150 | 1.000 | 0.407 | 0.407 | 0.436 |
| `flm_full` | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| `flm_blind_candidate_selection` | 1.000 | 1.000 | 0.987 | 0.987 | 1.000 |
| `flm_no_first_loss_rule` | 0.150 | 1.000 | 0.050 | 0.050 | 0.150 |
| `flm_no_invariant_checking` | 1.000 | 0.450 | 0.500 | 0.500 | 1.000 |
| `flm_no_upstream_exclusion` | 1.000 | 1.000 | 0.050 | 0.050 | 0.150 |
| `flm_no_minimal_probe` | 1.000 | 1.000 | 0.432 | 0.432 | 0.644 |
| `flm_no_intervention` | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| `flm_no_independent_replay` | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

## Paired comparisons: FLM vs each baseline

| Baseline | Metric | Δ | Bootstrap 95% CI | McNemar p |
|---|---|---:|---:|---:|
| `final_symptom` | FLA | +0.850 | [+0.829, +0.870] | 1.78e-307 |
| `final_symptom` | ILA | +0.550 | [+0.521, +0.578] | 4.181e-199 |
| `final_symptom` | RCA_stage | +0.950 | [+0.938, +0.962] | <1e-300 |
| `final_symptom` | RCA_confirmed | +0.950 | [+0.938, +0.962] | <1e-300 |
| `final_symptom` | 1-FDAR | +0.850 | [+0.830, +0.869] | 1.78e-307 |
| `component_level_rca` | FLA | +0.000 | [+0.000, +0.000] | 1 |
| `component_level_rca` | ILA | +0.000 | [+0.000, +0.000] | 1 |
| `component_level_rca` | RCA_stage | +0.580 | [+0.552, +0.608] | 6.083e-210 |
| `component_level_rca` | RCA_confirmed | +0.580 | [+0.552, +0.608] | 6.083e-210 |
| `component_level_rca` | 1-FDAR | +0.422 | [+0.395, +0.452] | 4.773e-153 |
| `existence_only_provenance` | FLA | +0.000 | [+0.000, +0.000] | 1 |
| `existence_only_provenance` | ILA | +0.550 | [+0.522, +0.578] | 4.181e-199 |
| `existence_only_provenance` | RCA_stage | +0.500 | [+0.472, +0.529] | 4.82e-181 |
| `existence_only_provenance` | RCA_confirmed | +0.500 | [+0.472, +0.528] | 4.82e-181 |
| `existence_only_provenance` | 1-FDAR | +0.000 | [+0.000, +0.000] | 1 |
| `pattern_rca_proxy` | FLA | +0.000 | [+0.000, +0.000] | 1 |
| `pattern_rca_proxy` | ILA | +0.000 | [+0.000, +0.000] | 1 |
| `pattern_rca_proxy` | RCA_stage | +0.000 | [+0.000, +0.000] | 1 |
| `pattern_rca_proxy` | RCA_confirmed | +0.000 | [+0.000, +0.000] | 1 |
| `pattern_rca_proxy` | 1-FDAR | +0.000 | [+0.000, +0.000] | 1 |

## Independent-window stability

| Split | n | FLM RCA stage | FLM RCA confirmed | FLM 1-FDAR |
|---|---:|---:|---:|---:|---:|
| `replay` | 600 | 1.000 | 1.000 | 1.000 |
| `test` | 1200 | 1.000 | 1.000 | 1.000 |

### Split-level FLM vs symptom-biased LLM proxy

| Split | Metric | Δ | Bootstrap 95% CI | McNemar p |
|---|---|---:|---:|---:|
| `test` | RCA_stage | +0.593 | [+0.566, +0.622] | 9.283e-215 |
| `replay` | RCA_stage | +0.575 | [+0.535, +0.615] | 2.79e-104 |
| `test` | RCA_confirmed | +0.593 | [+0.565, +0.621] | 9.283e-215 |
| `replay` | RCA_confirmed | +0.575 | [+0.535, +0.615] | 2.79e-104 |
| `test` | 1-FDAR | +0.564 | [+0.537, +0.592] | 3.19e-204 |
| `replay` | 1-FDAR | +0.542 | [+0.502, +0.582] | 2.926e-98 |

## Ablations

| Variant | RCA stage | RCA confirmed | 1-FDAR |
|---|---:|---:|---:|---:|---:|
| `flm_no_first_loss_rule` | 0.050 | 0.050 | 0.150 |
| `flm_no_invariant_checking` | 0.500 | 0.500 | 1.000 |
| `flm_no_upstream_exclusion` | 0.050 | 0.050 | 0.150 |
| `flm_no_minimal_probe` | 0.432 | 0.432 | 0.644 |
| `flm_no_intervention` | 1.000 | 1.000 | 1.000 |
| `flm_no_independent_replay` | 1.000 | 1.000 | 1.000 |

## Notes and limits

- This is a synthetic replay benchmark designed to test attribution rules under controlled fault injection.
- `pattern_rca_proxy` is a deterministic trace-pattern baseline, not a proprietary LLM run.
- Root cause is compared at stage level; predicate-level confirmation requires the saved traces.
- Ground truth is generated from the frozen injection spec before any method runs.
- Independent-window replay uses a different seed stream but the same deterministic generator; it does not yet simulate heterogeneous runtimes.
- `flm_blind_candidate_selection` models a blinded draw from intervention candidates (85% primary candidate), not a human-subject study.
