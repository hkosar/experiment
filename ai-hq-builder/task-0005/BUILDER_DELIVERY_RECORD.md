# Builder Delivery Record — TASK-0005 rework cycle R1 (P2V enforcement corrections)

**Task:** TASK-0005, rework cycle R1 (parent topic TOPIC-0002).
**Builder:** Claude Code session, model `claude-opus-5` (standing authorized substitution, trail entry 69).
**Branch:** `claude/task-0002-builder-handoff-g97x8j` (operator-designated; see §8).
**Instruction authority:** `34_` Task Packet + `37_` Rework Packet R1. Governing findings `35_`/`35A_`, dispositions `36_` — **see §7: I do not hold those three documents.**
**Returned to:** **Fable**, not the verifier. Fable verifies independently, integrates on acceptance, and assembles the verifier packet.
**Status:** **Built; Fable's verification pending.** No design-gate passage is claimed and no acceptance is implied.

---

## 1. Disposition of the four findings

| # | Finding | What changed | Shipped-evidence proof |
| --- | --- | --- | --- |
| **RW-28** | **P2V-01** — a production-reachable disable path for the global blocking-finding check | The `--p2u05-defect-witness` flag is **deleted**. No argv, environment variable, or module attribute can skip check 9. The counterfactual still exists, but it is built by **eliding the check from a throwaway copy** of the file in a temp directory — the thing that can be turned off is a copy the test writes, not the shipped command. | `13V_ --self-test`: **END-TO-END PROBE PASS — 5 gate cases + 4 disable-spelling cases.** The deleted flag and three other plausible spellings each run against a repository with six open blocking findings and **exit 1**; a source check confirms the constant is gone, not merely ignored. The four gate probes still show witness exit 0 through the elided copy. |
| **RW-29** | **P2V-02** — `verification_receipt` was any nonempty string | A receipt is now a reference in the same grammar that must resolve to a **registered record in the same hash-bound manifest**: exists, version matches, content hash matches. The chain terminates at the first record carrying no receipt (the attestation root); **self-reference and mutual attestation are refused** and the chain is depth-bounded. | `out/basis_validation.json` — six new failing cases: arbitrary string, unregistered attestation, wrong version, wrong content hash, self-reference, mutual cycle. All six are marked **accepted by the TASK-0005 contract** in the shipped table. The positive case now resolves through a real attestation record and still folds. |
| **RW-30** | **P2V-03** — the digest bound only `records`; duplicate identities were accepted | `computed_digest()` binds every field in **`DIGEST_BOUND_FIELDS`** (`records`, `resolver_known_ids`, `resolver_state`), with `DIGEST_EXEMPT_FIELDS` naming the one field that cannot be inside it and why. `_check_digest_field_coverage()` fails any manifest whose dataclass carries a field in neither list. Duplicate `store:object_id` identities fail the manifest before any reference consults it. | Two new failing cases: **`resolver-state-edited-under-a-valid-digest`** (the same records, resolver flipped `unavailable → available`; the previous digest verified it) and **`duplicate-external-record-identity`**. Both marked accepted by the TASK-0005 contract. **`digest_enumeration_guard_discriminates: true`** — the guard is shipped *failing* under a dropped control field and under a stale name, and `computed_digest()` is shown refusing to hash a payload missing a bound field. |
| **RW-31** | **P2V-04** — a retired schedule version could re-enter force with its pre-retirement horizon | Retirement is **permanent**. `change_schedule()` refuses a spec whose version has been retired and **adopts nothing**; `register()` refuses one too. Reinstating a schedule is `reactivate()`, which mints a version number never before in force and an empty horizon the scheduler must extend. | `out/p2s04_schedule_liveness.json` — **5/5 behaviors discriminate**. Behavior 5 is the reactivation probe: permanent → re-entry refused, **v2 stays in force, 0 eligible ticks, warning still up**; lapsing → **re-entry accepted, v1 back in force, 41 stale ticks eligible, warning `None`**. `reactivate()` mints v3 with 0 eligible ticks and the warning stays up. The journal is shipped. |

## 2. What these four findings have in common, and what I take from it

Every one is the **same defect the previous cycle was correcting, one layer in**. P2U-02 said a declared external basis must resolve; I made the reference resolve and left its *attestation* a free-text string. P2U-03 said the horizon must be version-bound; I bound it and left retirement reversible. P2U-05 said the gate must not be switchable off by clearing rows; I made it unconditional and then shipped a flag that switched it off.

