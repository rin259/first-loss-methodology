# Public postmortem demonstration: no-ground-truth bounded attribution

This note documents a demonstration of First Loss Methodology (FLM) applied to
five public incident reports from five different operators between 2017 and
2022. The machine-readable encodings live in
`benchmark/public_postmortem_cases.jsonl` and are checked by
`benchmark/validate_postmortem_cases.py`.

## Why this exists

The controlled benchmarks in this repository use authored ground truth. The two
production investigations in the paper are the author's own systems. Both
limitations are disclosed. This demonstration addresses a third setting: real,
non-authored incidents, reported publicly by the operator, where no ground
truth can be manufactured because no intervention is possible. The question is
narrow: **do the FLM rules produce well-formed, useful attribution outputs from
narrative evidence alone, and do they fail safe when the narrative is thin?**

## Protocol

1. **Source selection.** Public post-incident reports that (a) name concrete
   stages and mechanisms rather than only customer impact, (b) contain a
   timeline with timestamps, and (c) are published by the operator itself.
   Primary sources only; no press coverage or third-party summaries.
2. **Encoding.** For each incident we record the stage path (ordered evidence
   transformations), the evidence item, every boundary state the narrative
   supports (each with a timestamp or verbatim citation), the FLM output
   (status, Invariant Loss, First Loss or bounded interval, nonlocal and
   reacquisition flags, candidate set), and the operator's own conclusion.
3. **No ground truth.** The operator's conclusion is recorded as a
   *reference*, not as truth. Nothing here confirms a root cause: no
   intervention was possible on third-party systems, so every output is a
   **candidate set** under the paper's confirmation protocol.
4. **Success criteria (structural).** For each case: (S1) the output is
   well-formed under the validator; (S2) the candidate set is non-empty and
   every member names a mechanism that appears in the narrative before the
   observed failure; (S3) when the narrative supports an exact boundary, the
   boundary is stage-level and cited; (S4) when the narrative does not support
   an exact claim, the output degrades to bounded/exception status rather than
   overclaiming.

## Cases

Five operators, five years, four failure shapes (capacity removal, network
partition with automated failover, resource exhaustion via configuration,
configuration command with cascade, mass deletion):

| # | Case | Operator | Date | Status | IL stage | FL stage |
|---|---|---|---|---|---|---|
| 1 | `aws-s3-us-east-1-2017` | AWS | 2017-02-28 | exact | capacity removal | index subsystem serving |
| 2 | `github-oct21-2018` | GitHub | 2018-10-21 | exception | West-coast replicas | replication link |
| 3 | `cloudflare-july2-2019` | Cloudflare | 2019-07-02 | exact | one-shot deployment | WAF regex evaluation |
| 4 | `meta-oct4-2021` | Meta | 2021-10-04 | exception | command audit gate | BGP advertisements |
| 5 | `atlassian-april-2022` | Atlassian | 2022-04-05 | reacquisition | deletion API gate | tenant destruction |

### 1. AWS S3 US-EAST-1, 2017-02-28

