# Builder Delivery Record — TASK-0005 (P2U executable corrections)

**Task:** TASK-0005 — P2U corrections (parent topic TOPIC-0002; trail entry 102).
**Builder:** Claude Code session, model `claude-opus-5` (standing authorized substitution, trail entry 69).
**Branch:** `claude/task-0002-builder-handoff-g97x8j` (operator-designated; see §8).
**Instruction authority:** `34_` Task Packet; governing findings `32_`/`32A_` (the verifier's exact required-correction texts govern); dispositions `33_`.
**Status:** **Built; independent verification pending.** No design-gate passage is claimed; the verifier's FAIL stands until the verifier changes it.

**H-06 gate:** `EXPORT_MANIFEST.json` validated before any file was opened for writing — **49/49 declared hashes valid, 0 mismatches, 0 missing, 0 undeclared extras.** Declared writable area: `design/traces/behavioral/**` + `13V_validate_design_matrix.py` only.

---

## 1. Disposition of the four work items

| # | Finding | What changed | Shipped-evidence proof |
| --- | --- | --- | --- |
| **W1** | **P2U-01** — five receipt PRESENTATION expectations classified `mapped` with an empty comparator | `KIND_PRESENTATION` is **deleted**. Those five values resolve `NOT_SIMULATED`, which is not a mapped kind: they leave the mapped count, leave the governed pairs, and are never described as compared. Each carries a rationale in `NOT_SIMULATED_RATIONALE`. The verifier's invariant is enforced by `judge`, which records the NAME of every comparison each dimension ran and **fails the case** when a `mapped` dimension ran none. | `out/results.json` — receipt: **60 compared / 15 not-simulated / 6 not-applicable = 81**, was 75/0/6. `min_comparisons_when_mapped = 1` on all four dimensions. Criterion 16 now requires the four buckets to total 81 and the minimum to be ≥1, instead of `compared > 0`. |
| **W2** | **P2U-02** — `external_basis` accepted any string with an allowed store prefix | New engine module `external_basis.py`: a reference must parse as `store:object-id@version#content-hash` and resolve against a **hash-bound `ExternalManifest` supplied with the fold input**. `validate_basis(events, external_manifest=…)` delegates to it; `fold(…, external_manifest=…)` passes it through. No manifest + an external basis in use = fail closed. | `out/basis_validation.json` — **14/14 external cases fail closed**, the four verifier probe strings among them; **13 of the 14 were accepted by the prefix check this replaces**; the resolvable reference folds (`external_positive_resolves: true`). New gate criterion **18b**. |
| **W3** | **P2U-03** — an atomic schedule change left the prior version's horizon eligible | `Watchdog.expected_runs` is keyed schedule → **version** → ticks. `change_schedule()` retires every prior-version horizon entry and establishes the new version's state in the same transaction. `horizon_exhausted()` counts only entries materialized under the version in force. Behavior 3 now inspects `wd.horizon_state()` instead of recomputing from the spec. | `out/p2s04_schedule_liveness.json` — **4/4 behaviors discriminate**. Behavior 4 is the verifier's probe step for step: v1 horizon 984 ticks past `now`, atomic change to v2, scheduler dies → version-bound **0 eligible ticks, warning fires**; unversioned **41 eligible ticks, warning `None`** (the verifier's recorded observation, reproduced). |
| **W4** | **P2U-05** — `--final-gate` blocked only row-named findings | New **check 9**, computed from the findings authority with **no matrix input at all**: a missing / unreadable / schema-invalid `13F_` fails, and any `blocks_gate: true` finding fails, whether or not a row names it. `load_open_findings` is replaced by `load_findings`, which validates the schema instead of degrading a malformed file to "nothing is open". Rows remain traceability and gained an unresolvable-reference check. | `13V_ --self-test`: **SELF-TEST PASS, 25 cases** (was 11) — including the five the verifier named. **END-TO-END PROBE PASS, 5 cases**: the real command, run as a subprocess against a synthetic repository, returns **exit 1** where the verifier recorded exit 0 — and **exit 0 again with check 9 disabled**, so the probes are shown reproducing the defect, not just failing. |

