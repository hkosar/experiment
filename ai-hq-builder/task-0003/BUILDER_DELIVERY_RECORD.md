# Builder Delivery Record — TASK-0003 (rework cycle R2)

**Task:** TASK-0003 — P2S-01 Behavioral Candidate-Transition/Fold Simulator (parent topic TOPIC-0002).
**Builder:** Claude Code session, model `claude-opus-5` (standing authorized substitution, trail entry 69).
**Branch:** `claude/task-0002-builder-handoff-g97x8j` (operator-designated; see §6).
**Instruction authority:** `22_` Task Packet + `23_` Rework Packet R1 + `24_` Rework Packet R2.
**Status:** **Reworked (R2); independent re-verification pending.** No design-gate passage, P2S-01 closure, or record-shape selection is claimed.

---

## 1. Disposition of RW-11..RW-18

I reproduced the two High findings before fixing them. Both were exactly as reported, and both were **my padding, in a subtler form than R0's**: I built the NOT-EVALUABLE machinery in R1, then routed four predicates through channels only the mutations wrote and reported 56/56 with the exclusion list empty.

| # | Finding | What changed | Proof |
| --- | --- | --- | --- |
| **RW-11** | 4 predicates reachable only through mutation-written `extras` flags | **Modelled the mechanisms** rather than declaring them out. The engine now computes and emits `WatchdogHeartbeatEvent` (D-KR §3 liveness), `FocusPointerEvent` (Desk/interjection focus projection) and `RecallResultEvent` (recall against the recorded prior capture). Predicates read those events; mutations drop or perturb them. The two `is not False` evidence matchers now require the computed events. | Verified zero engine writers existed before the fix; all three event types are now emitted in production and their mutations are event-level. `out/results.json`, `out/seeded_defects.json` |
| **RW-12** | 4 predicates detected mutation-authored tokens | (1) attention-relax now compares the **computed band** against `composition_attention_min`; (2) correction→policy reads the real `caused_by` edge, and the mutation no longer writes a confession flag; (3) attention events carry a computed `source_origin`/`source_trust`/`quiet_hours`, so sleep interruption is detectable from engine output; (4) S4 now emits a real `OverrideEvent` in production, so nagging is a duplicate of a real event. | Each rewritten predicate re-proven reachable through the corrected channel. |
| **RW-13** | NOT-SIMULATED incomplete; completeness sentence false | New **`run_composition.py`** drives PC-1, PC-2, PC-3, PC-4, PC-6, PC-7, PC-9, PC-10, PC-11 plus D-B8 §2 `scope` and `applicability_predicate` through the **real `compose_policies`**, each with a composition-path defect. `scope`/`applicability_predicate` added to `PolicyObject`; `at_time` and the envelope are now passed, so PC-4 and predicate filtering are live. The false sentence is deleted; the declaration is expanded (incl. 13 never-emitted event types and the PC-6 timing caveat). | **11/11 cases pass, 11/11 flip under a composition-path defect.** New criterion 12. `out/composition_cases.json` |
| **RW-14** | A12 `notification_preview` unauthorized; masked-render check circular | `notification_preview` **removed** from A12. The engine emits a computed render-policy application record; the `masked_render` pass-rule check now reads that computed output instead of asking whether the scenario declared a floor. | A `render-leak` mutation flips it; A13's fixture-grounded preview path is unchanged. |
| **RW-15** | A10's refusal came from the envelope, not the degradation | Encoded the D-B5 rule **as quoted in `24_`**: consequential classes are refused during degradation **regardless of envelope authority**, and the refusal cites the degradation. | **Counterfactually live:** with degradation → 1 refusal citing it; with `ignore_degradation` seeded → 0. |
| **RW-16** | S2 hearsay and A8 OD-1-pending carried but inert | S2's attributed mention now produces a computed `ProvenanceRecord` marked `hearsay-attributed`, checked by a new `hearsay_provenance` pass-rule check. A8's decision basis now carries `interrupt_policy` + `interrupt_policy_status`, with a **pending** policy citable as pending, never ratified (D-B7 §3 as quoted in `24_`). | Three new mutations: `hearsay-provenance-lost`, `interrupt-policy-uncited`, `pending-policy-cited-as-ratified`. |
| **RW-17** | Documentation/honesty set | `scenarios.py` docstring restated with the Builder-added minimal stimuli **enumerated**; the `derived` field comment corrected; quarantine operationalization disclosed in `engine_core.py` and the README; `revoked_by_policy_event` reuse commented; dead code removed (3 unreferenced helpers, the unreachable `_render_leak` branch, the unused constant); receipt mutations now **perturb events and refold** instead of writing `receipt_violations`; S6/A12 lifecycles collapsed to **one action carrying its own XR → VR → RE chain**. | `unreferenced private helpers: NONE`; witness-channel integrity check passes. |
| **RW-18** | Citation alignment | `events.py` now cites the amended D-B9 P2S-06 store-priority list (control-journal first, D-SM row 13) instead of D-KR §1.4. No behavior change. | Comment-only diff. |

## 2. Witness-channel integrity — now proven, not asserted

R2 return requirement 3 asks that no mutation write a token whose only reader is its paired predicate. That is a **structural** pattern, so it gets a structural check: `run_defects.py` parses `mutations.py` and fails if any mutation assigns into `result.extras[...]` or appends to `receipt_violations` — the two artifact channels the reviews found.

