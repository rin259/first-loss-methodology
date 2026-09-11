# Data card

## Purpose

Evaluate whether explicit evidence-survival and attribution-boundary rules reduce downstream misattribution in observable multi-stage systems.

## Composition

- 1,200 frozen test cases and 600 independent-window replay cases.
- 7 abstract engineering domains.
- 16 single-fault families and 4 two-fault compound families.
- Full per-stage evidence survival traces.
- Exact stage-level ground truth generated from frozen injection specifications.
- 360 executable-runtime cases across separate RAG, ETL, and build implementations.
- Runtime stress profiles for hidden observations, noisy probes, nonlocal effects, and evidence reacquisition.

## Intended use

Research on evidence-centric root-cause attribution, ablation, and benchmark design. Suitable for testing attribution rules, not for estimating production incident frequencies.

## Limitations

- Case generation is synthetic; it cannot represent all nonlocal causality, shared-state failures, or distributed runtime behavior.
- Domain transfer is simulated through role naming, not real heterogeneous implementations.
- Ground truth uses primary component selection for compound failures, which is a simplifying convention.
- LLM baselines are deterministic proxies, not model runs.
- Blind intervention is a stochastic simulation, not human-subject evidence.
- The executable runtimes reduce role-label reuse but remain small authored reference systems.
