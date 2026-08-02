# 41 — ChatGPT Scoped Re-Verification: TASK-0005 R2

## Verdict

**FAIL — TASK-0005 R2 is not accepted; the Decision Engine design gate remains open.**

The packet is mechanically excellent and closes two of the five P2W findings. The strict final-gate CLI now fails closed, the superseded scheduler-self-notice rule is consolidated, the bundle is reproducible, and the supplied evidence reruns cleanly.

Independent falsifier testing found five High-severity gaps in the external-evidence and schedule-authority contracts. These are bounded corrections. They do not reopen discovery, the owner decisions, the record-shape candidates, or the recommendation-versus-policy hypothesis.

---

## 1. Independent packet verification

```text
Uploaded ZIP SHA-256
15fcc2a6a009ceea0ca191db1d90844387656ae9dfe5dddcd3d2a9c3659a59fb

Export manifest
51 / 51 payload hashes passed

checksums.sha256
52 / 52 entries passed

Candidate commit
6b6e0b413983c32efc068cb463d71a9f8562e340

Candidate tree
cda2083cdb2a29c890a37cdc406eb37021b393f5

Base commit
0e906694b7298e12596cbbef6c989300da54ad31

Git bundle
Fresh clone passed
git fsck --full passed
Fresh checkout clean

Base-to-candidate diff
git diff --check passed
Supplied patch is byte-identical to an independently generated Git diff
```

### Supplied evidence reproduced

```text
Behavioral gate
2 runs passed
Generated outputs byte-identical between runs
Regenerated outputs byte-identical to the shipped outputs

13V design-matrix validator
25 / 25 self-tests passed
5 / 5 end-to-end gate cases passed
28 / 28 strict CLI cases passed
Plain --final-gate exited 1 with the blocking findings open

Supersession checker
Clean corpus passed
Self-test passed, including the retired scheduler-self-notice phrase
```

---

## 2. Prior-finding disposition

| Prior finding | Result |
| --- | --- |
| **P2W-01 — final-gate mode bypass** | **Closed.** CLI modes are explicit and mutually exclusive; mixed modes and unknown arguments exit 2 before tests execute. |
| **P2W-02 — independent receipt evidence** | **Open; materially improved.** A separate registry and distinct declared actor now exist, but the consuming manifest does not bind the exact registry snapshot and receipt semantics are not matched to use. |
| **P2W-03 — manifest authority/snapshot/schema context** | **Open; materially improved.** The external manifest now binds a broad control envelope, but the exact receipt-registry content and several receipt-level authority semantics remain unbound. |
| **P2W-04 — durable schedule identity and replay** | **Open; materially improved.** Normal API paths enforce monotonic versions and journal-derived retirement, but concurrency is optional, run receipts are unversioned, and malformed journal histories fold without refusal. |
| **P2W-05 — scheduler self-notice contradiction** | **Closed.** D-B11 now states the three-part liveness contract consistently and the supersession checker demonstrates the retired phrase is rejected. |
| **P2T-06 — self-contained history/evidence** | **Closed.** The supplied full-history bundle, patch, manifests, and evidence are independently reproducible. |

---

## 3. New findings

### P2X-01 — High: the external manifest does not bind the exact receipt-registry snapshot

**Affected:** `external_basis.py`, P2W-02/P2W-03 structural-independence contract, deterministic replay basis.

**Problem:** The manifest binds the receipt authority ID, authority version, and a registry `snapshot_id`, but it does not bind the registry's declared/computed digest. Two separately valid registries can therefore use the same authority, version, and snapshot label while carrying different receipt content.

**Independent probe:**

1. Create a frozen manifest containing a record that cites receipt `r-late`.
2. Supply a valid, bound registry with the declared authority/version/snapshot but without `r-late`: resolution fails.
3. Supply a second valid, bound registry with the **same** authority/version/snapshot label but with `r-late`: resolution passes.
4. The manifest remains byte-identical throughout.

```text
Registry before digest
6d29bf478bd204b49a815a7899573f40c8a7d970b1c04cea19367c0d5210eca0

Registry after digest
a409ab989217c43e63ca6dc3fa74f62ff8e2e9eb3edfbd4d46d57ffe60542160

Same declared snapshot ID
true

Before
unresolved

After
resolved
```

