# 20 — ChatGPT Scoped Re-Verification: P2T Correction Packet 4

**Role:** Independent verifier  
**Scope:** P2T-01 through P2T-06 and any Critical/High defect directly introduced by their corrections  
**Packet reviewed:** `P2T_Correction_Packet_4.zip`  
**Packet SHA-256:** `c6a9c18b370182087b4a88e9b2ce3082736115b91179a1fe2da3fb00c9a01798`

## 1. Verdict

# **FAIL — design gate remains open**

The packet is mechanically strong and the correction cycle is clearly converging. P2T-06 closes, and P2T-01 through P2T-05 are materially improved. However, independent falsifier probes found five High-severity defects in the corrected enforcement mechanisms:

1. Receipt expectations classified as `mapped` can still pass without any comparison to computed presentation behavior.
2. A nonexistent causal dependency can still be accepted by relabelling it as an `external_basis` reference to an allowed store.
3. A versioned schedule change leaves the prior version's materialized horizon active, allowing stale records to suppress the new version's horizon-exhaustion warning.
4. The normative ritual and gate-report documents still contain mutually incompatible current mechanisms and status snapshots despite the supersession checker reporting PASS.
5. The final-gate validator can pass while six findings marked `blocks_gate: true` remain open, and can also pass when the open-findings file is absent.

No rediscovery, owner-decision reopening, or architecture restart is required. Fable should disposition P2U-01 through P2U-05 and issue one narrowly bounded correction cycle.

---

## 2. Independent packet and repository verification

### 2.1 Packet integrity

- ZIP SHA-256: `c6a9c18b370182087b4a88e9b2ce3082736115b91179a1fe2da3fb00c9a01798`
- `checksums.sha256`: **54/54 passed**
- `EXPORT_MANIFEST.json`: **54/54 declared payload hashes passed**
- No undeclared payload file was found

### 2.2 Git provenance

The supplied full-history bundle cloned successfully and passed full object verification.

```text
Candidate commit
bbc58dc6f5d5aed6f1f947a1c92beb7853747044

Candidate tree
977eea7231b8f03e7a45c2dec237d9af8da92f69

Required ancestry
20ad093  ancestor: yes
68f768d  ancestor: yes
ffd5cc6  ancestor: yes
```

The fresh checkout was clean. `git diff --check 68f768d..HEAD` passed. The supplied patch was byte-identical to an independently generated standard binary Git diff:

```text
SHA-256
ad07c51a5b86ed5a06ef8192b37cd141af7a7e04d0a4c0fd0eb73c32e2e2f8b2
```

### 2.3 Supplied test reproduction

The complete behavioral gate ran twice with byte-identical outputs. The supplied suite reported:

- **81/81** candidate/fixture combinations computed
- **19/19** supplied gate criteria PASS
- **9/9** named defect classes effective
- **56/56** forbidden predicates defect-reachable
- **81/81** combinations invariant across six causal-preserving permutations
- **5/5** P2S-05 linearization traces discriminating
- **2/2** P2S-07 tests PASS
- **11/11** policy-composition cases discriminating
- **8/8** supplied missing-basis cases rejected
- **3/3** supplied P2S-04 behaviors discriminating
- Supersession checker and self-test: PASS
- Matrix structural validator and self-test: PASS
- Current matrix `--final-gate`: correctly FAILS while its four row dependencies remain incomplete

These results establish deterministic execution and faithful reproduction of the supplied evidence. They do not cure the independent probes below.

---

## 3. Controlling-finding dispositions

| Finding | Scoped disposition | Reason |
| --- | --- | --- |
| **P2T-01** — complete expected result not enforced | **OPEN; substantially narrowed** | Route, authority, attention, and most receipt semantics now carry real checks. Five presentation-kind receipt values are nevertheless classified as mapped and counted as compared even though no computed presentation value is evaluated. |
| **P2T-02** — incomplete causal basis accepted | **OPEN; substantially improved** | Missing direct and transitive `caused_by` references now fail. An unresolved external dependency still folds when its string merely uses an allowed store prefix. |
| **P2T-03** — recurring-schedule liveness evidence missing | **OPEN; substantially improved** | The three promised synthetic tests now exist. The schedule-change test does not inspect the actual materialized horizon, and the implementation leaves prior-version horizon entries eligible. |
| **P2T-04** — normative supersession incomplete | **OPEN; substantially improved** | The map-driven checker and structural families are useful, but D-B11 and D-B12 still contain active contradictory mechanisms/status snapshots that the checker misses. |
| **P2T-05** — requirements gate internally contradictory/fail-open | **OPEN; substantially improved** | Row-derived counts and dependency checks work in the current state. The final gate does not globally honor `blocks_gate: true` and does not fail when the findings file is absent unless a row happens to name a finding. |
| **P2T-06** — non-self-contained bundle | **CLOSED** | The unshallowed bundle cloned into an empty directory, passed `git fsck --full`, contained the required ancestors, and reproduced the declared commit and tree. |

---

## 4. New findings

### P2U-01 — High — Presentation receipt expectations are reported as mapped and compared but are no-ops

