# Release notes

## v1.1.3 manuscript revision

This release is permanently archived at DOI [10.5281/zenodo.22764125](https://doi.org/10.5281/zenodo.22764125).

### External validity

- Adds five public postmortem encodings (AWS S3 2017, GitHub 2018, Cloudflare 2019, Meta 2021, Atlassian 2022) with a source-selection protocol, a structural validator (`benchmark/validate_postmortem_cases.py`), and per-case readings (`experiments/PUBLIC_POSTMORTEMS.md`). All outputs are candidate sets; the operator's conclusion is a narrative reference, not truth.

### Paper minor revisions

- Adds a notation table and a per-evidence-item aggregation rule for multi-item losses.
- Defines FDAR in the paper and reports ablation significance (exact McNemar vs the full method) in the ablation table.
- Adds the per-family breakdown as Appendix B and the controlled-benchmark post-hoc report (`benchmark/results/ANALYSIS.md`).
- Moves the bootstrap-correction note to the artifact disclosure and reports content-level repeat verification for the LLM baseline (raw outputs byte-distinct in 60/60 cases at temperature zero).
- CI now regenerates the per-benchmark `ANALYSIS.md` reports and fails on drift from the frozen result files.

### Artifacts

- Preprint PDF: `first-loss-v1.1.3-preprint.pdf`
- arXiv-ready source bundle: `first-loss-v1.1.3-arxiv-source.tar.gz`

## v1.1.2 manuscript revision

This release is permanently archived at DOI [10.5281/zenodo.22734754](https://doi.org/10.5281/zenodo.22734754).

### Paper

- Promotes the controlled-benchmark ablations to the main text and moves the full five-method comparison to an appendix.
- Restates the method with segment-local definitions covering acquisition boundaries, bounded intervals, nonlocal exceptions, and reacquisition; adds formal propositions (existence boundary, provenance recoverability, attribution bound, invariant priority) and an attribution algorithm.
- Adds enumeration loss as an operational surface and a surface-to-fault-family mapping table; the second production case now aligns with the taxonomy.
- Adds a motivating figure and a loss-surface figure.
- Adds related work on algorithmic debugging, delta debugging, database causality, and LLM-based RCA.

### Evaluation

- Reframes the executable-runtime evaluation as 18 fault configurations replayed 20 times each (360 runs) and reports per-profile safe attribution.
- Adds exact McNemar tests and configuration-clustered bootstrap intervals; the replay ablation corrects 7 runs and reverses 4, a net effect that is not statistically separable ($p=0.549$).
- Adds an FLM error taxonomy: all exact-attribution errors are noisy-probe runs claiming a wrong exact stage.
- Adds Wilson intervals, denominators, temperature, and stratification detail to the real-LLM baseline; reports the Invariant Loss hallucination pattern and the FLM/LLM overlap on the 60 shared cases.
- Maps the registered hypotheses H1--H4 to the evaluations that can decide them.

### Artifacts

- Preprint PDF: `first-loss-v1.1.2-preprint.pdf`
- arXiv-ready source bundle: `first-loss-v1.1.2-arxiv-source.tar.gz`
- Adds `benchmark/analyze_results.py`, which regenerates every reported interval and test from the frozen result files into per-benchmark `ANALYSIS.md` reports.

## v1.1.1 manuscript revision

This release is permanently archived at DOI [10.5281/zenodo.22734716](https://doi.org/10.5281/zenodo.22734716).

- Adds acquisition, admission, assembly, and rendering as operational First Loss surfaces.
- Distinguishes candidate-seat guarantees from filtering, ordering, and final-output guarantees.
- Adds a redacted production investigation covering self-capture pollution, semantic-gate rejection, a merged retrieval leg that bypassed lane precedence, and incomplete enumeration.
- Treats candidate-pool membership and source timestamps as part of the frozen replay context.
- Preserves the archived `v1.1.0` DOI as the previous version in the Zenodo version chain.

## v1.1.0

This release narrows the paper from a generality claim to evidence-boundary reasoning supported by controlled evaluations. The release is permanently archived at DOI [10.5281/zenodo.22709898](https://doi.org/10.5281/zenodo.22709898).

### Paper

- Adds an English LaTeX manuscript and verified PDF.
- Adds formal citations for fault localization, cause transitions, provenance, distributed tracing, causal reasoning, microservice RCA, and RAG.
- Limits downstream exclusion to the observed direct lineage path.
- Adds bounded attribution, nonlocal exceptions, and evidence reacquisition.
- Separates stage-level confirmation from predicate-level confirmation.
- Consolidates repeated results and adds a dedicated threats-to-validity section.

### Evaluation

- Adds executable RAG, ETL, and build reference runtimes with 360 cases.
- Adds partial-observation, noisy-probe, nonlocal, and reacquisition profiles.
- Makes intervention and independent-replay ablations measurable.
- Fixes paired bootstrap resampling to use shared case indices.
- Reports underflowed exact p-values as bounds rather than zero.
- Adds a frozen 300-request real-LLM protocol and a preregistration draft for a blinded engineer study.

### Follow-up work

- Conduct the prepared human study in future work, subject to participant recruitment and an ethics or exemption determination.
- Submit the final PDF to arXiv and record the identifier.
- Update citation metadata with the arXiv ID after it is assigned.
