# Builder Delivery Record — TASK-0005 rework cycle R3 (P2X authority-binding corrections)

**Task:** TASK-0005, rework cycle R3 (parent topic TOPIC-0002).
**Builder:** Claude Code session, model `claude-opus-5` (standing authorized substitution, trail entry 69).
**Branch:** `claude/task-0002-builder-handoff-g97x8j` (operator-designated; see §8).
**Instruction authority:** `34_` + `37_` + `40_` + `43_` Rework Packet R3; governing findings `41_`/`41A_`; dispositions `42_` — **all four relayed in one zip and all four verified**.
**Returned to:** **Fable**, not the verifier.
**Status:** **Built; Fable's verification pending.** No design-gate passage is claimed.

**Relay integrity:** `SHA256SUMS.txt` verified **4/4 OK** (`41_`, `41A_`, `42_`, `43_`) before anything was read as authority.

---

## 1. Disposition of the five findings

| # | Finding | What changed | Shipped-evidence proof |
| --- | --- | --- | --- |
| **RW-37** | **P2X-01** — the manifest binds the registry's labels, not its content | `receipt_registry_digest` is a new bound envelope control and a `REQUIRED_CONTRACT_CONTROLS` entry. The supplied registry's **declared digest must equal it**, so a second body under the same authority/version/snapshot label is an integrity failure rather than a substitution. The fixtures bind the registry **first** and seal the manifest against it — a manifest cannot exist before the exact body it depends on. | Two new cases, the substitution **in both directions**: `registry-substituted-under-a-reused-label` (the body carrying `r-late`) and `registry-body-the-manifest-was-not-bound-to` (the body without it). Section C2 reports the verifier's own before/after digests and that the snapshot labels are identical. |
| **RW-38** | **P2X-02** — receipt semantics unbound to purpose or authority | Three separate bindings. (a) The consuming event declares `required_receipt_purposes`; the receipt's purpose must be in that set, and an event with an external basis and **no** declared requirement fails closed. (b) `receipt.authority_version` must equal the **owning registry's**, not merely the reference that cited it. (c) `content_hash` is the receipt's **canonical row digest** via `row_digest()`, so a self-declared value is refused. | Five new cases: purpose mismatch (`display-monthly-digest` vs `delete-production-data`), undeclared consumer, authority-version skew (`receipt-object-v999` in an `auth-v4` registry), self-declared content hash, and missing registry digest. |
| **RW-39** | **P2X-03** — compare-and-swap optional | `expected_current_version` takes a `NO_EXPECTATION` sentinel rather than `None`, because `None` is what an omitted argument looks like and that ambiguity **was** the finding. Omission on any change to an existing schedule is a usage error. `reactivate()` and all ten internal call sites now state the version they observed. | Behavior 12 is the verifier's probe: with expectation → accepted; **omitted → refused**; stale expectation (`v99`) → refused; v2 stays in force where the probe recorded v3. |
| **RW-40** | **P2X-04** — run receipts unversioned | `RunStarted` carries `version` and `occurrence`. `missed_deadlines()` matches per `(schedule, version, occurrence)`. A receipt whose version is **absent, retired, or not in force** is refused and journalled with the reason. | Behavior 13 is the verifier's race: the stale v1 receipt is **refused**, `missed_deadlines` at t11 is **`[10]`** where the probe recorded `[]`, and the current v2 receipt still clears it — so the check discriminates rather than refusing everything. |
| **RW-41** | **P2X-05** — replay accepts contradictory histories | `journal_problems()` runs before any state is produced and `from_journal()` raises `JournalError`. Eight invariants: known entry kind with its required fields, non-decreasing order, **one immutable definition per (schedule, version)**, monotonic transitions, the declared expected-current-version matching what the journal has in force at that point, complete retirement/adoption transactions via a shared `txn`, horizon/run rows referencing a defined version, and no version in force while retired. | Behavior 14 ships the verifier's exact contradictory history plus orphan-horizon, incomplete-transaction, out-of-order and unknown-kind. All five refuse; with validation off, all five fold — the contradictory one into `v1 first_due=11 period=7` with horizon `[10,20,30,40,50]`, which is the probe's recorded state. **A well-formed journal still replays identically** (positive control). |

## 2. What I did differently this cycle

