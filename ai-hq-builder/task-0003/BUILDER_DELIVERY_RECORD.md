# Builder Delivery Record — TASK-0003 (rework cycle R3)

**Task:** TASK-0003 — P2S-01 Behavioral Candidate-Transition/Fold Simulator (parent topic TOPIC-0002).
**Builder:** Claude Code session, model `claude-opus-5` (standing authorized substitution, trail entry 69).
**Branch:** `claude/task-0002-builder-handoff-g97x8j` (operator-designated; see §7).
**Instruction authority:** `22_` Task Packet + `23_` Rework Packet R1 + `24_` Rework Packet R2 + `25_` Rework Packet R3.
**Status:** **Reworked (R3); independent re-verification pending.** No design-gate passage, P2S-01 closure, or record-shape selection is claimed.

---

## 1. What R3 was, in one line

R0 shipped circular evidence; R1 shipped padded counts; R2 shipped auxiliary checks
whose falsifiability was asserted; R3 applies the same discipline to the suite's own
newest layer. The binding rule I worked to — **anything claimed able to fail must be
shown failing in a shipped run under its own seeded defect** — is the reason every
row below cites an output file rather than a manual experiment.

## 2. Disposition of RW-19..RW-24

I reproduced all three Medium findings before changing anything. All three were
exactly as reported.

| # | Finding | What changed | Shipped-evidence proof |
| --- | --- | --- | --- |
| **RW-19** | `ignore_degradation` in no runner; deleting the D-B5 rule does not flip A10 | New **layer E** in `run_defects.py`: a clearly-labeled *harness self-test* (not a fixture) that drives a synthetic degraded-stores stimulus with a step-up-completed, payment-affecting envelope through the **real action-emission path**. Following the `run_composition.py` precedent. New gate criterion 14. | `out/seeded_defects.json` → `degradation_rule_self_test`: clean → `envelope_would_authorize: true`, `action_emitted: false`, `refused_citing_degradation: true`; `ignore_degradation` seeded → `action_emitted: true`, `refused_citing_degradation: false`. `discriminates: true`. The corpus limitation is carried in the same object, in the NOT-SIMULATED list and in the README. |
| **RW-20** | `pending-policy-cited-as-ratified` had no detector; `"interrupt_policy": "OD-1"` an unconditional constant | **Both halves conditioned on the stimulus.** The engine no longer stamps a constant: `simulate.interrupt_policy_citation()` reads the policy id **and its ratification status out of the fixture's own `start_state`**, and a stimulus naming no interrupt policy gets no citation. The judge check now derives the expected status independently from that same text and **fails on the contradiction**, instead of accepting either status. The scenario flag `od1_policy_pending` is gone — the fact is read from the fixture, not transcribed. | Exactly one fixture emits a citation (`A8 / OD-1 / pending`); before, all 27 did. `out/seeded_defects.json` → `judge_check_falsifiability["pass_rule:interrupt_policy_cited"].witnesses` lists `pending-policy-cited-as-ratified@A8/S1,S2,S3` alongside `interrupt-policy-uncited` and `drop-decision`. |
| **RW-21** | Four judge checks with no shipped falsifier; `render_leak` orphaned | New **layer D**: runs the **real judge** over every seeded defect and every mutation and reports, per judge check, **every** witness that flips it — same reporting shape as `predicate_reachability`. `render_leak` promoted to a named engine defect class (`render-policy-ignored`). `lease_before_policy` **removed** (dead). New gate criterion 13, which fails on any orphaned switch. | **13/13 judge checks have a named witness; 0 NOT-FALSIFIABLE; 0 orphaned switches.** `masked_render` ← `render_leak@A12`; `hearsay_provenance` ← `hearsay-provenance-lost@S2`; `interrupt_policy_cited` ← three distinct witnesses; `no_restricted_token_on_any_surface` ← `floor-overwrite@A13`. Layer A: `render-policy-ignored` flips 6 combinations. |
| **RW-22** | Integrity check oversold; two residual answer-key writes | The check is renamed a **tripwire** and its docstring, its output header and the README now say what it does not establish. Coverage extended to all five reviewer evasion forms plus alias binding (7 forms). `normalizer-authority-leak` now perturbs **M2's recorded ceiling** and lets `simulate.recompute_normalizer_invariants` — the production writer, shared with the production path — re-derive `authority_invariant`. `evidence-tamper-succeeds` no longer writes `"tampered": True`; the confession token and the disjunct that read it are both gone. | Section C header now reads "regression check, NOT a proof"; `proves_absence_of_artifact_witnesses: false` is a field in the JSON. Both repaired mutations still witness real predicates: `normalizer-authority-leak` → "maximum authorized action increased by the M2 classification"; `evidence-tamper-succeeds` → "successful modification", "suppressed tamper evidence", "self-certified execution", "engine-written evidence rendered". |
| **RW-23** | PC-12 unlisted; "PC-1..PC-12" label false; synthetic-only coverage unsaid | `run_composition.py`'s header now carries an **exact accounting of the PC table** — 9 driven + 2 layers, PC-5/PC-8 not simulated, **PC-12 accounted** as mechanically PC-2's shape exercised fixture-side via A4. New `ACCOUNTED_ELSEWHERE` list in the gate report. Both substitutions (PC-3 floor, PC-7 third domain) carry a one-line note at the case and in the exercised list. The synthetic-only sentence for `scope`/`applicability_predicate`/`effective_window` is in the header, NOT-SIMULATED and the README. | `out/gate_report.json` → `accounted_elsewhere`, `exercised_by_composition_suite`, `not_simulated`. |
| **RW-24** | Residual honesty/fidelity set (7 items) | See §3 — each item taken separately. | Per item in §3. |

