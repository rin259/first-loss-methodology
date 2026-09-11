# Heterogeneous executable-runtime report

- Version: `flm-runtime-benchmark-1.1.0`
- Cases: `360` (20 repetitions per runtime/profile)
- Runtimes: executable RAG, ETL, and build-system reference implementations
- Stress profiles: local fault, direct loss, partial observability, noisy probes, nonlocal side effect, and reacquisition

| Method | Safe attribution | Exact FLA | Exact RCA | Confirmed RCA | Overclaim rate |
|---|---:|---:|---:|---:|---:|
| `final_symptom` | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| `component_heuristic` | 0.000 | 0.944 | 0.000 | 0.000 | 1.000 |
| `flm_no_intervention` | 0.981 | 0.961 | 0.961 | 0.000 | 0.000 |
| `flm_no_replay` | 0.972 | 0.944 | 0.944 | 0.944 | 0.000 |
| `flm_full` | 0.981 | 0.961 | 0.961 | 0.961 | 0.000 |

Safe attribution requires an exact answer on fully observed local paths, a containing interval when the loss stage is hidden, an explicit exception for nonlocal causality, and segment-aware handling when evidence is reacquired. Confirmed RCA additionally requires fail-before/pass-after intervention evidence.

These are small executable reference runtimes, not production deployments. They reduce the role-label transfer problem in the original synthetic benchmark but do not establish population-level generality.