R2's record said the operational change was to ask, of each new control, what an actor controlling the inputs could still do. Four of these five findings say that question was asked too narrowly: I asked it about the *object* I had just added and not about the *binding between* objects. P2X-01 through P2X-04 are all cross-object bindings — manifest↔registry content, receipt↔consumer, receipt↔registry identity, receipt↔version. P2X-05 is the same shape one level up: I made the journal the authority and did not ask what an authority owes its own readers.

So the question this cycle was: for every pair of artifacts that must agree, **what is actually compared, and is it content or a label?** That is why the registry binding is a digest and not a snapshot id, why the receipt's authority version is compared to its registry rather than to the reference that cited it, and why `content_hash` is computed rather than declared. Three of the five were the same substitution — a name standing in for a thing.

## 3. Regressions and behavior changes, each dispositioned

| # | Change | Disposition |
| --- | --- | --- |
| 1 | `Event` gains `required_receipt_purposes`; an event with an external basis and an empty tuple **fails closed** | Required by P2X-02. No corpus fixture declares an external basis, so no production path changes. The default is empty precisely so that a consumer which has not thought about its evidence contract is refused rather than defaulted. |
| 2 | `scheduler_completes_run()` gains `version`/`occurrence` and returns `bool` | Required by P2X-04. An unattributed receipt is refused, so the call must be able to report that. |
| 3 | `change_schedule()` signature changes from `Optional[int] = None` to a sentinel | Required by P2X-03 — `None` could not be told from omission, and that was the finding. All ten internal call sites updated. |
| 4 | Four section-B cases briefly failed for the wrong reason | Binding the receipts (`.bound()`) changed their content digests, so three records still cited the old ones and failed on hash mismatch instead of subject/revocation/purpose. A fourth (`registry-unbound`) failed on its manifest's own missing registry digest rather than on the registry. All four repointed; each case again fails for the reason it was written for. Caught by the per-case expected-substring rule, which is what it is for. |
| 5 | The journal preflight rejected a journal the writer methods had produced | `HorizonRetired` is written before `ScheduleChanged` in one transaction, so an entry-by-entry "retired while in force" test flagged every well-formed atomic change. Corrected to consult the transaction's adoption. Found by running the preflight against real output, not by re-reading it. |
| 6 | The R2-contract counterfactual is a **new** section C2, not an extension of C | Same reason C was rebuilt in R2: the R3 fixtures are not expressible in the R2 contract, so a per-row column would report "R2 rejected" everywhere. C2 re-implements only the three R2 predicates the findings are about and runs the verifier's probes through them. **3/3 witness.** |
| 7 | Gate criteria remain **21** | 18b's case set grows 37 → 44 and gains the C2 condition; 19's behaviors grow 11 → 14. |

## 4. Acceptance criteria — 21, all re-proven

Read back out of the shipped JSON after the final run:

**21/21 criteria PASS.** 81/81 combinations, 0 judged failures; 171 evaluations over 56 predicates, 56 defect-reachable; 0 receipt-ownership violations; 81/81 order-invariant; 81 divergences; E2E-1 with the seeded leak; 9/9 defect classes; 8b 56/56 via 62 mutations; P2S-05 5/5; P2S-07 2/2; 12 11/11; 13 18/19 judge checks with an engine witness + 1 oracle-side resolved through the criterion itself, 0 orphaned switches, 0 dead mutations; 14 D-B5 self-test; 15 attention 66/81; 16 all four dimensions accounting for all 81, min 1 comparison; 17 4/4 + 2/2 probes, 102/108 sentinels, 92/92 contradictory witnesses, same-kind 0 survived; 18 8/8 missing-basis; **18b 44/44 external-basis + independently attested positive + enumeration guards + 3/3 `38A_` and 3/3 `41A_` contract witnesses**; **19 14/14 schedule behaviors**.

`13V_`: **SELF-TEST PASS, 25 cases**; **END-TO-END PROBE PASS, 5 gate cases + 28 CLI cases**.

**Anti-circularity 4/4 PASS.** **Determinism: two runs byte-identical across 13/13 outputs**, and the shipped `out/` matches a fresh run. **Hygiene:** 0 CR, 0 trailing whitespace, single final LF across every file I wrote; the two flagged files are the frozen corpus and the verifier's own `32_` document. **pyflakes** reports nothing on any file this cycle touched (the two pre-existing unused imports in `engine_core.py` and `scenarios.py` remain, unchanged and not mine). **Allowlist: 21 modified + 1 added, 0 outside.**

## 5. Falsifier element (APP-06 / CPB-14, reflexive)

