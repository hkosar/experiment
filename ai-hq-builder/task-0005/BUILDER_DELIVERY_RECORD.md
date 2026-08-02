# Builder Delivery Record — TASK-0005 rework cycle R4 (P2Y design-portion corrections)

**Task:** TASK-0005, rework cycle R4 — the final design-gate cycle under the `47_` §1 terminal condition.
**Builder:** Claude Code session, model `claude-opus-5` (standing authorized substitution, trail entry 69).
**Branch:** `claude/task-0002-builder-handoff-g97x8j` (operator-designated; see §8).
**Instruction authority:** `34_` + prior rework packets + `47_` §3; **governing contract texts: `46_` §3's design-gate-portion specifications, adopted verbatim as design rulings by `47_` §2.**
**Returned to:** **Fable**, not the verifier.
**Status:** **Built; Fable's verification pending.** No design-gate passage is claimed.

**Relay integrity:** `SHA256SUMS.txt` verified **4/4 OK** (`44_`, `44A_`, `46_`, `47_`) before anything was read as authority.

**Scope note.** The owner arbitrated the design/build split (trail 110) and `47_` §1 sets the four blocking portions as the CLOSED list. I have implemented the four design portions and nothing from the deferred build-gate lists — no cryptography, no persistence, no clocks, no credentials.

---

## 1. Disposition of the four work items

| # | Finding | What changed | Shipped-evidence proof |
| --- | --- | --- | --- |
| **RW-42** | **P2Y-01** — the consuming event self-declared the purpose that authorized it | `Event.required_receipt_purposes` is **deleted**. The event carries an `ActionContext` — action class, scope, policy version, risk class — which are facts about itself. The permitted purposes come from `EvidencePolicy`, a bound policy-plane artifact holding `ActionEvidenceContract` rows keyed by exactly those four, authored by an authority distinct from both the manifest source and the receipt authority. `declared_contract_id` is optional and is **checked against the lookup, never trusted**. | The verifier's exact negative: `action_class=delete-production-data`, receipt purpose `display-monthly-digest` ⇒ **refused**, and the producer can no longer change one field to pass. Six more failing cases: no action context, ungoverned action class, naming a contract that does not govern it, no policy supplied, a policy authored by the manifest source, an unbound policy, two contracts for one key. The positive resolves under **three distinct authorities**. |
| **RW-43** | **P2Y-02** — transaction completeness and scope unenforced | All eight invariants from `46_` §3, in its order, and everything schedule-**scoped**: R3 reasoned about transactions globally, which is exactly how one `txn` string bridged two schedules. A change requires an in-force predecessor; one transaction, one schedule, one adoption; the retirement set is complete for that schedule's superseded versions; a retirement references a defined version of the same schedule; final state holds no version both active and retired. | Eight histories, the verifier's three (`missing retirement`, `cross-schedule txn`, `change without predecessor`) verbatim plus two-adoptions, retirement-of-an-undefined-version, retirement-with-no-adoption, empty transaction id, prohibited-field-for-kind. **All eight refuse; all eight fold with validation off.** The well-formed journal still replays. |
| **RW-44** | **P2Y-03** — malformed recurrences admitted as durable state | `recurrence_problems()` is the **one** normative schema, called by `register()`, by `change_schedule()` and by `journal_problems()` — the required correction's "a journal cannot represent a state the governed API itself would refuse". Positive integer version and period, non-negative integer first-due, integer **non-boolean** logical time (in Python `bool` is an `int`; it is not one here), typed expected-current-version, non-empty transaction id, and per-kind **prohibited** fields as well as required ones. | Nine histories including the verifier's `period=0` and `period=-1`. All refuse. The writer-API block shows `register()` refusing the same three definitions and admitting the legal one. |
| **RW-45** | **P2Y-04** — a receipt could pre-satisfy an arbitrary future deadline | `RecurrenceSpec` carries `max_early_ticks` (**default 0** — no early execution) and `max_late_ticks`. A receipt must name an occurrence the recurrence actually produces, and its execution time must fall inside that occurrence's admissible window. Unlimited early running is an explicit schedule policy, per `46_`'s "cannot be the accidental result of accepting any `(version, occurrence)` pair". | The verifier's probe: a receipt at t0 claiming occurrence t10 is **refused**, and `missed_deadlines` at t11 is **`[10]`** where `44A_` recorded `[]`. Three companions: an explicitly authorized `max_early_ticks=10` window **accepts** (the contract is about explicitness, not prohibition), an occurrence the schedule never produces is refused, and the on-time receipt still clears the deadline. |

