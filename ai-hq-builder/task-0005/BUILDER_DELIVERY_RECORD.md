# Builder Delivery Record — TASK-0005 rework cycle R2 (P2W corrections)

**Task:** TASK-0005, rework cycle R2 (parent topic TOPIC-0002).
**Builder:** Claude Code session, model `claude-opus-5` (standing authorized substitution, trail entry 69).
**Branch:** `claude/task-0002-builder-handoff-g97x8j` (operator-designated; see §8).
**Instruction authority:** `34_` + `37_` + `40_` Rework Packet R2; governing findings `38_`/`38A_`, **both relayed this time**; dispositions `39_` (not held — see §8).
**Returned to:** **Fable**, not the verifier.
**Status:** **Built; Fable's verification pending.** No design-gate passage is claimed. **RW-36 is not executed — it is returned as a change request (§7).**

---

## 1. Disposition of the five findings

| # | Finding | What changed | Shipped-evidence proof |
| --- | --- | --- | --- |
| **RW-32** | **P2W-01** — `--final-gate` bypassable by mode combination and unknown arguments | Four explicit modes (`--structural`, `--final-gate`, `--self-test`, `--end-to-end-probe`), **exactly one selectable**, resolved by `parse_cli()` **before anything executes**. Combining `--final-gate` with a test mode is a usage error raised before a single test runs; unknown arguments exit 2. `parse_cli` is total — there is no "ignored" outcome, which is how `--definitely-unknown` rode along. | `--end-to-end-probe`: **28 CLI cases**, every one of `38A_`'s argv forms against **both** the six-open-findings repo and the clear one. `--final-gate --self-test`, `--self-test --final-gate`, `--final-gate --definitely-unknown` → **exit 2**, and each asserts **no test output leaked**, so the failure precedes the test rather than following it. Baselines still work: `--final-gate` exits 1 / 0 on the two repos, no arguments exits 0. |
| **RW-33** | **P2W-02** — a same-manifest unattested root self-certifies | Per Fable's ruling, independence is **structural**. Two independently bound artifacts: `ExternalManifest` (authored by `source_id`) and `ReceiptRegistry` (authored by `authority_id`, which must differ and which the manifest names **in advance**). A receipt is a `receipt:` reference that **cannot name a manifest record**, carries the **full reference of its subject**, a purpose, and a revocation state bound to the manifest's `revocation_snapshot_id`. Content identity is full-length sha256. | 13 new failing cases including the verifier's exact probes: **`receipt-attests-to-another-subject`** (a real, registered, bound attestation naming a different subject) and **`abbreviated-content-hash`** (`cafebabe`/`deadbeef`). Plus: receipt naming a manifest record, unregistered, wrong authority version, wrong hash, revoked, purposeless, no registry, wrong authority, same authority, manifest naming itself as its own authority, stale revocation snapshot, unbound registry, duplicate receipt ids. The positive case resolves **under two distinct declared authorities**. |
| **RW-34** | **P2W-03** — the envelope binds no authority or snapshot context | `ExternalManifest` carries and binds all 20 fields: schema and canonicalization version, snapshot id/epoch, source, creation context, record-identity rule, digest algorithm and length, resolver id/version/state, receipt-authority id/version/config, trust-root id and key version, revocation snapshot, records, resolver-known ids. The validator refuses unknown schemas, unapproved algorithms, ambiguous identities, missing controls and post-binding change. | `snapshot-identity-edited-under-a-valid-digest` fails — the R1 envelope could not represent a snapshot id, so `same_records_same_digest` was **true by construction**. Four envelope-control cases ship failing. **`REQUIRED_CONTRACT_CONTROLS`** maps each item of the verifier's enumeration to its field and is guarded; the coverage guard extends to `as_row()` for both record types. |
| **RW-35** | **P2W-04** — versions reusable through unguarded paths and restart | Per Fable's ruling the **control journal is the authority**. Every governed transition is an entry; the live spec, materialized horizons, retired set and highest-version-ever are all **derived by `_replay()`**. `register()` is initial-only (idempotent for the exact immutable spec); `change_schedule()` requires a version strictly above the highest ever used and takes an `expected_current_version` for optimistic concurrency; a restart is `Watchdog.from_journal()`. | **11/11 behaviors discriminate.** Six new: falsifier A (same-version changed recurrence), falsifier B (`register()` replacement), monotonic identity (duplicate and lower version), **falsifier C (restart preserves retirement through the journal fold)**, concurrent change, and replay determinism. Each ships its journal. |
| **RW-36** | **P2W-05, checker leg** | **NOT EXECUTED — change request.** `check_supersessions.py`, `D-SM` and `D-B11` are not in the Builder snapshot, and `design/traces/check_supersessions.py` is outside the allowlist (`design/traces/behavioral/**`). See §7. | — |

## 2. What the four findings had in common, and what I did about it

