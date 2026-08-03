# CP-P2-A — Decision Engine Design Phase Change Plan (Revision 2, corrected; presented for owner approval)

**Status:** Revision 2, corrected — the verifier's scoped confirmation returned **PASS WITH TWO PRE-AUTHORIZED CONTROL CORRECTIONS** (`16_Verifier_Scoped_Confirmation_CP-P2-A_Rev2.md`, SHA-256 `b84dd3e4667431db8e60a17c214a59299dc0aa55a8c8ae571df50f13a8a8810b`; P2A-01..P2A-12 substantively closed). The two corrections, **P2A-13** (gate-evidence/status contract, reproduction records, scorecard preregistration — §4, §6, §7, `13G_`, `13V_`) and **P2A-14** (CAP-01..CAP-04 operationalization — §7, §12, B9/B10/B11/B14, `13M_` CAP rows), are applied in this document under the confirmation's §5 pre-authorized correction path: the DE-R texts are byte-identical, S1/S2/S3 remain equally viable, owner decisions are not reopened, and the v1.3 baseline is untouched. **Per the confirmation, owner plan approval is AUTHORIZED; design execution and TASK-0003+ Builder authorization remain BLOCKED until owner approval.** Revision 1 lineage: review `14_Verifier_Response_CP-P2-A_Rev1.md` (PASS WITH CHANGES, twelve findings, all concurred in `15_P2A_Dispositions.md`; SHA-256 `5030ef513d4d89bc56b273015619453ff070f2adfeede5470bd33313304757db`).

**Review lineage:** Revision 1 (SHA-256 `6049f60d352bc3363fabe3702a700b26e46de0cf771c587b658892e768e1fa16`) reviewed at gate commit `0c2a7c79a0a2d6b3c9588bc2d2ad2a76304d2543`, tree `0e07a04693d2aaef66c19c8fa4a64838cd57e420`; packet `d48bc5cd49b6c0d3747179bdd782741740167e4607a67d835ead615bd74bcaee` verified 12/12 + 12/12 + 1/1. OD-1, OD-2 with DE-R8 modification, OD-3, and discovery acceptance (trail entry 82) were **not reopened** and are not reopened here.

**Roles (standing separation):** Fable — architect/designer, planner, project manager, dispositions; ChatGPT — independent verifier; Claude Opus 5 — Builder for separately authorized TASK-0003+ only (APP-05 template `../v1.2-ideas-pass/19_`); Hunter — owner, final authority.

---

## 1. Canonical identity and frozen Design Authority Manifest

### 1.1 Canonical identity

- **Canonical parent:** **TOPIC-0002** (Phase 2 — Decision Engine; `../v1.2-ideas-pass/bootstrap_id_registry.md`). All design work items, TASK-0003+ allocations, and gate records attach to this topic.
- **Change-plan ID:** CP-P2-A. **This document:** Revision 2. **Version identity (N-03 pattern):** the design outputs form a **v1.4-proposed** layer; change log `../phase1-audit-v1.0/07c_Change_Log_v1.3_to_v1.4.md` at build time; the post-release owner event is **acceptance of v1.4**.
- **No-self-hash rule:** the approved revision of this plan is identified at approval time by its SHA-256 recorded in the trail/gate record of that event; this document cannot contain its own hash.

### 1.2 Design Authority Manifest (frozen; P2A-02)

Design execution reads **only** the objects below. Paths are relative to `fable/phase2-decision-engine/` unless noted. Each object is bound by SHA-256 (and Git blob where stated); the corpus is reproducible from the repository history plus this table.

| # | Authority object | Path | SHA-256 |
| --- | --- | --- | --- |
| 1 | Accepted v1.3 Operating Manual (owner acceptance trail entry 73; historical filename) | `../phase1-audit-v1.0/04_Proposed_Operating_Manual_v1.1.md` | `30b020c5724308373c289c28c030c48e8cbdb6d317062dea0e9197a69219f867` (blob `2bbb3904fce278c07be43a6833caab5d5f86c099`) |
| 2 | Accepted v1.3 Requirements Register (md) | `../phase1-audit-v1.0/05_Requirements_Register_v1.1.md` | `972be5cad10061e66b855425e97de44edc196d845a57710aa36f407fdcc95046` (blob `f5d49b4417591f499dd68a2aeada940ec51ef8dd`) |
| 3 | Accepted v1.3 Requirements Register (csv, 125 rows) | `../phase1-audit-v1.0/05_Requirements_Register_v1.1.csv` | `8fb88b6b6bd762029703f24a8a0bbb5f61284f58a9c3a9eceb69c5c010ffb24c` (blob `0785b81d64e6388e1b7f4693ebf32064dc962322`) |
| 4 | Owner-approved discovery plan (P2-DP Rev 2 body) | `00_Phase2_Discovery_Plan.md` | `75c636801ef112f08876c17f5dde28caa0d628c838fed8d8d917c19ce3bc7c99` |
| 5 | Frozen discovery intent corpus manifest (single-tree snapshot at discovery-gate commit `fa01b9d`; validator `04V_`, 13/13) | `04_Discovery_Source_and_Exclusion_Manifest.md` | `136cd8ac15a5dae586d31331c199fd5328d708770daf806ad468169d3b9803a1` |
| 6 | Frozen authority trail, entries 41–75 (byte-preserved) | `06_Frozen_Authority_Trail_41-75.md` | `60c55ee0f0db610208ee90a55c64550172612012ce6f6b7b253782e470999828` |
| 7 | Discovery report (corrected, verifier-confirmed) | `01_Decision_Engine_Discovery_Report.md` | `44cf800e083504d95e097faedd689eeea255d6949adcaf3225ddafbea9d15286` |
| 8 | Open-question dispositions OQ-01..10 (corrected) | `02_Open_Question_Dispositions.md` | `868f425d80d2c6ad3ee3f4c76768b5841e47be3fd2dcf7b87957465227cfcd3b` |
| 9 | Discovery authority and traceability matrix | `00A_Discovery_Authority_and_Traceability_Matrix.md` | `e632678576dd52617a01021df45aa1ad585abef57d42cef51e3586b19f1e086b` |
| 10 | Scenario and adversarial replay matrix (26 discovery + 1 design-gate case) | `03_Scenario_and_Adversarial_Replay_Matrix.md` | `520540b535a39fbef331a5fdcd346215b9f49853a8c1a236358786943b3aa72e` |
| 11 | Replay fixtures, schema SV-1 (27 fixtures, 35 structured envelopes) | `03F_Replay_Fixtures.json` | `77efff5c051c4c31ddbe8768d4d06027076641b923704d8b28483216d8fcb784` |
| 12 | Replay count reconciliation | `03R_Replay_Count_Report.txt` | `d708b16608ece676cd20e7b30bf8863e6fa398052e8079d825082ed8078ff879` |
| 13 | Fixture envelope validator | `03V_validate_fixture_envelopes.py` | `8ba5d05d02d8ea53cee60f94200a3b4599d0450fd91f8c72fbd9ad9cb7668b70` |
| 14 | Owner decision package as decided | `04_Owner_Decision_Package.md` | `cd212cc1cbb325ab4e0090524eb838954480363e73c10ac2a2b4b7d15b5b4f7c` |
| 15 | Owner gate record — OD-1, OD-2(+DE-R8), OD-3, discovery acceptance (trail entry 82) | `12_Owner_Gate_Record.md` | `988b3f68b650f2c82172b93c4c4dd0eb25f444181aaa1d82cdc610bbd524162a` |
| 16 | Verifier record — post-discovery review | `07_Verifier_PostDiscovery_Response.md` | `9c0d0d039af22c183259cae62f3c975f9e25967c24b46a0f5a98c3cd38ad33c1` |
| 17 | Verifier record — scoped re-verification | `09_Verifier_Scoped_Reverification_P2_Discovery.md` | `dd917981d4ba4d0213022e69afbb7d60447117fd4f950c096af7446046c7039d` |
| 18 | Verifier record — narrow confirmation | `11_Verifier_Narrow_Confirmation_P2R.md` | `134f707a930092d170084f9191186a9a04ad9808b0412f2081220cec25456383` |
| 19 | Verifier record — CP-P2-A Revision 1 review | `14_Verifier_Response_CP-P2-A_Rev1.md` | `5030ef513d4d89bc56b273015619453ff070f2adfeede5470bd33313304757db` |
| 20 | This plan's approved revision + its applicability matrix `13M_` and validator `13V_` | `13_`, `13M_`, `13V_` | identified at the approval event per §1.1 (no self-hash) |