**Affected:** P2T-01; `oracle_schema.py`; `judge.py`; `run_oracle_mutations.py`; gate criteria 16 and 17

#### Problem

`KIND_PRESENTATION` is included in `MAPPED_KINDS`. `parse_receipt()` returns that kind for values such as:

```text
Desk view
Desk brief line
Mailroom brief
reconnect brief
monthly digest
```

Those expectations contain only a `surface` string. `_compare_dimension()` checks `requires` and `forbids`, then contains special comparisons only for route and authority. It never compares `surface` or any computed receipt-presentation field. With empty `requires` and `forbids`, the presentation expectation returns success and is counted as mapped/compared.

#### Independent falsifier

I changed only S1's frozen expected receipt:

```text
Desk view
→ completely wrong card
```

and separately:

```text
Desk view
→ completely wrong summary surface
```

Both remain recognized `PRESENTATION` values. The complete gate returned exit code 0 and `GATE PASS`; all three candidate shapes reported the receipt dimension as mapped.

The supplied contradictory-witness routine proves that *some* borrowed wrong value can fail, often because it changes the expectation kind or adds a structural feature. It does not prove that the original presentation value is evaluated.

#### Required correction

Use one truthful model:

1. **Preferred:** compute a presentation/receipt-surface value on the engine side and compare exact or explicitly allowed surfaces on the oracle side; add same-kind mutations that must fail.
2. If presentation is intentionally outside this design simulator, classify these values as explicitly unmappable/not simulated, remove them from compared counts, and state the limitation without calling them load-bearing.

Add a gate invariant:

> A `mapped` expectation must execute at least one nonempty comparison or required/forbidden feature check. A mapped expectation with an empty comparator fails the gate.

---

### P2U-02 — High — `external_basis` is an unresolved-reference bypass

**Affected:** P2T-02; `events.py`; `fold.validate_basis()`; replay-basis contract

#### Problem

The validator checks only whether an `external_basis` string begins with one of four allowed store names. It does not establish that the referenced external object:

- exists;
- belongs to the frozen replay snapshot;
- has the named version or content hash;
- was independently verified; or
- is available through an authoritative resolver.

#### Independent falsifier

For each of these values:

```text
control-journal:definitely-missing
evidence:definitely-missing
provider:definitely-missing
schedule:definitely-missing
```

I created one non-genesis `DecisionEvent` with no `caused_by` event and that value as its sole `external_basis`.

The result in every case was:

```text
validate_basis problems: []
fold accepted: true
fold order: [decision-ext]
causal violations: []
```

The incomplete-basis defect therefore remains available through a different field.

#### Required correction

An external basis reference must be resolved against a supplied, hash-bound external-basis snapshot or resolver result before fold. It should identify, at minimum:

```text
store
object/event ID
version or content hash
verification receipt
```

Missing, mismatched, unavailable, or unverified external references must fail before state emission. If no external resolver belongs in this design-gate harness, fail closed on every `external_basis` use and mark external-basis replay as build-gate deferred.

Add tests for nonexistent object, wrong version/hash, omission from the frozen external manifest, valid resolved reference, and unavailable/degraded resolver.

---

### P2U-03 — High — A schedule change can retain a stale prior-version horizon

**Affected:** P2T-03; `run_p2s04.py`; D-KR P2S-04 rules 2–3; D-B11

#### Problem

`Watchdog.change_schedule()` updates the recurrence specification but does not version, invalidate, clear, or regenerate `expected_runs`. `horizon_exhausted()` then reads the unversioned materialized list. The supplied atomic-change test computes expectations directly from the new spec and never inspects the watchdog's actual horizon state.

#### Independent falsifier

```text
1. Register v1.
2. Materialize v1 ExpectedRun records far into the future.
3. Atomically change to v2.
4. Simulate the scheduler dying before extending the v2 horizon.
```

Observed:

```text
current spec version:       2
materialized horizon:       still v1
horizon warning at v2 start: None
```

The old v1 horizon falsely satisfies the current v2 early-warning check. This conflicts with the normative claim that versioned schedule changes create no orphaned old or missing new expectation.

#### Required correction

ExpectedRun horizon records must be version-bound. The governed schedule-change transaction must make old-version horizon entries ineligible immediately and establish the new version's horizon state atomically. If the scheduler does not extend the v2 horizon, the watchdog must warn even when v1 had ample future coverage.

Add the combined discriminating test:

```text
v1 horizon extends far ahead
→ atomic change to v2
→ scheduler dies before extending v2
→ v1 entries cannot satisfy v2 coverage
→ v2 horizon-exhaustion warning fires
```

---

### P2U-04 — High — The supersession checker passes while active normative contradictions remain

**Affected:** P2T-04; D-B11; D-B12; D-SM; `check_supersessions.py`

#### Problem

The corrected checker is materially better, but the closure falsifier still fails: a Builder can read mutually incompatible current instructions while remaining textually compliant.

Examples:

- **D-B11 line 11** says a missed/failed scheduled run “emits its own DegradationEvent-class notice.” Lines 25 and 36–59 later say that self-report mechanism is circular and superseded by watchdog-owned recurrence. The first statement remains in the current envelope definition rather than a marked non-normative history block.
- **D-B12** retains multiple incompatible current-status snapshots. Its early section reports 35 Complete/55 Incomplete and all DE-R rows Incomplete; later line 63 reports 90 Complete and all DE-R rows Complete with `--final-gate PASS`; line 88 repeats the stale 90/8 Complete snapshot. These blocks are not consolidated into one current surface and one clearly non-normative history appendix.

The checker reports PASS because its map-derived and structural patterns do not cover these contradictions.

#### Required correction

1. Replace D-B11's active self-report sentence with the watchdog-owned mechanism; retain the historical statement only in a clearly marked non-normative history/errata block.
2. Rebuild D-B12 as one current result surface generated from or directly linked to the authoritative matrix and gate output. Move prior snapshots into a clearly non-normative appendix or the decision trail.
3. Extend the checker so the exact retired self-report mechanism and stale current-status declarations cannot survive unmarked.
4. Add a self-test that seeds each of these contradiction classes and proves the checker fails.

---

### P2U-05 — High — The final-gate validator ignores globally blocking findings

**Affected:** P2T-05; `13F_Open_Findings.json`; `13V_validate_design_matrix.py`; owner-gate integrity

#### Problem

`13F_Open_Findings.json` marks all six P2T findings:

```json
"blocks_gate": true
```

But `--final-gate` checks an open finding only when a matrix row explicitly names it in the dependency cell. The findings file is not itself a global gate input. If dependency cells are accidentally or deliberately cleared, the open findings stop blocking. If the findings file is absent and no row names a finding, the gate also passes.

#### Independent falsifier

In a temporary copy, I changed APP-04, RES-02, SCH-02, and DE-R7 to `Complete`, cleared their dependency cells, and regenerated the declared count summary. The six findings remained present and `blocks_gate: true`.

Result:

```text
13V_validate_design_matrix.py --final-gate
exit code: 0
open findings reported: 6 gate-blocking
verdict: PASS
```

I then removed `13F_Open_Findings.json` entirely. The same final-gate command again returned exit code 0 and PASS.

The validator's own self-test explicitly defines “no row names a finding, list unavailable” as PASS, confirming that this is designed behavior rather than an incidental bug.

#### Required correction

Under `--final-gate`:

1. Absence, unreadability, or schema failure of the open-findings file must always fail closed.
2. Every finding with `blocks_gate: true` must block globally until its authoritative disposition is closed, regardless of whether a requirement row cites it.
3. Row dependencies remain required for traceability and semantic reclassification, but they are not the sole gate mechanism.
4. Add self-tests for:
   - open global finding with no row dependency;
   - missing findings file with no row dependency;
   - malformed findings file;
   - closed/nonblocking findings only;
   - row dependency referencing a missing finding ID.

---

## 5. Required correction packet

Fable should disposition P2U-01 through P2U-05 and issue narrowly scoped Builder work for:

1. truthful receipt-presentation comparison/accounting;
2. externally resolved causal-basis validation;
3. version-bound schedule horizons and the combined stale-horizon test;
4. globally fail-closed open-finding enforcement.

Fable should own the D-B11/D-B12 consolidation and corresponding D-SM updates. The next packet should contain:

- keyed dispositions;
- the exact corrected code and normative artifacts;
- same-kind oracle mutation evidence;
- external-basis resolution tests;
- combined version-change/horizon test;
- supersession self-tests covering the remaining contradictions;
- global open-finding fail-closed tests;
- updated matrix dependencies and truthful gate output;
- exact diff, cloneable bundle, manifest, checksums, and unchanged-v1.3 proof.

The next review remains scoped to these five findings and any Critical/High defect directly introduced by their corrections. P2T-06 should not be reopened absent contradictory evidence.

---

## 6. Gate state

```text
Accepted v1.3 baseline:             UNCHANGED
Accepted Phase 2 discovery:         VALID
Approved CP-P2-A plan:              VALID
Packet integrity:                   PASS
Supplied test reproduction:         PASS
P2T-06:                             CLOSED
P2T-01 / P2U-01:                    OPEN — HIGH
P2T-02 / P2U-02:                    OPEN — HIGH
P2T-03 / P2U-03:                    OPEN — HIGH
P2T-04 / P2U-04:                    OPEN — HIGH
P2T-05 / P2U-05:                    OPEN — HIGH
Design-gate verdict:                FAIL
Record-shape selection:             NOT MADE
DE-R1 through DE-R8 acceptance:     NOT AUTHORIZED
Owner decision package:             BLOCKED
Owner design acceptance:            BLOCKED
Builder correction work:            REQUIRED after Fable disposition
v1.4 work:                          BLOCKED
Next actor:                         FABLE
Hunter action required now:          NONE
```

The correction cycle remains bounded and convergent. The remaining defects are five explicit enforcement and record-integrity boundaries, not a rejection of the operating philosophy, discovery conclusions, or owner decisions.
