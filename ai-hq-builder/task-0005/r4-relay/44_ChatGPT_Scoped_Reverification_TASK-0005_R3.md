# 44 — ChatGPT Scoped Re-Verification: TASK-0005 R3

## Verdict: FAIL — TASK-0005 R3 is not accepted; the design gate remains open

The packet is mechanically strong and the supplied correction evidence reproduces exactly. Two findings are closed at their scoped boundary, and the remaining work is narrower than the prior cycle.

Independent falsifier testing nevertheless found four High-severity defects. The central pattern is that several new controls verify **declared labels inside the same record or journal**, but do not yet prove that those declarations are authorized, complete, or temporally valid.

No rediscovery or owner-decision reopening is required.

---

## 1. Independent packet and repository verification

```text
Uploaded ZIP SHA-256
085373e40bcb81933f28f3f178f0008567c824c4953d5647c6f1217e070a662b

EXPORT_MANIFEST.json
48 / 48 payload hashes passed

checksums.sha256
49 / 49 entries passed

Candidate commit
8c821cce2249b2ca174eac049a3da3ef4767b888

Candidate tree
fff3c8255e6232be370d96409e0273b5c9335f10

Last-reviewed base
6b6e0b413983c32efc068cb463d71a9f8562e340

Git bundle
Fresh clone passed
git fsck --full passed
Required ancestry present
Fresh checkout clean

git diff --check
Passed

Supplied patch
Byte-identical to an independently generated standard `git diff --binary`
from 6b6e0b4... to the candidate

Changed paths
20 total
0 CR-containing files
0 trailing-whitespace lines
0 files missing final LF
```

Accepted v1.3 baseline content remained unchanged:

```text
04_Proposed_Operating_Manual_v1.1.md          unchanged
05_Requirements_Register_v1.1.md             unchanged
05_Requirements_Register_v1.1.csv            unchanged
```

Repository checksum sets independently validated:

```text
Phase 1                     24 / 24 passed
Phase 2                    127 / 127 passed
v1.2 ideas-pass             26 / 26 passed
```

---

## 2. Supplied evidence reproduction

The behavioral gate was executed twice from a fresh candidate checkout.

```text
Gate executions                         2 / 2 passed
Generated output files                 13
Outputs byte-identical across runs     yes
Regenerated outputs match shipped      13 / 13
```

The design-matrix validator reproduced as reported:

```text
--self-test                 exit 0; 25 / 25 passed
--end-to-end-probe          exit 0; 5 gate + 28 CLI cases passed
--final-gate                exit 1; failed closed on the six open findings
```

The new evidence also demonstrates the scoped corrections it claims:

- Registry body substitution under reused authority/version/snapshot labels is refused when the manifest is bound to the other registry digest.
- Receipt authority-version skew and self-declared receipt row hashes are refused.
- Omitting `expected_current_version` from a normal schedule change is refused.
- A stale v1 run receipt cannot satisfy a v2 occurrence.
- The shipped contradictory, orphaned, incomplete, out-of-order, and unknown-kind journal cases are refused, while the shipped positive journal replays.

---

## 3. Prior-finding disposition

| Prior finding | Scoped result |
| --- | --- |
| **P2X-01 — exact receipt-registry snapshot** | **Closed.** The manifest binds the registry's exact declared content digest, and same-label body substitution is refused. |
| **P2X-02 — receipt purpose and authority identity** | **Partially closed.** Receipt-row integrity and registry authority-version agreement are enforced. Purpose remains self-declared by the consuming event; see P2Y-01. |
| **P2X-03 — mandatory schedule compare-and-swap** | **Closed for the normal mutation API.** Omission is refused and the supplied concurrent/stale cases pass. |
| **P2X-04 — schedule-version-bound run receipts** | **Closed at the version-binding boundary.** A stale-version receipt is refused. Temporal/occurrence admissibility remains open under P2Y-04. |
| **P2X-05 — invariant-validated journal replay** | **Open; materially improved.** The shipped corruptions are refused, but incomplete and cross-schedule transactions, predecessor gaps, and invalid recurrence domains still replay. See P2Y-02 and P2Y-03. |

