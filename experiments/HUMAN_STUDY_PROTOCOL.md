# Blinded engineer study protocol (preregistration draft)

## Status

This protocol is prepared but has not been run. No human-subject result may be claimed until the responsible institution determines whether ethics review or exemption is required, participants consent, and the analysis plan is registered before outcomes are inspected.

## Question

Does the FLM worksheet reduce unsafe downstream attribution or diagnosis time compared with ordinary trace inspection?

## Design

- Within-subject, counterbalanced comparison.
- Target: at least 12 software engineers with debugging experience.
- Materials: 24 cases sampled from the executable RAG, ETL, and build runtimes; no participant sees two seeded variants of the same scenario.
- Conditions: ordinary trace plus incident prompt versus the same trace plus the FLM evidence-survival worksheet.
- Blinding: condition labels do not mention the expected root cause; case order and condition order are randomized.
- Primary outcome: unsafe downstream attribution rate.
- Secondary outcomes: stage-level RCA, calibrated confidence, time to decision, and probe count.
- Exclusions: incomplete session, prior access to case ground truth, or failure to answer the attention-check case.

## Analysis

Use a mixed-effects logistic model for correctness and unsafe attribution, with participant and case as random intercepts. Analyze decision time on the log scale. Report effect sizes and confidence intervals; treat p-values as secondary. Preserve all exclusions and missing observations in the released flow diagram.

## Release requirements

Publish the exact case set, randomization seed, worksheet, anonymized responses, analysis script, consent text, and ethics determination. Do not publish employer, production-system, or personally identifying data.