| # | Claim | What would disconfirm it | Status |
| --- | --- | --- | --- |
| 1 | The replay is bound to its own declared evidence basis | A registry body the manifest did not bind that still resolves. The digest comparison is exact and the fixtures seal the manifest against a specific body. The **limit**: this binds the *pair*. Nothing here establishes that either artifact is the one the design intended — it establishes that they cannot be mixed after the fact. | Not disconfirmed; limit stated |
| 2 | A receipt is evidence for the use it is consumed by | A consumer that gets evidence it did not ask for. The **limit is the same one R2 disclosed and it has not moved**: `required_receipt_purposes` is a string set, matched by equality, declared by the consuming event. There is no purpose taxonomy, no subsumption, and nothing stops a consumer declaring the purpose it happens to have been given. Structural separation still makes the manifest author unable to act alone; two colluding authorities still pass. **This is the row I expect the next review to open.** | Not disconfirmed; **boundary unchanged and restated** |
| 3 | Journal replay refuses contradictory histories | A malformed history that folds. Eight invariants, five probes, and the positive control. The **limit**: the list is my transcription of the verifier's enumeration, and I stopped where that list stopped. "Deterministic order" is implemented as non-decreasing `at`, which is weaker than a stable per-entry identity — I did not add entry ids, because the required-correction text says "stable event/transaction identity and deterministic order" and I judged `txn` plus ordering to cover it. **That judgement is mine and is the second row to audit.** | Not disconfirmed; **judgement disclosed** |
| 4 | Compare-and-swap cannot be declined | A change that lands without stating what it observed. The sentinel makes omission distinguishable from `None`. The **limit**: `optimistic_concurrency=False` still exists as the targeted defect for behavior 10, and it is a constructor field. It is not reachable from any CLI and no production path sets it — but it is the same *shape* as the P2V-01 flag, and I am naming it rather than waiting to be asked. | Not disconfirmed; **named pre-emptively** |
| 5 | My record matches my code | A claim here the shipped files do not support. This has failed in R3, R4, C1, TASK-0004, TASK-0005, R1 and R2. Caught before shipping this cycle: four section-B cases failing for the wrong reason (§3 row 4) and a preflight that rejected well-formed output (§3 row 5) — both found by running, not reading. | **Failed seven times; two caught here before shipping** |
| 6 | Determinism, hygiene, allowlist | Any output byte-differing across runs, or a file outside the two writable areas. 13/13 identical; 22 files touched, all inside. | Not disconfirmed |

## 6. What R3 did NOT change

Everything the verifier listed under "corrections that should be preserved" is intact and re-proven: strict total CLI parsing and mutually exclusive modes; global fail-closed open-finding handling; full manifest field coverage and digest enumeration; separate manifest and registry objects with distinct declared actors; full-length content identity; duplicate record and receipt-id refusal; monotonic versions on normal mutation paths; durable retirement from the control journal; version-bound horizons. No fixture, document, gate artifact, `13F_` or checker was touched. `03F_Replay_Fixtures.json` is byte-identical to the snapshot.

**RW-36 (P2W-05 checker leg) remains outstanding and is not in this packet's scope.** `41_` closes P2W-05 on the strength of Fable's document fix and the checker's own self-test, so the change request I raised in R2 — for `check_supersessions.py`, `D-SM` and an allowlist extension — appears to be moot. I have not assumed that; if Fable still wants the Builder-side self-test case, the request stands as written.

## 7. Open items and deviations

- **The full `13V_` structural run still cannot execute here**: the requirements register, the change plan and `13D_` are not in the snapshot. `--self-test` and `--end-to-end-probe` are the shipped evidence.
- **No scope deviations.** Nothing written outside `design/traces/behavioral/**` and `13V_validate_design_matrix.py`.
- **Branch deviation (unchanged, disclosed):** operator-designated branch.
- **Recommended reviewer focus:** falsifier rows 2 and 3. Row 2 is the collusion boundary, unchanged since R2 and now the oldest open thing in this contract; row 3 is where I judged the verifier's "stable identity" requirement satisfied by a transaction id and ordering rather than per-entry identifiers. If either judgement is wrong I would rather hear it from Fable than from `41A_`'s successor.

---

*Builder-authored completion claim and evidence index — not independent evidence (APP-06). Every proof is reproducible from the pinned snapshot with the commands in `design/traces/behavioral/README.md`.*
