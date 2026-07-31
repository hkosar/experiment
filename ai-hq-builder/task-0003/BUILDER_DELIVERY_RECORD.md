# Builder Delivery Record — TASK-0003 (rework cycle R4)

**Task:** TASK-0003 — P2S-01 Behavioral Candidate-Transition/Fold Simulator (parent topic TOPIC-0002).
**Builder:** Claude Code session, model `claude-opus-5` (standing authorized substitution, trail entry 69).
**Branch:** `claude/task-0002-builder-handoff-g97x8j` (operator-designated; see §8).
**Instruction authority:** `22_` Task Packet + `23_` R1 + `24_` R2 + `25_` R3 + `26_` R4.
**Status:** **Reworked (R4); independent re-verification pending.** No design-gate passage, P2S-01 closure, or record-shape selection is claimed.

---

## 1. ERRATUM against the R3 Delivery Record

R3's RW-22 row stated that `evidence-tamper-succeeds`'s confession token *"and the
disjunct that read it are both gone."* **That was false.** The mutation stopped
writing `"tampered": True`, but the predicate disjunct that read it survived at
`oracle.py:122`, byte-identical to R2. The behavior was correct — the mutation
discriminated through the second, computed disjunct — but the sentence described a
deletion that had not happened, in the cycle whose subject was claims matching code.

I did not verify that row against the file before writing it. The disjunct is deleted
in R4 (RW-25), and the correction is recorded here rather than quietly folded into the
disposition table. Two consequences I have applied to this round: every claim in §2
and §3 below was re-checked against the shipped file before it was written, and the
one R3 disclosure that R4 *makes* false — the NOT-SIMULATED and README entries saying
the attention band is never compared — has been rewritten rather than left standing.

## 2. Disposition of RW-25..RW-27

All findings reproduced before any change; all concurred; none contested.