**Why it matters:** A replay bound to one external manifest can change from refusal to acceptance merely because a different registry body is supplied under a reused snapshot label. The current result is deterministic only over the pair of runtime arguments, not over the manifest's declared evidence basis.

**Required correction:**

- Add a manifest field such as `receipt_registry_digest` or an equivalent immutable registry content ID.
- Include it in the manifest digest and required-control coverage.
- Require the supplied registry's declared and computed digest to equal that exact value.
- Treat a reused snapshot label with different content as an integrity failure.
- Add the exact before/after registry substitution above as a shipped failing probe.

**Boundary:** This does **not** require cryptographic signatures at this design gate. Hash-binding the exact separately controlled registry snapshot is sufficient for this finding; cryptographic attestation may remain a build-gate obligation under Fable's ruling.

---

### P2X-02 — High: receipt semantics are not bound to the consuming purpose or registry authority version

**Affected:** `Receipt`, `_resolve_receipt()`, external evidence contract, action/evidence authority.

**Problem:** `_resolve_receipt()` verifies that `purpose` is nonempty, but it never compares the receipt's purpose with the action/evidence purpose for which the record is being consumed. It also does not require `receipt.authority_version` to equal `registry.authority_version`.

**Independent probes:**

```text
Receipt purpose
"display-monthly-digest"

Consuming ActionRequest action_class
"delete-production-data"

Basis validation problems
[]

Fold result
ActionRequest accepted
```

A second probe used:

```text
Manifest expected authority version: ra-v1
Registry authority version:          ra-v1
Receipt authority version:           receipt-object-v999
Result:                               accepted
```

**Why it matters:** A valid receipt for one purpose can currently be used as the evidence basis for a materially different action class, and receipt-level authority-version identity can drift from the registry that supposedly owns it.

**Required correction:**

- Make the consuming evidence contract explicit: the event/action must declare the required receipt purpose or allowed purpose set.
- Compare `receipt.purpose` with that contract; nonempty is not sufficient.
- Require each receipt's `authority_version` to equal the registry authority version.
- Bind the receipt reference to a canonical digest of the receipt row, or remove the misleading self-declared `content_hash` semantics and rely on the exact registry digest from P2X-01.
- Ship wrong-purpose and wrong-authority-version probes that fail closed.

---

### P2X-03 — High: optimistic concurrency is optional on schedule changes

**Affected:** `Watchdog.change_schedule()`, P2W-04 durable identity ruling, schedule change contract.

**Problem:** `expected_current_version` defaults to `None`, and the compare-and-swap check only runs when the caller supplies it. A caller can therefore bypass the concurrency control simply by omitting the parameter.

**Independent probe:**

```text
Register v1
Change v1 -> v2 with expected_current_version=1: accepted
Change v2 -> v3 with expected_current_version omitted: accepted
Version in force: v3
```

**Why it matters:** The design claims that two changes computed against one observed state cannot both land. That property is not enforced by an API in which the observation token is optional.

**Required correction:**

- Require `expected_current_version` for every change to an existing schedule.
- Refuse a missing expectation rather than treating it as an unconditional update.
- Keep `register()` as the only initial-create path.
- Update `reactivate()` and every internal caller to supply the current version explicitly.
- Ship a stale-concurrent-writer probe and a missing-expectation probe.

---

### P2X-04 — High: `RunStarted` receipts are not bound to schedule version or activation

**Affected:** `J_RUN_STARTED`, `scheduler_completes_run()`, `_replay()`, `missed_deadlines()`, D-B11 missed-run contract.

**Problem:** A run receipt records only `(schedule_id, at)`. `missed_deadlines()` considers any matching timestamp for that schedule answered, regardless of which schedule version or activation produced the run.

**Independent probe:**

```text
Register schedule v1, due at t10
Change atomically to v2 at t5, also due at t10
A stale v1 scheduler reports RunStarted at t10 after v2 is in force
Watchdog evaluates v2 at t11

Current version:       v2
Missed deadlines:      []
```

The stale v1 receipt satisfied the v2 deadline.

**Why it matters:** A superseded scheduler instance can mask the failure of the current schedule. It also weakens the duplicate-tick and idempotency claims in D-B11.

**Required correction:**