R1's record said I "stop at the layer the finding names". P2W says it again, four times, and adds a sharper version: **three of the five were places where my own disclosure was the finding.** I wrote that the receipt root "cannot be attested without recursion" and that `retired_versions` was "in-memory only", and the verifier turned both sentences into falsifiers within one cycle. A disclosed limit is not a mitigated one; it is an unmitigated one with a note attached.

The operational change: for each new control this cycle I asked what an actor who controls the inputs could still do, and encoded the answer as a refusal rather than a paragraph. That is why the receipt registry has a declared authority the manifest must name in advance (an actor supplying both artifacts is now visible), why the journal is the only thing a restart reads (there is no partial-restore path to describe), and why `parse_cli` is total (there is no "ignored argument" state to disclose).

## 3. Regressions and behavior changes, each dispositioned

| # | Change | Disposition |
| --- | --- | --- |
| 1 | `13V_` gains `--end-to-end-probe` as its own mode; `--self-test` no longer runs it | Required by P2W-01's "exactly one mode". Both are in the README run list. Two commands where there was one. |
| 2 | Unknown arguments now **exit 2**, not 1 | R1's disable-spelling probes asserted exit 1 (the gate ran and failed anyway). The stronger property is that the argument is refused outright, so those probes now assert exit 2 with no gate run. |
| 3 | All content hashes in the fixtures changed to 64-hex | Required by P2W-02. Derived from a fixed label via `_h()`, never from the record that carries them — a hash computed from the record would make every comparison a comparison with itself. |
| 4 | The R1 per-row "would the previous contract accept this?" column is **removed** and replaced by a dedicated section C | The column reported **0 witnesses**, and the reason matters: the R2 fixtures are not expressible in the R1 contract (a receipt is now a registry reference and R1 had no registry), so every row came back "R1 rejected" — true and useless. Section C runs `38A_`'s probes **in the shape the verifier built them** under both contracts; all 3 witness their finding. I caught this by reading the output, which is the second cycle running that this counterfactual has been wrong on its first draft. |
| 5 | Three of my own `detected` predicates were wrong, not the implementations | `same-version-changed-recurrence` demanded a horizon warning after a correctly-refused change — but nothing changed, so v1's horizon legitimately covers v1 and there is nothing to warn about. `register-is-initial-only` demanded that re-registering the **identical immutable spec** return False — but the required correction explicitly permits idempotence, so the contract was being reported as a failure. Both rewritten to assert the property that actually matters (the recurrence in force is unchanged), and a mutated-same-version registration added. |
| 6 | Two behaviors needed their own defect switches | `concurrent-change-attempts` and `register-is-initial-only` were enforced by paths independent of `monotonic_versions`, so the seeded run behaved identically and neither discriminated. Added `optimistic_concurrency` and `register_replaces_live`, each read by exactly one predicate. |
| 7 | Gate criteria remain **21** | No new criterion. 18b's case set grows 22 → 37 and gains the R1-witness condition; 19's behaviors grow 5 → 11. RW-32's evidence is in `13V_ --end-to-end-probe`. |

## 4. Acceptance criteria — 21, all re-proven

Read back out of the shipped JSON after the final run:

**21/21 criteria PASS.** 81/81 combinations, 0 judged failures; 171 evaluations over 56 predicates, 56 defect-reachable; 0 receipt-ownership violations; 81/81 order-invariant; 81 divergences; E2E-1 with the seeded leak; 9/9 defect classes; 8b 56/56 via 62 mutations; P2S-05 5/5; P2S-07 2/2; 12 11/11; 13 18/19 judge checks with an engine witness + 1 oracle-side resolved through the criterion itself, 0 orphaned switches, 0 dead mutations; 14 D-B5 self-test; 15 attention 66/81; 16 all four dimensions accounting for all 81 with 0 unaccounted, min 1 comparison; 17 4/4 + 2/2 probes, 102/108 sentinels, 92/92 contradictory witnesses, same-kind **0 survived**; 18 8/8 missing-basis; **18b 37/37 external-basis + independently attested positive + 4 enumeration guards + 3/3 R1-contract witnesses**; **19 11/11 schedule behaviors**.

`13V_`: **SELF-TEST PASS, 25 cases**; **END-TO-END PROBE PASS, 5 gate cases + 28 CLI cases**.

**Anti-circularity 4/4 PASS.** **Determinism: two runs byte-identical across 13/13 outputs**, and the shipped `out/` matches a fresh run. **Hygiene:** 0 CR, 0 trailing whitespace, single final LF across every file I wrote; the two flagged files are the frozen corpus and the verifier's own `32_` document. **pyflakes** reports nothing on any file this cycle touched (the two pre-existing unused imports in `engine_core.py` and `scenarios.py` remain, unchanged and not mine). **Allowlist: 20 modified + 1 added, 0 outside.**

## 5. Falsifier element (APP-06 / CPB-14, reflexive)

