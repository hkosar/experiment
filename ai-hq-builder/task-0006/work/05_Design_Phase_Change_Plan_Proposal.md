# 05 — Design Phase Change Plan Proposal (CP-P2-A draft) — Expanded per P2D-11

**Status:** **Nonbinding draft only** — opened for approval after discovery acceptance. Exact requirement texts and acceptance criteria are authored in the real CP-P2-A at that point; this proposal fixes its complete scope so nothing discovered is dropped.

## Item 0 (isolated mechanical; NOT a discovery conclusion) — Standing-role refresh

Amend GOV-01, Manual §20A.1, ADR-019, §12.1.1 to name **Claude Opus 5** as standing Builder (trail-69 backlog; governed change with owner acceptance).

## Design scope (complete carried surface)

1. **Record-shape selection and schemas** — carry **S1, S2, and S3 as viable normalized alternatives** into design, with S2 as the leading hypothesis rather than the selected design. Compare all three against the tradeoff table, interactive-latency requirement, evidence-authority boundary, correction behavior, concurrency behavior, GAP-2, DE-R2, E2E-1, and check 4. S3-style materialized projections may also be combined with S1 or S2, but hybridization does not count as evaluating S3’s independent-record/event shape (P2R-04). Typed-record schemas; PLAT-02/04 and APP-02 as invariants.
2. **Field-authority contract** (OQ-02) — normative spec: authoritative control fields, deterministic derived fields, model-proposed semantic fields with the lower/escalate-only rule; disagreement/unknown behavior.
3. **Identity and deduplication design (GAP-2, open-blocking)** — five distinct identity concepts; source-aware, uncertainty-aware dedup; acceptance tests: no false-merge of legitimate identical events, transformed redeliveries caught, identity independent of normalization version.
4. **Serialization design (DE-R2)** with a latency bound protecting the capture experience (DP-001).
5. **Degraded-mode ladder (DE-R3)** — capture-only → read-only → refuse-consequential; A10/A15 oracles as tests.
6. **Tier system + policy function (DE-R4)** — deterministic tier/authority/attention mapping; OD-2 policy objects; **DE-R8 (owner modification, trail 82): pre-authorized versioned auto-expansion policy — the T2 cap grows automatically from measured resolution/correction evidence and contracts automatically on regression, every change a policy-version event with owner-visible receipt, owner override absolute.**
7. **Attention band function (DE-R5)** within ATT-01; OD-1 policy objects; quiet-hour scheduler.
8. **Policy-object representation (DE-R6)** — scope, authority domain, priority, effective dates, conflict behavior, rollback; **the four precedence alternatives compared via dedicated replay cases** (explicit priority+authority; deny/safety-floor; equal-priority fail-closed; owner-scoped exception with supersession target).
9. **Event model + replay (DE-R7)** — complete event/record set (OQ-05), recorded-model-output replay with provenance; replay harness proving the fold property.
10. **Queue mechanics (OQ-07)** — one governed mechanism with **hard Business/Personal partitions** (separately permissioned and prioritized; Executive Desk renders one frame without interleaving — PER-02/EX-03/QUE-01); admission by required-owner-action + attention contract (T3, T4, ACT-01 reviews, verification exceptions, policy conflicts); aging ladder events per partition; 18.1 metrics wiring.
11. **Ritual integration (OQ-08)** — SCH-02 envelope instantiation for AUD-03/LRN-09/LRN-10; A14 oracle as test.
12. **All six hypothesis checks executed as design-gate tests** — (1) substitution invariance scripted; (2) policy-version causality scripted; (3) missing-control fail-closed scripted; (4) evidence-separation harness (state must refuse to advance without the external receipt); (5) **correction-path execution** (COR-01 non-destructive replay; corrections provably remain weak evidence); (6) **separation-falsifier measurement** (raw-content-consultation rate over a real-input sample; E2E-1 raw-input substitution run) — with the reopen-question procedure if falsified.
13. **INT-01 card and owner-package templates** as designed artifacts.
14. **Operational-DB schema first cut** — schema only; any runtime build is a separately authorized TASK-000n under the `19_` APP-05 template (Builder: Claude Opus 5).

## Out of scope (unchanged deferrals)

Memory-provider selection (ADR-021 gate); MCP write boundaries; mailroom detail; Discord implementation; database product selection; hardware. Protection-layer constraints remain binding invariants.

## Pipeline

Discovery acceptance → CP-P2-A authored (exact texts, acceptance criteria, risk class, rollback, traceability to the corrected OQ/gap dispositions) → verifier review → Fable dispositions → owner approval → design execution with TASK-0003+ for build items → post-work verification → gate → GOV-03 release mechanics.