## 3. RW-24, item by item

| Item | What changed | Shipped-evidence proof |
| --- | --- | --- |
| `WatchdogHeartbeatEvent` hard-coded `fresh: True` | Derived from the recorded fact `derived["watchdog_fresh"]`, which now has a reader. | New `watchdog-heartbeat-stale` mutation witnesses "silence without watchdog" at `S1/S1,S2,S3`, alongside `watchdog-silent`. |
| `FocusPointerEvent.preserved` asserted | Derived by `simulate.focus_preserved()` from the computed band. **Threshold is the interrupting band, not needs-owner**: `needs-owner` queues an item for the owner; only `critical` seizes the surface being worked on, and seizing it is what loses the pointer. My first attempt used needs-owner and failed S3 — see §5. | `focus-displaced-by-escalation` perturbs the **band** and re-derives through the production writer; it witnesses "foreground context loss" at `S3/S1,S2,S3` alongside `foreground-loss`. |
| S4's dropped `OverrideEvent` undetected | "unlogged override" gained an OverrideEvent-presence leg requiring the consequence summary and the acknowledgment. | New `drop-override` mutation appears in that predicate's witness list at `S4/S1,S2,S3`. It would previously have been masked — see §4. |
| Builder-added stimuli enumeration incomplete | `scenarios.py` docstring now names **S2/A5/A9 `actions`** and **S6/A12 `verification_arrives`**, with what is narrative and what is Builder-added stated separately, plus a sentence saying this is the claim I cannot verify from inside. | Diff of `scenarios.py` docstring. |
| fold's "receipt referenced but absent from the basis" branch dropped in R2 | **Restored** in `receipt_ownership_violations`. | New `receipt-reference-dangling` mutation witnesses "engine self-marks executed/verified" and "self-certified execution", and flips the `receipt_ownership` judge check. |
| "suppression record" matcher vacuous | The engine now **computes** a suppression record during quiet hours for each input whose own band sits below the interrupting threshold, naming the held source and when it surfaces. The matcher requires that record. | A8 emits `suppressed_source_id: email-big-nonurgent`, `suppressed_until: morning-briefing`. New `suppression-record-lost` mutation flips `required_evidence_kinds` at `A8/S1,S2,S3` — the repaired matcher is shown discriminating. |
| PC-3 / PC-7 substitutions unnoted | One-line note at each case and in the exercised list. | `run_composition.py`; `out/gate_report.json`. |

## 4. Two further defects this round surfaced in my own code

Both found by making the witness searches complete, not by re-reading:

- **Both witness searches stopped at the first hit.** `prove_reachability` broke on
  the first mutation that fired, so a targeted defect could be masked by a blunter
  one that sorted earlier. Concretely: "unlogged override" would have reported
  `drop-decision` (which removes the whole DecisionEvent) and **never shown
  `drop-override`** — the RW-24 fix would have been a claim with no shipped run
  behind it. Both layers now record complete witness sets. This is what makes the
  §2/§3 proof columns mean what they say.
- **`step-up-bypass` was a dead mutation.** Its guard needed a case where the step-up
  is demanded and not satisfied; the only two step-up fixtures complete it, so the
  mutation had fired nowhere since it was written. Same "guarded by accident" shape
  as RW-15 and RW-19, one layer further out. It now drops the satisfaction and emits
  the gated action, and witnesses "approval without step-up". A new gate condition
  fails the run if **any** catalogue mutation witnesses nothing.

## 5. One finding I did not act on, disclosed instead

Deriving focus displacement from the computed band made S3 fail: the engine computes
`needs-owner` for S3's interjection while the fixture's `expected.attention` is
`None`. Investigating showed **the judge never compares the computed attention band
against `expected.attention` at all** — it maps `expected.authority`, quarantine and
receipt ownership. Bands are constrained only where a forbidden predicate happens to
read them.

I corrected my threshold (the interrupting band is the one that seizes a surface,
which is also the defensible reading), and I **did not** add a band-vs-expected
comparison: that is a new check across all 27 fixtures, not a rework item, and its
cascade is not mine to decide. It is now an entry in NOT-SIMULATED and in the README,
and it is my first recommended reviewer focus. If Fable wants it, that is a change
request I can execute.

## 6. Acceptance criteria — 15 re-proven

