# Redacted production case study: compound loss in memory recall

This note records the evidence used by the second production investigation in the manuscript. Tenant identifiers, source identifiers, hostnames, internal paths, deployment revisions, and exact timestamps are omitted.

## Initial symptom

A low-cost recall mode returned short field-like atoms and sometimes selected recently captured debugging text over committed memory. A deeper mode, which materialized source spans and used a stronger selection path, answered the same frozen queries more reliably.

## Revised attribution chain

The investigation rejected several early explanations before separating four boundaries:

1. **Acquisition loss:** query-echo captures and near-duplicate sources could crowd committed evidence out of the retrieval window.
2. **Admission loss:** an intact atom could be retrieved but rejected by a semantic-support floor whose premises depended on the changing candidate pool.
3. **Assembly contract loss:** one span-retrieval leg was merged after lane ordering, so an intermediate seat guarantee did not imply the promised final ordering or filtering behavior.
4. **Enumeration loss:** for questions requiring a complete set, relevant mentions could be present upstream but incompletely admitted to the reader context.

## Causal checks

- Gate diagnostics were exposed before changing admission behavior, distinguishing `no candidate` from `no semantic support`.
- A paired policy probe fixed the query and two source lanes while changing only lane policy.
- Moving lane partitioning to the final merged evidence set restored the end-to-end output contract.
- A separate semantic-admission intervention rescued verifiable evidence already present at the gate.
- Capture governance and cross-source canonical deduplication removed query echoes and punctuation-level duplicates without removing committed evidence in the controlled probes.
- Independent replay confirmed the corrected ordering and absence of the echo source.

## Boundary of the claim

The investigation supports stage-level attribution for the observed production path. It does not provide a public predicate-level reproduction because the source corpus, payloads, tenant state, and deployment revisions are not released. The low-cost mode also retains a documented quality boundary: a weak answer is not automatically a defect when committed evidence never enters its bounded retrieval window.

Candidate-pool membership, source timestamps, capture state, retrieval depth, and evidence limits must therefore be frozen or recorded during replay. A repeated query with different pool state is not an independent replay of the same causal condition.
