# ChatGPT Independent Verifier Response
## CP-P2-A — Third Scoped Re-Verification of P2S-01 through P2S-08

**Verifier:** ChatGPT  
**Role:** Independent stage-gate verifier; no architecture ownership, implementation authority, or owner-acceptance authority  
**Review scope:** P2S-01 through P2S-08 and any Critical/High defect introduced directly by their corrections  
**Packet under review:** `P2S_Reverification_Packet_3.zip`  
**Declared and independently computed packet SHA-256:** `4eb91e2d135403677562b39c7d24533b0384e32f4cc30d87cac3fe669aa638fc`  
**Candidate commit:** `68f768dba081030da8a88ae27133cddeba91b1ce`  
**Candidate tree:** `11cb7a83e145699993a38c795030166c63f69862`  
**Diff base:** `20ad093c7535928e07bcc7ef819236a6bed62929`  
**Date:** 2026-07-31

---

# 1. Verdict

## **FAIL — design gate remains open**

The correction cycle is materially converging. The principal P2S-01 defect identified in the prior review—copying fixture expectations and verifying them against themselves—has been removed. The new simulator computes events and folded state from an input-only `Stimulus`, reproduces deterministically, exercises E2E-1, evaluates all declared forbidden predicates, and contains effective seeded-defect suites.

The design gate nevertheless cannot pass. The new evidence still fails the exact P2S-01 closure contract in a decisive way: the gate does not enforce the complete expected result. I independently changed one fixture's expected route, authority, or receipt to an impossible sentinel value; **each altered packet still received a complete gate PASS**. The fold also accepts an event whose declared causal basis is absent, which means incomplete replay evidence can silently produce authoritative state.

Additional High findings remain in scheduled-run liveness evidence, normative supersession, and the requirements-status gate. These are bounded correction defects, not a reason to restart discovery or discard the design direction.

The following remain unchanged:

- The accepted v1.3 baseline.
- Accepted Phase 2 discovery.
- The approved CP-P2-A design plan.
- Owner decisions OD-1, OD-2 including the DE-R8 modification, and OD-3.
- S1, S2, and S3 as viable candidates; no record shape is selected.
- The standing separation among architect/project manager, Builder, verifier, and owner.

---

# 2. Independent Packet and Reproduction Results

## 2.1 Integrity and candidate identity

```text
Uploaded ZIP SHA-256
4eb91e2d135403677562b39c7d24533b0384e32f4cc30d87cac3fe669aa638fc

Declared payload checksums
44 / 44 passed

Candidate commit
68f768dba081030da8a88ae27133cddeba91b1ce

Candidate tree
11cb7a83e145699993a38c795030166c63f69862

Base commit
20ad093c7535928e07bcc7ef819236a6bed62929

Base tree
37f32c6b1501729df3f00770128431820891a295

Packet diff SHA-256
08ad80d2cf043b078ef0e879e51bc9a8ec2cfd6a8c5c8a5f26d418d54c065425

Independently generated base-to-candidate diff
Byte-identical to the packet patch
```

The accepted v1.3 Manual and both accepted Requirements Register files have identical Git blobs at the base and candidate commits.

## 2.2 Behavioral simulator reproduction

I independently ran:

```text
python3 run_gate.py --out <fresh-output-directory>
```

Two independent runs were byte-identical and reproduced the packet's ten output files.

The clean run reported:

```text
27 fixtures × 3 shapes = 81 computed combinations
81 judged passes
171 forbidden-predicate evaluations
56 distinct forbidden predicates
56 / 56 mutation-reachable predicates
0 receipt-ownership violations
81 / 81 causal-order shuffle invariance
5 / 5 P2S-05 traces passing and discriminating
2 / 2 P2S-07 tests passing
11 / 11 policy-composition cases passing and discriminating
E2E-1 authority invariant with seeded-leak detection
```

The independently reproduced gate report also disclosed:

```text
expected.authority: 36 mapped / 45 unmapped
expected.attention: 66 compared / 15 unmapped
three pass-rule checks never selected
one selected pass-rule check vacuous
thirteen registered event types never emitted
```

## 2.3 Requirements validators