---

## 4. New findings

### P2Y-01 — High: the receipt-purpose contract is self-declared by the consuming event

**Problem**

`Event.required_receipt_purposes` is accepted as the authoritative evidence contract, but no deterministic control binds it to the event's action class, policy evaluation, or independently owned action schema.

**Independent probe**

A receipt honestly declared this purpose:

```text
display-monthly-digest
```

The consuming `ActionRequest` declared:

```text
action_class = delete-production-data
required_receipt_purposes = [display-monthly-digest]
```

Result:

```text
basis problems: []
fold accepted:  true
action emitted: action-delete
```

When the same event instead declared `delete-production-data` as its required purpose, the display receipt was correctly refused. This proves the comparison works but also proves the action can choose the value it wishes to compare.

**Why this matters**

The prior exploit—display evidence grounding a destructive action—remains possible by changing one field on the same ActionRequest. Two self-consistent declarations by one producer are not an independently governed consuming contract.

**Required correction**

The required receipt purpose must be derived or validated against an independently controlled action/evidence contract keyed by at least action class, scope, policy version, and relevant risk/data class. The ActionRequest may carry the resolved contract ID and expected purpose, but it may not invent the purpose that authorizes itself.

A purpose taxonomy with subsumption may remain a later build-gate concern. The design gate must at minimum prove that a destructive action cannot declare a display purpose and pass.

---

### P2Y-02 — High: journal transaction completeness and scope remain unenforced

**Problem**

`journal_problems()` checks that a transaction which retires something also has some adoption with the same `txn` string. It does not require the adoption and retirements to belong to the same schedule, does not require a change to retire the prior in-force version, and does not require `ScheduleChanged` to have a predecessor.

**Independent probes**

#### A. Missing retirement

```text
ScheduleRegistered sched v1
ScheduleChanged    sched v2 expected v1 txn=sched@t1->v2
```

No `HorizonRetired` entry was supplied.

Result:

```text
journal problems: []
replay accepted:  true
v2 in force
retired versions: none
```

#### B. Cross-schedule transaction collision

```text
A v1 registered
B v1 registered
A v1 retired, txn=shared
B changes to v2, txn=shared
```

Result:

```text
journal problems: []
replay accepted:  true
A v1 is simultaneously in force and retired
B v2 is in force
```

The validator's stated invariant—no version both in force and retired—is therefore bypassed by reusing one transaction ID across schedules.

#### C. Change without a predecessor

```text
ScheduleChanged new v1 expected_current_version=None txn=new@t0->v1
```

Result:

```text
journal problems: []
replay accepted:  true
v1 created through the change path
```

**Required correction**

Journal validation must enforce a schedule-scoped transition contract:

- A `ScheduleChanged` event requires an existing in-force predecessor.
- Every change transaction has exactly one adoption for one schedule.
- Its retirement set is complete for the prior in-force/superseded versions of that same schedule.
- A transaction ID cannot bridge schedules or contain multiple adoptions.
- Every retirement references a defined version of the same schedule.
- The final reconstructed state is checked for `in_force ∩ retired = ∅` for every schedule.
- A missing, duplicate, cross-schedule, or asymmetric transaction refuses replay before state exists.

Fable's design-level ruling that transaction identity plus deterministic order can satisfy stable identity may remain viable only after transaction identity is actually scoped and invariant-checked.

---

### P2Y-03 — High: malformed recurrence definitions are accepted into the durable authority

**Problem**

The journal preflight verifies field presence but not the types and semantic domains required for a valid recurrence.

**Independent probes**

Both histories were accepted by `journal_problems()` and `Watchdog.from_journal()`:

