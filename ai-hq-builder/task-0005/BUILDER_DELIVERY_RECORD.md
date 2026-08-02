# Builder Delivery Record — TASK-0005 rework cycle R5 (RW-46, the last item)

**Task:** TASK-0005, rework cycle R5 — the single-item cycle `49_` §2 authorizes.
**Builder:** Claude Code session, model `claude-opus-5` (standing authorized substitution, trail entry 69).
**Branch:** `claude/task-0002-builder-handoff-g97x8j` (operator-designated; see §8).
**Instruction authority:** prior packets + `49_`; **governing text: `48_` §4, its required-correction and §4.3 negative-test lists verbatim.**
**Returned to:** **Fable**, not the verifier.
**Status:** **Built; independent verification pending.** No design-gate passage is claimed — `48_` §6 reserves that to the verifier's next response.

**Relay integrity:** `SHA256SUMS.txt` verified **3/3 OK** (`48_`, `48A_`, `49_`) before anything was read as authority.

**Scope note.** One item. `48_` §5 routes the `ActionContext`-to-payload binding to `13B_` as **B-12**, non-blocking — that is the change request I filed in §7 of the R4 record, and I have **not** implemented it. Nothing else was touched.

---

## 1. Disposition of the single work item

| # | Finding | What changed | Shipped-evidence proof |
| --- | --- | --- | --- |
| **RW-46(a)** | **`48_` §4.1** — the policy boundary could see only one of the two parties it had to be separate from | `governed_purposes()` takes the **receipt registry** as a fourth argument and refuses when `policy.authority_id == manifest.source_id` **or** `policy.authority_id == registry.authority_id`. Absence of either half of that context is itself a refusal, not a skipped check. R4's signature had no registry parameter at all, which is why "distinct from both" was enforced as "distinct from one". | Case `evidence-policy-authored-by-the-receipt-authority` ships **refusing**, naming the receipt-registry collision. Section C3 reproduces `48A_/probe_policy_authority_equals_receipt_authority` under the R4 contract and records it **accepted**, matching the verifier's `problems: []` / `folded: true` exactly. |
| **RW-46(b)** | **`48_` §4.2** — the bound artifact's declared version governed nothing | `EvidencePolicy.integrity_problems()` now refuses any artifact carrying a contract row whose `policy_version` is not the artifact's own, and `governed_purposes()` refuses an action context asking for a version the supplied artifact is not. One artifact, one version; a multi-version set has to be separately bound versioned artifacts, per `48_` §4.2's own words. | Case `evidence-policy-version-differs-from-its-contract-version` ships **refusing** (artifact P999, row P1 — the verifier's fixture). Section C3 records R4 **accepting** it. Case `action-context-requests-a-version-the-policy-is-not` ships refusing and naming the version. |
| **RW-46(c)** | **`48_` §4.3** — the three negatives, machine-runnable | All three are rows in the shipped external-basis table, so they run on every gate execution rather than in a one-off script. The positive control is tightened to assert what it is now a control *for*. | External-basis cases **53/53 closed** (50 → 53). The positive resolves and additionally reports `policy_authority_distinct_from_both`, `policy_version_coherent` and `action_context_version_matches_policy` — all true, and all three now gate `resolved_and_folded`, so a positive that passed by sidestepping the new rules would fail the run. |

## 2. Two things I am reporting against my own interest

Both concern how much the new controls actually do. I would rather name them than have them found.

**The action-context version check changes the reason, not the outcome.** With §4.2's first clause enforced, every row in an artifact carries the artifact's version — so a context asking for any other version can never match a row, and the lookup would refuse it regardless. `48_` §4.3(3) asks for the test by name and I have shipped it, but the check earns its place by making the refusal *say* "version", where R4 said "no contract for those keys". Section C3 ships that comparison rather than asserting it: row 3 records `r4_contract_accepted: false` and `r4_refusal_reason: "the policy holds no contract for those keys"`. **It is counted as a change in reason, not as a third previously-accepted probe** — `r4_accepted_count` is **2**, and the gate line says so.

