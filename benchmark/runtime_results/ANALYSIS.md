# Runtime results: post-hoc analysis

- Runs: 360 across 18 fault configurations
- Distinct ground truths per configuration: 1-1 (each configuration replays one injected fault)

The 360 runs are therefore 18 fault configurations sampled with 20 seeded replay repetitions each. Repetitions measure robustness of attribution under re-execution (probe noise, instrumentation), not sampling of independent faults. Method comparisons below are reported at both the run level and the configuration level.

## Run-level breakdown by stress profile (3 runtimes x 20 repetitions)

Exact metrics are defined only for eligible-exact runs (profiles local, direct, noisy; n=60 per profile); the eligible count is shown per row. Bounded, exception, and reacquired profiles are scored by safe attribution only.

| Profile | Method | Safe | Exact FLA | Exact RCA | Confirmed | Overclaim |
|---|---|---:|---:|---:|---:|---:|
| local | final_symptom | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| local | component_heuristic | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 |
| local | flm_no_intervention | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 |
| local | flm_no_replay | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |
| local | flm_full | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |
| direct | final_symptom | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| direct | component_heuristic | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 |
| direct | flm_no_intervention | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 |
| direct | flm_no_replay | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |
| direct | flm_full | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |
| partial | final_symptom | 0.000 | -- | -- | -- | 1.000 |
| partial | component_heuristic | 0.000 | -- | -- | -- | 1.000 |
| partial | flm_no_intervention | 1.000 | -- | -- | -- | 0.000 |
| partial | flm_no_replay | 1.000 | -- | -- | -- | 0.000 |
| partial | flm_full | 1.000 | -- | -- | -- | 0.000 |
| noisy | final_symptom | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| noisy | component_heuristic | 0.000 | 0.833 | 0.000 | 0.000 | 0.000 |
| noisy | flm_no_intervention | 0.883 | 0.883 | 0.883 | 0.000 | 0.000 |
| noisy | flm_no_replay | 0.833 | 0.833 | 0.833 | 0.833 | 0.000 |
| noisy | flm_full | 0.883 | 0.883 | 0.883 | 0.883 | 0.000 |
| nonlocal | final_symptom | 0.000 | -- | -- | -- | 1.000 |
| nonlocal | component_heuristic | 0.000 | -- | -- | -- | 1.000 |
| nonlocal | flm_no_intervention | 1.000 | -- | -- | -- | 0.000 |
| nonlocal | flm_no_replay | 1.000 | -- | -- | -- | 0.000 |
| nonlocal | flm_full | 1.000 | -- | -- | -- | 0.000 |
| reacquired | final_symptom | 0.000 | -- | -- | -- | 1.000 |
| reacquired | component_heuristic | 0.000 | -- | -- | -- | 1.000 |
| reacquired | flm_no_intervention | 1.000 | -- | -- | -- | 0.000 |
| reacquired | flm_no_replay | 1.000 | -- | -- | -- | 0.000 |
| reacquired | flm_full | 1.000 | -- | -- | -- | 0.000 |

## Configuration-level aggregation (18 units)

| Profile | Method | Safe | Exact FLA | Exact RCA |
|---|---|---:|---:|---:|
| local | final_symptom | 0.000 | 0.000 | 0.000 |
| local | component_heuristic | 0.000 | 1.000 | 0.000 |
| local | flm_no_intervention | 1.000 | 1.000 | 1.000 |
| local | flm_no_replay | 1.000 | 1.000 | 1.000 |
| local | flm_full | 1.000 | 1.000 | 1.000 |
| direct | final_symptom | 0.000 | 0.000 | 0.000 |
| direct | component_heuristic | 0.000 | 1.000 | 0.000 |
| direct | flm_no_intervention | 1.000 | 1.000 | 1.000 |
| direct | flm_no_replay | 1.000 | 1.000 | 1.000 |
| direct | flm_full | 1.000 | 1.000 | 1.000 |
| partial | final_symptom | 0.000 | 0.000 | 0.000 |
| partial | component_heuristic | 0.000 | 0.000 | 0.000 |
| partial | flm_no_intervention | 1.000 | 0.000 | 0.000 |
| partial | flm_no_replay | 1.000 | 0.000 | 0.000 |
| partial | flm_full | 1.000 | 0.000 | 0.000 |
| noisy | final_symptom | 0.000 | 0.000 | 0.000 |
| noisy | component_heuristic | 0.000 | 0.833 | 0.000 |
| noisy | flm_no_intervention | 0.883 | 0.883 | 0.883 |
| noisy | flm_no_replay | 0.833 | 0.833 | 0.833 |
| noisy | flm_full | 0.883 | 0.883 | 0.883 |
| nonlocal | final_symptom | 0.000 | 0.000 | 0.000 |
| nonlocal | component_heuristic | 0.000 | 0.000 | 0.000 |
| nonlocal | flm_no_intervention | 1.000 | 0.000 | 0.000 |
| nonlocal | flm_no_replay | 1.000 | 0.000 | 0.000 |
| nonlocal | flm_full | 1.000 | 0.000 | 0.000 |
| reacquired | final_symptom | 0.000 | 0.000 | 0.000 |
| reacquired | component_heuristic | 0.000 | 0.000 | 0.000 |
| reacquired | flm_no_intervention | 1.000 | 0.000 | 0.000 |
| reacquired | flm_no_replay | 1.000 | 0.000 | 0.000 |
| reacquired | flm_full | 1.000 | 0.000 | 0.000 |

