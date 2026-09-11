# Vector-arm ordering incident replay

## Identity

- System instance: SPM-Polaris production recall pipeline

- Incident class: `rank_loss_positional_truncation`
- Domain: `knowledge_assistant`
- Benchmark mapping: metadata lookup loses rank invariant; cap causes First Loss.
- Ground truth:
  - Invariant Loss: `metadata`
  - First Loss: `cap`
  - Root cause: `metadata`
  - Predicate: `metadata.drop_rank`

## Fail-before

The vector retrieval arm produced ranked evidence. Metadata enrichment returned an unordered collection. The downstream cap applied positional truncation, so the target evidence disappeared. Selector, gate, assembly, and reader never received the target evidence.

## Minimal probe

The probe recorded the retrieval rank at lookup input and lookup output, then recorded cap membership. It changed only observation instrumentation; corpus, query, retrieval parameters, cap size, selector, gate, and reader remained frozen.

## Single-variable intervention

The only intervention was to preserve the retrieval rank across metadata lookup. The corpus, query, retrieval arm, cap size, selector, gate, assembly, and reader configuration remained frozen.

## Pass-after

After preserving rank across metadata lookup, the same query and window kept the target evidence through cap. The downstream symptoms disappeared without changing selector, gate, or reader behavior.

## Independent replay

An independent process and window reproduced the same Invariant Loss at metadata lookup, First Loss at cap, and root cause at the metadata rank-preservation predicate.

## Confirmation decision

The incident is a **confirmed stage-level root cause** at metadata lookup. Predicate-level attribution additionally requires the original query ID, corpus revision, configuration hash, code revision, and before/after artifacts.