| # | Finding | What changed | Shipped-evidence proof |
| --- | --- | --- | --- |
| **RW-25** | `tampered` disjunct survived as dead code; R3's record claimed it was gone | Disjunct **deleted**. What remains is the computed witness: the refusal that should have recorded the rejected write is absent. The erratum is §1 above, not a table cell. | `grep -rn tampered *.py` returns two **comments** documenting the removal and no code. `evidence-tamper-succeeds` still witnesses "successful modification", "suppressed tamper evidence", "self-certified execution" and "engine-written evidence rendered" in `out/seeded_defects.json`. |
| **RW-26 (a)** | Citation identity leg unanchored — `ZZ-9 / ratified` passed | **Both legs** now read from the fixture. New `oracle.expected_interrupt_policy()` parses the expected id **and** status from `start_state`, deliberately as a second parser rather than borrowing the engine's — the judge cannot disagree with the engine if both call the same function. The emitted citation must match both; a stimulus naming no policy makes any citation a failure. | `interrupt-policy-id-fabricated` (new mutation) is in the shipped witness list for `pass_rule:interrupt_policy_cited`, beside `pending-policy-cited-as-ratified` and `interrupt-policy-uncited`. Re-ran the reviewer's exact probe: `ZZ-9/ratified` now fails the check and the case. |
| **RW-26 (b)** | OD-1 rule 2 unmodeled and unlisted | NOT-SIMULATED entry added, quoting the rule and stating why it is **deliberately not implemented**: no fixture exercises it (A8's trigger is watchdog-confirmed, i.e. rule 1), so the code would be untestable. Not implemented, per instruction. | `out/gate_report.json` → `not_simulated`. |
| **RW-26 (c)** | Standalone runner did not gate on `judge_checks_not_falsifiable` | Condition added; the standalone runner and gate criterion 13 now agree on what passes. | `run_defects.py:621`. |
| **RW-27** | `expected.attention` uncompared on all 27 fixtures | Full mapping + comparison implemented. See §3 — including the two disagreements I could **not** ground, which are returned as change requests rather than reinterpreted. | `out/results.json` → `attention_mapping` per combination and the summary counts; new gate criterion 15. |

## 3. RW-27 in full — the last uncompared dimension of requirement 4

**Coverage, stated as counts and not as a headline:**

| | Fixtures | Combinations |
| --- | --- | --- |
| **Compared** | **20 / 27** | **60 / 81** |
| Unmapped — the expectation names no D-B7 §2.1 band | 5 | 15 |
| **UNRESOLVED — returned as change requests** | **2** | **6** |

Unmapped (reported, never guessed): S10 `"per class"`, A1 `"security event"`, A6
`"per outcome"`, A10 `"RES alarm"`, A16 `"per ATT-01 security assessment"`. Each
defers to another rule or names a channel rather than a band; guessing which band the
author meant is exactly what earlier cycles were reworked for.

**Two comparison semantics, and the split is grounded, not convenient.** Expectations
naming a demanding band (Critical, Needs-Owner) or a specific channel (Briefing, Hub)
are compared for **equality**. Expectations of "None", "Record-only" or a pure display
surface are compared as a **ceiling** — the computed band must not reach Needs-Owner
— because the corpus uses "None" that way in its own words: A11 pairs
`attention: "None"` with a `"monthly digest"` receipt and a forbidden entry reading
literally *"owner attention consumed"*; S5 pairs `"None (brief line only)"` with a
`"Desk brief line"` receipt. Reading those as equality against §2.1's Record-only
("filed, findable") would contradict the fixtures' own receipts. The ceiling reading
is weaker than equality, it is labelled `"comparison": "ceiling"` in every shipped
record, and it still fails everything at Needs-Owner or Critical.

**Seven combinations failed on first run. Each diagnosed, none papered over:**

| Fixture | Diagnosis | Basis | Action |
| --- | --- | --- | --- |
| **S3** | **Encoding defect (Builder).** The AUT-05 inputs were missing, exactly as RW-05 found them missing on S2 and A9 — the third instance of the same omission. Without `placement_scope`/`proposed_action_class` there is no routine-filing path and the engine fell to T3 owner judgment. | D-B6 AUT-05, and the RW-05 precedent. Derived from `normalized_input` ("'usage costs?' during design session") + `start_state` (a recorded foreground focus): an interjected question captured alongside the running work is an in-subtree filing. **No oracle field was consulted.** | Fixed in `scenarios.py`. Computes `none`. |
| **S9** | **Engine defect.** S9's encoding already said `read_only_view` and "recall-by-description is a read path" — the *engine* had no read path for an owner query and assigned Needs-Owner to an answered retrieval. | D-B7 §2.1 as quoted in R4: Needs-Owner is *"queue admission, next natural session"*. An inline-answered recall queues nothing, so that band contradicts its own definition. Mirrors the engine's existing derived-views read path. | Fixed in `engine_core.py`. Computes `none`. |
| S5, S8, A11, S1 | **Not defects.** All four are "None"/display expectations whose computed band is `none` or `briefing`, i.e. below Needs-Owner. They pass under the ceiling semantics above. | Grounded as described above. | No change. |
| **S7** | **UNRESOLVED — change request.** Expects Briefing; the engine raises the six-message batch to `hub` because one input is a spoof. Two questions: whether `hub` is a sanctioned band, and whether one flagged input raises the whole batch's band. | Neither §2.1's quoted vocabulary (Critical / Needs-Owner / Briefing / Record-only — **no Hub**) nor the corpus settles either question. | **Not counted as compared. Not silently passed.** Named in the runner output, the gate report and NOT-SIMULATED. |
| **A14** | **UNRESOLVED — change request.** Expects Hub; the SCH-02 expired path computes needs-owner. | Same root cause: `hub` is absent from the quoted §2.1 vocabulary, so which side is wrong is not determinable from the Builder snapshot. | Same. |

**The change request, stated plainly:** the engine carries a fifth band, `hub`, that
the D-B7 §2.1 vocabulary quoted in R4 does not contain, and two fixtures turn on it.
I cannot resolve S7 or A14 without the document. Both possibilities are live — the
band is real and §2.1's quotation is partial, or the band is a Builder invention and
the engine should not emit it — and picking one would be reinterpreting a design
document I cannot see. Fable's call.

**Falsifiability, like every other judge check:** `expected_attention` has **102**
named witnesses in the shipped layer D output (headline `attention-relax@A12/S1`);
`expected_attention_surface` has 6 (headline `admit_forbidden@S1/S1`). Both appear in
criterion 13's 15/15.

## 4. Zero regressions

81/81 combinations still pass. The only two behavioral changes are S3's encoding and
S9's engine read path, each dispositioned above; every other previously-passing
combination is unchanged, and the 10 shipped outputs regenerate byte-identically
across two consecutive runs.

## 5. Acceptance criteria — 16 re-proven

All PASS. Anti-circularity (textual + import + structural); 81/81 combinations, 0
unclassifiable; 171 evaluations over 56 predicates, **56 reachable, 0 NOT-EVALUABLE**;
0 receipt-ownership violations; 81/81 order-invariant over 6 permutations; 81
divergences; E2E-1 with the seeded leak detected; 9/9 named defect classes; 8b 56/56
via a **61-mutation** catalogue; P2S-05 5/5 discriminating; P2S-07 2/2; 12 — 11/11
composition cases flipping; 13 — **15/15 judge checks flippable**, 0 orphaned
switches, 0 dead mutations; 14 — the D-B5 rule shown load-bearing; **15 — 60/81
attention comparisons, with the unmapped and unresolved counts printed on the same
line so neither can hide inside a green result.**

Determinism: **10/10 outputs byte-identical** across consecutive runs. Hygiene: 28
files, 0 CR, 0 trailing whitespace, single final LF. Allowlist: 28 files, all inside
`design/traces/behavioral/`. Dead-code scan: no unused imports, no unreferenced
private helpers.

## 6. Falsifier element (APP-06 / CPB-14, reflexive)

| # | Claim | What would disconfirm it | Status |
| --- | --- | --- | --- |
| 1 | Every judge check and predicate can fail | A check or predicate with no witness. Gated: 15/15 and 56/56. **Limit unchanged:** each can fail *somehow*, not necessarily for the right reason (row 2). Three pass-rule checks are never selected by any fixture and one is vacuous; all four named in the output. | Not disconfirmed; **limits stated** |
| 2 | Witness pairings are causally right | A pairing where defect and detection are only incidentally aligned. R2 removed eight, R3 removed a dead mutation and a masked pairing, R4 removed a dead disjunct. The base rate has not reached zero in four cycles. Complete witness lists make sampling cheap; **hand-checking remains the only real assurance.** | **Explicitly unverified by me** |
| 3 | No witness is an artifact | A mutation writing a channel only its predicate reads. The tripwire covers 7 known forms over 2 known channels with one named exemption, and says so. RW-25's dead disjunct is the proof of the stated limit: a *payload key* is not one of the tripwire's channels, so it sat inside the blind spot the docstring already described. | Not disconfirmed; **limit demonstrated, not just asserted** |
| 4 | My record matches my code | A claim in this document that the shipped files do not support. This failed at R3 (§1). Every §2/§3 row was re-checked against the file this round — but that is the same assurance I gave last time, and the honest status is that a reviewer's diff is what catches it. | **Failed once; re-checked, not proven** |
| 5 | The attention mapping is faithful | A fixture whose expectation §2.1 settles differently than I mapped it, or a "ceiling" reading that should have been an equality. The ceiling semantics are the judgment call of this round: I grounded them in A11's and S5's own receipts, and a reviewer who reads those fixtures differently would map them differently. | **Explicitly unverified by me** |
| 6 | Scenario encodings are faithful | An independent reader judging a `ScenarioSpec` field to encode an outcome rather than a stimulus. **S3's AUT-05 addition is this round's exposure** — I added it after a comparison against `expected.attention` failed, which is precisely the sequence that could smuggle an answer into an encoding. My guard was to justify it only from `normalized_input` + `start_state` and to check it is the same fact RW-05 required on S2 and A9. Worth a reviewer's direct look. | **Explicitly unverified by me; flagged** |
| 7 | The NOT-SIMULATED list is complete | A mechanism neither exercised nor listed. R4 added OD-1 rule 2 and the attention-mapping coverage, and **deleted one entry that R4 made false**. Incomplete at every prior cycle. | **Explicitly unverified by me** |
| 8 | Determinism, hygiene, allowlist | Any output byte-differing across runs, or a file outside `design/traces/behavioral/`. 10/10 identical; 28 files, all inside. | Not disconfirmed |

## 7. Open change requests to Fable

1. **The `hub` band (S7, A14).** As §3. Two fixtures cannot be compared until Fable
   says whether D-B7 sanctions a fifth band, and whether one flagged input in a batch
   raises the whole batch's band. Both are one-line answers on Fable's side; both
   would let me close the last two attention comparisons.
2. **Carried forward, unchanged:** the D-B5 row-level granularity limit (my rule
   refuses consequential classes under any degradation where D-B5 assigns
   per-failure-row safe modes) remains open and is Fable's to carry to the verifier.

## 8. Deviations and open items

- **No scope deviations.** Nothing outside `design/traces/behavioral/` written; no
  design document, gate artifact, trail, registry or checksum touched.
- **Two engine/encoding changes**, both required by RW-27's diagnosis clause and both
  individually dispositioned in §3 with their cited basis. No other behavior changed.
- **Branch deviation (unchanged, disclosed):** operator-designated branch.
- **Residual-risk item from `23_` §carried-to-verifier** (rule-table branches
  mirroring fixture routes) remains open, as `24_`, `25_` and `26_` also leave it.
- **Recommended reviewer focus, in order:** (1) S3's AUT-05 encoding addition, per
  falsifier row 6 — it is the one change this round made after seeing a comparison
  fail; (2) the ceiling-vs-equality split, per row 5, especially A11 and S5; (3) the
  two unresolved `hub` fixtures, which need a Fable decision rather than a review.

---

*Builder-authored completion claim and evidence index — not independent evidence (APP-06). Every proof is reproducible from the pinned snapshot with the commands in `README.md`.*