- Include `schedule_version` or immutable `activation_epoch` and an occurrence identity in every `RunStarted` receipt.
- Match missed deadlines against the exact current `(schedule_id, version/activation, occurrence)`.
- Refuse or quarantine receipts whose version/activation is absent, retired, or not current for the claimed occurrence.
- Add the exact stale-scheduler race above as a shipped probe.

---

### P2X-05 — High: journal replay accepts contradictory authority histories

**Affected:** `Watchdog.from_journal()`, `_replay()`, control-journal authority contract, schedule horizon integrity.

**Problem:** The normal mutation methods prevent version reuse, but `_replay()` trusts arbitrary journal rows. It accepts two different recurrence definitions for the same schedule/version and retains a horizon computed under the earlier definition.

**Independent probe:**

```text
ScheduleRegistered: conflict v1, first_due=10, period=10
HorizonExtended:    conflict v1, through=50
ScheduleChanged:    conflict v1, first_due=11, period=7
```

Replay result:

```text
Accepted without error
Current spec:        v1, first_due=11, period=7
Eligible horizon:    [10, 20, 30, 40, 50]
Horizon matches current spec: false
```

**Why it matters:** The journal is declared the sole durable authority. If replay does not validate the journal's transition invariants, bypassing the writer methods or receiving a corrupted/incomplete journal silently reconstructs impossible authoritative state.

**Required correction:**

Introduce a fail-closed journal preflight/fold contract that verifies at minimum:

- Journal schema and entry type validity.
- Stable event/transaction identity and deterministic order.
- One immutable definition per `(schedule_id, version or activation_epoch)`.
- Strictly monotonic version/activation transitions.
- Required expected-current-version on changes.
- Atomic retirement/adoption grouping or a commit marker proving the group is complete.
- Horizon and RunStarted rows reference an existing exact version/activation.
- No current version is simultaneously retired.
- Contradictory, orphaned, duplicated, or incomplete transitions cause replay refusal before derived state is emitted.

Ship the exact contradictory-journal probe above, plus orphan-horizon and incomplete-transaction probes.

---

## 4. Corrections that should be preserved

The next cycle should retain the following R2 work:

- Strict, total CLI parsing and mutually exclusive gate/test modes.
- Global fail-closed handling of open blocking findings.
- Full external-manifest field coverage and digest enumeration.
- Separate manifest and receipt-registry objects and distinct declared actors.
- Full-length content identity grammar.
- Duplicate record and receipt-ID refusal.
- Monotonic schedule versions on normal mutation paths.
- Durable retirement derived from the control journal.
- Version-bound ExpectedRun horizons.
- Consolidated watchdog-owned liveness language and supersession checks.

The defects are in the remaining cross-object bindings and replay preconditions, not in the overall direction.

---

## 5. Required next cycle

Fable should:

1. Disposition P2X-01 through P2X-05.
2. Amend the normative external-evidence and schedule/journal contracts before issuing Builder work.
3. Issue a narrow APP-07 Rework Packet covering the machine-enforceable corrections.
4. Update the authoritative open-findings registry and requirement dependencies without marking anything closed before verifier confirmation.
5. Return one integrated scoped packet with:
   - Exact candidate commit/tree and base-to-candidate patch.
   - Full-history Git bundle.
   - Complete manifests/checksums.
   - Updated design text and supersession map.
   - Shipped tests for every probe above.
   - Reproduced legacy tests proving no regression.

No rediscovery, owner decision, or record-shape selection is required in this cycle.

---

## 6. Gate state

```text
Accepted v1.3 baseline:             Unchanged
Accepted Phase 2 discovery:         Valid
Approved CP-P2-A plan:              Valid
Packet integrity:                   Pass
Supplied evidence reproduction:     Pass
P2W-01:                             Closed
P2W-05:                             Closed
P2W-02 / P2W-03 / P2W-04:          Open under P2X-01..05
TASK-0005 R2:                       Not accepted
Decision Engine design gate:        Fail
Record-shape selection:             Not made
DE-R1 through DE-R8 acceptance:     Not authorized
Owner decision package:             Blocked
Owner action required now:          None
Next actor:                         Fable
```

The standing role separation remains unchanged: Fable owns architecture, dispositions, and project management; the Builder implements only authorized corrections; ChatGPT independently verifies; and Hunter retains final authority.
