# Builder Delivery Record — TASK-0003 (rework cycle R1)

**Task:** TASK-0003 — P2S-01 Behavioral Candidate-Transition/Fold Simulator (parent topic TOPIC-0002).
**Builder:** Claude Code session, model `claude-opus-5` (standing authorized substitution, trail entry 69).
**Branch:** `claude/task-0002-builder-handoff-g97x8j` (operator-designated; see §6).
**Instruction authority:** `22_TASK-0003_Task_Packet_P2S01_Behavioral_Simulator.md` + `23_TASK-0003_Rework_Packet_R1` only.
**Status:** **Reworked; independent re-verification pending.** No design-gate passage, P2S-01 closure, or record-shape selection is claimed.

---

## 1. Disposition of the rework findings

I verified each finding before fixing it rather than accepting it on report. **RW-04 and RW-02 I reproduced independently first** — the floor-overwrite bug and the 5-of-56 vacuity measurement both confirmed exactly as written. All ten findings are concurred; none contested.

| # | Finding | What changed | Proof |
| --- | --- | --- | --- |
| **RW-01** | A7 encoded the fired call as a refusable request | New `AccomplishedAction` stimulus type. A7's external call is now an accomplished fact the engine cannot refuse; with no receipt it computes the ACT-01 halt → Needs-Review → reconcile-before-retry path. | A7 now emits `ReconciliationEvent` + `AttentionChangeEvent(needs-owner)` and sets `uncertain_outcome`; previously it emitted a `RefusalEvent` and nothing else. `out/results.json` |
| **RW-02** | 51 of 56 predicates could never fire | Every predicate rewritten to read the **computed result**; new `mutations.py` catalogue (51 candidate defects); `run_defects.py` now proves reachability per predicate and reports `NOT-EVALUABLE` with rationale, excluded from counts. Stimuli for S6/A12/A5/A10 fixed so their consequential lifecycles actually execute. | **56/56 defect-reachable, 0 NOT-EVALUABLE**, each with a named witness defect. `out/seeded_defects.json` → `predicate_reachability` |
| **RW-03** | P2S-05 traces 2, 3, 5 asserted literal constants | `PolicyPlane` gained real provider/receipt/reconciliation state. Every verdict field is computed from the objects the trace manipulates; each trace has a seeded defect variant. | **5/5 pass and 5/5 flip under their own seeded defect.** `out/p2s05_linearization.json` → `falsifier` |
| **RW-04** | Non-floor policy could overwrite a protection floor's render class | `compose_policies` rewritten with `OUTPUT_OWNER` enforcement: a non-protection policy writing another domain's output is **structurally refused**; floors intersect and are non-overridable. | Reproduced the bug first (`full-content` won), then fixed: floor holds, write refused with `render_class-not-owned-by-autonomy`. PC-10 + floor-overwrite mutation both exercise it. |
| **RW-05** | S2's tier discriminator hand-authored under a false sourcing claim | `routine_filing` flag **removed**. New `routine_filing_eligible()` computes it per D-B6 AUT-05 from placement scope + action class. Hearsay attribution encoded input-side. `scenarios.py` docstring corrected to state honestly which `derived` keys are D-B2 §2.3 computed vs Builder-authored. | S2 still computes T2, now *derived*: in-subtree + filing-routing → True; cross-subtree or consequential class → False. |
| **RW-06** | A4/A8/A13/A15 dropped or reshaped input-side facts | A4 → two **versions of one policy id** (newest-wins now constructible; composite fails closed to T3). A8 → `od1_policy_pending`. A13 → `notification_preview` surface. A15 → three `InFlightAction`s the kill must halt and list. | A4 now computes `ceiling=none, tier=T3`; A15 halts 3 in-flight actions with `RefusalEvent`s. `out/results.json` |
| **RW-07** | Fixture-ID conditional in a predicate | `... if c["stim"].id == "S1"` removed; "silence without watchdog" now reads computed watchdog state. | `grep '== "S[0-9]"' oracle.py judge.py` → no match. |
| **RW-08** | Kill-plane events folded through the policy store | New `control-journal` store per D-B9 P2G-11 row 9, ordered ahead of the engine control plane because kill efficacy never depends on the engine log (D-KR §1.4). | `EVENT_STORE_PHASE["KillCommandEvent"] = ("control-journal", …)`; fold basis preserves the separation. |
| **RW-09** | D-B8 layers dead schema or unencoded | **Implemented:** effective-window filtering (PC-4), exception displacement with floor-target rejection (PC-3) and `exception_authority=none` rejection (PC-6), priority resolution within same-domain same-output, contradiction detection across all outputs. **Declared NOT-SIMULATED:** `conflict_behavior`, `rollback_pointer`/PC-5, `schema_compat`, calibration versioning, live DP-001 latency. | PC-3/PC-4/PC-6/PC-10 all verified; `not_simulated` block in `out/gate_report.json` and README. |
| **RW-10** | Miscellaneous honesty/fidelity set | `required_evidence` now matches **named kinds** via `EVIDENCE_KIND_MATCHERS`. `expected.authority` mapping coverage reported per combination (36 mapped / 45 unmapped). Blanket quarantine replaced with the D-B6 §2.2 policy-scoped rule (quarantine only where the source is unclassifiable — A3's route). `ingest_seq` now used as the declared intake ordering key. `NormalizationRecord`/`RecommendationRecord` moved to model-output/phase-2. Stage reordering documented. | The stricter `required_evidence` check immediately found three real gaps (S6 reconciliation, A2 identical-placement matching, A10 refusal record) — all fixed rather than loosened. |

## 2. Acceptance criteria — all 14 re-proven

| # | Criterion | Result |
| --- | --- | --- |
| 1 | Anti-circularity, grep-verifiable | **PASS** — textual + import + structural; `mutations.py` added to the checked set |
| 2 | 81 combinations, none skipped | **PASS** — 81/81, 0 unclassifiable |
| 3 | Computed-vs-expected; every forbidden list evaluated | **PASS** — 171 evaluations over 56 distinct predicates, **56 defect-reachable, 0 NOT-EVALUABLE** |
| 4 | External-receipt ownership | **PASS** — 0 violations |
| 5 | Multi-store fold with P2S-06 ordering | **PASS** — 81/81 order-invariant |
| 6 | Candidate-specific divergences | **PASS** — 81 computed |
| 7 | E2E-1 two-normalizer + seeded defect | **PASS** |
| 8 | Every named defect flips a case | **PASS** — 8/8 |
| 8b | Every predicate provably able to fire | **PASS** — 56/56 via a 51-mutation catalogue |
| 9 | Shuffle-invariance ≥3 permutations | **PASS** — 6 per combination, 0 violations |
| 10 | P2S-05 five traces, computed and discriminating | **PASS** — 5/5 pass, 5/5 flip under seeded defect |
| 11 | P2S-07 negative + positive | **PASS** — 2/2 |
| 12 | Two runs byte-identical | **PASS** — 8/8 output files identical |
| 13 | No file outside the allowlist | **PASS** — 26 files, all under `design/traces/behavioral/` |
| 14 | Delivery Record with reflexive falsifier | **PASS** — this document, §4 |

**Byte hygiene (trail-67 rule):** all 26 files — 0 CR, 0 trailing whitespace, single final LF, checked at byte level on working-tree files, not via `git diff --check`.

## 3. The honest count restatement (RW-02 requirement 3)

| Figure | Before (R0) | Now (R1) |
| --- | --- | --- |
| Predicate evaluations reported | 171 | 171 |
| Distinct predicates | 56 | 56 |
| **Able to fire under any condition** | **5** | **56** |
| **NOT-EVALUABLE (excluded)** | not reported | **0** |
| P2S-05 verdicts computed | 2 of 5 | **5 of 5** |
| P2S-05 traces that can fail | 2 of 5 | **5 of 5** |

Per-predicate witnesses are in `out/seeded_defects.json` → `predicate_reachability`, each naming the mutation, fixture and shape that makes it fire. If any predicate becomes unreachable again the runner reports it `NOT-EVALUABLE` with rationale and drops it from the count.

## 4. Falsifier element (APP-06 / CPB-14, reflexive)

| # | Claim | What would disconfirm it | Status |
| --- | --- | --- | --- |
| 1 | Every predicate is now genuine evidence | A predicate whose witness mutation is tuned to it rather than modelling a real defect. Mitigated structurally: mutations perturb computed **events/state**, never a predicate's answer, and `mutations.py` is inside the anti-circularity check. **Residual:** reachability proves a predicate *can* fire, not that it fires for the *right* reason. A reviewer wanting more should check a sample of witness pairings by hand. | Not disconfirmed; limit stated |
| 2 | The scenario encodings are faithful | An independent reader judging any `ScenarioSpec` field to encode an outcome rather than a stimulus. **Six were wrong last cycle** and review caught them; that base rate is the honest prior for the remaining 21. Still the layer I cannot self-verify. | **Explicitly unverified by me** |
| 3 | The engine rules match the design documents | An independent implementation disagreeing. Still none exists. Two more fidelity errors surfaced during this rework — the D-B4 §2.3 lease semantics (I was applying the epoch check to an already-held in-flight lease, which rule 3 forbids) and the blanket-quarantine rule — both found by computed traces failing, not by re-reading. | **Explicitly unverified by me** |
| 4 | RW-04 is fixed, not masked | Composing a floor with a non-floor writer and seeing the floor lose. Tested directly; also covered by a `floor-overwrite` mutation and the PC-10 case. | Not disconfirmed |
| 5 | All 81 combinations still execute | A fixture missing from `results.json`, or an unclassifiable case passing. `scenarios.get()` raises on an unknown fixture and the runner counts it a failure. | Not disconfirmed |
| 6 | Determinism holds after the rework | Any output byte-differing across runs. 8/8 identical. Mutation search uses a fixed catalogue order and fixed seeds. | Not disconfirmed |
| 7 | Nothing outside the allowlist was touched | A file outside `design/traces/behavioral/`. Dotfile-inclusive walk: 26 files, all inside. | Not disconfirmed |
| 8 | The NOT-SIMULATED list is complete | A D-B8/D-B9 mechanism a reviewer believes is implicitly credited but is neither implemented nor listed. I enumerated from the design documents' own schema; **an omission here would be invisible to me by definition** — this is the honesty claim most worth an independent pass. | **Explicitly unverified by me** |

## 5. What this rework did not change

The verification summary in `23_` §"what STANDS" carries forward and was re-proven, not assumed: return mechanics, the anti-circularity boundary, determinism, byte hygiene, supersession compliance, D-B2 §3 enumeration, P2S-07 rules, P2S-06 ordering, E2E-1 normalizer independence. Criterion 1 regressed once mid-rework (a prose `notes=` string contained an oracle field word) and was fixed by rewording rather than whitelisting, on the same principle as last cycle: a reviewer's plain grep must return zero hits.

## 6. Deviations and open items

- **No scope deviations.** Nothing outside `design/traces/behavioral/` written. No design document, gate artifact, decision trail, registry, or checksum touched. No change request was required — every rework item was correctable within the allowlist.
- **Branch deviation (unchanged, disclosed):** work is on the operator-designated `claude/task-0002-builder-handoff-g97x8j` rather than a task-specific branch. Flagging again so Fable can re-home the change set.
- **Residual-risk item from `23_` §"carried to the verifier"** (rule-table branches mirroring fixture routes) is acknowledged and unchanged; `23_` states no R1 action is required, and I made none.
- **Recommended reviewer focus:** (1) `scenarios.py` — the 27 encodings, per falsifier row 2, six of which were wrong last cycle; (2) the witness pairings in `predicate_reachability`, per falsifier row 1; (3) the NOT-SIMULATED list's completeness, per falsifier row 8.

---

*Builder-authored completion claim and evidence index — not independent evidence (APP-06). Every proof is reproducible from the pinned snapshot with the commands in `README.md`.*