The pattern is that I stop at the layer the finding names. A control I add is checked; the control that guards *it* is asserted. Three of the four probes here would have been found by asking, of each new control, "what would have to be true for this to be waived, and is that reachable?" — which is now a step I take rather than a thing I say.

## 3. Regressions and behavior changes, each dispositioned

| # | Change | Disposition |
| --- | --- | --- |
| 1 | `run_basis.py`'s `GOOD_RECORD` gained a real attestation record; `MANIFEST` now holds 2 records | Required by RW-29 — the previous fixture's `verification_receipt="ctrl-receipt-77"` named nothing and was accepted because it was nonempty. The positive case is materially stronger: it resolves a receipt chain rather than reading a truthy string. |
| 2 | `Watchdog.register()` and `change_schedule()` now **return `bool`** and can refuse | Required by RW-31 — a refusal that adopts nothing has to be reportable. Both refusals are journalled with the reason and the stale-tick count. |
| 3 | Section B grew a **second counterfactual column** (`P2U CONTRACT` beside `PREFIX`) | There are now two superseded contracts, and one column could not say which cycle's defect a row witnesses. My first implementation of it reported **0 witnesses** because it compared a records-only digest against manifests bound with the *new* digest — so every row read "the old contract caught this too", which was false. Corrected via `_p2u_declared_digest()`; the reasoning is in that function's docstring. |
| 4 | Anti-circularity A-textual failed on first run — again on the identifier `actual`, in `external_basis.py` | **Second time in the same file, same word, two cycles running.** Renamed to `present`. I am not weakening the check: it caught the mistake both times, which is the argument for keeping it blunt. Noted in falsifier row 5. |
| 5 | `HorizonRetired` was journalled twice for one version | Found while reading the shipped journal, not the code: `reactivate()` re-retired v1 because `retired_versions` was appended to unconditionally. Retirement is permanent, so retiring twice is incoherent. Already-retired versions are skipped. |
| 6 | Gate criteria remain **21**; 18b and 19 restated | No new criterion. RW-29/30 extend 18b's case set (14 → 22) and add the enumeration-guard condition; RW-31 extends 19's behaviors (4 → 5). RW-28's evidence is in `13V_ --self-test`, which is outside `run_gate.py` by design — see §7. |

## 4. Acceptance criteria — 21, all re-proven

Read back out of the shipped JSON after the final run, not recalled:

**21/21 criteria PASS.** 81/81 combinations, 0 judged failures; 171 evaluations over 56 predicates, 56 defect-reachable; 0 receipt-ownership violations; 81/81 order-invariant; 81 divergences; E2E-1 with the seeded leak; 9/9 defect classes; 8b 56/56 via 62 mutations; P2S-05 5/5; P2S-07 2/2; 12 11/11; 13 **18/19 judge checks with an engine witness + 1 oracle-side resolved through the criterion itself**, 0 orphaned switches, 0 dead mutations; 14 D-B5 self-test; 15 attention 66/81; 16 all four dimensions accounting for all 81 with 0 unaccounted and min 1 comparison; 17 4/4 `28A_` probes, 2/2 `32A_` presentation probes excluded, 102/108 sentinels, 92/92 contradictory witnesses, same-kind 74/2/9/7 with **0 survived**; 18 8/8 missing-basis; **18b 22/22 external-basis + positive + enumeration guard**; **19 5/5 schedule behaviors**.

`13V_`: **SELF-TEST PASS, 25 cases**; **END-TO-END PROBE PASS, 5 gate cases + 4 disable-spelling cases**.

**Anti-circularity 4/4 PASS.** **Determinism: two consecutive runs byte-identical across 13/13 outputs**, and the shipped `out/` matches a fresh run. **Hygiene:** 0 CR, 0 trailing whitespace, single final LF across every file I wrote; the two flagged files are the frozen corpus (no final newline, byte-identical to the snapshot) and the verifier's own `32_` document. **pyflakes clean** on every file this cycle touched. **Allowlist: 20 modified + 1 added, 0 outside.**

## 5. Falsifier element (APP-06 / CPB-14, reflexive)