## 2. The two `32A_` P2U-01 probes — and why "defeated" is the wrong word for them

The verifier rewrote S1's receipt to `completely wrong card` and to `completely wrong
summary surface`. Both are shipped, in `out/oracle_mutations.json` section A2. **The
gate still returns PASS on both**, and reporting anything else would be the dishonesty
the finding is about. What changed is the claim: both values now resolve
`not-simulated`, execute zero comparisons, and are excluded from the mapped count. The
enforced requirement is that a mutated presentation value is **never reported mapped
and never appears in a comparison list** — 2/2 — because the harness no longer says it
checks a projection surface it does not compute.

Fable's disposition allowed either branch: *"Compute and compare the requested surface,
or reclassify those expectations NOT-SIMULATED/outside-simulator truthfully."* I took
the second, and §6 is the change request explaining why the first is not available to
the Builder.

## 3. Regressions and behavior changes, each dispositioned

| # | Change | Disposition |
| --- | --- | --- |
| 1 | Receipt mapped coverage **25 → 20 fixtures**; the `DECLARED_COVERAGE` floor is **lowered** for the first time in its history | Intended and it is the correction. A floor that protects a false claim protects nothing. The reduction is a reviewable diff in one table, is printed by criterion 16 in its own column, and every reclassified pair carries a rationale the gate requires. |
| 2 | `run_basis.py` case `unknown-external-reference-type` changed which problem it detects | `hearsay:some-id` used to fail the store whitelist; it now fails the **grammar** first, so the store rule never runs on it. Recorded in the case's own comment. The store rule is still exercised on a well-formed reference by section B's `undeclared-store` case, so both orderings are covered rather than one being lost. |
| 3 | Criterion 13 failed on first run: the new judge check `mapped_dimensions_have_comparators` had no witness | Correct behavior, not a false positive — layer D perturbs the **engine**, and this check reads only the oracle side, so no engine defect can flip it. Rather than exempting it, `run_defects.ORACLE_SIDE_JUDGE_CHECKS` declares where its witness lives and **`run_gate.py` criterion 13 resolves that pointer**: the named key in the oracle-mutation summary must be true. A declaration layer D *can* flip, or one that names a witness that has gone quiet, fails. |
| 4 | Anti-circularity A-textual failed on first run: `external_basis.py` used the identifier `actual` and the word `expected` | The check is deliberately blunt and bans oracle field vocabulary from engine code by word-boundary match. **The engine avoids the word; the check learns no exceptions** — a whitelist there is how it would stop working. Renamed to `computed`, message reworded, comment left at the site. |
| 5 | `13F_Open_Findings.json` gains an **optional `closed` list** | Without it, every id not in `open` looks closed, so a typo'd or invented dependency reference reads as satisfied — which is the "row dependency referencing a missing finding ID" test the verifier asked for. The reader accepts the file with or without it; while it is absent, `--final-gate` **names each row-referenced id it cannot resolve and fails**, because "I cannot tell whether this is closed" is the state this module already fails on. See §6. |
| 6 | Gate criteria **19 → 21** (18b added, 8b and 18b now separate lines) | An external basis and a causal basis failed for different reasons; one green line covering both is how the second stayed open for a cycle. |

## 4. Acceptance criteria — 21, all re-proven

All PASS, read back out of the shipped JSON rather than from memory:

- **81/81** combinations, **0** judged failures; 171 evaluations over **56** predicates, 56 defect-reachable; 0 receipt-ownership violations; **81/81** order-invariant across 6 permutations; 81 divergences; E2E-1 with the seeded leak; **9/9** defect classes; 8b **56/56** via 62 mutations; P2S-05 **5/5**; P2S-07 **2/2**; 12 **11/11**; 13 **18/19 judge checks with an engine witness + 1 oracle-side, resolved through criterion 13 itself**, 0 orphaned switches, 0 dead mutations; 14 D-B5 self-test; 15 attention **66/81**.
- **16** every dimension accounts for all 81 combinations with **0 unaccounted** and a minimum of **1** comparison per mapped combination.
- **17** 4/4 `28A_` probes defeated; **2/2** `32A_` presentation probes excluded from the compared set; **102/108** sentinels rejected; **92/92** governed pairs with a contradictory witness; same-kind **74 witness / 2 discriminating elsewhere / 9 declared coarsened / 7 no corpus alternative, 0 survived, 0 stale declarations**; the restored-defect witness caught by both guards.
- **18** 8/8 missing-basis cases; **18b** 14/14 external-basis cases + the positive; **19** 4/4 schedule behaviors.

**Anti-circularity: 4/4 checks PASS** (textual, import, structural, stimulus-enumeration registry — 21 pairs in use, 0 unenumerated). **Determinism: two consecutive runs byte-identical across 13/13 outputs**; the only stdout difference is the `--out` path echoed in the final line. **Hygiene:** 0 CR, 0 trailing whitespace, single final LF across every file I wrote; the two flagged files are `03F_Replay_Fixtures.json` (frozen corpus, no final newline, verified byte-identical to the snapshot) and `32_…md` (the verifier's own document). **Dead-code scan:** pyflakes reports nothing on any file this task added or modified — including a pre-existing unused import in `oracle_schema.py` that I removed while I was in the file. It still reports one pre-existing unused import in `engine_core.py` and one in `scenarios.py`; **neither is mine and neither is touched by this task**, so I left them rather than widen the diff, and I name them here instead of writing "clean" and letting the reader find them. **Allowlist: 20 modified + 1 added, 0 outside** the two writable areas.

## 5. Falsifier element (APP-06 / CPB-14, reflexive)

| # | Claim | What would disconfirm it | Status |
| --- | --- | --- | --- |
| 1 | No mapped expectation has an empty comparator | A mapped dimension reaching the report with zero recorded comparisons. Two guards: `judge` fails the case, criterion 16 reports the minimum. The **limit**: the invariant counts comparisons, it does not weigh them. A comparison that runs and checks something trivially true satisfies it. Section D is what addresses that, and section D's own answer is that **9 pairs are declared coarsened** — real comparisons that do not read the whole value. | Not disconfirmed; **limit stated and quantified** |
| 2 | Reclassifying the five receipts is truthful, not convenient | A held design document that defines the Desk/Mailroom surfaces or the artefact forms, which would make them computable and the reclassification an evasion. I searched D-B2, D-B7, D-B9 and D-KR: "mailroom" appears in none, and D-B7 §2.1 defines bands, not surfaces. The forms are not a function of the band either — S5 and A11 compute the same band and the corpus names "Desk brief line" for one and "monthly digest" for the other. **This is the row to audit**: it is a coverage reduction I proposed and then justified. | Not disconfirmed; **adjudication invited** |
| 3 | The external-basis contract is fail-closed, not refuse-everything | A resolvable reference that will not fold. The positive case is shipped for exactly this reason and folds clean. The **limit**: no corpus fixture declares an external basis, so all 14 negative cases and the positive are synthetic. Production is unaffected because production never used the field — which also means this contract has **zero fixture-driven coverage**. | Not disconfirmed; limit stated |
| 4 | My record matches my code | A claim here the shipped files do not support. This has failed in R3, R4, C1 and the TASK-0004 return. Every number in §1, §3 and §4 was read back out of `out/*.json` by a script after the final run, not recalled. Two things that re-check caught this cycle: section D's first version called nine pairs "discriminating" on the strength of an extra check **that also passed**, which is not discrimination — corrected, and the correction is in the code comment at `run_oracle_mutations._dimension_verdict`; and section E's first version claimed the restored defect exercised section D, which it does not, because the judge invariant fails the case first. | **Failed four times; re-checked, and this cycle it caught two overstatements before shipping** |
| 5 | Determinism, hygiene, allowlist | Any output byte-differing across runs, or a file written outside the two writable areas. 13/13 identical; 20 files touched, all inside. | Not disconfirmed |
| 6 | The `13V_` end-to-end probe reproduces the verifier's evidence | A probe that fails for a reason unrelated to check 9. Each of the four failing probes is run a second time with check 9 disabled and must return the exit code the verifier recorded — three return 0. The **control** case (identical rows, clear findings file) returns 0 with the check on, so the validator has not simply learned to always fail. The **limit**: the synthetic repository is Builder-generated; it exercises the real command and the real code path, but it is not the live matrix set, which is not in this snapshot. | Not disconfirmed; limit stated |

## 6. Change requests to Fable

1. **P2U-01, the verifier's preferred option is blocked on a design document.** Computing the receipt surface needs a normative rule mapping computed state onto a projection plane: the surfaces (Desk, Mailroom), the artefact forms (view, brief, brief line, digest), and which state produces which. No document in the Builder snapshot defines any of the three, and the corpus rules out the obvious derivations — form is not a function of band (S5 and A11 share a band, differ in form), and channel is not a function of origin (S5 is system-internal and names Desk; A11 is email-inbound and names no channel). Authoring that rule is a normative decision and not the Builder's. If Fable supplies it, the five pairs become computable and the reclassification should be reversed.
2. **`13F_Open_Findings.json` needs a `closed` list.** `13V_`'s docstring documents the format and the format is Builder-designed, so the reader accepts the key as optional — but while it is absent, `--final-gate` cannot tell a genuinely closed finding from an id nobody has heard of, and it now says so and fails rather than reading the unknown as satisfied. Adding `"closed": [{"id": "P2T-06"}, …]` alongside `open` resolves it. This does not change today's verdict, which is FAIL on six open blocking findings either way.
3. **`13F_` must exist wherever `--final-gate` runs.** Its absence is now an unconditional failure. That is the correction, and it is worth stating plainly because it changes the operational contract: the command can no longer be run in a directory that lacks the findings authority.

## 7. Carried as disclosed limits (no action)

`03F_Replay_Fixtures.json` frozen and byte-identical. L-4 (13 vs 14 D-SM rows — snapshot-true); L-5 (basis-validator loosenesses against D-B9's table); L-6 (map-derived patterns artifact-scoped). E1 records envelope-level fail-closed reasons only. The nine coarsened attention comparisons, declared in `COARSENED_COMPARISONS` with what is and is not compared. The interrupt-policy citation parsed by two structurally independent but textually identical functions. `check_supersessions.py` is **not in this snapshot and not in this allowlist** — P2U-04 is Fable's and was applied by Fable; nothing here touches it.

## 8. Open items and deviations

- **No scope deviations.** Nothing written outside `design/traces/behavioral/**` and `13V_validate_design_matrix.py`. `13F_` was present in this snapshot for the first time and was **read, never written**.
- **The full `13V_` structural run still cannot execute here**: the requirements register, the change plan and `13D_` are not in the Builder snapshot. `--self-test` and the new end-to-end probe are the shipped evidence, and the probe closes most of that gap by running the real command against a complete synthetic repository.
- **Branch deviation (unchanged, disclosed):** operator-designated branch.
- **Recommended reviewer focus:** falsifier row 2 — whether the five receipt reclassifications are honest or convenient — and the nine declared coarsened comparisons in §5 row 1, which are the nearest thing left to the defect P2U-01 named.

---

*Builder-authored completion claim and evidence index — not independent evidence (APP-06). Every proof is reproducible from the pinned snapshot with the commands in `design/traces/behavioral/README.md`.*