All PASS. Anti-circularity (textual + import + structural); 81/81 combinations, 0
unclassifiable; 171 evaluations over 56 predicates, **56 reachable, 0
NOT-EVALUABLE**; 0 receipt-ownership violations; 81/81 order-invariant over 6
permutations; 81 divergences; E2E-1 two-normalizer with the seeded leak detected;
**9/9 named defect classes effective**; 8b 56/56 reachable via a **60-mutation**
catalogue; P2S-05 5/5 computed and discriminating; P2S-07 2/2; 12 — 11/11
composition cases all flipping; **13 — 13/13 judge checks flippable, 0 orphaned
switches, 0 dead mutations**; **14 — the D-B5 rule shown load-bearing by the
self-test**.

Determinism: two consecutive `run_gate.py` runs are **byte-identical across 10/10
output files** (was 9 — see below). Hygiene: 28 files, 0 CR, 0 trailing whitespace,
single final LF. Allowlist: 28 files, all inside `design/traces/behavioral/`.

Three hygiene repairs found while re-proving the above, all disclosed rather than
folded in silently: `check_anticircularity.py` **accepted `--out` and ignored it**,
so `run_gate.py --out DIR` produced nine of the ten declared outputs and the
determinism comparison silently skipped `anticircularity.json`; the README claimed
all runners take `--fixtures` when three take `--out` only; and twelve unused imports
across six modules (one of them, `copy` in `mutations.py`, a regression I introduced
in this cycle) are removed.

## 7. Falsifier element (APP-06 / CPB-14, reflexive)

| # | Claim | What would disconfirm it | Status |
| --- | --- | --- | --- |
| 1 | Every judge check and every predicate can fail | A check or predicate with no witness. Reported per run and gated: 13/13 and 56/56. **Limit:** this establishes each can fail *somehow*, not that it fails for the *right* reason — see row 2. Three pass-rule checks are never selected by any fixture and one is selected but vacuous; all four are named in the output rather than counted. | Not disconfirmed; **limits stated** |
| 2 | Witness pairings are causally right, not coincidental | A pairing where the defect and the detection are only incidentally aligned. R2 removed eight; R3 removed one dead mutation and one masked pairing. That base rate is the reason this row has not moved: **hand-checking a sample remains the only real assurance.** Complete witness lists now make the check cheaper for a reviewer — a predicate whose only witness is a blunt instrument is visible in the JSON. | **Explicitly unverified by me** |
| 3 | No witness is an artifact | A mutation writing a channel only its predicate reads. The tripwire matches 7 known forms over 2 known channels, with one named exemption. **It does not prove the property and no longer says it does.** A novel channel passes it untouched. | Not disconfirmed; **claim downgraded to match the check** |
| 4 | The scenario encodings are faithful | An independent reader judging a `ScenarioSpec` field to encode an outcome rather than a stimulus. R1 fixed six; R2 fixed one and enumerated four; R3 enumerated five more and **removed one transcription entirely** (`od1_policy_pending` — the engine reads the fact from the fixture text now). Two successive reviews each found the enumeration incomplete. | **Explicitly unverified by me** |
| 5 | The NOT-SIMULATED list is complete | A mechanism neither exercised nor listed. R3 added five entries, including two I found while doing other work (the D-B5 corpus limitation, the never-compared attention band). This is the claim I have flagged since R1 as invisible-to-me by definition, and it has been incomplete at every cycle. | **Explicitly unverified by me** |
| 6 | The D-B5 / D-B7 §3 encodings are faithful | Neither document is in my snapshot. Fable closed this for the encodings themselves at R3; the **row-level granularity limit stays open** — my rule refuses consequential classes under any degradation where D-B5 assigns per-failure-row safe modes. Fable is carrying that to the verifier. | **Closed by Fable for fidelity; granularity limit open** |
| 7 | Determinism and allowlist hold after R3 | Any output byte-differing across runs, or a file outside `design/traces/behavioral/`. 10/10 identical; 28 files, all inside. | Not disconfirmed |

## 8. Deviations and open items

- **No scope deviations.** Nothing outside `design/traces/behavioral/` written; no
  design document, gate artifact, trail, registry or checksum touched.
- **No change request was required.** Every RW-19..RW-24 item was correctable inside
  the allowlist, as `25_` predicted. The one thing I chose not to build — the
  attention-band comparison in §5 — is offered as a change request, not taken
  unilaterally.
- **Branch deviation (unchanged, disclosed):** operator-designated branch rather than
  a task-specific one.
- **Residual-risk item from `23_` §carried-to-verifier** (rule-table branches
  mirroring fixture routes) remains open and unactioned, as `24_` and `25_` also
  leave it.
- **Recommended reviewer focus, in order:** (1) the never-compared attention band
  (§5) — decide whether it is a gap or out of scope; (2) witness pairings, per
  falsifier row 2, now that complete witness lists make sampling cheap — a predicate
  whose only witness is `drop-decision` or `authority-raise` is the shape to look at;
  (3) the NOT-SIMULATED list, per row 5, which has been incomplete every cycle.

---

*Builder-authored completion claim and evidence index — not independent evidence (APP-06). Every proof is reproducible from the pinned snapshot with the commands in `README.md`.*