**The fail-closed-on-absent-authority-context clause is over-determined.** `governed_purposes()` is reached only when an event has an external basis, and every such reference is separately refused downstream when its manifest or registry is missing. `no-manifest-supplied` and `no-receipt-registry-supplied` therefore each carry two independent refusals now. The clause is in because §4.1 requires the separation check to fail closed rather than be skipped — not because it is load-bearing on this corpus. Both facts are stated in the code at the site, not only here.

## 3. Regressions and behavior changes, each dispositioned

| # | Change | Disposition |
| --- | --- | --- |
| 1 | `governed_purposes()` signature gains a required `registry` parameter | The only caller is `fold.validate_basis`, which has the registry in hand. Checked: no other call site exists anywhere in the tree. |
| 2 | Two previously-accepted policy artifacts are now rejected | That is the finding. Neither shape occurs in the corpus — no fixture declares an external basis — so no production path changes; `production_basis_problems` is still empty over all 81 combinations. |
| 3 | The positive control's pass condition is stricter | It now requires the three-authority separation *and* version coherence *and* context agreement. A control that passes without exercising the rule it controls for is the P2W-03 defect, and I did not want to reintroduce it one artifact along. |
| 4 | Section C3 (`r4_contract_witnesses`) added | The R4 boundary is reconstructed rather than re-typed: its integrity list is the shipped one with the version-coherence problems filtered out, so the reconstruction cannot drift from the real class in any other respect. |
| 5 | Gate criteria remain **21** | 18b's case set grows 50 → 53 and its pass condition gains the C3 clause. No criterion added or removed. |
| 6 | A comment in `external_basis.py` used an oracle field name | Caught by anti-circularity A-textual reporting `doc_mentions` 21 → 22 (code hits stayed 0, so it never failed). Reworded rather than left as tolerated prose. Third cycle running that this check has caught something of mine. |

## 4. Acceptance criteria — 21, all re-proven

Read back out of the shipped JSON after the final run:

**21/21 criteria PASS.** 81/81 combinations, 0 judged failures; 171 evaluations over 56 predicates, 56 defect-reachable; 81/81 order-invariant over 5 seeds; 9/9 defect classes; P2S-05 5/5; P2S-07 2/2; composition 11/11; 18/19 judge checks with an engine witness + 1 oracle-side resolved through the criterion itself, **0 orphaned switches, 0 dead mutations**; attention 66/81 compared, 15 unmappable, 0 unresolved; 102/108 sentinels rejected, 92/92 contradictory witnesses, same-kind 0 survived; 4/4 verifier probes defeated; 18 missing-basis **8/8**; **18b external-basis 53/53 closed**, the positive resolving under three distinct authorities and a version-coherent policy, **3/3 `38A_` + 3/3 `41A_` + 3/3 `48A_` probes** refusing and naming their own defect; 19 schedule behaviors **17/17**.

`13V_`: **SELF-TEST PASS, 25 cases**; **END-TO-END PROBE PASS, 5 gate cases + 28 CLI cases**.

**Anti-circularity 4/4 PASS**, 0 oracle field names in engine code. **Determinism: two runs byte-identical across 13/13 outputs**, and the shipped `out/` matches a fresh run. **Hygiene:** the same two pre-existing flags as every prior cycle — the frozen corpus and the verifier's own `32_` document, neither mine. **pyflakes** reports nothing on any file this cycle touched. **Allowlist: 21 modified + 1 added, 0 outside.** `03F_Replay_Fixtures.json` is byte-identical to the snapshot.

## 5. Falsifier element (APP-06 / CPB-14, reflexive)