Both commands return PASS:

```text
python3 13V_validate_design_matrix.py
python3 13V_validate_design_matrix.py --final-gate
```

The row data currently parses as:

```text
Accepted rows
90 Complete
11 Binding invariant
14 Deliberately deferred
8 Build-gate deferred
2 N/A

Proposed rows
8 Complete
```

The semantic accuracy of those statuses is addressed below.

## 2.4 Git-bundle qualification

The packet calls `ai-hq_full_history.bundle` a full-history bundle. `git bundle verify` reports it as complete, but an independent fresh clone fails:

```text
error: Could not read ffd5cc6ce6626f18de73f671c362806b4a168afe
fatal: Failed to traverse parents of commit 18c571bcb3ed9491eaa23a28cc948cb221eb307e
fatal: remote did not send all necessary objects
```

The current and base commit/tree objects were available and sufficient for this review, but the bundle is not a self-contained, freshly cloneable full-history export.

---

# 3. P2S Finding Dispositions

| Prior finding | Scoped result | Verifier disposition |
| --- | --- | --- |
| **P2S-01** — Circular trace evidence | **Substantially improved but open** | The simulator now computes behavior and no longer copies oracle fields into the engine. E2E-1 and seeded defects are real. However, the complete expected result is not enforced; route and receipt are not semantically compared, unknown authority values silently become unmapped, and unmapped attention remains non-failing. See P2T-01. |
| **P2S-02** — Conflicting normative mechanisms | **Open** | A supersession map exists, but active authoritative text still directs Builders to the circular scripts and retains obsolete scheduler and evidence claims. The checker covers only nine literal patterns and misses the remaining conflicts. See P2T-04. |
| **P2S-03** — Silent common-mode kill/watchdog failure | **Substantively closed at design level** | The phone-side dead-man alarm, heartbeat-fresh short leases, declared stop bound, provider revocation, and degraded-read path form a coherent fail-safe contract. Live phone/provider drills remain correctly deferred to a later activation gate. |
| **P2S-04** — Scheduler death before next occurrence | **Open** | The watchdog-owned schedule and rolling-horizon design are directionally correct, but the two deterministic tests explicitly required by the prior finding are not implemented or included. An older contradictory ExpectedRun rule also remains active. See P2T-03 and P2T-04. |
| **P2S-05** — Policy/lease linearization | **Closed at design-simulator level** | The five traces compute real outcomes, distinguish policy-first from lease-first, preserve provider-accepted history, enforce lease expiry, and halt uncertain retries until reconciliation. Each trace flips under its targeted defect. |
| **P2S-06** — Deterministic cross-store replay | **Open** | The tie-break and shuffle tests are real, but the fold treats a missing causal reference as satisfied. An incomplete basis can therefore fold successfully. See P2T-02. |
| **P2S-07** — Untrusted-content proposal eligibility | **Closed at design-simulator level** | The default produces no proposal from external-untrusted content without an approved eligibility policy; the positive filing-only case permits filing while preserving the outbound floor. |
| **P2S-08** — Counts and deferral gate | **Open** | The dedicated deferral register and structural validator are useful, but the authoritative matrix contains contradictory count/status claims and marks requirements Complete while their supporting P2S mechanisms remain open. See P2T-05. |

---

# 4. Remaining and Newly Introduced Findings

## P2T-01 — Critical: The gate does not enforce the complete expected result

**Affected:** P2S-01; `judge.py`; `oracle.py`; `run_all.py`; `run_gate.py`; all 27 replay fixtures

### Problem

Every fixture has four expected-result dimensions:

```text
route
attention
authority
receipt
```

The clean report itself shows only 36 of 81 authority expectations mapped and 66 of 81 attention expectations compared. Route and receipt have no complete fixture-level equality or semantic-mapping gate.

I performed three one-field falsifier probes. In each probe, only fixture `S1` was changed; its expected value was replaced by an impossible sentinel while the engine, design, and all other oracle data remained unchanged.

```text
Probe                                      Gate result
S1 expected.route    = __IMPOSSIBLE_ROUTE__       PASS
S1 expected.authority = __IMPOSSIBLE_AUTHORITY__  PASS
S1 expected.receipt   = __IMPOSSIBLE_RECEIPT__    PASS
```