```text
ScheduleRegistered period = 0
ScheduleRegistered period = -1
```

Result for each:

```text
journal problems: []
replay accepted:  true
```

A zero or negative period can make deadline generation non-terminating or move backward indefinitely when the schedule is later evaluated.

**Required correction**

Before replay, validate every control field's type and domain, including at minimum:

- Positive integer schedule versions
- Positive recurrence period
- Valid first-due/occurrence values
- Integer, non-boolean logical times
- Expected-current-version type and predecessor existence
- Nonempty, schema-valid transaction identity
- Version/occurrence fields appropriate to each entry kind

The writer API and replay validator must share one normative recurrence schema so a journal cannot represent a state the governed API itself would refuse.

---

### P2Y-04 — High: a run receipt can pre-satisfy an arbitrarily future deadline

**Problem**

A `RunStarted` receipt is now bound to schedule version and claimed occurrence, but the watchdog does not validate that the receipt was produced within an admissible execution window for that occurrence.

**Independent probe**

```text
Schedule v1: first_due=10, period=10
RunStarted recorded at t0, claiming occurrence t10
Watchdog evaluated at t11
```

Result:

```text
receipt accepted:          true
missed deadlines at t11:   []
```

The receipt was recorded ten logical ticks before the occurrence but permanently suppressed the missed-deadline alarm.

**Required correction**

Define and enforce the occurrence contract:

- A receipt must reference an existing ExpectedRun/occurrence identity for the same schedule version or activation epoch.
- The contract must define whether early execution is permitted and, if so, the maximum early window.
- The receipt's authoritative execution time must fall inside the allowed window.
- A future-dated claim outside that window cannot satisfy a later deadline.
- The receipt/evidence source and temporal fields must remain independently owned at the later build gate.

If early execution is intentionally unlimited, that must be an explicit owner/policy decision; it cannot be the accidental result of accepting any `(version, occurrence)` pair.

---

## 5. Required next correction cycle

Fable should disposition P2Y-01 through P2Y-04 and issue a narrowly scoped rework packet.

Builder work is appropriate for:

1. An independently governed action-to-receipt-purpose contract and failing self-declaration probe.
2. Schedule-scoped, symmetric, unique transaction validation with predecessor and final-state checks.
3. Full recurrence-entry type/domain validation.
4. ExpectedRun/activation-bound run receipts with an explicit admissible execution window.

Fable should preserve the already-correct mechanisms:

- Exact registry-content digest binding
- Receipt canonical-row digest validation
- Receipt/registry authority-version agreement
- Mandatory compare-and-swap for existing schedule changes
- Version-bound horizons and stale-version receipt refusal
- Strict final-gate CLI and global open-finding enforcement
- Fable-owned normative consolidation already completed in earlier cycles

The next packet may remain scoped to these four findings and any Critical/High defect directly introduced by their corrections. No rediscovery or owner-decision cycle is needed.

---

## 6. Gate state

```text
Accepted v1.3 baseline:             UNCHANGED
Accepted Phase 2 discovery:         VALID
Approved CP-P2-A plan:              VALID
Packet integrity:                   PASS
Supplied evidence reproduction:     PASS
P2X-01:                             CLOSED
P2X-03:                             CLOSED
P2X-02 / P2X-04 / P2X-05:          OPEN OR PARTIAL under P2Y-01..04
TASK-0005 R3:                       NOT ACCEPTED
Decision Engine design gate:        FAIL
Record-shape selection:             NOT MADE
DE-R1 through DE-R8 acceptance:     NOT AUTHORIZED
Owner decision package:             BLOCKED
Owner design acceptance:            BLOCKED
v1.4 implementation/release:        BLOCKED
Hunter action required now:          NONE
Next actor:                         FABLE
```

The standing separation remains unchanged: Fable owns architecture, dispositions, and project management; the Builder implements only authorized corrections; ChatGPT independently verifies; and Hunter retains final authority.
