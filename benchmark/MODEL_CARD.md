# Method card: FLM

## Intended use

FLM supports attribution in systems that expose ordered evidence transformations, stable identities, formalizable invariants, and minimal observability or probeability.

## Inputs

Frozen traces with stage names, evidence presence, rejection reasons, and invariant violations. Optional blind candidate-selection controls draw 85% primary root-cause stages and 15% other related components. This is not a human-subject study.

The real-LLM baseline receives a ground-truth-free JSON trace under a frozen prompt and strict output schema. It does not receive the FLM boundary rule. Each sampled case is repeated five times.

The completed baseline requested `glm-5.3-flash` through an OpenAI-compatible Responses endpoint; the provider reported `glm-5-3-flash`. Because the gateway did not enforce `json_schema`, the final frozen protocol used `json_object` plus exact field validation. Two compatibility pilots were excluded before the final `llm-rca-v1.1.1` run.

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
- A real-model result is reportable only with exact model ID, temperature, prompt hash, raw responses, usage, and repeat consistency.

## Completed real-model baseline

- 60 stratified cases, five runs each, 300 responses.
- Attribution accuracy: `0.920`.
- Exact-path FLA / ILA / RCA: `0.987` / `0.813` / `0.973`.
- Status accuracy: `0.927`; risky-case overclaim rate: `0.047`.
- Exact agreement across all five runs: `0.200` when comparing status, First Loss, Invariant Loss, and root-cause stage.
- Schema adherence: `1.000` under the final JSON-object protocol.
