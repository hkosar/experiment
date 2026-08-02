# Builder Delivery Record — TASK-0004 (closure micro-round, C1)

**Task:** TASK-0004 — P2T corrections (parent topic TOPIC-0002).
**Builder:** Claude Code session, model `claude-opus-5` (standing authorized substitution, trail entry 69).
**Branch:** `claude/task-0002-builder-handoff-g97x8j` (operator-designated; see §7).
**Instruction authority:** `30_` Task Packet + `31_` Closure Note; governing findings `28_`/`28A_`; dispositions `29_`.
**Status:** **Closure return delivered; independent re-verification pending.** No design-gate passage is claimed; the verifier's FAIL stands until the verifier changes it.

---

## 1. Erratum against the TASK-0004 return (L-3)

The §1 P2T-02 row said *"Each ships its defect witness: with both new layers disabled
the same basis folds with `causal_violations=0`."* That is true for **7 of 8** cases.
`duplicate-event-ids` is rejected by the topological sort's ID-uniqueness check even
with both new layers off, so its row reads *"not reproducible with both checks off"* —
which the shipped JSON has recorded correctly all along. The sentence generalised from
seven rows to eight; the artifact did not. Corrected here.

## 2. Disposition of M-1, M-2 and the three Low items

| # | Finding | What changed | Shipped-evidence proof |
| --- | --- | --- | --- |
| **M-1** | The Builder-added-stimulus enumeration was stale for the third time, and S3's inline comment claimed an entry that did not exist | Both fixed — **and made structural**. `scenarios.BUILDER_ADDED_FIELDS` / `BUILDER_ADDED_ACTION_FIELDS` declare which fields require an entry; new `check_anticircularity.check_stimulus_enumeration()` (check **D**) fails the gate for any fixture-field pair that is set but not enumerated. The docstring's "exhaustive as far as I can determine" is replaced: the check now determines it. | Anti-circularity output: **D-stimulus-enumeration PASS — 21 pairs in use, 30 enumerated.** Run against the shipped return before the fix, it fails and names the pairs. |
| **M-2** | The supersession checker dropped malformed D-SM rows silently — fail-open on its own input | Once the table header is seen, **every** `\|`-leading line must be a well-formed data row (≥4 cells, numeric ID). Anything else is collected in `malformed_map_rows`, printed, and **fails the run**. Header/separator detection is anchored on the header rather than sniffed per line, so a second table added to the map later gets its own region instead of being reported as damage. | `--self-test` gained two cases: **mangled row ID** and **row with a dropped cell**, both now FAIL (the second still passed after my first attempt — it hit the `len < 4` guard, which is why the rule is anchored on the table region rather than on cell count). **SELF-TEST PASS, 8 cases.** |
| **L-1** | The E2 refusal fired on any `proposed_ceiling` and labelled it a rejected *raise* | The record is emitted only where the proposal exceeds the model-free base ceiling. D-B2 §2.4 permits lowering; filing a permitted lowering as a refusal would be a false record, which is worse than none. | A2's shipped record now carries `base_ceiling: record-only` beside `proposed_ceiling: outbound` — the comparison is in the artifact, not just in the code. |
| **L-2** | `fold.py` annotated `Tuple` without importing it | Imported. | `from typing import Dict, List, Optional, Sequence, Tuple`; used at `fold.py:163`. |
| **L-7** | A malformed finding token in a dependency cell silently became a non-reference; dead `got` variable | A cell whose leading token mixes letters and digits but does not parse as a finding id is now reported. Dead variable removed. | `13V_ --self-test` gained three cases: `P2T2:` and `p2t-02:` are reported, and ordinary prose (`Build gate: …`) is **not** mistaken for one. **SELF-TEST PASS, 11 cases.** |

## 3. The guard found more than the review did

M-1 asked for two entries (S3 `actions`; S10 `placement_scope`/`proposed_action_class`).
The structural guard found **five** unenumerated pairs: those two plus **S6 `actions`**
and **A12 `actions`**, which had never been enumerated in any cycle — their
`owner_step_up_provided` and `verification_arrives` were listed while the action tuples
that make those flags mean anything were not.

That is the argument for the guard in one line: a registry maintained by memory was
wrong in a way three consecutive reviews had not caught, and the first mechanical check
of it found more than the review that demanded the check.

**It also caught two bugs in itself.** My first version used `"  * "` as an
end-of-loop sentinel to flush the final bullet; `"  * ".strip()` is `"*"`, which fails
a `startswith("* ")` test, so the last bullet was never parsed — the same class of
quiet omission the guard exists to prevent. Fixed by flushing after the loop.

