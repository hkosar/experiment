# Builder Delivery Record — TASK-0004 (P2T oracle/fold/schedule/validator corrections)

**Task:** TASK-0004 — P2T corrections (parent topic TOPIC-0002). New task; TASK-0003 is CLOSED (trail 98).
**Builder:** Claude Code session, model `claude-opus-5` (standing authorized substitution, trail entry 69).
**Branch:** `claude/task-0002-builder-handoff-g97x8j` (operator-designated; see §9).
**Instruction authority:** `30_` Task Packet; governing findings `28_`/`28A_`; dispositions `29_`.
**Status:** **Built; independent verification pending.** No design-gate passage is claimed. The verifier's FAIL stands until the verifier changes it.

---

## 0. H-06 gate, reported before any edit

`EXPORT_MANIFEST.json` — **42/42 hashes valid**, 0 mismatches, 0 missing, 0 undeclared
extras. I additionally verified the snapshot's 28-file behavioral tree is byte-identical
to my accepted TASK-0003 C1 return (28 verbatim, 0 differ), so the tree I extended is
the one that was accepted.

## 1. Disposition of P2T-01, P2T-02, P2T-03 and the W4/W5 halves

| # | Finding | What changed | Shipped-evidence proof |
| --- | --- | --- | --- |
| **P2T-01** (Critical) | Gate does not enforce the complete expected result; corrupting one expected value — or all 27 authority values — still yielded PASS | New `oracle_schema.py`: a typed schema over **all four** dimensions (EXACT / ALTERNATIVES / CEILING / CONDITIONAL / STRUCTURAL / RELATIONAL / PRESENTATION / NOT_APPLICABLE / UNMAPPED), 38 named computed features, and a **fail-closed coverage floor** that makes mapping collapse a gate failure. The judge compares every dimension. New `run_oracle_mutations.py`. New criteria 16, 17. | **All 4 of the verifier's probes now FAIL the gate** (`out/oracle_mutations.json` → `verifier_probes`). **102/108** fixture-dimension sentinel corruptions rejected; the other 6 are declared-unmappable and each carries a recorded reason. **97/97 governed pairs have a named contradictory witness** — an actual value borrowed from another corpus fixture, so "schema-valid but wrong" is proven, not asserted. |
| **P2T-02** (High) | Fold accepted a `caused_by` reference to a nonexistent event | `Event.external_basis` declares out-of-basis dependencies as a *different kind* of edge instead of inferring one from absence. New `fold.validate_basis()` runs **before any ordering, state or projection**; `fold(..., enforce_basis=True)` refuses on any problem. `topological_order`'s `or (ref not in by_id)` escape — the literal defect — is gone. New `run_basis.py`, criterion 18. | **8/8 missing-basis cases fail closed**, including the verifier's exact probe. Each ships its defect witness: with both new layers disabled the same basis folds with `causal_violations=0`, reproducing the verifier's recorded observation. 81 production combinations validate clean, so the check is fail-closed rather than refuse-everything. |
| **P2T-03** (High) | The promised P2S-04 tests were never delivered | New `run_p2s04.py`: a watchdog that holds versioned recurrence specs and **computes** deadlines from them (D-KR P2S-04 rule 1), a rolling-horizon monitor (rule 2), and atomic versioned change (rule 3). Logical ticks only — no wall-clock. New criterion 19. | **3/3 behaviors discriminate** under their targeted defects: scheduler-self-report dependence restored → the missed deadline vanishes (`[264]` → `[]`); horizon monitoring disabled → no early warning; non-atomic change → no version in force. `out/p2s04_schedule_liveness.json`. |
| **P2T-04** (executable half) | Checker matched nine hand-copied literals | `check_supersessions.py` rewritten: patterns are **parsed out of D-SM at runtime**, so a row Fable adds is enforced next run with no code change. Each row's patterns are **scoped to the artifact that row names**. Four Builder-declared structural families (retired artifact paths / parameter values / evidence labels / mechanism identifiers). | 13 D-SM rows → 10 map-derived patterns + 13 structural = 23, against 9 before. `--self-test` seeds four violations into a scratch copy and requires each to fail, plus two negative cases. **SELF-TEST PASS.** |
| **P2T-05** (executable half) | `13V_` validated the table and never read the document's own summary; rows sat Complete under open findings | Check 7 parses any declared status-count block and fails on disagreement. Check 8 reads finding dependencies (`P2T-02: …`) and fails `--final-gate` while a referenced finding is open — **fail-closed when the open-findings list is absent**, because unknown is not closed. `13F_Open_Findings.json` format designed and documented in the docstring. | `--self-test`: 8 cases, **PASS**. Exercised against the real `13G_`: the declared block agrees with the rows; injecting the verifier's stale counts produces `says Complete: 33, rows say 87`. The four real rows naming findings (APP-04, RES-02, SCH-02, DE-R7) block `--final-gate` with the list absent. |