## 2. What was different about this cycle

The previous four cycles each found a control that named a thing without establishing it. P2Y-01 is the same shape at the top of the stack — the consumer named its own requirement — and I want to be exact about my part in it: **R3's falsifier row 2 predicted this finding almost word for word.** I wrote that purposes were "a string set, matched by equality, declared by the consuming event" and that "nothing stops a consumer declaring the purpose it happens to have been given". Disclosing it did not fix it, and the verifier turned that sentence into `44A_/purpose_self_declaration` within one cycle. That is now the third time a disclosure of mine has become the next finding.

So the operational change here is narrower than a principle: **when a falsifier row says a control can be defeated by the party it governs, that row is a work item, not a disclosure.** The three rows in §5 below are written to that standard — each names who would have to be wrong, not merely what is unproven.

## 3. Regressions and behavior changes, each dispositioned

| # | Change | Disposition |
| --- | --- | --- |
| 1 | `Event.required_receipt_purposes` **removed**; `Event.action_context` added | Required by P2Y-01 — the field being removed *was* the finding. No corpus fixture declares an external basis, so no production path changes. |
| 2 | `validate_basis()` / `fold()` take an `evidence_policy` | The policy plane is a third supplied artifact, distinct from the manifest and the registry, for the same structural reason those two are separate. `None` is not permissive. |
| 3 | The R3 case `consuming-event-declares-no-required-purpose` is **deleted** | It tested a concept that no longer exists — an event stating its own requirement. Its successor is `consuming-event-declares-no-action-context`. Recorded rather than silently dropped. |
| 4 | Behavior 17's explicitly-authorized-early-window row failed on first run | `max_early_ticks` was a field on the spec only, so `_replay()` rebuilt every schedule with the strict default and an authorized window did not survive a fold. The window is **journalled** now. This is the same class as P2W-04's in-memory retirement, in a field I added this cycle — caught by the positive row, which is why that row exists. |
| 5 | Malformed-type journal rows crash rather than fold with validation off | `first_due="soon"` raises inside `int()` in the previous contract; it does not fold into wrong state. `_journal_case()` reports that as an unhandled exception and does **not** count it as a refusal, because calling it either "accepted" or "refused" would misreport what the previous contract did. The verifier's own rows (`period=0`, `period=-1`) do fold cleanly, which is why those carry the finding. |
| 6 | Journal entries gain optional `max_early_ticks` / `max_late_ticks` | Optional so pre-existing histories stay valid; omission defaults to the **strictest** reading, so a journal cannot widen a window by saying nothing. |
| 7 | Gate criteria remain **21** | 18b's case set grows 44 → 50; 19's behaviors grow 14 → 17. |

## 4. Acceptance criteria — 21, all re-proven

Read back out of the shipped JSON after the final run:

**21/21 criteria PASS.** 81/81 combinations, 0 judged failures; 171 evaluations over 56 predicates, 56 defect-reachable; 0 receipt-ownership violations; 81/81 order-invariant; 81 divergences; E2E-1 with the seeded leak; 9/9 defect classes; 8b 56/56 via 62 mutations; P2S-05 5/5; P2S-07 2/2; 12 11/11; 13 18/19 judge checks with an engine witness + 1 oracle-side resolved through the criterion itself, 0 orphaned switches, 0 dead mutations; 14 D-B5 self-test; 15 attention 66/81; 16 all four dimensions accounting for all 81, min 1 comparison; 17 4/4 + 2/2 probes, 102/108 sentinels, 92/92 contradictory witnesses, same-kind 0 survived; 18 8/8 missing-basis; **18b 50/50 external-basis + the three-authority positive + enumeration guards + 3/3 `38A_` and 3/3 `41A_` contract witnesses**; **19 17/17 schedule behaviors**.

`13V_`: **SELF-TEST PASS, 25 cases**; **END-TO-END PROBE PASS, 5 gate cases + 28 CLI cases**.

**Anti-circularity 4/4 PASS.** **Determinism: two runs byte-identical across 13/13 outputs**, and the shipped `out/` matches a fresh run. **Hygiene:** 0 CR, 0 trailing whitespace, single final LF across every file I wrote; the two flagged files are the frozen corpus and the verifier's own `32_` document. **pyflakes** reports nothing on any file this cycle touched (the two pre-existing unused imports in `engine_core.py` and `scenarios.py` remain, unchanged and not mine). **Allowlist: 21 modified + 1 added, 0 outside.**

## 5. Falsifier element (APP-06 / CPB-14, reflexive)

