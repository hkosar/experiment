# D-B9 — Event Model, Cross-Store Integrity, and Replay (DE-R7)

**B-item:** B9 (plan §4). **Status:** Complete (design; the executable replay harness is TASK-0003+ per plan §12). **Authority:** proposed DE-R7 (verbatim, plan §5); LOG-01/02, MEM-01..09, COR-01, APP-04, ACT-01, ORG-01..07, LRN-01..08, CAP-03/CAP-04 (P2A-14). **Depends on:** D-B3 (identities), D-B4 (boundaries/ordering), D-B5 (degradation events), D-B6 (disposition provenance), D-B8 (PolicyVersionEvents). **Feeds:** B1 (events are shape-neutral), B10/B11 (queue/ritual events), B12 (replay-divergence gate test), B14 (schema).

## 1. Objective

Fix the complete event/record taxonomy so every DE-R7 transition class has a typed, append-only representation with stable IDs and provenance; design the cross-store mechanism that exposes partial failure; and define the replay fold whose divergence on any authoritative surface is a gate failure.

## 2. Event/record taxonomy (DE-R7-complete)

Adopts OQ-05's corrected set and closes its gaps. Every event carries: event ID, `ingest_seq`/`caused_by` (D-B4 §3), basis versions (policy/schema/function/calibration), and the D-B3 identities applicable to it (explicit absence otherwise).

