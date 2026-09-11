# arXiv submission metadata

- Title: First Loss: Evidence-Boundary Reasoning for Root-Cause Attribution
- Author: KuangYu Chen
- Primary category: cs.SE (Software Engineering)
- License: CC BY 4.0
- Comments: 7 pages, 3 tables; accompanying reproducibility artifact at https://doi.org/10.5281/zenodo.22709898
- DOI: 10.5281/zenodo.22709898
- Corresponding email: rin@rin.red
- Additional affiliation contact: contact@veridicaltech.com

## Abstract

Failures in multi-stage software systems often become visible after the evidence needed for a correct result has already disappeared or changed meaning. Debugging from the final symptom can therefore blame a component that never received the relevant evidence. First Loss Methodology (FLM) treats an execution as a sequence of evidence transformations. First Loss marks the first boundary where evidence becomes unavailable to the next stage; Invariant Loss marks the first observed violation of identity, order, scope, time, provenance, authority, or lifecycle. Neither is automatically the root cause, which still requires intervention.

We formalize this distinction, limit the attribution rule to the observed lineage segment, and define bounded answers for missing observations, explicit exceptions for nonlocal effects, and segment-aware handling of evidence reacquisition. A controlled benchmark with 1,200 test cases and a 600-case replay window checks the internal behavior of the rules. Three separate executable reference runtimes for retrieval-augmented generation, ETL, and build dependency resolution add 360 cases with partial traces, noisy probes, nonlocal side effects, and reacquisition. FLM attains 0.981 safe-attribution accuracy in this second evaluation; removing independent replay lowers it to 0.972, while removing intervention reduces confirmed root-cause accuracy from 0.961 to zero. A 300-response GLM baseline reaches 0.920 overall attribution accuracy and 0.973 exact-path root-cause accuracy, but only 0.200 exact agreement across five repeated runs. These results establish reproducibility and boundary behavior in controlled systems. They do not establish production-wide generality.

## Upload

Upload `first-loss-v1.1.0-arxiv-source.tar.gz`. Confirm the generated preview matches `../pdf/first-loss-v1.1.0-preprint.pdf`, then stop before the final submission action unless the author has approved it.
