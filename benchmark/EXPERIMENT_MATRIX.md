# E1–E8 experiment matrix

The frozen test set intentionally over-samples compound and misattribution cases. Family sets below are machine-checkable invariants, not post-hoc filters.

| Experiment | Question | Family set | Primary metrics |
|---|---|---|---|
| E1 First-Loss Localization | Can FLM locate first disappearance and constrain the attribution boundary? | all non-dead-path single faults | FLA, RCA, 1-FDAR |
| E2 Invariant-Loss Detection | Can it find present-but-corrupted evidence? | order, scope, authority, provenance, temporal, identity | ILA |
| E3 Downstream Misattribution | Does it avoid blaming downstream stages? | invariant-first faults plus all compounds | FDAR, 1-FDAR |
| E4 Root-Cause Confirmation | Does single-variable intervention improve confirmed RCA? | all non-dead-path single faults | RCA stage, RCA confirmed |
| E5 Compound Failure | Does attribution remain valid under cascades? | four two-fault compounds | FLA, ILA, RCA, FDAR |
| E6 Latent Dead Path | Can it separate latent dead-path / precondition states? | path unreachable, path returns empty, path output rejected, precondition identity mismatch | per-class RCA |
| E7 Ablation | Which propositions, checks, and protocols contribute? | full test set | per-variant RCA and FDAR |
| E8 Cross-Domain | Does the protocol transfer across engineering domains? | all families sampled over seven domains | mixed/stratified RCA and FDAR |
| E9 Executable Runtimes | Does the method fail safely outside the shared nine-stage generator? | RAG, ETL, and build implementations under six stress profiles | safe attribution, exact RCA, confirmed RCA, overclaim rate |
| E10 Real LLM | How does a model behave without the FLM attribution rule? | 60 stratified E9 cases, five repeats | FLA, ILA, RCA, overclaim, repeat consistency |

## Interpretation

- E3 and E4 are primary: they distinguish symptom localization from causally confirmed RCA. FLA alone is not the headline because component-level RCA can also localize First Loss in this benchmark. The strong LLM proxy also reaches 1.0 in the full-trace setting; FLM is not claimed to beat real or idealized LLM RCA.
- E5 is deliberately adversarial: two components are defective, but the earliest invariant violation must be reported first.
- E8 currently tests protocol transfer through domain-specific stage names. It does not yet test heterogeneous runtimes.
- Pattern and strong LLM proxies see the same trace. They are not substitutes for a real LLM-RCA study.
- E9 tests three separate executable implementations, but they remain authored reference runtimes rather than production deployments.
- E10 is frozen before API execution. No model result may be reported until the exact model ID and raw responses are archived.