## 2. The nine changes to computed behavior, each dispositioned

The new comparisons surfaced twelve disagreements on first run. Each was diagnosed
before anything was changed — mapping defect, encoding defect or engine defect, with
its basis — and the fixes are these. **8 of 27 fixtures changed; 19 did not.**

| # | Kind | Change | Basis | Fixtures |
| --- | --- | --- | --- | --- |
| E1 | **Engine** | A per-envelope fail-closed reason now emits a `RefusalEvent` carrying it | DE-R4 (quoted in `engine_core`): a fail-closed result carries *"an explicit reason"*. The reason existed only as a Python string, never as a record — A1's expected IDN-failure/security-log evidence had nothing to point at. A reason that is not a record is not evidence. | A1, A3, A14, A16, S7 (+1 event each) |
| E2 | **Engine** | A model proposal that attempts to RAISE the ceiling emits a `RefusalEvent` | D-B2 §2.4 lower/escalate-only. The rejection was recorded only in a `proposal_notes` string; A2's expected "flag record on twin B" had no computed artefact. | A2 (+1 event) |
| E3 | **Engine** | The `system` trust branch honours routine-filing eligibility | The `connected-system` branch already cites *"D-B6 §3 scopes `autonomy.filing-routing` by ACTION CLASS, not by origin"* and has since TASK-0003. Applying it on one branch and not the other is an inconsistency in one function, not two rules. | S10 (T1→T2) |
| C1 | **Encoding** | S3 gains a filing `actions` tuple | S3's route is a file-with-receipt and the scenario emitted no action at all — nothing was filed and no receipt existed. Same omission RW-01 corrected on A10 and RW-24 enumerated for S2/A5/A9. From `normalized_input` + `start_state`; no oracle field consulted. | S3 (+2 events) |
| C2 | **Encoding** | S10 gains `placement_scope` / `proposed_action_class` | The AUT-05 inputs RW-05/RW-27 required on S2, A9 and S3. Folding a completed child into its named parent is an in-subtree filing-routing action. | S10 |
| M1 | **Mapping** | `computed_authority_class` measures authority **exercised**, not the ceiling available | The corpus says "none exercised". Measuring the ceiling made S1 (a Desk render) read as `read` and A15 (post-kill read-only) read as `step-up`. | — |
| M2 | **Mapping** | "internal" is a DOMAIN claim (ceiling at receipt-bearing + no outbound), not a rung | S2's "internal filing only" exercises act-with-receipt authority and is still internal. | — |
| M3 | **Mapping** | "none exercised" and "read" collapse; the schema says so | This engine models no difference between them. Inventing one to make a distinction the corpus draws in prose would be fitting the schema to the answer. | — |
| M4/M5 | **Mapping** | Quarantine reuses the already-accepted `quarantined or ceiling==none`; execution-receipt requirements moved from the receipt column to the route | A6's "ordered receipts" is a claim about ordering, not an external executor; whether an execution receipt is expected is what the ROUTE says the engine does. | — |

**One mapping I deliberately did not write.** A11's route says "NO case record". Encoding
that as a forbidden `PlacementEvent` would assert that one PlacementEvent *is* a case
record, and no document in the Builder snapshot establishes that. The clause is carried
by A11's tier equality and by its own `case per newsletter` forbidden predicate. Stated
because the absence of a check is exactly what this cycle is about.

## 3. Retired, not duplicated

The former `oracle.expected_exercised_authority` comparison (36/81 mapped) and
`authority_mapping_coverage` are **deleted**, not left beside the new ones. That is the
partial mapping the verifier's authority probe walked straight through; keeping both
would leave two comparisons of one dimension that can disagree — the same
two-incompatible-snapshots defect P2T-05 found in the ledger. The function is gone from
`oracle.py`, not merely unreferenced.

## 4. Acceptance criteria — 20, all PASS

1 anti-circularity (now including `oracle_schema.py` as an oracle-side module); 2 81/81,
0 unclassifiable; 3 171 evaluations, 56/56 reachable, 0 judged failures; 4 0
receipt-ownership violations; 5–6 81/81 order-invariant, 81 divergences; 7 E2E-1 with
the seeded leak; 8 9/9 named defect classes; 8b 56/56 via 62 mutations; 9 6 permutations;
10 P2S-05 5/5; 11 P2S-07 2/2; 12 11/11 composition; **13 18/18 judge checks flippable**
(15 before — the three new dimension checks acquired witnesses automatically), 0 orphaned
switches, 0 dead mutations, **0 vacuous pass-rule checks** (was 1); 14 D-B5 self-test;
15 attention 66/81; **16** all four dimensions compared with the floor holding; **17** 4/4
verifier probes defeated; **18** 8/8 missing-basis cases closed; **19** 3/3 schedule
behaviors discriminating.

