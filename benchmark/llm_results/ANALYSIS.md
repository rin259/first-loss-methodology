# Real-model baseline: post-hoc analysis

All intervals are Wilson score 95% intervals. Runs are the unit for per-run metrics; cases (n=60) are the unit for agreement.

## Stratification allocation

Round-robin sampling over 18 runtime/profile strata yields 60 cases: six strata contribute 4 cases and twelve strata contribute 3.

| Runtime | Profile | Cases |
|---|---|---:|
| build | direct | 4 |
| build | local | 4 |
| build | noisy | 4 |
| build | nonlocal | 4 |
| build | partial | 4 |
| build | reacquired | 4 |
| etl | direct | 3 |
| etl | local | 3 |
| etl | noisy | 3 |
| etl | nonlocal | 3 |
| etl | partial | 3 |
| etl | reacquired | 3 |
| rag | direct | 3 |
| rag | local | 3 |
| rag | noisy | 3 |
| rag | nonlocal | 3 |
| rag | partial | 3 |
| rag | reacquired | 3 |

## Headline metrics with Wilson 95% intervals

Per-run metrics use all 300 runs; exact-path metrics are gated on eligible-exact runs (profiles local, direct, noisy; n=150); the overclaim denominator is risky runs (n=150).

| Metric | Estimate [95% CI] |
|---|---|
| Attribution accuracy (n=300) | 0.920 [0.884, 0.946] |
| Exact-path FLA (n=150) | 0.987 [0.953, 0.996] |
| Exact-path ILA (n=150) | 0.813 [0.743, 0.868] |
| Exact-path RCA (n=150) | 0.973 [0.933, 0.990] |
| Status accuracy (n=300) | 0.927 [0.891, 0.951] |
| Overclaim rate (denominator: risky runs = 150) | 0.047 [0.023, 0.093] |
| Schema adherence (n=300) | 1.000 [0.987, 1.000] |

## Repeat agreement

- Cases with five identical answers: 12/60 (0.200)
- Distribution of distinct answers per case (of 5 repeats): 1 distinct: 12, 2 distinct: 25, 3 distinct: 18, 4 distinct: 5

Exploratory (not preregistered): majority-vote root-cause accuracy across the five repeats is 49/60 (0.817).

## Invariant Loss failures (eligible-exact runs)

- Runs with an IL error: 28/150; cases affected: 10 of the eligible cases
- Of these, runs that hallucinate an IL stage where ground truth is none: 28

| Runtime | Profile | Predicted IL | Ground-truth IL | Runs |
|---|---|---|---|---:|
| build | direct | link | - | 7 |
| etl | direct | join | - | 10 |
| rag | direct | answer | - | 2 |
| rag | direct | cap | - | 9 |

## Overlap with FLM on the same 60 cases

LLM attribution_correct requires the right status and, for eligible-exact cases, the right FL and RC stage. FLM values are the frozen run from the runtime benchmark (safe attribution).

- Attribution correct, FLM: 0.983 [0.911, 0.997]
- Attribution correct, LLM, strict (all five repeats): 0.750 [0.628, 0.842]
- Attribution correct, LLM, lenient (at least one of five): 1.000 [0.940, 1.000]
- Cases where both FLM and every LLM repeat are wrong: 0/60
- Oracle union (FLM or any LLM repeat correct): 60/60 (1.000)
- Oracle union (FLM or all LLM repeats correct): 59/60 (0.983)

Exact-path FL restricted to eligible cases (n=30):

- FLM: 0.967 [0.833, 0.994]
- LLM, strict: 0.933 [0.787, 0.982]