| # | Claim | Who would have to be wrong, and how | Status |
| --- | --- | --- | --- |
| 1 | The policy authority is separate from both parties | **All three authorities, or any two colluding.** Separation is compared by identifier equality between three declared strings. Two colluding actors, or one actor operating under two identifiers, still pass — nothing here binds an identifier to a real principal. That is cryptographic attestation and trust roots, explicitly build-gate under the owner's arbitration, and it is unchanged since R2. | Not disconfirmed; **deferred by ruling** |
| 2 | One artifact carries one version | **Me, about scope.** Coherence is checked between the artifact and its own rows and between the artifact and the consuming context. It is NOT checked across artifacts: nothing stops two differently-versioned policies existing, and nothing here decides which one a caller should have been given. `48_` §4.2 says a multi-version set must be separately bound versioned artifacts — this enforces the "one artifact" half; **selecting the right artifact is not modelled and no held document specifies the selection rule.** | **Open, named** — see §7 |
| 3 | The three §4.3 negatives ship failing | **The evidence, and it is in the box.** Each is a row in the gate's own table, refusing with a substring the row declares in advance. If any stopped refusing the run fails. The honest asymmetry is in §2: two of the three were accepted by R4, one was refused for a different reason, and the report separates them instead of claiming 3/3 acceptances reversed. | Not disconfirmed |
| 4 | This closes P2Y-01 | **The verifier, and only the verifier.** `48_` §6 limits the next review to these two corrections, the three tests, regression of prior evidence, and packet integrity. I have built to `48_` §4 as written. Whether it satisfies §4 is not mine to declare and I am not declaring it. | **Not claimed** |
| 5 | My record matches my code | **Me.** This has failed in R3, R4, C1, TASK-0004, TASK-0005, R1, R2 and R3. Caught before shipping this cycle: the over-claim in §2 row 1, which I first wrote as a third witness before running the R4 reconstruction and seeing it had refused that fixture already. Every number in §4 was read back out of the shipped JSON after the final run, not carried forward from R4. | **Failed eight times; one over-claim caught here** |
| 6 | Determinism, hygiene, allowlist | Any output byte-differing across runs, or a file outside the two writable areas. 13/13 identical; 5 files touched this cycle, all inside. | Not disconfirmed |

## 6. What R5 did NOT change

Everything `48_` §2 and §3 record as reproducing or closed is intact and re-proven from the same commands: the behavioral gate, incomplete-basis 8/8, schedule-liveness 17/17, P2Y-02/03/04 in full, the supersession checker, the strict `13V_` CLI. No fixture, document, gate artifact, `13F_` or checker was touched. Five files changed: `external_basis.py`, `fold.py`, `run_basis.py`, `run_gate.py`, `README.md`.

## 7. Change request to Fable (falsifier row 2)

**Which policy artifact a fold should have been given is not modelled.** §4.2 is enforced within an artifact and against the consuming context. But the artifact arrives as a fold argument, and nothing decides whether it is the *right* one — a caller holding two validly bound, internally coherent policies at different versions can supply either, and both resolve. Closing that needs a rule binding an action's governing policy version to something outside the fold input, and **no held design document specifies one.**

I am raising it now rather than letting it sit in a falsifier row, which is the R4 lesson. It looks to me like the same family as B-12 — a classification the executor must derive rather than accept — and if Fable agrees it belongs in `13B_` next to it. Under `48_` §6 it cannot extend this gate in any case, and I am not treating it as in scope.

## 8. Open items and deviations

- **The full `13V_` structural run still cannot execute here**: the requirements register, the change plan and `13D_` are not in the snapshot. `--self-test` and `--end-to-end-probe` are the shipped evidence.
- **No scope deviations.** Nothing written outside `design/traces/behavioral/**` and `13V_validate_design_matrix.py`. B-12 was not implemented.
- **Branch deviation (unchanged, disclosed):** operator-designated branch.
- **Recommended reviewer focus:** §2 first — both admissions are about how much the new controls do, and both are checkable in `out/basis_validation.json` under `r4_contract_witnesses`. Then §7.

---

*Builder-authored completion claim and evidence index — not independent evidence (APP-06). Every proof is reproducible from the pinned snapshot with the commands in `design/traces/behavioral/README.md`.*