For the authority probe, the mapped count simply fell from 36 to 33 and the case remained green. The route and receipt probes also completed with zero base judgement failures.

The same issue is even clearer at corpus scale:

```text
All 27 expected.authority values replaced by nonsense
Gate result: PASS
Authority coverage: 0 mapped / 81 unmapped
```

The harness therefore proves that it executed a model and satisfied the predicates it knows, but it does **not** prove that the computed result matches the fixture's complete expected outcome. That directly fails P2S-01 requirement 4 and undermines the reported 81/81 pass count.

### Required correction

1. Define a machine-readable oracle schema for every expected dimension rather than relying on free-text phrases.
2. Require every fixture/shape to resolve and compare route, attention, authority, and receipt/evidence behavior.
3. Treat an unknown or unmapped expected value as a gate failure, not a coverage note.
4. Separate exact outcomes, allowed alternatives, ceilings/floors, conditional expectations, and presentation-only qualifiers explicitly in the fixture schema.
5. Add an oracle-mutation suite that changes one expected dimension at a time and proves the clean computed result fails.
6. Gate criterion 3 must assert complete expected-result coverage, not merely zero recorded judgement failures and complete forbidden-predicate coverage.
7. Rebuild all 81 verdicts after the oracle schema is corrected.

### Closure falsifier

For every fixture and every governed expected dimension, replacing the expected value with a contradictory but schema-valid value must cause that fixture/shape to fail. An unrecognized value must fail fixture validation before execution.

---

## P2T-02 — High: The fold silently accepts an incomplete causal basis

**Affected:** P2S-06; DE-R7; APP-04; `fold.py::topological_order`; replay and recovery claims

### Problem

The fold's eligibility rule is:

```python
all((ref in done) or (ref not in by_id) for ref in e.caused_by)
```

A `caused_by` reference absent from the supplied event set is therefore treated as already satisfied. The later causal-violation check also ignores missing references because it checks only references present in the set.

Independent probe:

```text
Event
DecisionEvent decision-1
caused_by = [missing-policy-event]

Result
 topological_order accepted decision-1
 fold accepted decision-1
 causal_violations = []
```

This conflicts with the function's own stated `FoldError` contract and with the prior requirement that replay fail on a missing or incomplete basis. Shuffle invariance over a truncated basis does not establish replay correctness.

### Required correction

1. Every `caused_by` reference must resolve to an event in the replay basis unless it is explicitly typed as an external/genesis reference under a declared contract.
2. Add a preflight basis validator covering event IDs, causal references, policy/schema/calibration versions, recorded model outputs, receipts, and store sequences.
3. Missing basis must fail the fold before any authoritative state or projection is emitted.
4. Add seeded tests for:
   - Missing direct cause
   - Missing transitive cause
   - Missing external receipt basis
   - Unknown external/genesis reference type
   - Causal cycle
5. The gate must distinguish delivery-order invariance from basis completeness; both are required.

---

## P2T-03 — High: The required recurring-schedule liveness tests were not delivered

**Affected:** P2S-04; SCH-02; RES-02; `D-KR`; `D-B11`; behavioral simulator

### Problem

The corrected design correctly states that the watchdog owns authoritative recurrence definitions and that rolling `ExpectedRun` records are corroborating evidence. It explicitly promises deterministic tests for:

- Scheduler death after a run but before next-occurrence registration
- Rolling-horizon exhaustion
- Schedule change racing a computed deadline

No such executable test or output exists in the behavioral simulator. The only schedule-specific fixture is A14, which tests an expired scheduled-run control envelope. That does not exercise scheduler death before registration or horizon exhaustion.

The cover's cited watchdog heartbeat/staleness and A14 evidence therefore do not satisfy the precise P2S-04 test obligation.

### Required correction

Add a bounded P2S-04 test suite that independently computes watchdog deadlines from a recurrence specification and proves:

1. The next missed deadline is detected when the scheduler dies before creating any next-run record.
2. Horizon exhaustion produces an early warning before the next scheduled deadline.
3. A versioned schedule change atomically updates the watchdog's expectation and cannot create an orphaned old or missing new deadline.
4. Each case fails under a targeted defect that restores scheduler-self-report dependence or disables horizon monitoring.

---

## P2T-04 — High: Normative supersession remains incomplete and machine checking is too narrow

**Affected:** P2S-02; `D-B1`; `D-B11`; `D-B12`; `D-SM`; `check_supersessions.py`

### Problem

The supersession map is useful, but the authoritative artifacts still contain active conflicting directions.

Examples:

- `D-B1_Record_Shape_Comparison.md` lines 18–26 retain machine-verified and machine-executed claims based on the old circular evidence.
- The same file's active “Reproduction record” at line 44 still instructs the reader to run `gen_shape_traces.py` and `run_fold_comparison.py`, and states that this comparator fails on divergence.
- `D-B11_Ritual_Integration.md` line 59 still makes the scheduler write each `ExpectedRun` at scheduling time as the primary missed-run model, while `D-KR` says that dependency is superseded for liveness.
- `D-B12` contains old completion claims and later withdrawals/closures in the same normative artifact rather than one current, consolidated result surface.

`check_supersessions.py` searches only nine exact literal patterns. It does not detect the active old script names, the active ExpectedRun mechanism, or the old evidence classifications, so its PASS does not prove the design is contradiction-free.

### Required correction

1. Consolidate each normative artifact so it has one current mechanism and one current evidence status.
2. Move historical claims into a clearly non-normative history/errata appendix or preserve them only in the decision trail.
3. Replace D-B1's reproduction record with the current behavioral simulator and current coverage limits.
4. Replace D-B11's primary per-occurrence ExpectedRun text with the watchdog-owned recurrence contract; retain the rolling horizon only as corroboration.
5. Generate supersession checks from the authoritative supersession map rather than a manually incomplete list of nine phrases.
6. Add structural checks for retired artifact paths, retired parameter values, retired evidence labels, and retired mechanism identifiers.

### Closure falsifier

A Builder reading only the current normative artifacts must not be able to implement either the retired or replacement mechanism while remaining textually compliant.

---

## P2T-05 — High: The requirements gate is internally contradictory and semantically overstates closure

**Affected:** P2S-08; P2G-01; `13G`; `13V`; owner decision package readiness

### Problem

The actual 133 matrix rows currently say:

```text
Accepted rows
90 Complete
11 Binding invariant
14 Deliberately deferred
8 Build-gate deferred
2 N/A

DE-R rows
8 Complete
```

The same authoritative matrix ends with:

```text
Complete: 33
Incomplete: 57
DE-R1..DE-R8 all Incomplete
```

Both structural and `--final-gate` validators still return PASS because they validate the row table but do not validate the document's own declared count summary.

More importantly, rows dependent on open findings remain Complete, including:

- SCH-02 despite the missing P2S-04 tests
- DE-R7 despite the missing-causal-basis defect
- RES-02 and related liveness claims while the exact schedule evidence remains incomplete
- P2S-01-dependent evidence rows despite incomplete expected-result comparison

A requirements ledger cannot be the gate's evidence surface while simultaneously presenting two incompatible status snapshots and marking unresolved mechanisms Complete.

### Required correction

1. Remove the stale count/status block or regenerate it directly from the parsed rows.
2. Make `13V` fail when any declared summary count disagrees with the actual matrix.
3. Add a finding-dependency field or machine-readable mapping so a requirement cannot remain Complete while a controlling Critical/High finding against its evidence is open.
4. Reclassify every row dependent on P2T-01 through P2T-04 until its mechanism and evidence are corrected.
5. Regenerate the owner package only after the semantic ledger has been independently reviewed.

---

## P2T-06 — Medium: The “full-history bundle” is not self-contained

**Affected:** packet provenance and independent reproducibility

### Problem

The bundle advertises a complete history and `git bundle verify` repeats that claim, but a fresh clone fails because commit `ffd5cc6ce6626f18de73f671c362806b4a168afe` is missing from the bundle's object closure.