Second, and worse: I added check D to `check_anticircularity.main()` and **not** to the
list `run_gate.py` builds for criterion 1, so the guard ran when the checker was
invoked directly and did not run in the gate. A guard outside the gate is not a guard.
Found by re-reading the shipped `out/anticircularity.json` against the record's claim
rather than by re-reading the code — which is the whole point of that pass, and the
reason falsifier row 4 below says what it says. Criterion 1 now names the registry and
reports its counts.

## 4. Acceptance criteria — 20, all re-proven

All PASS. Anti-circularity now runs **four** checks (textual, import, structural, and
the new stimulus-enumeration registry). 81/81 combinations, 0 judged failures; 171
evaluations over 56 predicates, 56 reachable; 0 receipt-ownership violations; 81/81
order-invariant; 81 divergences; E2E-1 with the seeded leak; 9/9 named defect classes;
8b 56/56 via 62 mutations; P2S-05 5/5; P2S-07 2/2; 12 11/11 composition; 13 **18/18**
judge checks flippable, 0 orphaned switches, 0 dead mutations, 0 vacuous pass-rule
checks; 14 D-B5 self-test; 15 attention 66/81; 16 all four dimensions with the floor
holding; 17 **4/4** verifier probes defeated, 102/108 sentinels rejected, 97/97 governed
pairs with a contradictory witness; 18 **8/8** missing-basis cases closed; 19 **3/3**
schedule behaviors discriminating.

Determinism: two consecutive runs **byte-identical across 13/13 outputs**. Hygiene:
0 CR, 0 trailing whitespace, single final LF across every file I wrote. The one
flagged file is `03F_Replay_Fixtures.json`, which has no final newline — it is the
**frozen corpus**, verified byte-identical to the snapshot, and not mine to change.
Dead-code scan clean. **Allowlist: 20 modified + 7 added, 0 outside** the three
writable areas.

## 5. Falsifier element (APP-06 / CPB-14, reflexive)

| # | Claim | What would disconfirm it | Status |
| --- | --- | --- | --- |
| 1 | The stimulus registry can no longer go stale | A Builder-added stimulus field not in `BUILDER_ADDED_FIELDS`. The guard enforces the pairs it is told to watch; a **new kind** of Builder-added field would need adding to that tuple, and nothing detects that automatically. The recurrence class is closed for the four declared field families, not for all conceivable ones. | Not disconfirmed; **limit stated** |
| 2 | The supersession checker no longer fails open on its own input | A D-SM malformation neither rule catches — the checks are "well-formed row inside the table region" and nothing more. A semantically wrong but syntactically valid row still passes, as it must. | Not disconfirmed; limit stated |
| 3 | The schema reads the corpus faithfully | Unchanged from the TASK-0004 return, and still the row to audit: four of the nine dispositions changed what a dimension *means* after seeing a failure. Fable's verification found all nine GROUNDED and M1 continuous with the previously accepted reading, which is stronger evidence than mine — but it is not my claim to make. | **Independently adjudicated (Fable), not by me** |
| 4 | My record matches my code | A claim here the shipped files do not support. This has now failed in R3, R4, C1 and once more in the TASK-0004 return (L-3). Every number in §2–§4 was read back out of the shipped output or re-derived from the file it describes. That is the fourth time I have written that sentence. | **Failed four times; re-checked, not proven** |
| 5 | Determinism, hygiene, allowlist | Any output byte-differing across runs, or a file written outside the allowlist. 13/13 identical; 27 files touched, all inside. | Not disconfirmed |

## 6. Carried as disclosed limits (no action, per `31_`)

L-4 (13 vs 14 D-SM rows — snapshot-true; Fable's row 14 was picked up by the runtime
parser with no code change, which is the design's central claim confirmed); L-5
(basis-validator loosenesses against D-B9's table); L-6 (map-derived patterns are
artifact-scoped, structural families global); PRESENTATION-kind receipt
interchangeability, inside the disclosed falsifier-row-1 limit; criterion 16 enforcing
via judged failures plus criterion 2 rather than its own boolean; and the
`external_basis` whitelist, which no production event sets today — Fable's
residual-risk note stands.

## 7. Open items and deviations

- **`13F_Open_Findings.json` remains outside the allowlist**, so I still cannot create
  it. Fable has since exercised `--final-gate` with it live; the format in `13V_`'s
  docstring is what that run used.
- **E1 records envelope-level fail-closed reasons only** — A4's arises from policy
  composition and is not recorded by it. Disclosed in the TASK-0004 return, unchanged
  and still not widened, because widening it was not authorized.
- **No scope deviations.** Nothing written outside the three allowlisted areas.
- **Branch deviation (unchanged, disclosed):** operator-designated branch.
- **Recommended reviewer focus:** §3 — the two pairs the guard found beyond the two the
  review named, and whether `BUILDER_ADDED_FIELDS` covers every field family that
  ought to require an entry.

---

*Builder-authored completion claim and evidence index — not independent evidence (APP-06). Every proof is reproducible from the pinned snapshot with the commands in `README.md`.*