It caught one remaining violation on first run (`twin-placement-divergence`), which now perturbs the recorded model output instead. **Section C: PASS.**

## 3. Honest reachability restatement

| Figure | R0 | R1 | R2 |
| --- | --- | --- | --- |
| Distinct predicates | 56 | 56 | 56 |
| Able to fire | **5** | 56 (4 via artifact channels, 4 token-tuned) | **56, all through computed channels** |
| NOT-EVALUABLE declared | not reported | 0 (machinery unused) | **0 — and the machinery is live** |
| Mutation catalogue | — | 51 | **55** |
| Witness-channel integrity | — | not checked | **checked structurally, PASS** |
| P2S-05 computed / discriminating | 2 / 2 | 5 / 5 | 5 / 5 |
| D-B8 composition cases | — | — | **11 / 11, all discriminating** |

The R2 number is 56/56 again, but it now means something different: every witness fires through state the engine genuinely computes, and the claim is backed by an automated check rather than my assurance. Per-predicate witnesses are in `out/seeded_defects.json` → `predicate_reachability`.

## 4. Acceptance criteria — 14 (+8b, +12) re-proven

All PASS: anti-circularity (incl. `mutations.py`); 81/81 combinations, 0 unclassifiable; 171 evaluations over 56 predicates, 56 reachable, 0 NOT-EVALUABLE, 0 failures; 0 receipt-ownership violations; 81/81 order-invariant; 81 divergences; E2E-1 two-normalizer + seeded leak; 8/8 named defects; **8b 56/56 reachable**; 6 permutations, 0 violations; P2S-05 5/5 computed and discriminating; P2S-07 2/2; **12 — 11/11 composition cases, all flipping under a composition-path defect**; two runs byte-identical (9/9 files); 28 files all inside the allowlist; byte hygiene 0 CR / 0 trailing whitespace / single final LF.

## 5. Two further defects this round surfaced in my own code

Both found by the reachability search failing, not by re-reading:

- **`receipt_ownership_violations` masked a tampered receipt.** It tracked one receipt per action, so an engine-authored *execution* receipt was hidden by a later legitimate *verification* record for the same action. Now every evidence event answering an action is checked. This was a real hole in requirement 6.
- **`_receipt_overwrite` mis-read the XR → VR chain** as an overwrite once the per-action linkage landed. Overwrite now means two receipts *of the same kind*.

## 6. Falsifier element (APP-06 / CPB-14, reflexive)

| # | Claim | What would disconfirm it | Status |
| --- | --- | --- | --- |
| 1 | No witness is an artifact any more | A mutation writing a channel only its predicate reads. Checked structurally for the two known patterns (`extras`, `receipt_violations`). **Residual:** the check enumerates *known* artifact channels; a novel one — say a new summary field written only by mutations — would pass it. The general property is not decidable by this check, and I am not claiming it is. | Not disconfirmed; **limit stated** |
| 2 | Reachability means the predicate fires for the *right* reason | A witness pairing where the defect and the detection are only coincidentally aligned. R2 removed eight such pairings; that base rate suggests more may remain among the 48 the review sampled as genuine. Hand-checking a sample remains the only real assurance. | **Explicitly unverified by me** |
| 3 | The scenario encodings are faithful | An independent reader judging a `ScenarioSpec` field to encode an outcome rather than a stimulus. R1 fixed six; R2 fixed one more (A12's unauthorized preview) and enumerated four Builder-added stimuli that were previously undisclosed. | **Explicitly unverified by me** |
| 4 | The NOT-SIMULATED list is now complete | A mechanism neither exercised nor listed. R2 added five entries and a companion "exercised" list so the two together span the D-B8 layers — but this is the claim I flagged in R1 as invisible-to-me by definition, and it was in fact incomplete then. Treat the same way now. | **Explicitly unverified by me** |
| 5 | RW-15's degradation rule is faithful to D-B5 | D-B5 itself is **not in my snapshot**; I encoded from the rule text quoted in `24_`. If the quotation is partial, my encoding inherits that. Same for D-B7 §3 (RW-16). Disclosed rather than silently assumed. | **Cannot verify — source document absent** |
| 6 | Determinism and allowlist hold after R2 | Any output byte-differing across runs, or a file outside `design/traces/behavioral/`. 9/9 identical; 28 files, all inside. | Not disconfirmed |

## 7. Deviations and open items

- **No scope deviations.** Nothing outside `design/traces/behavioral/` written; no design document, gate artifact, trail, registry or checksum touched. No change request was required — RW-18's D-B9 amendment was already made by Fable.
- **Two rules encoded from packet quotations** (RW-15 D-B5, RW-16 D-B7 §3) because those documents are not in the Builder snapshot. Flagged in the NOT-SIMULATED list and falsifier row 5. If either quotation is partial, that is a change request, not something I can detect from here.
- **Branch deviation (unchanged, disclosed):** operator-designated branch rather than a task-specific one.
- **Residual-risk item from `23_` §carried-to-verifier** (rule-table branches mirroring fixture routes) remains open and unactioned, as `24_` also leaves it.
- **Recommended reviewer focus:** (1) witness pairings, per falsifier row 2 — eight were wrong last cycle; (2) the NOT-SIMULATED/exercised pair, per row 4, which was incomplete last cycle; (3) the two packet-quoted rule encodings, per row 5.

---

*Builder-authored completion claim and evidence index — not independent evidence (APP-06). Every proof is reproducible from the pinned snapshot with the commands in `README.md`.*