| # | Claim | What would disconfirm it | Status |
| --- | --- | --- | --- |
| 1 | No CLI combination bypasses the gate | An argv the parser accepts that skips check 9. `parse_cli` is total over its argument list, which is a stronger property than the four spellings R1 tested. The **limit**: it governs `sys.argv` only. An environment variable, a `PYTHONPATH` shim, or importing this module and calling into it are outside what a CLI parser can refuse, and I have not audited those paths. | Not disconfirmed; **limit stated** |
| 2 | Attestations are independent evidence | A path where the manifest's author supplies both artifacts and is accepted. The registry must declare an authority the manifest named in advance and that differs from `source_id` — so *this* pairing is refused. The **boundary, and it is the one the verifier will test next**: an actor who controls both authorities can still author a consistent pair, because there is no signature and no trust root. Structural separation makes collusion necessary; it does not make it impossible. Contract 2 (cryptographic attestation) is the only thing that would, and the envelope now carries the fields for it. | Not disconfirmed; **boundary stated, and it is a real one** |
| 3 | The envelope binds every control the contract requires | A control the verifier's enumeration names that no field carries. `REQUIRED_CONTRACT_CONTROLS` is my transcription of that list and is guarded against pointing at absent fields — but **the transcription itself is mine**, and a control I read as covered by an adjacent field would not show up. That mapping is the row to audit. | Not disconfirmed; **transcription disclosed** |
| 4 | Schedule identity is durable | A path that reuses a version or loses retirement. Retirement is a journal entry and a restart is a fold. The **limit**: the journal is an in-process list here — this harness persists nothing. What changed is that there is now exactly one artifact a real implementation must persist, and the fold is written and tested; R1's disclosure was that the authority itself was ephemeral. That is a different claim, and a weaker one than "durable in production", which I am not making. | Not disconfirmed; **limit restated more narrowly than R1's** |
| 5 | My record matches my code | A claim here the shipped files do not support. This has failed in R3, R4, C1, TASK-0004, TASK-0005 and R1. Caught by reading output this cycle, before shipping: the R1-contract counterfactual reporting 0 witnesses (§3 row 4 — **second cycle running that this specific comparison was wrong on the first draft**), and three `detected` predicates that reported correct behavior as failure (§3 row 5). Not caught by me: nothing this cycle, but see row 3. | **Failed six times; three overstatements caught here before shipping** |
| 6 | Determinism, hygiene, allowlist | Any output byte-differing across runs, or a file written outside the two writable areas. 13/13 identical; 21 files touched, all inside. | Not disconfirmed |

## 6. What R2 did NOT change

W1–W4 as delivered in TASK-0005 and the RW-28..RW-31 corrections all stand. No fixture, document, gate artifact, `13F_` or checker was touched. `03F_Replay_Fixtures.json` is byte-identical to the snapshot.

## 7. RW-36 — change request, not executed

**RW-36 asks me to verify that D-SM row 15 makes the supersession checker fire on the retired scheduler-self-notice phrase, and to ship that as a self-test case. I cannot, for three separate reasons, any one of which is sufficient:**

1. **`design/traces/check_supersessions.py` is not in the Builder snapshot.** The snapshot's `design/` tree contains four documents (D-B2, D-B7, D-B9, D-KR) and `design/traces/behavioral/`. There is no checker.
2. **`D-SM` is not in the snapshot**, so row 15 — committed with `39_`, which I also do not hold — cannot be read.
3. **`design/traces/` is outside the allowlist.** `34_` and `40_` both scope me to `design/traces/behavioral/**` and `13V_validate_design_matrix.py`. The checker is one directory up.

The standing rule is that a scope conflict returns as a change request rather than a silent expansion, so that is what this is. To execute RW-36 I need: the current `check_supersessions.py`, `D-SM` (with row 15), `D-B11`, and an allowlist extension covering `design/traces/check_supersessions.py`. Everything else in R2 is complete without it.

I have not guessed at the checker's contents, written a substitute, or claimed the leg is closed.

## 8. Open items and deviations

- **`39_` dispositions not held.** `38_` and `38A_` were relayed as promised and govern; the dispositions were not. `40_`'s per-finding bullets carry Fable's rulings for RW-33 and RW-35 explicitly, and I followed them.
- **The full `13V_` structural run still cannot execute here**: the requirements register, the change plan and `13D_` are not in the snapshot. `--self-test` and `--end-to-end-probe` are the shipped evidence.
- **No scope deviations.** Nothing written outside the two allowlisted areas.
- **Branch deviation (unchanged, disclosed):** operator-designated branch.
- **Recommended reviewer focus:** falsifier row 2. Structural separation is what Fable ruled for and what I built, and it stops the manifest author acting alone — but two colluding authorities still pass, and that is the next layer in. If the answer is cryptographic attestation, the envelope is ready for it and I would rather be told now than find it in `38A_`'s successor.

---

*Builder-authored completion claim and evidence index — not independent evidence (APP-06). Every proof is reproducible from the pinned snapshot with the commands in `design/traces/behavioral/README.md`.*