Determinism: two consecutive `run_gate.py` runs **byte-identical across 13/13 outputs**.
Hygiene: 35 files, 0 CR, 0 trailing whitespace, single final LF. Dead-code scan clean.
**Allowlist walk: 19 modified + 7 added, 0 outside the allowlist** — no document, matrix,
fixture, trail, registry or checksum touched.

## 5. What I could not execute, stated plainly

`13V_validate_design_matrix.py` **cannot run end-to-end in the Builder snapshot**: it
needs `../phase1-audit-v1.0/05_Requirements_Register_v1.1.csv`, the change plan, and
`13D_`, none of which are in it. So:

- The two new checks are proven by `--self-test` (8 synthetic cases) and by direct
  execution of their functions against the **real** `13G_` (§1 row 5).
- The **full** validator's structural PASS on the real repository is Fable's to confirm.
  I have not run it and do not claim it.

This is the one place in this return where a claim would outrun what I checked, so it is
stated as a limit rather than left for a reviewer to discover.

## 6. Falsifier element (APP-06 / CPB-14, reflexive)

| # | Claim | What would disconfirm it | Status |
| --- | --- | --- | --- |
| 1 | Every expected dimension is load-bearing | A fixture-dimension pair whose corruption still passes. Gated: 97/97 governed pairs have a contradictory witness, 102/108 sentinels rejected, 6 declared-unmappable with recorded reasons. **Limit:** load-bearing means *some* wrong value fails, not that *every* wrong value fails. | Not disconfirmed; limit stated |
| 2 | The schema reads the corpus faithfully | A fixture whose expectation I mapped to the wrong computable claim. The nine §2 dispositions are all judgment, and four of them (M1–M5) changed what a dimension *means* after seeing a failure — the sequence most likely to fit a schema to its answers. My guard was to ground each in the corpus's own words or an already-accepted definition, and to refuse the A11 mapping I could not ground. **This is the row to audit.** | **Explicitly unverified by me** |
| 3 | The three Builder-added stimuli are input-side faithful | An encoding that smuggles an outcome. S3's action and S10's AUT-05 inputs are the same class a reviewer adjudicated genuine on S2/A9/S3 two cycles ago; both derive from `normalized_input`/`start_state`, and no oracle field was read. Still mine, still unverified by me. | **Explicitly unverified by me** |
| 4 | The basis validator is complete | A malformed basis none of its nine checks names. It covers what D-B9's ordering-key table and P2G-11 store matrix declare; a store or family added later would need a check added. | Not disconfirmed; limit stated |
| 5 | The supersession checker is general | A live contradiction with no D-SM row and no declared structural family. The map-derived half grows by itself; **the four structural tables do not** — that half is as narrow as the nine literals were, just aimed at mechanisms instead of sentences. Said in the file's own docstring. | Not disconfirmed; **limit stated** |
| 6 | My record matches my code | A claim here the shipped files do not support. This failed in R3 and again in R4, and Fable caught a third in C1. Every §1–§5 number in this record was read back out of the shipped `out/*.json` or re-derived from the file it describes before being written. That is the same assurance I gave twice before. | **Failed three times; re-checked, not proven** |
| 7 | Determinism, hygiene, allowlist | Any output byte-differing across runs, or a file written outside the allowlist. 13/13 identical; 26 files touched, all inside. | Not disconfirmed |

## 7. Scope discipline

Per the verifier's §6 and the packet: corrections stayed inside simulator/oracle/fold/
schedule-test/validator code. I found and did **not** fix: A4's fail-closed comes from
policy composition rather than an envelope reason, so E1 does not record it (E1 covers
envelope-level reasons only). That is a coverage limit of E1, not a defect the packet
asked for, and widening it was not authorized. It is disclosed here rather than done.

## 8. Open items carried to Fable

1. **`13F_Open_Findings.json` does not exist and I cannot create it** — it sits outside
   the allowlist. Format is documented in `13V_`'s docstring. Until Fable writes it,
   `--final-gate` fails closed on the four rows naming P2T-02/P2T-03, which is the
   honest current state.
2. **P2T-04's normative-text half and P2T-05's matrix half are Fable's**, per `29_`.
   The checker and validator are ready for them.
3. **Carried forward unchanged:** the D-B5 row-level granularity limit; the `23_`
   residual-risk item on rule-table branches mirroring fixture routes.

## 9. Deviations

- **No scope deviations.** Nothing written outside the three allowlisted areas.
- **Branch deviation (unchanged, disclosed):** operator-designated branch.
- **Recommended reviewer focus, in order:** (1) falsifier row 2 — the nine mapping
  dispositions in §2, especially the four that changed a dimension's meaning after a
  failure; (2) S3's and S10's added stimuli; (3) §5's unexecuted validator.

---

*Builder-authored completion claim and evidence index — not independent evidence (APP-06). Every proof is reproducible from the pinned snapshot with the commands in `README.md`.*
