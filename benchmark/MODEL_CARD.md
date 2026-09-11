# Method card: FLM

## Intended use

FLM supports attribution in systems that expose ordered evidence transformations, stable identities, formalizable invariants, and minimal observability or probeability.

## Inputs

Frozen traces with stage names, evidence presence, rejection reasons, and invariant violations. Optional blind candidate-selection controls draw 85% primary root-cause stages and 15% other related components. This is not a human-subject study.

## Outputs

First Loss stage, Invariant Loss stage, candidate or confirmed stage-level root cause, and downstream-attribution flags.

## Advantages

- Prevents blaming stages that never received required evidence, while a strong trace-pattern or LLM proxy can match FLM when full traces are available.
- Distinguishes disappearance from semantic corruption.
- Makes attribution auditable with minimal probes and independent replay.
- Transfers across domains that preserve the evidence-conservation contract.

## Boundaries

- First Loss is an attribution boundary, not an automatic root cause.
- It assumes local propagation through the observed evidence path; nonlocal side effects require an explicit cross-stage causal exception.
- Invariant Loss can be silent, and First Loss can be delayed; absence of either is not proof of correctness.
- Incomplete observability yields bounded attribution, not guaranteed identification.
- Human intervention selection is outside the current synthetic evaluation.
