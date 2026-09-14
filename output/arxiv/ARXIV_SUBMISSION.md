# arXiv submission metadata

- Title: First Loss: Evidence-Boundary Reasoning for Root-Cause Attribution
- Author: KuangYu Chen
- Primary category: cs.SE (Software Engineering)
- License: CC BY 4.0
- Comments: 12 pages, 2 figures, 7 tables; accompanying v1.1.2 reproducibility artifact at https://doi.org/10.5281/zenodo.22734754
- DOI: 10.5281/zenodo.22734754
- Corresponding email: rin@rin.red
- Additional affiliation contact: contact@veridicaltech.com

## Abstract

Failures in multi-stage software systems often become visible after the evidence needed for a correct result has already disappeared or changed meaning. Debugging from the final symptom can therefore blame a component that never received the relevant evidence. First Loss Methodology (FLM) treats an execution as a sequence of evidence transformations. First Loss marks the first boundary where evidence becomes unavailable to the next stage; Invariant Loss marks the first observed violation of identity, order, scope, time, provenance, authority, or lifecycle. Neither is automatically the root cause, which still requires intervention.

We formalize this distinction with segment-local definitions that cover acquisition boundaries, bounded intervals, nonlocal exceptions, and evidence reacquisition, and we state the attribution rule as falsifiable propositions. A controlled benchmark with 1,200 test cases and a 600-case replay window checks the internal behavior of the rules: removing the First Loss rule or the attribution boundary drops root-cause accuracy from 1.000 to 0.050. Three executable reference runtimes for retrieval-augmented generation, ETL, and build dependency resolution are evaluated under six stress profiles. Eighteen fault configurations replayed twenty times each yield 360 runs with 0.981 safe-attribution accuracy. Every exact-attribution error occurs under probe noise, where the method claims a wrong exact stage instead of a bounded interval; five-probe replay corrects seven such runs but reverses four correct ones, a net effect that is not statistically separable (exact McNemar p = 0.549). A 300-response GLM baseline reaches 0.920 overall attribution accuracy, yet only 12 of 60 cases receive five identical answers even at temperature zero; on the shared cases the model matches FLM only when at least one of its five repeats is accepted. Two production investigations illustrate rank loss and a compound acquisition-admission-assembly-enumeration failure. These results establish reproducibility and boundary behavior in controlled systems. They do not establish production-wide generality.

## Upload

Upload `first-loss-v1.1.2-arxiv-source.tar.gz`. Confirm the generated preview matches `../pdf/first-loss-v1.1.2-preprint.pdf`, then stop before the final submission action unless the author has approved it.
