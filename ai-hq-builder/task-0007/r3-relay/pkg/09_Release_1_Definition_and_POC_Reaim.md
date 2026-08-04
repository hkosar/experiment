# 09 — Release 1 Definition and POC Re-Aim (owner ruling, trail 124)

**Owner ruling (verbatim, 2026-08-03):** *"I confirm that release 1 needs to be the app-building management platform."* Preceded by the owner's product-direction statement (same day, quoted in trail 124): the release use is managing the app-building process itself — rules passing files between agents and operators, a process overseer constantly tracking where each project is staged and what the next steps are, idea storage and iteration, separated stages, Zapier-class plugins for a unified central environment, remote operations. TNBS operational workloads (call review, CallRail, email triage as an operations task) are **Release 2**.

## 1. Release definitions (program-level, recorded here and in trail 124)

- **Release 1 — the App-Building Management Platform:** the AI OS running, automated, the process this program currently runs by hand: artifact passing between agent roles under manifest rules; stage/status tracking per project with next-step state; idea capture and staging; stage-gate cards to the owner; durable remote/overnight operations with independent watchdog; the adopted integration fabric as transport. The genuinely consequential acts (gate approvals, releases) remain owner-decided **by design, not by cap**.
- **Release 2 — Business-operations workloads:** call review/delegation, email triage as operations, and the autonomy-growth machinery in earnest (DE-R8 volume growth, the fork-level decision-learning proposal from the trail-124 discussion — parked with its design notes, not discarded).

**Nothing accepted reopens.** The Decision Engine core is workload-agnostic (stages, checkpoints, journal, receipts, tiers, watchdog); v1.4's content is unchanged and its owner acceptance remains pending as a separate one-line event. TOPIC-0003's plan, D1–D2 deliverables, shortlist, and boundaries stand; **only the D3 POC scenario content re-aims** to test the release workload.

## 2. THE authoritative D3 scenario definition (Revision 2 — verifier corrections R1P-01..05 applied from `10_`)

**Supersession statement (R1P-01):** this section is the ONE authoritative D3 scenario definition. It supersedes: the handoff `00_` §10 POC-1/POC-2 content; the plan `02_` §2's original POC-set description; and `05_` §4's scenario instruction — each of which now points here. **No current-facing instruction to run the Release-2 call/email scenarios in D3 exists**; those scenarios are parked verbatim as Release-2 planning inputs.

- **POC-1 — Builder-return pipeline.** Receive artifact → **bind task/transition identity** → hash and validate → create owner card → accept / rework / inspect → controlled relay (authorized via `/poc1/verify-decision`, the opaque-token pattern) → receipt → duplicate / replay / revocation / uncertain-result tests.
  **Idempotency identity (R1P-04), defined and tested:** `workflow/task ID + stage/expected transition + artifact content digest + route/target role + submission epoch (with the accepted retry policy)`. A raw zip hash alone is NOT the key. **Five required tests:** (1) same artifact, same task, same transition → suppress reprocessing, return the prior receipt; (2) same artifact, different task → process independently; (3) same task and artifact, different unauthorized target → REJECT, not duplicate-success; (4) replayed owner decision token → no second relay; (5) uncertain provider result → reconcile before any second side effect.
- **POC-2 — Idea capture & staging, two envelope cases (R1P-02).**
  **Case A — authenticated owner-authored idea:** origin owner; instruction authority owner-authorized within current session/policy; any embedded external content separately classified.
  **Case B — imported/forwarded note or content:** origin external; trust external-untrusted; instruction authority NONE; semantic use classification and summary only.
  Both cases → classify new-topic vs existing-project addition → staged record written → mobile briefing with suggested next → **no external action, no link followed**. The POC must prove external content informs classification **without acquiring instruction authority**.
- **POC-3 — Durable nightly integrity sweep.** Read designated project integrity inputs → checkpoint → deliberate mid-flight kill → safe retry → reconcile uncertain side effects → independently detect a missed run → report drift — **without the provider becoming authoritative for project truth** (the AI OS ledger stays canonical).
- **POC-4 (optional)** — unchanged; trigger condition per `07_` §1, re-evaluated at D2 evidence.

**Artifact-handling measures (R1P-05, provider-discriminating, added to the measure set):** max practical upload/webhook payload size; binary fidelity and digest preservation end-to-end; file-count/archive limits; safe treatment of nested archives, symlinks, traversal paths, malformed archives (failing closed is a recordable capability gap, not a POC failure); secret/restricted-file detection before provider transit; whether the provider stores, inspects, or retains artifact contents; retention/deletion controls; relay of the original artifact vs reconstituted content; mobile owner-card latency **without placing the artifact itself in Discord**. All shortlisted providers receive equivalent scenario inputs, limits, success criteria, and measurement methods.

## 3. Boundary deltas (additive to `05_` §2; for the verifier's scoped review)

Artifacts in scope are program artifacts (zips, manifests, docs, code) — Business-class; the Personal-partition exclusion stands unchanged. New rows: the fabric may hold **scoped read credentials for designated POC repositories only**; no credential that can push to a protected branch enters any provider in the POC round; agent-channel delivery endpoints (where packets get relayed) are enumerated in the ownership record like any connection. Providers still never hold the rulebook (policy artifacts, journal, receipts ledger).

## 4. Sequencing (no in-flight work disturbed)

TASK-0007 **R1 (wrapper stub) continues unchanged** — its endpoints are scenario-agnostic by design. On R1's return and verification, **R2 issues**: re-aimed POC-1/POC-2 workflow definitions + runbook updates to this section's scenarios (Builder work, same allowlist). The owner session then runs the re-aimed content. The verifier receives this document now for a **scoped ack of the D3 delta** (scenario content only; plan, criteria, axes, and boundaries otherwise standing); under the plan's own structure this is a bounded change, not a reopening.

## 5. Why this re-aim strengthens the evaluation (recorded so the reasoning is auditable)

The POC round now tests the fabric against the actual release workload — the artifact-relay, stage-card, and idea-staging flows the platform will run on day one — rather than a Release-2 workload standing in for it. The duplicate-suppression, approval-transport, and watchdog tests all keep their discriminating power; POC-1 gains realism (its test data is this very program's relay history).