This did not prevent the current semantic review because the current and base commits and exact patch were available. It does prevent the packet from satisfying its stated “full identical history” and fresh-replay claim.

### Required correction

Export a bundle that clones successfully into an empty directory, then record and reproduce:

```text
git bundle verify <bundle>
git clone <bundle> <fresh-dir>
git fsck --full
git rev-parse <candidate>^{tree}
git merge-base --is-ancestor <base> <candidate>
```

The packet validator should run the fresh-clone test rather than relying on `git bundle verify` alone.

---

# 5. Directions That Survived Review

The following mechanisms should be retained:

- Structural separation of input-side stimuli from oracle-only fields.
- Actual candidate event generation and state folding rather than copied fixture narration.
- Effective forbidden-outcome predicates with defect witnesses.
- External execution-receipt ownership.
- Real E2E-1 two-normalizer computation with an authority-leak falsifier.
- The P2S-05 policy/lease linearization model and ACT-01 uncertain-outcome path.
- The P2S-07 default-deny eligibility rule for external-untrusted content.
- Phone-side dead-man alarm plus heartbeat-fresh, short-lived executor leases.
- Watchdog ownership of recurrence definitions and the rolling horizon as a corroborating signal.
- Explicit store priority including the external control journal.
- S1, S2, and S3 remaining viable; storage/projection differences separated from authority policy.
- Dedicated deferral records and structural requirements validation, once their semantic statuses are corrected.

---

# 6. Required Next Packet

Fable should return one bounded correction packet containing:

1. Keyed dispositions for P2T-01 through P2T-06.
2. A Builder-produced oracle-schema and judgement correction proving complete route/attention/authority/receipt comparison.
3. Oracle-mutation tests proving every expected dimension is load-bearing.
4. A fail-closed causal-basis validator and missing-basis test suite.
5. The P2S-04 scheduler-death and horizon-exhaustion test suite.
6. Consolidated, contradiction-free D-B1, D-B11, and D-B12 artifacts.
7. A generated supersession checker derived from the authoritative supersession map.
8. A semantically rebuilt 13G matrix and validator with finding dependencies and self-consistent summaries.
9. A freshly cloneable Git bundle, exact base-to-candidate diff, manifest, and checksums.
10. Proof that the accepted v1.3 Manual and Requirements Register remain byte-unchanged.

No rediscovery is required. Owner decisions are not reopened. The Builder correction should remain narrowly scoped to the simulator/oracle/fold/schedule-test code; Fable owns the normative text, ledger, and packet-provenance corrections.

---

# 7. Gate State

```text
Accepted v1.3 baseline:             UNCHANGED
Accepted Phase 2 discovery:         VALID
Approved CP-P2-A plan:              VALID
Packet file integrity:              PASS
Simulator reproducibility:          PASS
P2S-01:                              OPEN — substantially improved
P2S-02:                              OPEN
P2S-03:                              CLOSED at design level
P2S-04:                              OPEN
P2S-05:                              CLOSED at design-simulator level
P2S-06:                              OPEN
P2S-07:                              CLOSED at design-simulator level
P2S-08:                              OPEN
Design-gate verdict:                FAIL
Recommendation/policy hypothesis:   PLAUSIBLE; not yet proven across full oracle
Record-shape selection:             NOT MADE
DE-R1 through DE-R8 acceptance:     NOT AUTHORIZED
Owner decision package:             BLOCKED
Owner design acceptance:            BLOCKED
Builder correction work:            REQUIRED after Fable disposition/authorization
v1.4 work:                           BLOCKED
Next actor:                         FABLE
Hunter action required now:          NONE
```

---

# 8. Scope and Termination Rule

The next review remains limited to P2T-01 through P2T-06 and any Critical/High defect directly introduced by those corrections.

- Unrelated improvements become later backlog items.
- The verifier will not demand production deployment proof at this design gate.
- The verifier will require the exact machine evidence already promised by the approved plan and prior correction contracts.
- The gate passes when the full expected result is load-bearing, incomplete causal bases fail closed, the two required schedule-liveness tests execute, the normative design is internally singular, and the requirements ledger truthfully reflects the evidence.
