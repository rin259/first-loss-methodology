# Controlled benchmark: post-hoc analysis (test split, n=1200 cases per method)

## FLM accuracy by fault family

| Family | n | FLM RCA | Component RCA | Existence-only RCA |
|---|---:|---:|---:|---:|
| assembly_duplicate_identity | 60 | 1.000 | 1.000 | 1.000 |
| authority_corruption | 60 | 1.000 | 0.383 | 0.000 |
| budget_off_by_one | 60 | 1.000 | 0.500 | 1.000 |
| cap_error | 60 | 1.000 | 0.483 | 1.000 |
| compound_identity_dead_path | 60 | 1.000 | 0.117 | 0.000 |
| compound_provenance_gate | 60 | 1.000 | 0.283 | 0.000 |
| compound_rank_scope | 60 | 1.000 | 0.967 | 0.000 |
| compound_temporal_budget | 60 | 1.000 | 0.200 | 0.000 |
| gate_error | 60 | 1.000 | 0.683 | 1.000 |
| identity_mismatch | 60 | 1.000 | 0.000 | 0.000 |
| latent_dead_path_empty | 60 | 1.000 | 0.100 | 1.000 |
| latent_dead_path_rejected | 60 | 1.000 | 0.783 | 1.000 |
| latent_dead_path_unreachable | 60 | 1.000 | 0.150 | 1.000 |
| provenance_corruption | 60 | 1.000 | 0.233 | 0.000 |
| rank_loss_positional_truncation | 60 | 1.000 | 0.183 | 0.000 |
| reader_error | 60 | 1.000 | 1.000 | 1.000 |
| retrieval_miss | 60 | 1.000 | 0.083 | 1.000 |
| scope_filter_mismatch | 60 | 1.000 | 0.217 | 0.000 |
| selector_error | 60 | 1.000 | 0.683 | 1.000 |
| temporal_invalidity | 60 | 1.000 | 0.350 | 0.000 |

FLM is exact on every family: True. The informative columns are the baselines, which lose accuracy precisely on the families whose failure semantics depend on the loss boundary.

## Ablation significance (exact McNemar vs FLM full, test split)

| Variant | RCA confirmed | 1-FDAR | p (confirmed) | p (1-FDAR) |
|---|---:|---:|---:|---:|
| flm_no_first_loss_rule | 0.050 | 0.150 | <1e-300 (0/1140) | <1e-300 (1020/0) |
| flm_no_invariant_checking | 0.500 | 1.000 | 4.82e-181 (0/600) | 1 (0/0) |
| flm_no_upstream_exclusion | 0.050 | 0.150 | <1e-300 (0/1140) | <1e-300 (1020/0) |
| flm_no_minimal_probe | 0.432 | 0.644 | 9.97e-206 (0/682) | 5.77e-129 (427/0) |
| flm_no_intervention | 1.000 | 1.000 | 1 (0/0) | 1 (0/0) |
| flm_no_independent_replay | 1.000 | 1.000 | 1 (0/0) | 1 (0/0) |
| flm_blind_candidate_selection | 0.987 | 1.000 | 3.05e-05 (0/16) | 1 (0/0) |

Discordant pairs are reported as (variant worse/full better). The two
confirmation ablations (no intervention, no replay) are identical to
the full method on localization metrics by design and differ only in
claim strength.