Source: [AWS summary of the S3 disruption](https://aws.amazon.com/message/41926/).

At 9:37AM PST an authorized operator ran a playbook command intended to remove
a small number of servers for the billing subsystem; an incorrect input removed
a larger set, which also supported the index subsystem (metadata and location
of all objects; required for GET/LIST/PUT/DELETE) and the placement subsystem
(storage allocation for PUT). While both restarted, S3 could not serve
requests; the index subsystem began serving at 12:26PM and finished at 1:18PM,
placement at 1:54PM.

- **FLM output.** IL at *capacity removal* (the capacity-floor invariant broke
  before any subsystem stopped serving); FL at *index subsystem serving*
  (metadata unavailable downstream). Nonlocal flag: one removal action
  simultaneously degraded three subsystems, so the billing path is not the
  only affected path — a cross-stage exception qualifies the candidate set.
  Candidates: the incorrect command input; the missing capacity-floor
  safeguard in the tool.
- **Reference.** AWS names the incorrect input and states the tool "allowed too
  much capacity to be removed too quickly", then added safeguards.
- **Reading.** The IL/FL separation adds information the narrative states only
  implicitly: the removal was already wrong (invariant) before the region
  observed loss (boundary), and the shared-capacity channel explains why an
  action on the billing path took down the index path.

### 2. GitHub, 2018-10-21

Source: [GitHub October 21 post-incident analysis](https://github.blog/2018-10-30-oct21-post-incident-analysis/).

At 22:52 UTC, maintenance on 100G optical equipment partitioned the East coast
hub from the primary East data center for 43 seconds. Orchestrator's Raft
quorum failed clusters over to the West; the application tier immediately
wrote to West primaries. East held seconds of writes the West lacked and West
accumulated ~40 minutes of writes the East lacked, so fail-back was unsafe;
the team chose fail-forward and paused webhooks and Pages builds. Recovery ran
through backup restore (multi-terabyte, remote blob storage) and finished at
23:03 UTC the next day. During backlog replay, ~200,000 webhook payloads had
outlived an internal TTL and were dropped.

- **FLM output.** Evidence item 1 (East writes and their replication stream):
  FL at *inter-site replication link*; IL at *West-coast replicas*
  (divergence invariant: both sites held writes absent from the other). The
  maintenance partition is an upstream shared-state cause, so the output is a
  **cross-stage exception** with candidates {Orchestrator cross-region
  promotion policy, network maintenance}. Evidence item 2 (queued webhooks):
  the TTL invariant broke at consumption, an **acquisition loss at delivery**;
  backlog replay is reacquisition for the surviving payloads.
- **Reference.** GitHub states Orchestrator behaved as configured and the
  partition triggered the chain; preventing cross-region promotion is the
  listed initiative.
- **Reading.** One incident, two evidence items, three different output
  statuses (exception, acquisition, reacquisition). Collapsing them into a
  single "database outage" cause would have mixed unrelated mechanisms — the
  same lesson as the paper's second production investigation.

### 3. Cloudflare, 2019-07-02

Source: [Cloudflare outage post](https://blog.cloudflare.com/cloudflare-outage/).

At 1342 UTC a routine deployment of WAF managed rules — running in simulated
mode that blocks no traffic — contained one regex that drove CPU to 100%
worldwide; 502s followed and traffic dropped 82% at worst. A global
termination of the ruleset at 1409 UTC restored CPU and traffic; the ruleset
returned at 1452 UTC after rollback and testing.

- **FLM output.** IL at *global one-shot deployment* (the progressive-rollout
  invariant broke even though the rule was simulated); FL at *WAF regex
  evaluation* (evaluation capacity unavailable downstream). Candidates: the
  regex; the bypassed progressive deployment.
- **Reference.** Cloudflare attributes the outage to a single misconfigured
  rule and states testing and deployment processes were insufficient.
- **Reading — applicability boundary, kept for honesty.** Here the "evidence"
  is a continuous resource (CPU capacity), not a discrete item. FLM still
  separates the violated rollout invariant from the capacity loss, but the
  evidence model maps weakly, and the simulated-mode detail is instructive in
  the paper's terms: a seat guarantee (rule does not block traffic) without an
  end-to-end guarantee (evaluation still consumes the resource). We retain the
  case precisely because it shows where the evidence-item abstraction strains.

### 4. Meta, 2021-10-04

Source: [Meta details about the October 4 outage](https://engineering.fb.com/2021/10/05/networking-traffic/outage-details/).

During routine maintenance, a command intended to assess global backbone
capacity disconnected the backbone; the audit tool that should have stopped it
had a bug. Edge facilities, designed to withdraw BGP advertisements when they
cannot reach data centers, declared themselves unhealthy and withdrew routes;
DNS servers became unreachable while still operational. Normal and out-of-band
access were down; DNS-dependent internal tools broke; physical access was slow
due to security hardening; services were brought back in stages to avoid a
power-surge crash.

- **FLM output.** IL at *command audit gate* (admission invariant: a
  destructive command that should have been blocked was not — an admission
  loss); FL at *BGP advertisements* (address evidence withdrawn downstream).
  Nonlocal flag: the health-check design converts an upstream backbone state
  change into downstream evidence withdrawal, so the output is a
  **cross-stage exception** with candidates {maintenance command, audit-tool
  bug}. Second loss surface: DNS-dependent investigation tooling lost its own
  evidence channel during response.
- **Reference.** Meta names both the command and the audit-tool bug and
  describes the BGP withdrawal as a designed fail-safe.
- **Reading.** The case shows a fail-safe mechanism acting as a nonlocal
  loss channel — the paper's exception rule is what keeps the health-check
  design from being blamed as a cause.

### 5. Atlassian, 2022-04-05

Source: [Atlassian post-incident review](https://www.atlassian.com/engineering/post-incident-review-april-2022-outage).

A script meant to delete a legacy app deleted 883 customer sites (775
customers) between 07:38 and 08:01 UTC. The operator names two problems: a
communication gap that put site IDs where app IDs were intended, and a
deletion API that "accepted both site and app identifiers and assumed the
input was correct" with no warning signal. Internal monitoring detected
nothing (the deletion ran through a standard workflow); a customer ticket at
07:46 UTC surfaced the incident. The same script deleted site identifiers and
admin contacts, blocking customers from filing support tickets. Recovery used
30-day immutable backups; Restoration 1 created new sites with new immutable
identifiers (~70 steps, ~48 hours per batch, 112 sites); Restoration 2
re-created records while re-using the old identifiers (~30 steps, ~12 hours
per site, 771 sites). RPO (1 hour) was met; RTO was missed.

- **FLM output.** IL at *deletion API* (identifier-type invariant violated at
  the gate — an admission loss); FL at *tenant lifecycle destruction* (site
  records destroyed). Monitoring showed an **observation gap** (P = ?), so the
  detected boundary is bounded from the narrative alone. Reacquisition from
  immutable backups yields status **reacquisition**; candidates: the
  communication gap; the missing identifier-type guard. Second evidence item:
  contact metadata deleted by the same script, an acquisition loss on the
  response path.
- **Reference.** Atlassian names the same two problems; the PIR's soft-delete
  learning matches the capacity-floor safeguard pattern of case 1.
- **Reading.** Restoration 2's decision to re-use old identifiers is direct
  public evidence for the paper's claim that lineage identity is a recoverable
  mapping rather than object identity: preserving identity removed the
  identifier re-mapping steps and roughly quadrupled throughput of recovery.

## Summary against the success criteria

| Criterion | Result |
|---|---|
| S1 well-formed outputs | 5/5 (validator) |
| S2 non-empty, narrative-grounded candidate sets | 5/5 |
| S3 cited stage-level boundaries where supported | 5/5 |
| S4 fail-safe status when narrative is thin | 5/5 (2 exceptions, 1 reacquisition, 0 overclaims) |
| Candidate set contains the operator's named mechanism | 5/5 (every operator-named mechanism appears in the FLM candidate set) |
| IL/FL separation adds structure beyond the narrative's own cause statement | 5/5 (capacity floor, divergence, rollout bypass, admission gate, identifier-type gate) |
| Observation gaps reported as bounded rather than guessed | 1/1 (Atlassian monitoring gap) |

## Limits

- **No ground truth.** Nothing here is a confirmed cause; the operator's
  conclusion is a narrative reference. The demonstration validates output
  *form* and *grounding*, not causal correctness.
- **Narrative completeness is inherited.** The encodings are as strong as the
  public reports; boundaries the reports do not support stay unobserved (the
  Atlassian monitoring gap is the honest example).
- **Two evidence items are continuous resources**, not discrete items
  (Cloudflare CPU). We keep such cases to show the applicability boundary, not
  to claim the model covers them fully.
- **Selection bias.** Reports that pass the source-selection criteria are,
  by construction, unusually detailed incidents from operators willing to
  publish; prevalence claims are impossible from this corpus.
- **Single encoder.** All five encodings were produced by the same author with
  AI assistance; an independent re-encoding of the same sources would measure
  encoding reliability and does not exist yet.