| Class | Types | Notes |
| --- | --- | --- |
| Intake | InputEvent, DuplicateDeliveryEvent | Capture layer (D-B4 boundary 1); dedup links per D-B3 §3.3 |
| Interpretation | NormalizationRecord, RecommendationRecord | Model outputs **recorded with model/context/version provenance — never regenerated**; the replay fold consumes these records (DE-R7's no-re-invocation rule) |
| Decision plane | PolicyEvaluationRecord, DecisionEvent (incl. owner approvals with IDN-02 step-up evidence refs), OverrideEvent, AttentionChangeEvent | Each carries its full recorded decision basis (DE-R6) |
| Action plane | ActionRequest (with `aik`), externally-owned ExecutionReceipt and VerificationRecord (**linked by ID, never authored by the engine**), ReconciliationEvent | OQ-09/P2R-05 ownership boundary; executed/verified state derives only from the external records |
| State organization | PlacementEvent, ReclassificationEvent, Fold-BackEvent, IntentEvent (D-B4 boundary 4), ConflictRecord, AgingEvent | ORG placement/rollup/fold-back all event-carried |
| Corrections/learning | CorrectionEvent (COR-01: non-destructive, references what it corrects, never rewrites it), LearningEvent, ObservationEvent (LRN-10 threshold crossings) | Corrections remain weak evidence — a CorrectionEvent never silently feeds authority expansion (DE-R8's exclusion list enforces this at the cap policy) |
| Governance/health | PolicyVersionEvent, DegradationEvent, RefusalEvent, RecoveryEvent, ScheduleEvent (B7 §4) | D-B5/D-B8 integration |
| Economics (P2A-14) | **CostEvidenceRecord** — provider-independent telemetry/evidence record: `{source, coverage_disclosed, amount, basis: billed/estimated/inferred, provenance ref, linked event/action IDs}`; **EconomicReviewEvent** — CAP-04 flag raised when cost-over-value evidence crosses the review threshold, carrying its partition and the protected-class exemption check result | CAP-03 contract schema (live collection = build gate); CAP-04 behavior: the EconomicReviewEvent *creates an AUD-03 review item* — it has no disable authority of any kind, and its schema carries no field that could express one |

**Coverage check against DE-R7's transition list:** input ✔ normalization ✔ recommendation ✔ policy evaluation ✔ decision/approval ✔ attention change ✔ override ✔ ActionRequest ✔ verification linkage ✔ reconciliation ✔ correction ✔ learning ✔ fold-back ✔ aging ✔ degradation ✔ authoritative state transitions (per-object CAS commits are themselves version-stamped record writes, D-B4) ✔ — 16/16, no transition class unrepresented.

## 3. Cross-store integrity (transactional outbox; partial failure exposed)

Stores are separately owned (canonical state, event log, queue projections, external evidence references). Mechanism per DE-R7: every canonical-state CAS commit (D-B4 boundary 2) atomically appends its outbound notifications to an **outbox** in the same store transaction; a relay drains the outbox to the event log and projections with at-least-once delivery (consumers dedup on event ID — D-B3 exact-layer logic reused); the D-B4 boundary-4 reconciliation sweep compares intent/outbox/applied sets and **surfaces any residue as a visible reconciliation item**. Partial failure is therefore a first-class, queryable state — never a hidden divergence (the DE-R7 "exposes partial failure rather than hiding it" clause, mechanically). Cross-store *reads* for evaluation pin versions per D-B4 §2.3.

## 4. Replay fold (the gate contract)

`state = fold(events, recorded_model_outputs)` — no model re-invocation anywhere in the fold. **Must reproduce (DE-R7 verbatim list):** canonical state · authority ceilings · decisions · emitted ActionRequests · queue/attention projections · all UI-observable state. **Any divergence is a gate failure** — not a warning. The harness that executes this fold mechanically is build mechanics → **TASK-0003+** (plan §12 Builder rule); its acceptance contract is fixed here: replay the full event log from empty state, compare every listed surface against the live projections, emit a divergence log that must be empty, plus targeted replays (single case, single day, post-correction COR-01 view). APP-04 falls out structurally: any worker's death loses nothing the fold cannot rebuild, because nothing authoritative lives outside the recorded events.

## 5. Required tests — executed at design level (recorded traces); harness re-execution at B12/build

**Reproduction record (P2A-13):** procedure = taxonomy-coverage audit (§2 table, 16/16) + per-scenario fold walk-throughs (line-cited analysis, plan §4 form); inputs = fixture set `03F_` (SHA-256 `77efff5c…8dfc784` — full value in §1 hash references of prior D-B artifacts), OQ-05/OQ-09 dispositions; the mechanical fold execution is the declared harness obligation above. Coverage limit: design-level walk-throughs prove representability and fold-closure; byte-level divergence checking needs the harness.

| Test | Trace | Verdict |
| --- | --- | --- |
| Replay-divergence surfaces | Fold walk-through of fixture S1 (morning reconnect): every surface the UI shows (queue contents, attention bands, case states) derives from §2 events + recorded model outputs; no surface found requiring live model output or unrecorded state | **PASS (design level)** |
| Check 4 — evidence separation | A12/A16 walk: DecisionEvent + ActionRequest exist; executed/verified state cannot advance — the fold has no rule producing "executed" from engine-side events alone; only a linked ExecutionReceipt ID satisfies it | **PASS** |
| Check 5 — correction path | COR-01 walk: CorrectionEvent references its target; fold produces corrected current-view while the original record remains reproducible at its version; DE-R8 exclusion list keeps corrections out of expansion evidence | **PASS** |
| Cross-store partial failure | Outbox walk: crash between CAS commit and relay → outbox residue visible; reconciliation item surfaces; no silent divergence window beyond the visible residue | **PASS** |
| Worker-loss resumption (APP-04) | Kill any worker mid-pipeline: durable state = events already committed; resumption = fold + continue; nothing authoritative in worker memory | **PASS** |
| CAP-03 schema checks | CostEvidenceRecord carries coverage/billed-estimated-inferred/provenance/linkage fields; provider-independent (source is a field, not a schema variant) | **PASS** |
| CAP-04 event representation | EconomicReviewEvent → AUD-03 review item in the correct partition; schema carries no disable authority; protected-class exemption check recorded on the event | **PASS** |

## 6. Calibration-state resolution (D-B2 §5 escalation — resolved)

Decision: calibration state lives as a **policy-plane object version** (`calibration_version`), referenced in every PolicyEvaluationRecord's basis — not a per-envelope field. Rationale: calibration changes are governed events (check 2), not per-input facts; putting them on the envelope would duplicate policy-plane state into every input and invite drift. The SV-1 envelope therefore stays as frozen; the evaluation basis (D-B6 §2.1) carries `calibration_version` alongside `policy_version`. B14 schema reflects this. D-B2 §5's gap is closed without touching frozen discovery authority.

## 7. Acceptance criteria — met

Zero unexplained divergence in design-level fold walks; executed/verified state derives only from externally owned receipts/records referenced by ID; every DE-R7 transition class has an event/record type (16/16); partial failure is exposed, not hidden; CAP-03/CAP-04 records representable with their required fields.

## 8. Falsifier / reopen condition

Reopens if any state transition is found unrepresentable as an event without model re-invocation (design-gate blocker — none found), or if the build-phase harness finds a divergence the design-level walks missed (then the specific surface's design reopens, not the whole taxonomy). Not triggered.

## P2G-11 correction — store-ownership and transition matrix; expanded replay basis

**The outbox contract covered only canonical-CAS commits; every authoritative store now has exactly one owner and one recoverable event path.**

| Object/transition | Authoritative store | Write authority | Atomic event/outbox mechanism | Source receipt/hash | Reconciliation | Replay input | Projections | Failure behavior |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Raw input intake | Intake log | Intake writer (per partition) | Append IS the event (single durable write) | Content hash + source identity per D-B3 | Buffer drain dedup (D-B5 §5.1) | Yes — IngestionEvent | Feed all | No ack without durable append (F1/F10) |
| Canonical state mutation | Canonical store | Engine via CAS | Transactional outbox: state row + event row commit together; publisher drains outbox | Object version chain | Outbox sweep exposes unpublished | Yes | Topic/case views | CAS miss → retry/ConflictRecord |
| Policy plane change | Policy store | Policy-plane writer (serialized) | PolicyVersionEvent IS the change (event-sourced plane) | Policy body hash | Epoch check (P2G-05) invalidates stale authorizations | Yes | Active-policy view | Unversioned change structurally impossible |
| Schedule plane | Schedule store | Scheduler | ScheduleEvent + ExpectedRun written together at scheduling time | Envelope hash (P2G-08) | Watchdog deadline audit (D-KR §3) | Yes | Due-run view | Dead scheduler detected externally |
| Queue admission/aging | Queue store (per partition) | Queue writer per partition | Admission/AgingEvent with per-partition CAS | Item refs | Per-partition sweep | Yes | Desk views | Partition isolation (PER-02) |
| Identity/session config | Identity config store | Identity service | IdentityEvent (grant/revoke/step-up policy) | Config hash | Kill-plane override (D-KR §1.2) | Yes | — | Fail closed on unknown (F5) |
| External receipt/verification | Evidence store | **Ingestion only — never engine-authored** | Receipt enters as an immutable **EvidenceIngestionEvent** carrying source identity + content hash; linkage by reference | Source-system identity + content hash | ACT-01 reconcile-before-retry | Yes | Executed/verified views | Missing receipt ⇒ state cannot advance (check 4) |
| Connector/registry change (BUS-10) | Registry store | Registry writer | RegistryEvent (no secret values — secrets live only in the secret manager) | Reference-doc hash | Freshness audit → Data HQ health + AUD-03 | Yes | Health view | Stale ⇒ health flag, never silent |
| Kill-plane commands | Control-service journal (external) | Control service | Journal append; mirrored into event log on reconnect | Command receipt | D-B5 §5 step 2 | Yes (mirrored) | — | Kill never depends on engine log (D-KR §1.4) |

**Expanded replay basis (DE-R7 corrected):** the fold consumes — in recorded order — ingestion events, recorded model outputs, policy/identity/schedule/connector/evidence-ingestion events, and canonical events. Every external fact enters as an immutable ingestion event with exact source identity and content hash **before** any state depends on it; nothing folds from live lookups. The worker-loss claim is downgraded to `design-complete / build-verification pending` until the executable fold (P2G-02 comparator) runs over this full basis.

## P2G-03 correction — the DEC-02 consequential-decision falsifier contract

Every DecisionEvent/record classified consequential under the impact/risk policy carries:

```text
falsifier_status: identified | unknown | none_identified
falsifier_statement                      # evidence/conditions that would materially change or reverse the decision
supporting_or_disconfirming_evidence_refs[]
review_trigger                           # the event/condition that forces governed re-review
rationale_when_unknown_or_none           # required for unknown / none_identified — no false precision
last_evaluated_at
```

Carried through: the event taxonomy (this section), the schema (D-B14 P2G-12 section), the replay basis (falsifier fields reproduce on replay), the owner card tap-through (D-B13 — "what would change this decision"), and the correction path (a matching `review_trigger` event opens a governed re-review linked to — never rewriting — the original decision). **Tests:** positive — a consequential filing-policy decision carries `identified` + trigger; a later matching event opens re-review with the original intact (simulated). Unknown — a decision records `unknown` + rationale + time-based trigger; validator accepts, no false precision forced (simulated). Both cases re-execute in the P2G-02 trace set.

## Small-item closures (exact-requirement mechanisms)

- **AUT-07:** `AssignmentRecord` (assignee, scope, consequence class) linked to its closeout: delegation transfers execution; the record keeps coordinator accountability until a CloseoutPackage with completion mode resolves it.
- **AUT-09:** completion mode enum on closeout/verification linkage: `verified (external evidence) / owner-accepted (explicit owner event) / needs-review` — exactly the three accepted modes.
- **COR-01:** the seven operations enumerated as typed CorrectionEvents: `re-parent, merge, split, reclassify, promote/demote, duplicate-link, archive` — all history-preserving folds behind the one-tap "Wrong place" gesture (D-B13), each feeding calibration as weak evidence.
- **MEM-05:** checkpoint refresh triggers: stage transition, recorded decision, bounded work-unit completion, heartbeat interval, before any consequential external action — each a CheckpointEvent.
- **MEM-06:** `WorkerSession` record (identity, heartbeat, execution journal ref, last confirmed side effect); replacement reconciles checkpoint vs branch vs event log; divergence ⇒ Needs Review.
- **MEM-08:** knowledge-layer claims admit only with provenance; conflicts create a versioned `Disputed` record linking competing claims into governed resolution (ConflictRecord subtype) — the knowledge layer never owns state/decisions/authority (store matrix above).
- **WF-04/WF-05:** `KickoffRecord` on topic creation; `CloseoutPackage` (outcome, evidence refs, completion mode, fold-back targets) on child completion.
- **WF-11:** selective-rationale rule: owner divergence from a recommendation MAY prompt one rationale request per the calibration policy (rate-limited, never blocking); response recorded as a LearningEvent.
- **ORG-04:** To-Do/To-Did projections: layered topic + next-action format, derived views over canonical state + events (never authoritative), AUT-11 reconciliation preserves To-Did history.

## P2S-06 correction — deterministic cross-store fold order

**"In recorded order" was undefined across separately sequenced stores.** The corrected contract:

### Ordering-key declaration (every authoritative event type)

| Event family | Ordering key | Causal dependencies (`caused_by[]` mandatory refs) | Conflict behavior | Fold phase |
| --- | --- | --- | --- | --- |
| PolicyVersionEvent / lease events | Policy-plane sequence (one total order — D-B4 §2.3) | Prior policy version | Serialized — none possible | 1 (control) |
| IdentityEvent | Identity-store sequence | Prior identity state | Serialized per store | 1 (control) |
| ScheduleEvent / watchdog registrations | Schedule-store sequence | Schedule spec version | Serialized per store | 1 (control) |
| RegistryEvent | Registry sequence | Prior registry state | Serialized per store | 1 (control) |
| IngestionEvent (intake) | `(intake_partition, ingest_seq)` | None (roots) | Append-only — none | 2 (facts) |
| EvidenceIngestionEvent (receipts/verifications) | Evidence-store sequence | The ActionRequest it answers | Append-only | 2 (facts) |
| RecordedModelOutput | Ingestion ref + invocation seq | Its input event | Append-only | 2 (facts) |
| Canonical events (decision/correction/fold-back/queue/attention/aging) | Per-object version chain | Basis events (envelope, policy version, model outputs, prior object version) | CAS — miss retries or ConflictRecord | 3 (derivations) |

### Deterministic fold

The fold is a **causal topological sort with a total deterministic tie-break**: an event is eligible when every `caused_by[]` ref is folded; among eligible events, order = **fold phase → store priority (control-journal < policy < identity < schedule < registry < intake < evidence < model-output < canonical) → partition/object key (lexicographic) → store sequence**.

> **Amendment (2026-07-30, correction cycle 2 / TASK-0003 R1 review):** the store-priority list above originally omitted the external control-service journal that P2G-11 row 9 already names as the authoritative store for kill-plane commands — the fold order for its mirrored events was undeclared, a genuine gap surfaced when the behavioral simulator had to place `KillCommandEvent`/`KillReceiptEvent` in the tie-break. The list now declares **`control-journal` first**, ahead of the policy plane: kill-plane supremacy (IDN-03; D-KR §1.2) means a folded kill command must precede any same-phase policy or engine event it ties with, and kill efficacy never depends on engine-log state (D-KR §1.4 — an independence property; the fold-order placement is this amendment's, not §1.4's). Mirrored control-journal events remain replay inputs per P2G-11 row 9 ("mirrored into event log on reconnect"). No other row changes. Every component is recorded data — no wall-clock, no arrival nondeterminism. **Commutativity statement:** phase-2 fact events from different partitions/stores are mutually independent by construction (no shared state, no cross-refs except into phase 1) — their relative order cannot change any phase-3 derivation because every phase-3 event names its complete basis explicitly in `caused_by[]`; the tie-break therefore only fixes *presentation* order for facts, while phase-3 events are ordered by their own version chains. Non-commutative pairs are exactly: same-store sequenced events (ordered by their store sequence) and causal chains (ordered by the topology).

**Shuffle-invariance requirement (simulator, P2S-06 set):** the behavioral fold must produce byte-identical final state, projections, and divergence lists when fed the same event set under multiple seeded delivery-order permutations that preserve causal edges (fixed seed list — deterministic reproducibility while exercising order-independence). Any difference is a gate failure.