Written to the §2 standard: each row names **who would have to be wrong**, not merely what is unproven.

| # | Claim | Who would have to be wrong, and how | Status |
| --- | --- | --- | --- |
| 1 | An action cannot authorize itself | **The policy authority.** The action can no longer pick its purpose, its contract, or its keys' meaning — but it does declare the four keys, so an event that misdescribes its own action class gets the contract for the class it claimed. Nothing here validates `action_class` against what the event actually does; that binding lives between the event's payload and its context, and no held document specifies it. **This is a real remaining gap and I am naming it as a gap, not a limit** — see §7. | **Open gap, named** |
| 2 | Three authorities must agree | **Any two of the three, colluding.** Manifest source, receipt authority and policy authority must be distinct and each artifact separately bound. Two colluding parties still pass; that boundary is unchanged since R2 and remains, per the owner's arbitration, a build-gate obligation (cryptographic attestation, trust roots). Recorded so it is not mistaken for closed. | Not disconfirmed; **deferred by ruling** |
| 3 | The journal cannot represent an impossible state | **Me, about the invariant list.** Eight invariants are `46_` §3's list transcribed; the schema is its enumeration transcribed. If the ratified list is complete, this is complete. If I mis-transcribed one — read two clauses as one, or scoped one too narrowly — the shipped code is wrong in exactly that place, and the transcription is auditable against `46_` §3 line by line. | Not disconfirmed; **transcription auditable** |
| 4 | A receipt satisfies only its own occurrence | **The schedule author.** `max_early_ticks` defaults to 0 and must be widened deliberately. A schedule that sets a large early window gets what it asked for; that is the contract `46_` specifies. What is NOT established is that `at` is an authoritative execution time — it is whatever the caller passed, and clock authority is explicitly build-gate. | Not disconfirmed; **deferred portion named** |
| 5 | My record matches my code | **Me.** This has failed in R3, R4, C1, TASK-0004, TASK-0005, R1, R2 and R3. Caught before shipping this cycle: the journalled-window bug (§3 row 4) and the crash-vs-fold misreport (§3 row 5), both by running rather than reading. The §2 admission — that R3's falsifier row 2 predicted P2Y-01 and I disclosed instead of fixing — is the one I most want on the record. | **Failed eight times; two caught here, one predicted-and-not-fixed** |
| 6 | Determinism, hygiene, allowlist | Any output byte-differing across runs, or a file outside the two writable areas. 13/13 identical; 22 files touched, all inside. | Not disconfirmed |

## 6. What R4 did NOT change

Everything `44_` §5 lists as already-correct is intact and re-proven: exact registry-content digest binding; receipt canonical-row digest validation; receipt/registry authority-version agreement; mandatory compare-and-swap; version-bound horizons and stale-version receipt refusal; strict final-gate CLI and global open-finding enforcement. No fixture, document, gate artifact, `13F_` or checker was touched. `03F_Replay_Fixtures.json` is byte-identical to the snapshot.

## 7. Change request to Fable (falsifier row 1)

**The event still declares its own `action_class`.** P2Y-01 is closed as specified — the purpose comes from the policy plane, keyed by the four values `46_` §3 names. But an event that declares `action_class="render-digest"` while emitting a destructive ActionRequest would resolve the display contract. Closing that needs a binding between an event's declared context and its actual payload/effect, and **no held design document specifies one**; inventing it would be normative discretion.

I have not implemented it, and I am flagging it now rather than disclosing it in a falsifier row and waiting — that is the §2 lesson. If Fable judges it inside the `47_` §1 closed list, I need the rule; if outside, it belongs in `13B_` as a named residual with the other authority-binding deferrals.

## 8. Open items and deviations

- **The full `13V_` structural run still cannot execute here**: the requirements register, the change plan and `13D_` are not in the snapshot. `--self-test` and `--end-to-end-probe` are the shipped evidence.
- **No scope deviations.** Nothing written outside `design/traces/behavioral/**` and `13V_validate_design_matrix.py`. Nothing from the deferred build-gate lists was implemented.
- **Branch deviation (unchanged, disclosed):** operator-designated branch.
- **Recommended reviewer focus:** §7 first — it is the one thing I would expect a fifth cycle to find, and I would rather it be dispositioned now than discovered. Then falsifier row 3: the eight invariants and the recurrence schema are transcriptions of `46_` §3 and should be read against it line by line.

---

*Builder-authored completion claim and evidence index — not independent evidence (APP-06). Every proof is reproducible from the pinned snapshot with the commands in `design/traces/behavioral/README.md`.*
