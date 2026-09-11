# Release notes

## v1.1.0 release candidate

This candidate narrows the paper from a generality claim to evidence-boundary reasoning supported by controlled evaluations.

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

### Release blockers

- Decide whether to conduct the human study or state that it is future work.
- Create a new Zenodo version and obtain its version DOI.
- Submit the final PDF to arXiv and record the identifier.
- Update `CITATION.cff`, `CITATION.md`, and `citation.bib` with the new DOI and arXiv ID.