| # | Claim | What would disconfirm it | Status |
| --- | --- | --- | --- |
| 1 | No production path disables check 9 | An argv, environment variable, or attribute that skips it. Four spellings are tested and the constant's absence is checked in the source. The **limit**: those are four strings I chose, and the source check looks for one identifier. It is not a proof that no waiver exists — it is a proof that the one I shipped is gone and that three plausible replacements do nothing. A reviewer reading the argv handling directly is worth more than this test. | Not disconfirmed; **limit stated** |
| 2 | A verification receipt is now an attested object | A receipt that satisfies the checks without naming a real attestation. The chain terminates at the first record carrying no receipt, and **that root record is not itself attested** — it cannot be, without recursion. So the contract proves the attestation is *registered and hash-bound*, not that it is *trustworthy*. Anyone who can write the manifest can write a root. This is the honest boundary of a manifest-based scheme and I am not claiming past it. | Not disconfirmed; **boundary stated** |
| 3 | The digest binds every security-relevant control field | A field that matters and is in neither list. The guard is mechanical over the dataclass, so a *new* field cannot escape — but whether the three currently bound are the right three is a judgement, and `resolver_known_ids` is bound mainly because leaving it out would repeat the mistake, not because an attack through it is demonstrated. | Not disconfirmed; **judgement disclosed** |
| 4 | Retirement is permanent | A path that puts a retired version back in force. `change_schedule` and `register` both refuse. The **limit**: `retired_versions` is in-memory state on the Watchdog; a fresh Watchdog reading a persisted schedule would not know what had been retired. Nothing in this harness persists, so the question does not arise here — and it would arise immediately in a real implementation. **Flagged for Fable as a design question, not fixed, because fixing it would be inventing a persistence contract.** | Not disconfirmed; **carried as an open design question** |
| 5 | My record matches my code | A claim here the shipped files do not support. This has now failed in R3, R4, C1, TASK-0004 and TASK-0005. Two things the re-read caught this cycle before shipping: the P2U-contract counterfactual reported 0 witnesses because it compared against the wrong digest (§3 row 3), and `HorizonRetired` was journalled twice (§3 row 5) — both found by reading shipped output, not code. One thing it did **not** catch until the checker did: `actual` as an identifier, for the second cycle running, in the same file. | **Failed five times; two overstatements caught here, one recurrence caught by a tool and not by me** |
| 6 | Determinism, hygiene, allowlist | Any output byte-differing across runs, or a file written outside the two writable areas. 13/13 identical; 21 files touched, all inside. | Not disconfirmed |

## 6. What R1 did NOT change

The four TASK-0005 work items stand as delivered: the `NOT_SIMULATED` receipt reclassification and the mapped-comparator invariant (P2U-01), the external-basis resolver's structure (P2U-02, extended here not replaced), version-bound horizons (P2U-03), and the global open-finding gate (P2U-05, hardened here). No fixture, document, gate artifact, `13F_`, or checker was touched. `03F_Replay_Fixtures.json` is byte-identical to the snapshot.

The three change requests from the TASK-0005 return are **unchanged and still open**: the projection-plane design document that P2U-01's preferred option needs; the optional `closed` list in `13F_`; and the fact that `13F_` must now exist wherever `--final-gate` runs.

## 7. Open items and deviations

- **I do not hold `35_`, `35A_` or `36_`.** Only `37_` was relayed. The packet says the verifier's exact required-correction texts govern, so I worked from `37_`'s four bullets and from reproducing each defect in my own shipped code first — all four reproduce exactly as described, and the reproductions are in the shipped output. **Where `35A_`'s probes differ in form from the ones I reconstructed, this return has not defeated them as written.** Please relay `35_`/`35A_`/`36_` if the exact probe forms matter to Fable's verification; I will re-run against them.
- **RW-28's evidence is in `13V_ --self-test`, not `run_gate.py`.** `13V_` lives outside `design/traces/behavioral/` and the behavioral gate does not invoke it — the same split as the previous two cycles. Both are named in the README's run list. If Fable wants one command covering both, that is a change request I can take.
- **Falsifier row 4's persistence question is open** and is a design matter, not a Builder one.
- **No scope deviations.** Nothing written outside `design/traces/behavioral/**` and `13V_validate_design_matrix.py`.
- **Branch deviation (unchanged, disclosed):** operator-designated branch.
- **Recommended reviewer focus:** §2 — whether the "stop at the layer the finding names" pattern is actually closed this time, or whether each of the four new controls has a guard of its own that I have again only asserted. The specific candidates are falsifier rows 1, 2 and 4.

---

*Builder-authored completion claim and evidence index — not independent evidence (APP-06). Every proof is reproducible from the pinned snapshot with the commands in `design/traces/behavioral/README.md`.*