## Paired comparisons: FLM full vs ablations

Run-level exact McNemar p-values treat the 360 runs as paired binary outcomes; because runs of one configuration share the injected fault, a configuration-clustered bootstrap 95% CI of the mean difference is reported alongside.

| Pair | Metric | Discordant (full/abl) | Run McNemar p | Clustered 95% CI of delta |
|---|---|---|---:|---|
| flm_full vs flm_no_replay | safe | 7/4 | 0.549 | [-0.006, +0.028] |
| flm_full vs flm_no_replay | exact_fl | 7/4 | 0.549 | [-0.006, +0.028] |
| flm_full vs flm_no_intervention | safe | 0/0 | 1 | [+0.000, +0.000] |
| flm_full vs flm_no_intervention | exact_fl | 0/0 | 1 | [+0.000, +0.000] |
| flm_no_replay vs flm_no_intervention | safe | 4/7 | 0.549 | [-0.028, +0.006] |
| flm_no_replay vs flm_no_intervention | exact_fl | 4/7 | 0.549 | [-0.028, +0.006] |

## FLM error taxonomy (eligible-exact runs only)

Exact-attribution errors are only defined for eligible-exact runs (profiles local, direct, noisy; 180 of 360 runs). Runs in the bounded, exception, and reacquired profiles are scored by safe attribution and cannot produce an exact-stage error.

| Profile | Exact-FL errors (of eligible runs) |
|---|---:|
| local | 0 |
| direct | 0 |
| noisy | 7 |

| Runtime | Profile | FL prediction | Ground truth | Runs |
|---|---|---|---|---:|
| build | noisy | test | link | 2 |
| etl | noisy | sink | join | 2 |
| rag | noisy | answer | cap | 3 |

Safe-attribution failures of the full method:

- build-noisy-20283914: claimed status=exact with FL=test, ground truth FL=link; the no-replay ablation answered this case correctly
- build-noisy-20283919: claimed status=exact with FL=test, ground truth FL=link
- etl-noisy-20273916: claimed status=exact with FL=sink, ground truth FL=join
- etl-noisy-20273928: claimed status=exact with FL=sink, ground truth FL=join; the no-replay ablation answered this case correctly
- rag-noisy-20263917: claimed status=exact with FL=answer, ground truth FL=cap
- rag-noisy-20263920: claimed status=exact with FL=answer, ground truth FL=cap; the no-replay ablation answered this case correctly
- rag-noisy-20263927: claimed status=exact with FL=answer, ground truth FL=cap; the no-replay ablation answered this case correctly

## Replay ablation detail (full vs no-replay, safe attribution)

- Errors of the full method: 7; errors without replay: 10
- Cases corrected by replay: 7
- Cases where replay turned a correct answer into a wrong exact claim: 4

The four reversed cases show that majority aggregation over five noisy probe repetitions can itself manufacture an overconfident exact answer; replay is not monotone under probe noise.

## Ground-truth shapes per profile

| Profile | First Loss stage | Invariant Loss stage | Runs |
|---|---|---|---:|
| direct | cap | - | 20 |
| direct | join | - | 20 |
| direct | link | - | 20 |
| local | cap | enrich | 20 |
| local | join | map | 20 |
| local | link | resolve | 20 |
| noisy | cap | enrich | 20 |
| noisy | join | map | 20 |
| noisy | link | resolve | 20 |
| nonlocal | answer | - | 20 |
| nonlocal | sink | - | 20 |
| nonlocal | test | - | 20 |
| partial | cap | enrich | 20 |
| partial | join | map | 20 |
| partial | link | resolve | 20 |
| reacquired | map | - | 20 |
| reacquired | resolve | - | 20 |
| reacquired | retrieve | - | 20 |
