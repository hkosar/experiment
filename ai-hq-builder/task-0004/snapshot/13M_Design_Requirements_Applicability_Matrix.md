# 13M — Design Requirements Applicability Matrix (CP-P2-A; rebuilt from exact accepted text per P2G-01)

**Status:** Rebuilt row-by-row from the **exact accepted requirement text** (`Text hash` = first 12 hex of SHA-256 of the register's Requirement field, machine-verified by `13V_`). Treatments keep the plan vocabulary (Binding / Design subject / Deferred / N/A — applicability), while the **honest gate status per row lives in `13G_`**. Each row names the specific mechanism/invariant and the specific test or review method for THIS requirement — family shorthand is retired. Semantic sufficiency of evidence is judged by the human verifier, not by `13V_` (which validates structure, order, hashes, and referential integrity only).

| ID | Text hash | Treatment | Specific mechanism / invariant | Artifact + section | Test / review method |
| --- | --- | --- | --- | --- | --- |
| ACT-01 | `0153e101d5f4` | Design subject | aik one-per-attempt-contract + uncertain-outcome halt + external receipt linkage | D-B3 §2 r5 + §4 T5; D-B9 §5 | T5 trace; check-4 |
| APP-01 | `47473bfc4d60` | Binding | Authority from control envelope only; model-free ceiling precedes proposals; replay uses recorded outputs | D-B2 §2.1; D-B6 §2.1–2.2; D-B9 §4 | Check 1 — structural proof (live two-model run = build gate) |
| APP-02 | `2283a2bf14c9` | Binding | All design outputs durable, versioned, hash-bound, ID-keyed repo records | Repo mechanics; packet manifests | Packet checksum/manifest validation |
| APP-03 | `060f90a7f4dd` | Binding | Independent review separate from builder — binds TASK-0003+ only | Plan §12 Builder rule | APP-05 packet review at task issue |
| APP-04 | `5d339d777ffe` | Binding | Worker loss survivable via events + checkpoints + reconciliation | D-B9; D-B5 §5 | Executed fold + worker-loss trace |
| APP-05 | `374d3729b6be` | Binding | Build machinery binding separately authorized TASK-0003+ tasks | Plan §12 Builder rule; §8 envelopes | Per-task APP-05 conformance |
| APP-06 | `824c48898734` | Binding | Build machinery binding separately authorized TASK-0003+ tasks | Plan §12 Builder rule; §8 envelopes | Per-task APP-05 conformance |
| APP-07 | `12ba73db888a` | Binding | Build machinery binding separately authorized TASK-0003+ tasks | Plan §12 Builder rule; §8 envelopes | Per-task APP-05 conformance |
| APP-08 | `a98e4063ef89` | Binding | Build machinery binding separately authorized TASK-0003+ tasks | Plan §12 Builder rule; §8 envelopes | Per-task APP-05 conformance |
| APP-09 | `c0725b6e2fb8` | Binding | Build machinery binding separately authorized TASK-0003+ tasks | Plan §12 Builder rule; §8 envelopes | Per-task APP-05 conformance |
| APP-10 | `ef88fd7b3de0` | Binding | Build machinery binding separately authorized TASK-0003+ tasks | Plan §12 Builder rule; §8 envelopes | Per-task APP-05 conformance |
| ATT-01 | `1296bb515bbd` | Design subject | Critical only via owner-ratified policy on verified evidence within the accepted category boundary | D-B7 §2–§3 | Five-category verified + ambiguous boundary traces |
| ATT-02 | `b7b6cdb7bd82` | Design subject | Needs Owner emitted as band; queues/badges render without foreground switch | D-B7 §2; D-B10 §3; D-B13 §2 | Attention fixture replays; card/queue instantiation |
| ATT-03 | `d67b856afc6f` | Design subject | Background completions → hub updates; safe retries/first overdue → Briefing | D-B7 (band map) | Explicit class→band mapping cases |
| AUD-01 | `8349d75dfe9c` | N/A | Historical Phase 1 gate, passed (trail 53) | — | — |
| AUD-02 | `52d449894523` | N/A | Historical Phase 1 gate, passed | — | — |
| AUD-03 | `34f81bae5d37` | Design subject | Scheduled read-only self-audit: versioned rubric (dimensions/weights/denominators/missing-data), one-screen output, unknown≠zero, no self-attestation of independent controls | D-B11 §2–§3 | A14 oracle; rubric-completeness audit against the exact field list |
| AUT-01 | `248a8958bca5` | Design subject | Approval requirements as class/scope-keyed versioned policy objects; learned via governed workflow | D-B8 §2 (scope, applicability); D-B6 §3 | Policy replay per class/scope |
| AUT-02 | `5a0b24a0f9df` | Design subject | Expansion only through measured-evidence DE-R8 policy + governed policy topics; no silent adoption | D-B6 §4; D-B11 (LRN-10 no-silent rule) | DE-R8 witness set; check 2 |
| AUT-03 | `c5a3dff3cc7e` | Binding | Technical verification supplied by the accepted build machinery (APP-06/07/09/10, GOV-02/03) plus engine-side staged activation + version rollback | Accepted register rows; D-B8 §2 rollback; AUT-12 staging | N/A — no new engine design; binds TASK-0003+ builds |
| AUT-04 | `650c6cf4293d` | Design subject | Owner surfaces present problem/process/business effect/outcome/consequential risk | D-B13 §2 (card fields) | Template instantiation per card class |
| AUT-05 | `e0e449a8f4d8` | Design subject | In-scope child records auto-created at T1/T2; cross-cutting/high-impact dispositions escalate to T3 | D-B6 (disposition outputs) | Explicit disposition rule + fixture case |
| AUT-06 | `175b2eb5ce36` | Design subject | Override only where permitted; consequence friction before acceptance | D-B8 §2 exception_authority + §4 PC-3/PC-6; D-B13 consequence field | PC-3/PC-6 replay; card instantiation |
| AUT-07 | `256ca6fdf38f` | Design subject | Delegation tracked to closeout: assignment records linked to closeout/verification events | D-B9 (taxonomy) | Assignment→closeout linkage trace |
| AUT-08 | `562ddffc9e0b` | Design subject | Delegation/follow-up policies scoped by person, assignment type, sensitivity, consequence | D-B8 §2 scope | Scope-key vocabulary audit |
| AUT-09 | `1ad3d41c48af` | Design subject | Completion resolves as verified / owner-accepted / needs-review | D-B9 (verification linkage) | Completion-mode enum + per-mode trace |
| AUT-10 | `5fe4b37885e9` | Design subject | Automatic verification read-only by default; employee-facing corrective follow-up a separate owner-controlled action class | D-B6 (action classes) | Class-taxonomy audit + ceiling test |
| AUT-11 | `d991e2952761` | Design subject | Later-evidence reconciliation via ReconciliationEvent; append-only history preserves To-Did | D-B9 §2, §5 (check 5); COR-01 fold | Reconciliation trace; check 5 |
| AUT-12 | `d0e79a5bc9db` | Design subject | Staged autonomy ladder driven by measured outcomes; raw confidence never unlocks; tunable pilot volume | D-B6 §3–§4 | Stage-ladder mapping + DE-R8 witnesses |
| BUS-01 | `7d2768cb7d8a` | Binding | System both builds and operates — program architecture posture | Program structure (accepted) | — |
| BUS-02 | `33f66972063f` | Design subject | Data HQ subsystem (connections, health, permissions, definitions, cross-system topics) | — | — |
| BUS-03 | `58cda6a4bb06` | Design subject | Lead/ad/call/transcript/rating/insight/improvement closed loop | — | — |
| BUS-04 | `72dd4b9d0db6` | Design subject | MCP starts read-only; expansion via scoped action policies | D-B6 ceilings (read-only defaults) | — |
| BUS-05 | `ca66977d027b` | Design subject | Work/personal email triaged separately; both presented in the Desk frame | D-B10 §2–§3; email fixtures | Partition + email routing fixture replays |
| BUS-06 | `beabf7c10352` | Binding | Functional HQs as views; systems keep authoritative hubs | BUS-08/09 boundaries | — |
| BUS-07 | `955bfb5fd482` | Binding | Discord = pilot/attention layer; purpose-built apps own structured records | PLAT-02 design invariant | Authoritative-store test |
| BUS-08 | `f62e0c24beba` | Design subject | Apps own operational facts; engine owns coordination/attention/decisions/verification state via external-evidence boundary | D-B9 §5; D-B2 §2.1 | Check 4 |
| BUS-09 | `23fc9e9aa626` | Design subject | Linked views are projections, never competing copies | D-B14 §4; D-B9 (projections) | Projection non-authority audit |
| BUS-10 | `e08b5b9ff2d1` | Design subject | Connections registry record (mechanism/scope/auth-health/last-verified/domain/classes/version/doc pointer; no secrets; freshness feeds Data HQ + AUD-03, not RES-02) | D-B14 (to add) | Registry schema audit + freshness-event case |
| CAP-01 | `23373d33d001` | Binding | Stage declares maxima; pause/park on breach — this stage's instance declared | Plan §12; D-B12 §3 | Actuals-vs-caps record |
| CAP-02 | `2d585990e127` | Binding | Measurable stage gate with cost side + stop/continue | D-B12 §3 | Capacity record + disposition |
| CAP-03 | `2d980837df71` | Binding | Telemetry/evidence contract: coverage, billed/estimated/inferred, provenance, no content ingestion for cost | D-B9 (CostEvidenceRecord); D-B14 | Field audit vs exact text |
| CAP-04 | `e2db25e8119c` | Binding | Cost-over-value ⇒ AUD-03 review flag; never auto-disable; protected classes exempt | D-B9 EconomicReviewEvent; D-B10 admission; D-B11 case | Synthetic gate case |
| COR-01 | `539ce4991e27` | Binding | Seven history-preserving correction operations + one-tap gesture; corrections feed calibration as weak evidence | D-B9 §2 corrections; D-B13 (gesture) | Check 5; per-operation coverage audit |
| DAT-01 | `5b44ae146ea4` | Binding | Per-class lifecycle rules: collection/storage/retention/model access/rendering/redaction/preview/export/deletion | D-B2 §2.1 (class fields); lifecycle objects (to add) | Lifecycle-policy audit per class |
| DAT-02 | `144d8d0a58b6` | Binding | Masked metadata + authenticated deep link; stricter previews | D-B13 §2, §4 | Card instantiation incl. masking |
| DEC-01 | `da765e2536a9` | Binding | Phase 2 parent topic + recommendation/policy separation as tested hypothesis | TOPIC-0002; check framework | Discovery + design-gate check execution |
| DEC-02 | `88cac0a1b77d` | Binding | Falsifier on consequential Decision records (status/statement/evidence/trigger/rationale) | D-B9/D-B13/D-B14 (to add) | Positive + unknown falsifier cases; replay reproduces falsifier |
| EX-01 | `a14ecc9e8c94` | Design subject | Intake accepts unstructured input before any classification; capture never blocked | D-B4 §2.1; D-B3 §4 T3/T4 | Word-vomit + no-native-ID fixtures |
| EX-02 | `56f98f57c567` | Design subject | Desk composition: recent context, recent events, suggested next, full summary path | D-B13 (to extend) | Desk-content contract audit |
| EX-03 | `b028987aee56` | Design subject | Business/Personal lists segregated inside one frame | D-B10 §2–§3 | No-interleaving fixture |
| EX-04 | `9a153109e947` | Binding | One visible coordinator fronts specialists (accepted D9/EX-04 config) | Accepted config | — |
| EX-05 | `dfc93d8ac640` | Binding | Device-interchangeable operation — no device-local authority; state in canonical stores | PLAT-02; D-B14 §4 | — |
| EX-06 | `e60da966cf3a` | Binding | Same structured data, per-device rendering | Projections (D-B9) | — |
| EX-07 | `195e28ede76d` | Design subject | Progress via verified stages/status/blockers/next actions from recorded state | D-B13 §2; D-B9 state | Card instantiation from fixtures |
| EX-08 | `dddc679b9ad4` | Design subject | Layman consequences + click-by-click on owner surfaces | D-B13 §2 (standard) | Template standard audit |
| EX-09 | `9ac21a874240` | Design subject | Breadcrumb density by message class | — | — |
| EX-10 | `a1603c29ac52` | Design subject | Every view routes to parent/children/related/prior/hub from recorded links | D-B6 outputs (links recorded) | — |
| EX-11 | `b8dbe6c3fe7e` | Design subject | Free-text/semantic retrieval with match explanation | — | — |
| GOV-01 | `ff9c983ce86f` | Binding | Role refresh via v1.4 amendment package with history preservation | D-AM §1 | Scan report + amendment texts |
| GOV-02 | `df6a9f470e60` | Binding | Eleven-item gate packet discipline each stage | Gate records 14_/16_/17_ | Per-gate verifier records |
| GOV-03 | `3efcb4ba1548` | Binding | Controlled Release Executor with CAS + receipts | Plan §7 build-gate row | Release-time verification |
| HW-01 | `1c2f0a44e3e6` | Deferred | Owner-timed hardware purchase | Plan §12 | — |
| IDN-01 | `7e3ad98a94fc` | Binding | Channel never authority; identity/session as mandatory-when-applicable control | D-B2 §2.1, §3 | F5 trace; fail-closed case |
| IDN-02 | `a2e0b17cd1a9` | Binding | Risk-tiered step-up per consequential action class; routine one-tap | D-B6 (DE-R8 owner-increase); per-class flag (to add) | Per-class step-up mapping audit |
| IDN-03 | `7ee720d62e1f` | Binding | Independent kill/revoke + credential recovery + emergency read-only | D-B5 §2–§3 (availability asserted) | Failure traces independent of failed components |
| INT-01 | `5cbfc03b1076` | Binding | Genuine-tradeoff decision prompts; no completeness ladder | D-B13 §2 | Instantiation vs the standard |
| LOG-01 | `2e8d06e62891` | Binding | Append-only tamper-evident action log with true actor/session identity + component versions across all listed event kinds | D-B9 §2 (taxonomy) | Schema field audit vs exact list |
| LOG-02 | `80e5130a820a` | Binding | Central logger owns writes; workers cannot edit history; log reconstructs sessions; feeds Recent-log views | D-B9 (append-only) | Writer-isolation representation audit |
| LRN-01 | `eb7c778c6495` | Design subject | Observations = weak evidence, zero operating effect | D-B11 §3 (ObservationEvent) | Zero-authority trace |
| LRN-02 | `20f4569b52f2` | Design subject | Preferences/rules/skills/policies share the governed workflow | D-B8 §2 change path | PolicyVersionEvent-only change test |
| LRN-03 | `1915cb5a7679` | Design subject | Every learned object declares scope | D-B8 §2 (scope required) | Schema requiredness |
| LRN-04 | `1f52a7506105` | Design subject | Propose exception / reopen topic instead of silent violation | D-B8 §4 (exceptions); D-B6 fail-closed→T3 | Conflict-path trace |
| LRN-05 | `a8e5e40bc1d0` | Design subject | Active/inactive/archived/deleted lifecycle; deletion not default | D-B14 (to add) | Lifecycle-state field audit |
| LRN-06 | `cf84ea98f55e` | Design subject | Inactivity → review, not removal (90d provisional) | D-B11 (to add) | Inactivity-review case |
| LRN-07 | `d75e64fa1594` | Design subject | Rejected ideas + rationale retained as learning evidence | D-B9 append-only; LearningEvent | Retention trace |
| LRN-08 | `0cb1432f9f6e` | Design subject | Category/subcategory organization + semantic retrieval | — | — |
| LRN-09 | `d3c26bce527d` | Design subject | Bounded improvement ritual, ≤1 artifact/cycle, smallest-machinery ladder | D-B11 §2–§3 | A14 + cap trace |
| LRN-10 | `a1aede1ef1a4` | Design subject | 3-verified-occurrence threshold → observation only; exclusions; no silent automation | D-B11 §3 | Threshold + exclusion cases |
| MEM-01 | `fa8ac84cc531` | Binding | Separate authoritative stores per state kind | D-B14 §2; D-B9 | Store-ownership matrix |
| MEM-02 | `99ba08da4be2` | Binding | Topic checkpoint = durable resumption record | D-B5 §3 F3, §5 | Checkpoint record schema + resume trace |
| MEM-03 | `a88b515ac2d3` | Binding | Compaction/replacement behind same visible topic | D-B9; D-B5 §5 | Worker-replacement trace |
| MEM-04 | `7c84ede584f7` | Binding | Knowledge provider capability contract | — | — |
| MEM-05 | `68a863192e16` | Binding | Checkpoint refresh triggers (stages, decisions, work units, heartbeat, pre-consequential) | D-B9 (to add) | Trigger-rule audit |
| MEM-06 | `a9128189af99` | Binding | WorkerSession record + replacement reconciliation + divergence→Needs Review | D-B9 (to add) | Replacement/divergence traces |
| MEM-07 | `f014b2c07f3f` | Binding | Protected vs generated checkpoint fields; versioned; audited | D-B14 (to add) | Field-class audit |
| MEM-08 | `d36f22e7f321` | Binding | Knowledge layer never canonical for state/decisions/authority; provenance; Disputed records; DAT/TRS/PER obeyed | D-B14 §4 (canonical stores); ConflictRecord | Boundary audit + Disputed-record case |
| MEM-09 | `c60b7eb742b4` | Binding | Interview answers persisted at the moment given; resume from record; §15.3.1 rules | — | — |
| ONB-01 | `c9726f01ce8d` | Binding | One bounded setup session; secrets only via protected surface; staged activation; batched reauth | D-B14 §3 (activation posture noted) | — |
| ORG-01 | `f67bfc9e616a` | Design subject | Arbitrary-depth typed-role tree (roles semantic, not slots) | D-B14 (to extend) | Tree/role representation audit |
| ORG-02 | `7fee3d18a87e` | Design subject | Recursive hubs; tasks leaves with recorded promotion rule | D-B14 (to extend) | Promotion-rule case |
| ORG-03 | `154cbb2525a6` | Design subject | Categories/subcategories orthogonal to hierarchy/stage/status/focus | D-B14 (to extend) | Dimension-independence audit |
| ORG-04 | `50cd62407c64` | Design subject | To-do/To-did layered topic+next-action projections | D-B9 projections (to extend) | Projection-format case |
| ORG-05 | `7e057a2ef945` | Design subject | Excessive unresolved children → housekeeping review | D-B10 aging (to extend) | Threshold case |
| ORG-06 | `9f8047330286` | Binding | Employees use purpose-built apps, never the owner environment | Identity boundary (IDN-01) | — |
| ORG-07 | `5e592e13da1b` | Design subject | Three-question advisory test; capture never gated; quarterly sweeps via AUD-03 | D-B11 (to extend) | Advisory + sweep cases |
| PER-01 | `17f6a4de1615` | Binding | Personal is first-class | D-B10 §2 | Partition parity check |
| PER-02 | `97a2d3d8d79e` | Binding | Personal/Business memory, permissions, records, queues separated | D-B10 §2–§3 | Separation + no-interleave traces |
| PLAT-01 | `f67c42daf206` | Deferred | Discord-first preference | — | — |
| PLAT-02 | `81db94fbce88` | Binding | Discord never sole database/source of truth | D-B14 §4; D-B1 §2 | Authoritative-store audit |
| PLAT-03 | `a010c8b422bc` | Deferred | Companion dashboard only on demonstrated limits | — | — |
| PLAT-04 | `90f994570913` | Binding | Portability across interface/model/memory/host | D-B14 §4; D-B1 §3 c11 | Conceptual-type audit |
| QUE-01 | `092c4637865d` | Design subject | One governed queue: attention classification, caps, batching, dedup, snooze, escalation, aging, load measures | D-B10 §2–§3 (partial) | Field-by-field audit vs exact text |
| RES-01 | `1ea9f096ba22` | Binding | Automated versioned backups + verified restore tests | (to design) | Restore-proof case |
| RES-02 | `d931d286feb2` | Binding | Watchdog independent of host and Discord; silence = safe | (to design) | Independent-liveness case |
| RES-03 | `9a15ef00801d` | Binding | Degraded read-only access + export + recovery runbook | D-B5 §3 (read rows only) | Runbook + export audit |
| SCH-01 | `19bc57988692` | Binding | schema_version everywhere; versioned reversible migrations; backward-readable exports | D-B14 (partial) | Migration-contract audit |
| SCH-02 | `5b110206d776` | Binding | Complete scheduled-run control envelope per the exact field list; hash-bound time-bounded manifest; fail closed | D-B11 (partial) | Field-by-field audit vs exact text |
| SEC-01 | `7a94322e569e` | Binding | Per-stage security gate before activation | Plan §8 (this phase's posture) | Stage-gate security checklist |
| SEC-02 | `587cd73b462e` | Binding | Owner-voice profile controls (authentic samples, separated action classes, no bypass) | — | — |
| TRS-01 | `17e806d30553` | Binding | Envelope carries origin/trust/instruction-authority/sensitivity/verification | D-B2 §2.1, §4 T1–T2 | Envelope validation + twin oracle |
| TRS-02 | `a991d93defba` | Binding | Untrusted content: data not instructions; reduced-tool isolated processing; cannot directly trigger proposals/outbound | D-B2 §4 T2 (authority separation only) | Adversarial content trace per P2G-13 condition |
| TRS-03 | `aa92563d5412` | Binding | Trust class + provenance first-order in the input schema | D-B2 §2.1 | Schema requiredness |
| WF-01 | `7ed4ea904a6c` | Design subject | Topics persist; stages are state not locations | D-B9 state model | Stage-transition trace |
| WF-02 | `7f2bf6060b34` | Design subject | Stages skip/repeat/move backward | D-B9 state model | Nonlinear-transition case |
| WF-03 | `bfd91c58b9e5` | Design subject | Stage/work_status/attention/focus independent canonical dimensions | D-B9/D-B14 | Dimension-independence audit |
| WF-04 | `7a4b5e25684f` | Design subject | Kickoff record per new topic | D-B9 (to add) | Kickoff-record case |
| WF-05 | `ca520e8bf56a` | Design subject | Closeout package per completed child; fold accepted outcomes to parent | D-B4 §2.4; D-B9 Fold-BackEvent | Fold-back fixture; closeout-record audit |
| WF-06 | `f766c52dcdde` | Design subject | Advisory-but-explicit blocking; override needs consequence summary + acknowledgment | D-B9 OverrideEvent; D-B13 consequence field; blocking links | Override-friction trace |
| WF-07 | `de8f4218d5d0` | Design subject | Pause/return/impact state across focus switches | D-B9 (to add) | Focus-switch case |
| WF-08 | `1515729abfa8` | Design subject | One foreground; many background/queued | D-B7 (owner mode); D-B9 focus dim | Focus-dimension case |
| WF-09 | `8dcbd04bad21` | Design subject | Routing dimensions with authority-class resolution (provisional taxonomy fixed) | D-B2 §2.4; D-B6 §2.4 | Dimension→authority-class coverage test |
| WF-10 | `44326723484b` | Design subject | Recommend one, present alternatives, record owner selection | D-B6 outputs; D-B13 options; DecisionEvent | Alternative-presentation trace |
| WF-11 | `d4a3d2f6a7f4` | Design subject | Selective rationale requests on divergence; calibrate | D-B9 LearningEvent (to extend) | Divergence-rationale case |
| WF-12 | `e739d82b45da` | Design subject | Coordinator manages protocol/housekeeping | D-B11 rituals; D-B10 aging | Housekeeping-automation cases |

## Proposed design-phase requirements (DE-R1..DE-R8)

| ID | Text hash | Treatment | Specific mechanism / invariant | Artifact + section | Test / review method |
| --- | --- | --- | --- | --- | --- |
| DE-R1 | `25f115850486` | Design subject (proposed) | Identity concepts + uncertainty-aware dedup designed and traced | design/D-B3 §2–§4 | Per-DE-R acceptance set (plan §5) |
| DE-R2 | `75d505062296` | Design subject (proposed) | Consistency boundaries + CAS/intent designed; six scenarios traced | design/D-B4 §2–§4 | Per-DE-R acceptance set (plan §5) |
| DE-R3 | `cf31054a94dc` | Design subject (proposed) | Dependency-by-capability matrix designed | design/D-B5 §3–§6 | Per-DE-R acceptance set (plan §5) |
| DE-R4 | `73375b7bdab2` | Design subject (proposed) | Deterministic staged policy function designed | design/D-B6 §2, §5 | Per-DE-R acceptance set (plan §5) |
| DE-R5 | `100168f039d7` | Design subject (proposed) | Attention band function within ATT-01 | design/D-B7 §2–§4 | Per-DE-R acceptance set (plan §5) |
| DE-R6 | `984e8966ddef` | Design subject (proposed) | Policy objects + layered composite | design/D-B8 §2–§5 | Per-DE-R acceptance set (plan §5) |
| DE-R7 | `1b2a131b1a4e` | Design subject (proposed) | Event taxonomy + replay definition + outbox direction | design/D-B9 §2–§6 | Per-DE-R acceptance set (plan §5) |
| DE-R8 | `650997c6d0e2` | Design subject (proposed) | Per-class bounded cap policy with full parameter set | design/D-B6 §4 | Per-DE-R acceptance set (plan §5) |

**Coverage:** 125/125 accepted rows rebuilt from exact text; treatments unchanged from the approved plan vocabulary. Gate statuses (incl. the honest Incomplete set) live in `13G_`.