### 1.3 Exclusions (with rationale)

- **The live decision trail after entry 82** — control-plane record only; admission solely via §1.4. The frozen intent corpus ends at entry 75; entries 76–82 enter only through the gate records listed above.
- `05_Design_Phase_Change_Plan_Proposal.md` — nonbinding draft, wholly superseded by this plan.
- `03_Requirements_Applicability_Matrix.md` — discovery-stage checklist; superseded **for design purposes** by `13M_` (P2A-02); remains the discovery record.
- `02_P2_Finding_Dispositions.md`, `08_P2D_Dispositions.md`, `10_P2R_Dispositions.md`, `15_P2A_Dispositions.md` — process records whose outcomes are already folded into the frozen deliverables above.
- The original ChatGPT Phase 1 baseline packet and all pre-v1.3 layers — superseded by the accepted v1.3 baseline (rows 1–3).
- The Nate Herk research corpus — consumed by accepted CP-v1.2-B; only the accepted v1.3 requirements carry its authority.

### 1.4 Later-entry admission rule (change control; P2A-02)

Later owner signals, new evidence, or new trail entries enter the design corpus **only** through: (a) a **versioned amendment to this plan** (Revision N+1 through verifier review → Fable dispositions → owner approval where owner intent changes), or (b) a **bounded MEM-09 admission** — a dated manifest addendum naming the admitted object and hash, its scope of effect, and the affected B items, logged in the decision trail. Opportunistic reads of the growing live trail are prohibited; design work cites only §1.2 objects and logged admissions.

## 2. Design Requirements Applicability Matrix (plan-specific; P2A-02)

The complete matrix is `13M_Design_Requirements_Applicability_Matrix.md`, machine-validated by `13V_validate_design_matrix.py` against the accepted register: **125/125 accepted requirements** in register order, each mapped to exactly one treatment — **Binding: 60; Design subject: 60; Deferred: 3; N/A: 2** *(restamped from 53/67 by a §1.4 versioned amendment per P2S-08 — the P2G-01 exact-text rebuild honestly reclassified seven rows between the two equally-gate-required categories; no owner intent touched; verifier review of this amendment rides with the corrected packet)* — with B-item owner, design artifact, and gate test per row, plus the eight proposed DE-R rows (treatment *Design subject (proposed)*; acceptance status per §9). Semantics: **Binding** = invariant on every design output; **Design subject** = the design determines operationalization and never means optional-to-honor; **Deferred/N/A** rows carry rationale and any discovered dependency escalates via §1.4. It becomes the design execution checklist only after owner approval of this plan.

## 3. Item 0 — versioned standing-role refresh to Claude Opus 5 (isolated mechanical; P2A-10 method)

Closes the trail-69 backlog as a governed change **without rewriting history**:

1. **GOV-01 amendment** — replacement register text (verifier's form, adopted verbatim), carrying an explicit **`Amended v1.4`** status marker and the APP-01 portability basis:

> **GOV-01** — Standing program roles: Fable (architect/designer, project manager, integration owner, stage-gate approver), ChatGPT (independent verifier), Builder role currently assigned to Claude Opus 5 under APP-01 provider portability, Sonnet (reader/context librarian), and owner (final authority), with the boundaries of Manual §20A.1.

2. **Current-facing tables** — update every current-facing role/configuration surface, explicitly including the **§12.1 Builder mapping** where presented as current, §12.1.1 role tables, and §20A.1, each tagged *(v1.4 — CP-P2-A Item 0; trail entries 69/82)*.
3. **ADR-019 is preserved, not rewritten** — append a dated amendment note to ADR-019 stating that the Builder assignment changed from Claude Opus 4.8 to Claude Opus 5 at trail entry 69 (owner-authorized standing substitution) while role boundaries remained unchanged. The 2026-07-25 decision text stays byte-intact.
4. **History preserved** — the Phase 1 current-state inventory, TASK-0001/TASK-0002 records, and all time-of-event records remain byte-identical.
5. **Scan report** — acceptance evidence is an explicit **included-path/excluded-path scan report**: included = current-facing Manual sections and register text; excluded (with the reason "historical record") = enumerated historical files. No unqualified repository-wide zero-count claim is made.

**Acceptance criteria:** amended GOV-01 text in place with `Amended v1.4` status; ADR-019 amendment note appended with original text byte-intact; scan report shows zero current-facing standing-role naming of Opus 4.8 within the included paths and enumerates every excluded path with rationale; TASK-0001/0002 records byte-identical.

## 4. Part B — item-level design execution contracts (B1–B14; P2A-01)

Every item carries the same contract fields: **Objective · Authority (accepted requirement IDs per `13M_`) · Inputs/dependencies · Output artifacts (§11 paths) · Alternatives kept viable · Decision owner · Required tests · Evidence and independent reproduction · Acceptance criteria · Falsifier/reopen · Downstream dependencies.**

**Common gate-evidence contract (P2A-13):**

- **Status enum** (per B item in `D-B12` and per requirement row in `13G_`): `Not started / Complete / Incomplete / Blocked / Build-gate deferred / Deliberately deferred / N/A`.
- **Final-gate rule:** every Binding, Design subject, and proposed DE-R row must be `Complete` or an explicitly permitted `Build-gate deferred` item cited to §7. `Not started`, `Incomplete`, and `Blocked` block the design gate. `Deliberately deferred` requires the plan-authorized rationale and a recorded gate disposition.
- **Independent-reproduction record — mandatory in every D-B artifact:** input/object hashes; exact procedure or commands (for non-executable analysis, a deterministic line-cited reasoning procedure); tool/environment versions; expected result; actual result; trace/evidence hashes; falsifier outcome; known coverage limits.
- **Machine validation:** the requirement-level overlay is `13G_Design_Gate_Status_and_Evidence_Matrix.md` (all 133 IDs — 125 accepted in register order + DE-R1..DE-R8 — with `Gate status`, `Evidence pointer`, and `Test result` columns). `13V_validate_design_matrix.py` validates the overlay's structure and enum in every run and, in `--final-gate` mode, fails the gate while any required row remains `Not started`, `Incomplete`, `Blocked`, or unsupported by evidence. A reviewer determines every B-item and requirement-row gate result from `D-B12`, `13G_`, and the §7 matrix without inference.

### B1 — Record-shape comparison (S1 / S2 / S3)

- **Objective:** normalized typed-record schemas for S1 (aggregate root), S2 (Decision Case linking separately-owned typed records), S3 (independent records/events + projections), compared under the §6 neutral scorecard to a design-gate selection or explicit deferral.
- **Authority:** discovery report §candidates; P2R-04 carry rule; PLAT-02, PLAT-04, APP-01, APP-02, MEM-01, LOG-01/02, DEC-01/02.
- **Inputs/dependencies:** `03F_` fixtures; B2 (shared field semantics); B4 (consistency boundaries).
- **Outputs:** `design/D-B1_Record_Shape_Comparison.md` (three schemas + scorecard results).
- **Alternatives kept viable:** S1, S2, S3 — equivalent authority, evidence, persistence, concurrency, and projection capabilities; a hybrid S2+projection result does not count as an independent S3 evaluation; S2 remains leading hypothesis only.
- **Decision owner:** design gate per §6 selection rule (owner decides only if owner-visible tradeoffs surface; §9).
- **Required tests:** all 27 fixtures per shape under the constant common policy; B3 identity tests; B4 interleavings; E2E-1.
- **Evidence:** per-shape machine-checkable replay traces; scorecard with §6 pre-declared criteria/weights.
- **Acceptance:** every scorecard criterion scored with cited trace evidence; selection or explicit deferral recorded with rationale.
- **Falsifier/reopen:** a shape structurally failing a Binding invariant is eliminated only with the failing trace and verifier concurrence; if all three fail one criterion, the criterion's source requirement is escalated via §1.4.
- **Downstream:** B9, B14, the build change plan.

### B2 — Field-authority contract (OQ-02)

- **Objective:** normative specification of authoritative control fields, deterministic derived fields, and model-proposed semantic fields with the lower/escalate-only rule; explicit disagreement/unknown/disputed behavior; enumeration of the **mandatory authority-bearing controls** whose absence triggers DE-R4 fail-closed (P2A-06).
- **Authority:** TRS-01..03, DAT-01/02, IDN-01/02, SEC-01/02, WF-09.
- **Inputs/dependencies:** SV-1 envelope schema (`03F_`/`03V_`); OQ-02 disposition.
- **Outputs:** `design/D-B2_Field_Authority_Contract.md`.
- **Alternatives kept viable:** none required — the contract is additive over the accepted trust envelope.
- **Decision owner:** Fable, verifier-reviewed.
- **Required tests:** mandatory-envelope validation; twin-input injection oracle; zero-instruction-authority test for external-untrusted content used as semantic data (P2A-06 — no blanket quarantine).
- **Evidence:** field census table mapping every SV-1 field to its authority class; executed oracle traces.
- **Acceptance:** every field classified; every mandatory control named; untrusted content remains semantically analyzable with zero instruction authority.
- **Falsifier/reopen:** any field needing model-supplied authority to function → reopen against TRS-01..03 via §1.4.
- **Downstream:** B3, B6, B7, B8, B12.

### B3 — Identity and deduplication (GAP-2, open-blocking; DE-R1)

- **Objective:** design the five identity concepts with instantiate-only-when-applicable semantics, explicit absence, and source-aware, fingerprint-version-aware, uncertainty-aware dedup per revised DE-R1.
- **Authority:** ACT-01, LOG-01, MEM-04; proposed DE-R1.
- **Inputs/dependencies:** B2 (identity fields' authority classes); source inventory from discovery.
- **Outputs:** `design/D-B3_Identity_and_Deduplication.md`.
- **Alternatives kept viable:** fingerprint algorithm/versioning alternatives carried until tested.
- **Decision owner:** Fable, verifier-reviewed.
- **Required tests (DE-R1 acceptance set):** no false-merge of distinct legitimate identical events; transformed-redelivery detection; routine no-case processing; source-without-native-ID processing; one idempotency key per action attempt.
- **Evidence:** executed test traces over fixture-derived and synthetic event streams.
- **Acceptance:** all five DE-R1 acceptance tests pass on the designed mechanism; absence semantics explicit in the schema.
- **Falsifier/reopen:** a legitimate stream indistinguishable from a duplicate under every carried fingerprint design → GAP-2 escalates to the owner package as residual risk.
- **Downstream:** B4, B6, B9, B14.

### B4 — Concurrency and ordering (DE-R2)

- **Objective:** define the consistency boundaries (pre-placement intake, topic/object state, policy and queue state, cross-object operations), the serialization or CAS/optimistic protection per boundary, causal/source-order recording, the total-order-vs-conflict-detection decision per boundary, and the DP-001 capture-latency bound.
- **Authority:** proposed DE-R2; MEM-01..03; DP-001 (Manual); ACT-01.
- **Inputs/dependencies:** B3 identities; B1 shape candidates (boundary definitions must be shape-neutral).
- **Outputs:** `design/D-B4_Concurrency_and_Ordering.md`.
- **Alternatives kept viable:** per-boundary mechanism choices (serialization point vs CAS) remain open until tested; no global total order presumed.
- **Decision owner:** Fable, verifier-reviewed.
- **Required tests (DE-R2 acceptance set):** unplaced inputs; same-topic conflicts; cross-topic reclassification; policy changes racing evaluation; duplicate delivery; multi-object fold-back.
- **Evidence:** interleaving matrices with recorded outcomes; declared latency bound with its protection argument.
- **Acceptance:** every tested interleaving prevents lost updates and records unresolved conflicts; capture acknowledgment occurs only after durable intake commit within the declared bound.
- **Falsifier/reopen:** any boundary where no carried mechanism prevents lost updates → design-gate blocker.
- **Downstream:** B1, B9, B10, B14.

### B5 — Degraded operation (DE-R3)

- **Objective:** the dependency-by-capability matrix — for each failed/stale/disputed dependency (canonical state, policy, identity, append-only logging, evidence services, intake store), the proven-safe capability set; kill/revoke effective in every mode; recovery reconciliation.
- **Authority:** proposed DE-R3; RES-01..03, IDN-03, MEM-01..08.
- **Inputs/dependencies:** B4 boundaries; B9 event set (degradation/refusal events).
- **Outputs:** `design/D-B5_Degraded_Operation_Matrix.md`.
- **Alternatives kept viable:** none — the matrix replaces the Revision 1 single-ladder presumption per P2A-05.
- **Decision owner:** Fable, verifier-reviewed.
- **Required tests:** each dependency independently; combined failures; intake-queue unavailability (no acknowledgment without durable persistence); stale snapshots; kill during degradation; recovery with duplicate/conflicting events (A10/A15 oracles).
- **Evidence:** executed matrix — one row per failure mode with tested capability outcome.
- **Acceptance:** no external mutation or autonomous side-effecting action at any tier in any degraded mode; every degradation/refusal is an event; recovery reconciles before ordinary authority resumes.
- **Falsifier/reopen:** any failure mode with no safe capture path → escalate as an owner-visible availability/safety tradeoff (§9).
- **Downstream:** B6, B9, B10.

### B6 — Tier/policy function, OD-2 policy objects, and DE-R8 autonomy expansion (DE-R4, DE-R8)

- **Objective:** the versioned deterministic policy function per revised DE-R4 (verified mandatory control envelope; lower/escalate-only model influence; full output set including placement/relationship/blocking/disposition recommendations and the required receipt/evidence contract); the OD-2 starting-autonomy policy objects (filing/routing, 20/day, batched overflow); the complete DE-R8 per-class cap-policy schema with every P2A-09 parameter.
- **Authority:** proposed DE-R4/DE-R8; AUT-01..12, WF-01..12, TRS-01..03, IDN-02/03, BUS-01..10; owner gate record (`12_`).
- **Inputs/dependencies:** B2 (mandatory controls); B3 (identity inputs); B8 (policy-object representation).
- **Outputs:** `design/D-B6_Tier_Policy_Function_and_Autonomy.md`.
- **Alternatives kept viable:** policy-function decomposition alternatives until tested; DE-R8 evidence-rule parameterizations compared before fixing defaults.
- **Decision owner:** Fable, verifier-reviewed; **material change to DE-R8's owner intent → owner decision (§9)**.
- **Required tests:** hypothesis checks 2 and 3; WF-09 routing-dimension coverage; untrusted-content semantic-use (with B2); and the eleven DE-R8 tests: sparse sample, delayed regression, cross-category contamination, missing provider telemetry, manipulated success labels, cap oscillation, maximum-bound enforcement, owner reduction, owner increase with step-up, automatic contraction, and kill/revoke during expansion.
- **Evidence:** decision-table traces from (envelope, policy version) pairs; executed DE-R8 simulation runs on recorded/synthetic evidence streams.
- **Acceptance:** identical inputs yield identical outputs across the carried record shapes; every DE-R8 parameter has a designed default and bound; all eleven DE-R8 tests pass in design-level simulation.
- **Falsifier/reopen:** any input requiring raw-content consultation to compute tier (beyond the recorded separation-falsifier threshold) feeds check 6; a DE-R8 safety parameter that cannot be evidenced without engine self-attestation → redesign of the evidence sourcing before the gate.
- **Downstream:** B7, B10, B12, B13.

### B7 — Attention band and quiet-hour scheduling (DE-R5; OD-1)

- **Objective:** the deterministic attention-band function per revised DE-R5 over tier, action-class risk, blocking, aging, domain partition, owner mode, system health/degradation, and the versioned interrupt/quiet-hour policy; OD-1's ratified operating policy encoded as versioned policy objects (verified-event triggers, corroboration bar, quiet hours 10 PM–6:30 AM tunable, contacts-as-scrutiny-signal, ambiguity holds except physical-danger/security).
- **Authority:** proposed DE-R5; ATT-01..03, SCH-01; OD-1 (`12_`).
- **Inputs/dependencies:** B6 outputs; B8 policy representation; B5 health states.
- **Outputs:** `design/D-B7_Attention_and_Quiet_Hours.md`.
- **Alternatives kept viable:** band-boundary calibrations carried as versioned policy parameters, never hard-coded.
- **Decision owner:** Fable, verifier-reviewed; OD-1 policy content is owner-ratified and not modifiable here.
- **Required tests:** attention fixtures; ATT-01 boundary cases (Critical only via owner-ratified policy on verified evidence; model output never qualifies or suppresses); quiet-hour scheduler cases including the fail-toward-interrupt exceptions.
- **Evidence:** band-function decision tables; executed fixture traces.
- **Acceptance:** deterministic bands across replays; OD-1 objects reproduce the ratified policy exactly; no recalibration path outside PolicyVersionEvents.
- **Falsifier/reopen:** any Critical emission reachable from unverified evidence → design-gate blocker.
- **Downstream:** B10, B12, B13.

### B8 — Policy objects and precedence (DE-R6)

- **Objective:** the policy-object type per revised DE-R6 (scope, authority domain, explicit priority, applicability predicate, effective window, conflict behavior, non-overridable protection floors, exception authority only where permitted, supersession target, schema compatibility, rollback pointer) and the four-alternative precedence comparison.
- **Authority:** proposed DE-R6; AUT-06, GOV-02, MEM-09.
- **Inputs/dependencies:** B2; B6; the four precedence alternatives from discovery (explicit priority+authority; deny/safety-floor; equal-priority fail-closed; owner-scoped exception with supersession target).
- **Outputs:** `design/D-B8_Policy_Objects_and_Precedence.md`.
- **Alternatives kept viable:** all four precedence models until the dedicated replay comparison completes.
- **Decision owner:** design gate; owner package if the precedence choice is owner-visible (§9).
- **Required tests:** dedicated precedence replay cases including equal-priority fail-closed and owner-scoped exceptions that cannot supersede a declared protection floor; full decision-basis replay per revised DE-R6; rollback-vs-history test (rollback changes future evaluation only).
- **Evidence:** per-alternative replay traces on identical case sets.
- **Acceptance:** one precedence model selected (or deferral recorded) on cited traces; protection floors non-overridable in every alternative's traces.
- **Falsifier/reopen:** an alternative permitting a floor override survives only as documented elimination; if all four fail a governance invariant → §1.4 escalation.
- **Downstream:** B6, B7, B9, B12.

### B9 — Event model, cross-store integrity, and replay (DE-R7)

- **Objective:** the complete event/record taxonomy per revised DE-R7; the cross-store transactional-outbox / CAS / reconciliation design exposing partial failure; the replay harness proving the fold property over recorded events and recorded model outputs.
- **Authority:** proposed DE-R7; LOG-01/02, MEM-01, COR-01, APP-04, ACT-01, ORG-01..07, LRN-01..08, CAP-03/CAP-04 (telemetry evidence records and economic-review events; P2A-14).
- **Inputs/dependencies:** B1 shapes; B3 identities; B4 boundaries; B5 degradation events.
- **Outputs:** `design/D-B9_Event_Model_and_Replay.md`; replay-harness build mechanics as TASK-0003+ (§12 Part D rule).
- **Alternatives kept viable:** outbox vs CAS vs reconciliation per store pair until tested.
- **Decision owner:** Fable, verifier-reviewed.
- **Required tests:** replay-divergence gate test — replay reproduces canonical state, authority ceilings, decisions, emitted ActionRequests, queue/attention projections, and all UI-observable state; hypothesis checks 4 and 5; cross-store partial-failure exposure tests; worker-loss resumption (APP-04); CAP-03 telemetry/evidence record schema checks (coverage, billed/estimated/inferred, provenance, event linkage); CAP-04 economic-review event representation.
- **Evidence:** harness-executed replay reports; divergence log (must be empty or each divergence dispositioned as a gate failure).
- **Acceptance:** zero unexplained divergence; executed/verified state derives only from externally owned ExecutionReceipts/VerificationRecords referenced by ID; every DE-R7 transition class has an event/record type.
- **Falsifier/reopen:** any state transition unrepresentable as an event without model re-invocation → design-gate blocker.
- **Downstream:** B12, B14, build change plan.

### B10 — Partitioned queue mechanics

- **Objective:** one governed queue mechanism with hard Business/Personal partitions — separately permissioned and prioritized, rendered by the Executive Desk in one frame without interleaving; admission by required-owner-action + attention contract (T3, T4, ACT-01 reviews, verification exceptions, policy conflicts); per-partition aging ladders as events; §18.1 metrics wiring.
- **Authority:** PER-01/02, EX-01..11, QUE-01, ORG-01..07 (verifier P2R-01 partition text, carried unchanged), CAP-04 (economic-review admission; P2A-14).
- **Inputs/dependencies:** B6 dispositions; B7 bands; B9 events.
- **Outputs:** `design/D-B10_Partitioned_Queues.md`.
- **Alternatives kept viable:** aging-ladder step calibrations as versioned policy parameters.
- **Decision owner:** Fable, verifier-reviewed.
- **Required tests:** no-interleaving partition test; separate-permission test; admission-contract fixtures; aging-ladder replay per partition; CAP-04 partitioned admission of AUD-03 economic-review items.
- **Evidence:** executed fixture traces; a rendered one-frame mock demonstrating partition separation.
- **Acceptance:** no fixture shows cross-partition interleaving or permission bleed; every admission maps to the contract.
- **Falsifier/reopen:** an input requiring simultaneous membership in both partitions → escalate to the owner package as a partition-policy question.
- **Downstream:** B12, B13.

### B11 — Ritual integration

- **Objective:** SCH-02 envelope instantiation for AUD-03 (weekly audit), LRN-09, and LRN-10 rituals feeding the engine as governed inputs.
- **Authority:** SCH-01/02, AUD-03, LRN-01..10, CAP-03/CAP-04 (economic-review ritual surface; P2A-14).
- **Inputs/dependencies:** B9 events; B7 scheduling.
- **Outputs:** `design/D-B11_Ritual_Integration.md`.
- **Alternatives kept viable:** cadence parameters as versioned policy, not design constants.
- **Decision owner:** Fable, verifier-reviewed.
- **Required tests:** A14 oracle; envelope instantiation checks per ritual; learning-event fold-back replay; CAP-04 synthetic cost-over-value case — the AUD-03 review item is created in the correct partition, nothing auto-disables, and protected control classes (safety, resilience, security, audit, legally required) are exempt from cost-only retirement.
- **Evidence:** instantiated envelopes validating against SCH-02; executed A14 trace.
- **Acceptance:** each ritual has a complete, validating envelope whose outputs enter the engine only as governed events.
- **Falsifier/reopen:** a ritual output that must bypass the event model to function → reopen against LOG-01 via §1.4.
- **Downstream:** B12.

### B12 — Design-gate test execution (six hypothesis checks + E2E-1 + separation falsifier)

- **Objective:** execute, as design-gate tests with recorded results: (1) substitution invariance; (2) policy-version causality; (3) missing-control fail-closed; (4) evidence separation (state refuses to advance without the external receipt); (5) correction-path execution (COR-01 non-destructive replay; corrections provably weak evidence); (6) separation-falsifier measurement — raw-content-consultation rate over the §8-governed sample with the pre-declared denominator, sampling method, and privacy-preserving evidence format — plus the E2E-1 raw-input substitution run.
- **Authority:** APP-01, DEC-01/02, COR-01, the discovery hypothesis framework; P2A-11 controls (§8).
- **Inputs/dependencies:** B1–B11 designed mechanisms; §8 data/sandbox contract **agreed before execution**.
- **Outputs:** `design/D-B12_Design_Gate_Test_Report.md` (per-test: procedure, inputs, environment class, result, trace pointer, per-B-item completion status).
- **Alternatives kept viable:** n/a — tests bind whichever designs are carried.
- **Decision owner:** Fable executes; verifier reviews; the reopen-question procedure runs if check 6 falsifies.
- **Required tests:** the six checks, E2E-1, and the §7 must-pass set.
- **Evidence:** machine-checkable traces; for check 6, the privacy-preserving evidence format from §8 (no restricted raw content in Git/Discord/verifier packets).
- **Acceptance:** every §7 design-gate must-pass test executed with a recorded result; failures dispositioned (fix → retest, or blocker declared).
- **Falsifier/reopen:** check 6 exceeding the recorded separation threshold triggers the discovery-recorded reopen procedure — an owner-visible event, never silently absorbed.
- **Downstream:** design-gate summary, owner package.

### B13 — INT-01 card and owner-package templates

- **Objective:** the INT-01 decision-card template and owner-decision-package templates as designed artifacts (calibrated by the owner's recorded plain-language preference, trail entry 77).
- **Authority:** INT-01, EX-01..11, AUT-04.
- **Inputs/dependencies:** B6/B7 outputs (cards render their dispositions); `04_Owner_Decision_Package.md` as calibration precedent.
- **Outputs:** `design/D-B13_INT01_Card_and_Owner_Templates.md`.
- **Alternatives kept viable:** presentation variants may be carried to the owner as a preference choice.
- **Decision owner:** Fable, verifier-reviewed; format preferences owner-decidable.
- **Required tests:** template instantiation against the INT-01 standard for each card class (T3 decision, T4 chain, verification exception, policy conflict, DE-R8 cap receipt).
- **Evidence:** instantiated example cards from fixture cases.
- **Acceptance:** every owner-facing surface class has a template meeting INT-01; DE-R8 cap-change receipts render owner-visibly.
- **Falsifier/reopen:** a card class that cannot render its decision basis without raw restricted content → reopen against DAT-01/02 via §1.4.
- **Downstream:** owner package.

### B14 — Operational-DB schema first cut (schema only)

- **Objective:** a first-cut schema for the operational database covering the selected/carried record shapes, identity fields, event store, policy versions, outbox/reconciliation structures, and provenance — **schema only; no runtime build**.
- **Authority:** MEM-01..09, ONB-01, PLAT-02/04, LOG-01/02, CAP-03 (telemetry evidence schema; P2A-14); proposed DE-R7 cross-store mechanics; bootstrap-registry migration contract (aliases on DB arrival).
- **Inputs/dependencies:** B1 outcome; B3, B4, B9 designs.
- **Outputs:** `design/D-B14_Operational_DB_Schema.md`; any executable validation as TASK-0003+.
- **Alternatives kept viable:** DB product selection remains out of scope (§12); the schema stays product-portable.
- **Decision owner:** Fable, verifier-reviewed.
- **Required tests:** schema-level checks — every B9 event type and B3 identity concept representable; outbox/partial-failure fields present; bootstrap-ID alias migration path expressible; CAP-03 telemetry/evidence records representable with coverage, billed/estimated/inferred, and provenance fields.
- **Evidence:** schema documents plus a coverage table (event/record type → table/collection).
- **Acceptance:** 100% coverage of the designed event/record taxonomy; no authority stored in any interface layer.
- **Falsifier/reopen:** a designed record with no product-portable representation → escalate via §1.4.
- **Downstream:** build change plan (TASK-0003+).

## 5. Part C — proposed requirement texts DE-R1..DE-R8 (Revision 2; verifier replacement texts adopted verbatim, P2A-03..P2A-09)

These are **proposed** texts: they become accepted register rows only through the §10 pipeline ending in owner acceptance of the built v1.4 layer — owner approval of this plan does **not** accept them (§9). Machine-comparable copies travel in the re-verification packet.

> **DE-R1 (identity and deduplication)** — The Decision Engine MUST preserve five distinct identity **concepts** and instantiate each only when applicable: a local ingestion ID for every accepted input; a source-native event ID when the source supplies one; a versioned deduplication fingerprint when deduplication evaluation applies; a case/correlation ID when the input is linked to a case, topic, or multi-event activity; and an action idempotency key for each emitted ActionRequest. Absence MUST be explicit and MUST NOT be replaced with fabricated authoritative values. Deduplication MUST be source-aware, fingerprint-version-aware, and uncertainty-aware; an uncertain match creates a review/link candidate and MUST NOT silently merge or drop either event. Identity semantics MUST remain independent of model and normalization versions. Acceptance tests include no false merge of distinct legitimate identical events, transformed-redelivery detection, routine no-case processing, source-without-native-ID processing, and one idempotency key per action attempt contract.

> **DE-R2 (concurrency and ordering)** — Events capable of mutating the same authoritative consistency boundary MUST be serialized or protected by versioned compare-and-swap / optimistic-concurrency controls such that every tested interleaving prevents lost updates and records unresolved conflicts. The design MUST define consistency boundaries for pre-placement intake, topic/object state, policy and queue state, and cross-object operations; record causal and source ordering separately; and state when a total order is required versus when conflict detection and reconciliation are sufficient. Capture acknowledgment MUST occur only after a durable intake commit and MUST remain within a declared latency bound protecting DP-001; downstream classification and policy evaluation may continue asynchronously. Acceptance tests cover unplaced inputs, same-topic conflicts, cross-topic reclassification, policy changes racing with evaluation, duplicate delivery, and multi-object fold-back.

> **DE-R3 (degraded operation)** — Degraded behavior MUST be defined as a dependency-by-capability matrix rather than a single assumed sequence. The system MUST NOT acknowledge capture unless the input is durably persisted to an intake store that remains available independently of the failed dependency. When canonical state, policy, identity, append-only logging, or evidence services are missing, stale, disputed, or unverifiable, the engine may provide only the capture and read capabilities explicitly proven safe for that failure mode; it MUST NOT perform external mutation or autonomous side-effecting action at any tier. Consequential requests are refused and recorded. Kill/revoke remains effective in every mode. Recovery MUST reconcile queued inputs, uncertain outcomes, and derived projections before ordinary authority resumes. Tests cover each dependency independently, combined failures, queue unavailability, stale snapshots, kill during degradation, and recovery with duplicate/conflicting events.

> **DE-R4 (tiers and deterministic policy evaluation)** — Input disposition MUST be computed by a versioned deterministic policy function over a verified mandatory control envelope, the applicable canonical state/checkpoint versions, and the active policy/schema/function/calibration versions. Recorded model outputs are semantic proposals only: they may increase scrutiny, lower the authority ceiling, or escalate to owner review, but may never raise authority, relax a mandatory trust/data/attention floor, or supply identity, instruction authority, policy, or verification state. Missing, stale, disputed, or unknown **mandatory authority-bearing controls** produce a no-action fail-closed result with an explicit reason. Trusted owner-origin input may be routed to T3 when owner judgment is required; external-untrusted content remains semantically analyzable with zero instruction authority and is quarantined only when the governing policy requires it. The function outputs the processing tier, maximum authority, attention band, placement/relationship/blocking/disposition recommendations, and required receipt/evidence contract.

> **DE-R5 (attention)** — Attention MUST be a deterministic function of the processing tier, action-class risk, blocking relationships, aging, domain partition, current owner mode, system health/degradation state, and the active interrupt/quiet-hour policy. Critical may be emitted only when an owner-ratified policy maps verified evidence into the accepted ATT-01 boundary; model output alone can never qualify an event as Critical or suppress a qualifying event. Attention recalibration occurs only through governed PolicyVersionEvents, and no recalibration may weaken a non-overridable protection floor.

> **DE-R6 (policy objects and precedence)** — Policies MUST be versioned typed objects carrying scope, authority domain, explicit priority, applicability predicate, effective window, conflict behavior, non-overridable protection floors, exception authority **only where exceptions are permitted**, explicit supersession target, schema compatibility, and rollback pointer. Changes travel exclusively through governed PolicyVersionEvents. A policy decision MUST be replayable from the complete recorded decision basis: normalized input record, identity/trust/data/verification envelope, relevant canonical state and checkpoint versions, the complete applicable policy set and versions, policy-function/schema/calibration versions, and recorded model outputs. Policy rollback changes future evaluation; prior actions and receipts remain historical facts and require separate reconciliation. The design gate compares the four carried precedence alternatives, including equal-priority fail-closed and owner-scoped exceptions that cannot supersede a declared protection floor.

> **DE-R7 (events, evidence linkage, and replay)** — Every input, normalization, recommendation, policy evaluation, decision/approval, attention change, override, ActionRequest, verification linkage, reconciliation, correction, learning, fold-back, aging, degradation, and authoritative state transition MUST be represented by an append-only event or versioned canonical record with stable IDs and provenance. Cross-store creation and linkage MUST use a defined transactional-outbox, compare-and-swap, or reconciliation mechanism that exposes partial failure rather than hiding it. Executed and verified state derives only from externally owned ExecutionReceipts and VerificationRecords referenced by ID. Replay consumes recorded events and recorded model outputs—never model re-invocation—and MUST reproduce canonical state, authority ceilings, decisions, emitted action requests, queue/attention projections, and all UI-observable state. Any divergence is a gate failure.

> **DE-R8 (automatic T2 volume expansion)** — Each eligible T2 action class and scope MUST have an independent, pre-authorized, versioned cap policy specifying: initial cap; hard owner-approved maximum; eligible evidence sources and coverage requirements; minimum verified sample size; observation window; correction/reversal/failure definitions; delayed-outcome treatment; confidence or uncertainty rule; maximum step size; cooldown; exclusion rules for duplicate, owner-accepted-but-unverified, disputed, degraded-telemetry, and externally untrusted evidence; automatic contraction and freeze thresholds; and the action-class/risk/data/authority ceiling that may never be crossed. Expansion uses independently owned outcome and verification evidence and MUST NOT rely on engine self-attestation, raw model confidence, overflow volume alone, or missing/incomplete telemetry. Every cap change is a PolicyVersionEvent with an owner-visible receipt and reversal path. Owner override applies within the permitted cap domain, requires the applicable identity/step-up control, cannot override a non-overridable protection floor, and is subordinate to IDN-03 kill/revoke. New action classes, tier changes, or authority-ceiling changes remain governed by AUT-12 and the ordinary policy workflow.

**DE-R8 required design tests (P2A-09):** sparse sample, delayed regression, cross-category contamination, missing provider telemetry, manipulated success labels, cap oscillation, maximum-bound enforcement, owner reduction, owner increase with step-up, automatic contraction, and kill/revoke during expansion.

## 6. Candidate-neutral comparison scorecard and selection rule

**Neutrality preconditions (verifier §5):** S1, S2, and S3 receive equivalent authority, evidence, persistence, concurrency, and projection capabilities; the common processing policy is held constant across shapes; a hybrid S2+projection result does not count as an independent S3 evaluation; S2 may remain the leading hypothesis but is not selected before gate evidence exists.

**Criteria and weights — declared here, before any result exists; changes only by plan amendment (§1.4):**

| # | Criterion | Kind |
| --- | --- | --- |
| 1 | Binding-invariant compliance (every `13M_` Binding row) | Pass/fail precondition |
| 2 | Fixture correctness — all 27 fixtures, no forbidden outcome | Pass/fail precondition |
| 3 | Identity/dedup behavior — B3/DE-R1 acceptance set | Pass/fail precondition |
| 4 | Concurrency behavior — B4/DE-R2 acceptance set | Pass/fail precondition |
| 5 | Evidence-authority boundary — check 4 | Pass/fail precondition |
| 6 | Correction behavior — check 5 (COR-01) | Pass/fail precondition |
| 7 | Interactive capture-latency envelope (DP-001) | Scored, weight 1 |
| 8 | Degraded-mode behavior quality (B5 matrix outcomes) | Scored, weight 1 |
| 9 | Experience economy — owner-visible complexity (EX rows) | Scored, weight 1 |
| 10 | Operational complexity and failure surface | Scored, weight 1 |
| 11 | Portability (APP-01, PLAT-04) | Scored, weight 1 |

**Selection rule:** a shape passes only if criteria 1–6 pass with cited traces; among passing shapes, scored criteria 7–11 (equal weights) order the recommendation. The design gate records **selection or explicit deferral** with evidence. Structural elimination requires the failing trace and verifier concurrence. Owner involvement only where tradeoffs are owner-visible (§9); otherwise the selection is a documented technical decision reviewed by the verifier.

**Preregistered scoring calibration (P2A-13) — frozen here, before any candidate-specific execution exists; changes only by §1.4 amendment, and any change after the first candidate trace invalidates the affected comparisons:**

- **Scale and direction:** criteria 7–11 are each scored 0–4 on an ordinal scale, higher is better, scored independently per candidate against the measurement method below.
- **Measurement method and evidence source per criterion:** 7 — analyzed capture-path latency against the declared DP-001 bound, from B4 traces; 8 — proportion of B5 dependency-matrix failure modes with proven-safe capability outcomes, from the executed B5 matrix; 9 — owner-visible surface count and interaction burden in fixture renderings, from D-B10/D-B13; 10 — component and failure-surface census of the shape's design, from D-B1/D-B9; 11 — substitution-invariance and portability findings, from B12 check 1 and D-B1.
- **Missing-evidence rule:** a criterion without qualifying evidence scores 0 and is flagged `insufficient evidence`; a candidate carrying any such flag cannot be selected — selection defers until the evidence exists or the gate records explicit deferral.
- **Tie/near-tie rule:** weighted totals within 2 points are a near-tie; a near-tie defers selection to the owner package with the tied candidates carried, unless a pass/fail criterion differentiates them.
- **Selection-versus-deferral rule:** selection requires criteria 1–6 passed, zero insufficient-evidence flags, and a margin greater than 2 points; anything else is recorded as explicit deferral with rationale.

## 7. Design-test and evidence matrix (design gate vs build gate; P2A-01)

The requirement-to-artifact-to-test mapping is `13M_`'s per-row columns; this table fixes **which tests must pass at the design gate** versus which remain **build-gate obligations**:

| Test set | B owner | Evidence artifact | Gate |
| --- | --- | --- | --- |
| Six hypothesis checks (1–6) | B12 | D-B12 + traces | **Design gate — must pass** |
| E2E-1 raw-input substitution | B12 | D-B12 | **Design gate — must pass** |
| DE-R1 acceptance set (GAP-2) | B3 | D-B3 | **Design gate — must pass** |
| DE-R2 acceptance scenarios | B4 | D-B4 | **Design gate — must pass** |
| DE-R3 dependency-matrix tests | B5 | D-B5 | **Design gate — must pass** |
| DE-R8 eleven-test set (design-level simulation on recorded/synthetic evidence) | B6 | D-B6 | **Design gate — must pass** |
| Attention/ATT-01 boundary + OD-1 replay | B7 | D-B7 | **Design gate — must pass** |
| Four-alternative precedence replay | B8 | D-B8 | **Design gate — must pass** |
| Replay-divergence gate test | B9 | D-B9 | **Design gate — must pass** |
| Partition/no-interleaving + aging tests | B10 | D-B10 | **Design gate — must pass** |
| A14 ritual oracle | B11 | D-B11 | **Design gate — must pass** |
| Twin-input injection oracle + envelope validation | B2 | D-B2 | **Design gate — must pass** |
| INT-01 template instantiation | B13 | D-B13 | **Design gate — must pass** |
| Schema coverage checks | B14 | D-B14 | **Design gate — must pass** |
| CAP-03 telemetry/evidence contract schema — provider-independent; coverage and billed/estimated/inferred fields; source provenance; event linkage (P2A-14) | B9, B11, B14 | D-B9, D-B11, D-B14 | **Design gate — must pass** (live provider collection remains the build-gate row below) |
| CAP-04 synthetic cost-over-value case — partitioned AUD-03 review item created; never auto-disables; safety/resilience/security/audit/legal controls exempt from cost-only retirement (P2A-14) | B9, B10, B11 | D-B12 | **Design gate — must pass** |
| Capacity and spend record — actuals versus every §12 cap, coverage gaps, rework burden, explicit stop/continue/redesign disposition (CAP-02; P2A-14) | B12 | D-B12 | **Design gate — must pass** |
| CAP-03 runtime telemetry | — | build layer | Build gate |
| Live latency measurement under real load | — | build layer | Build gate |
| Runtime kill/revoke drills | — | build layer | Build gate |
| Provider-integration receipts (real ExecutionReceipts) | — | build layer | Build gate |
| GOV-03 release mechanics (CAS two-step, receipts) | — | release records | Build gate |
| DE-R8 live-evidence expansion run | — | build layer | Build gate (design-level simulation passes at design gate) |

At the design gate every `13M_` Binding, Design subject, and proposed DE-R row must resolve in `13G_` per the §4 status enum (`D-B12` carries the per-B-item record); `Not started`, `Incomplete`, or `Blocked` rows block the gate unless the row is an explicitly permitted `Build-gate deferred` obligation cited to the table above — enforced by `13V_validate_design_matrix.py --final-gate`.

## 8. Design-test data and sandbox contract (P2A-11)

1. **Synthetic fixtures are the default** for every design test.
2. **Real-input sampling** (check 6's sample and any other real data) requires: a separately listed source; owner authorization; a data-class policy per DAT-01/02; minimization/redaction before use; a retention/deletion rule; and declared provider/model eligibility for any model that sees the data.
3. **External-untrusted content** has no instruction authority and is processed only in a reduced-tool, isolated context.
4. **No production mutation credentials and no outbound communication capability** exist in any design-test environment.
5. **Builder tasks (TASK-0003+)** carry APP-05 trust/data/action envelopes and run in isolated workspaces.
6. **Test output hygiene:** restricted raw content is never copied into ordinary Git, Discord, or verifier packets; evidence uses privacy-preserving formats (counts, hashes, redacted excerpts under the data-class policy).
7. **Separation-falsifier measurement (check 6):** the denominator, sampling method, and privacy-preserving evidence format are specified in `D-B12`'s procedure section **before execution**; execution without that specification is a gate violation.

## 9. Owner-decision and change-control boundaries (P2A-12)

1. **Owner approval of CP-P2-A authorizes the scope, controls, and execution of the design work — it does not accept the final record shape, policy precedence model, operational-DB schema, or DE-R1..DE-R8 texts.** Those are accepted only through the §10 pipeline's later owner events.
2. **DE-R8 owner-intent boundary:** material changes to DE-R8's owner intent (automatic expansion from observed resolution patterns, automatic contraction, owner-visible receipts, owner override within the authorized domain) require an owner decision; technical refinements within that intent are Fable/verifier work.
3. **Owner-level choices expected from design:** record-shape consequences if they carry business-visible tradeoffs; the precedence model if owner-visible; any B-item falsifier escalation marked owner-visible (B5, B10, GAP-2 residual risk); INT-01 format preferences.
4. **Change control:** all later-entry admission per §1.4; OD-1/OD-2/OD-3 are decided and not reopened by design work.

## 10. Post-design correction/re-verification pipeline (P2A-12)

```text
design deliverables
→ verifier review
→ Fable keyed dispositions
→ corrections / Builder rework where applicable
→ scoped re-verification
→ concise owner decision package for owner-level choices and residual risk
→ owner design acceptance
→ v1.4-proposed build change plan / Task Packet authorization
```

**No v1.4 release or owner acceptance of v1.4 is implied by design acceptance alone** — the build layer routes through its own change plan, TASK-0003+ builds, post-build verification, GOV-03 release mechanics, and the owner's v1.4 acceptance event.

## 11. Deliverable paths and final gate packet contents

**Design deliverables** (all under `fable/phase2-decision-engine/design/`):

```text
D-B1_Record_Shape_Comparison.md        D-B8_Policy_Objects_and_Precedence.md
D-B2_Field_Authority_Contract.md       D-B9_Event_Model_and_Replay.md
D-B3_Identity_and_Deduplication.md     D-B10_Partitioned_Queues.md
D-B4_Concurrency_and_Ordering.md       D-B11_Ritual_Integration.md
D-B5_Degraded_Operation_Matrix.md      D-B12_Design_Gate_Test_Report.md
D-B6_Tier_Policy_Function_and_Autonomy.md  D-B13_INT01_Card_and_Owner_Templates.md
D-B7_Attention_and_Quiet_Hours.md      D-B14_Operational_DB_Schema.md
D-GS_Design_Gate_Summary_and_Selection_Record.md
D-ODP_Owner_Decision_Package.md
D-AM_v14_Amendment_Package.md          (proposed Manual/register amendments for the build gate)
artifacts/                             (TASK-0003+ outputs: harnesses, validators, executed traces)
```

**Final design-gate packet** (to the verifier): the full `design/` set; executed traces; the §6 scorecard with results under the preregistered calibration; the updated `13G_Design_Gate_Status_and_Evidence_Matrix.md` status/evidence overlay, passing `13V_validate_design_matrix.py --final-gate`; the D-B12 capacity and spend record; complete Git bundle with commit/tree binding; `EXPORT_MANIFEST.json` + checksums validating 100%; enumerated proof that the accepted v1.3 Manual/register identities (§1.2 rows 1–3) are unchanged; an explicit statement of claims not made (no owner acceptance, no release).

## 12. Version, rollback, capacity, spend, and exclusions

- **Risk class:** design-governance / high leverage; runtime or external-action authority: **none**.
- **Rollback:** design artifacts are additive under `fable/phase2-decision-engine/`; pre-release rollback = branch/commit abandonment; the accepted v1.3 baseline is untouched until a GOV-03 release the owner later accepts.
- **Design-phase capacity contract (CAP-01/CAP-02; P2A-14) — exact maxima:**

  | Dimension | Cap |
  | --- | --- |
  | Active design branches | 3 |
  | Queued TASK-0003+ Builder tasks | 2 |
  | Concurrent Builder sessions | 1 |
  | Open verifier findings / rework items | 15 |
  | Review-item aging | 14 days to an escalation event |
  | Owner decision-minutes | ≤ 30 minutes per gate package; owner attention only at the named §9/§10 gates |
  | Spend / session proxy | ≤ 12 Fable design sessions and ≤ 4 Builder sessions before a mandatory stop/continue check (spend itself remains under the standing not-measured disclosure until CAP-03 telemetry exists — a build-gate obligation, §7) |

  **Pause/park rule:** when any cap is exceeded, no new work item starts; excess items are parked with an aging event and reported in the D-B12 capacity record; a cap breach that blocks a gate beyond the aging limit escalates to the owner.
- **Gate capacity record (CAP-02):** `D-B12` reports actuals against every cap above, coverage gaps, rework/failure burden, and an explicit **stop / continue / redesign** disposition (§7 must-pass).
- **CAP-03/CAP-04 engine behavior (P2A-14):** the provider-independent telemetry/evidence contract is designed in B9/B11/B14; the CAP-04 economic-review behavior in B9/B10/B11 — cost-over-value evidence raises a correctly partitioned AUD-03 review item, never auto-disables the automation, and safety, resilience, security, audit, and legally required controls are exempt from cost-only retirement.
- **Out of scope (unchanged deferrals):** memory-provider selection (ADR-021 gate); MCP write boundaries; mailroom detail; Discord implementation; database product selection; hardware (HW-01).
- **Builder rule (Part D):** design work is Fable-owned; any artifact requiring build mechanics becomes TASK-0003+ under the `19_` APP-05 template with Claude Opus 5 as Builder, its own allowlist, trust/data/action envelope (§8), and post-build verification.
- **Not claimed:** any owner approval, design selection, requirement acceptance, build authorization, release, or baseline change.
