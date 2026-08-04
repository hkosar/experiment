# 31 — ChatGPT Independent Security Review: TASK-0007 R2+R3 Wrapper Stub

**Reviewer:** ChatGPT, independent verifier  
**Review target:** `poc/stub/stub_server.py`  
**Governing request:** `30_ChatGPT_Independent_Security_Review_Request_R2_R3_Stub.md`  
**Review type:** Terminal independent security gate before Hunter's hands-on provider POC session  
**Packet SHA-256:** `60ae30f709f4f30b7c287329636a4efc73cfecda5ba11245dc4d7eba33d54359`

## 1. Verdict

**FAIL — the owner POC session remains blocked.**

The stub materially improves the R1/R2 apparatus, and the two explicitly requested amendments are correctly reflected in the implementation. The new `Disclose` response-only mechanism also survived the requested direct attacks.

The end-to-end authority boundary is nevertheless not safe under the actual threaded HTTP surface. Independent concurrency probes produced each of the following:

- Two registrations for one registration identity.
- Two review cases and two resume tokens for one submission identity.
- Two ActionRequests and two execution capabilities from one resume token.
- Two non-replay delivery receipts from one supposedly single-use capability.
- A successful owner revocation followed by a successful delivery that overwrote the revoked state.
- Two POC-3 runs for one schedule occurrence.

The central POC claim—*the provider can carry a paused approval but cannot make or execute the decision itself*—therefore fails under concurrent requests. A single owner approval can amplify into multiple authority artifacts and multiple represented side effects.

This is bounded stub rework. It does **not** reopen the Release-1 definition, Capability Portfolio work, provider selection, Decision Engine design, v1.4 baseline, or production-wrapper architecture.

## 2. Packet and Baseline Verification

An untouched extraction produced:

```text
Packet SHA-256
60ae30f709f4f30b7c287329636a4efc73cfecda5ba11245dc4d7eba33d54359

SHA256SUMS.txt
58 / 58 passed

Authority manifest
57 / 57 file hashes passed
Exactly one governing instruction

Target stub SHA-256
7f13494ee510ef6e863f7324680832a582fb075f6d6ccf4442b379345b90f572

Declared base tree
bc940604315f27b6c9cce6fe9a0b42c87d8b758c

Independently reconstructed base tree
bc940604315f27b6c9cce6fe9a0b42c87d8b758c
```

The Builder-authored suites reproduced as claimed:

```text
R3 self-test
167 / 167 passed

Pinned R1/R2 witness suite
34 / 34 passed

Measurement validator
160 / 160 passed
```

The full n8n structural harness could not run because `n8n-nodes-base` was unavailable in the review environment. The packet disclosed that limitation in advance; this review does not convert that environment limitation into a new finding.

## 3. Requested Attack-Surface Dispositions

### 3.1 `Disclose` response-only redaction exemption

**Disposition: PASS for the current code paths.**

The HTTP response delivered the service-minted resume token and capability as usable strings. Neither appeared in capture files or route logs. The only two `Disclose` construction sites are the service-minted resume token and execution capability (`stub_server.py:1085-1089`, `1185-1190`). Provider JSON cannot instantiate the Python `Disclose` type, and a fake JSON object shaped like one remained ordinary untrusted data. Capture and log paths use `disclose=False` (`312-365`, `475-535`), while the HTTP response alone uses `disclose=True` (`1875-1892`).

This is not a permanent proof against future unsafe call sites. The Builder's stated limitation remains valid: every newly added `Disclose` construction site needs review and a regression test.

### 3.2 R3 analogue of the R2 layer mismatch

**Disposition: FOUND — gate-blocking.**

The sequential in-process tests pass, but the caller-visible `ThreadingHTTPServer` permits concurrent requests (`1964-1968`). Several handlers perform a protected read, release the lock, then create and commit a new authority object. The tested sequential layer therefore differs materially from the concurrent HTTP layer a provider actually meets.

### 3.3 A.4 `UNCERTAIN` amendment

**Disposition: PASS.**

Provider-reported `uncertain` remains corroborating evidence only and does not move capability state. `/poc1/reconcile` returns an uncertain reconciliation result without inventing `RECONCILED_NOT_DELIVERED`; the actual capability remains in its valid state unless the service-established transition conditions apply (`1350-1411`, `1417-1470`).

### 3.4 A.7 prepared/committed evidence ordering

**Disposition: FAIL outside the enumerated happy-path tests.**

Independent fault injection found success evidence for state that never became effective, state changes with no transition evidence, and capture writes that can leave an empty final artifact while consuming quota.

### 3.5 Outcome-coverage guard

**Disposition: INSUFFICIENT AS SECURITY EVIDENCE.**

The guard proves that every source outcome label appears in at least one test. It does not prove that the correct branch produced the correct outcome for each security scenario. The concurrency failures all coexist with a 167/167 suite and a green outcome-coverage result.

## 4. Findings

### SEC-R3-01 — Critical — Authority and idempotency transitions are not linearizable

**Affected surfaces**

- `POST /owner/artifact/register`
- `POST /poc1/review-case`
- `POST /poc1/verify-decision`
- `POST /relay/deliver`
- `POST /poc3/run-started`

**Problem**

Each flow checks the prior state under a lock, releases or exits the critical section, performs additional work, and later writes the new state. Two concurrent requests can both observe the same precondition and both become effective.

**Code evidence**

- Artifact registration checks `reg_by_identity` at `stub_server.py:740-747`, then creates and inserts the record later at `748-761`.
- Review-case duplicate detection occurs at `1039-1053`, while case/token creation and identity publication occur later at `1059-1084`.
- Token validity is read under a lock at `1099-1107`, but token consumption occurs only after capability minting at `1179-1184`.
- Relay state and prior receipt are read at `1193-1224`, while attempt, status, and receipt state are committed in later critical sections at `1264-1321`.
- Run duplicate detection occurs at `1621-1636`, while run publication occurs later at `1640-1661`.

**Independent observations**

```text
One registration identity
→ 2 x 200 registered
→ 2 registration records

One POC-1 submission identity
→ 2 x 200 case-opened
→ 2 cases
→ 2 resume tokens

One resume token
→ 2 x 200 authorized
→ 2 ActionRequest IDs
→ 2 execution capabilities

One execution capability
→ 2 x 200 delivered
→ 2 distinct receipt IDs
→ both replayed=false

One schedule occurrence
→ 2 x 200 run-started
→ 2 run IDs
```

A separate 50-thread token probe also produced seven authorizations from one token before connection saturation, but the deterministic two-request barrier tests above are the controlling evidence.

**Required correction**

Implement one linearizable transition mechanism per subject identity:

- Atomic insert-if-absent for registrations, cases, and run declarations.
- Atomic token claim/spend before minting an ActionRequest.
- Atomic capability claim/lease before execution.
- A single transition lock or compare-and-swap boundary covering precondition, reservation, evidence preparation, state publication, and terminal result.
- Deterministic concurrent live-HTTP tests proving one winner and bounded, truthful loser outcomes.

A global lock is acceptable for this throwaway stub. Production scalability is not required at this gate.

---

### SEC-R3-02 — Critical — An acknowledged owner revocation can lose to an in-flight delivery

**Problem**

The owner can receive a successful `REVOKED` response while an already admitted relay continues and later writes `DELIVERED_WITH_RECEIPT`, replacing the revocation.

`h_owner_revoke` changes status and commits the revocation at `stub_server.py:899-921`. `h_relay_deliver` checks status near the start at `1193-1209`, then performs a long multi-step flow and sets the terminal delivered state at `1295-1321` without a final revocation/epoch check.

**Independent observation**

```text
Owner revoke response
200 / REVOKED

Concurrent relay response
200 / delivered

Final capability status
DELIVERED_WITH_RECEIPT
```

**Required correction**

Choose and implement a clear linearization rule:

- A capability execution claim obtains an execution lease/epoch.
- Owner revocation atomically increments a revocation epoch or cancels an uncommitted lease.
- The relay revalidates authority at the represented side-effect linearization point.
- Once revocation returns success, no later delivery may become effective under the revoked generation.

Add a deterministic barrier test for revoke-before-commit, revoke-after-claim, and revoke-after-delivery.

---

### SEC-R3-03 — High — Evidence can assert transitions that never became effective

**Problem**

Two independent fault probes produced durable success evidence for authority/state that did not exist after the request failed.

**Case creation**

`h_poc1_review_case` writes a single-phase `case-opened` capture before minting the resume token (`stub_server.py:1065-1077`). When token minting was forced to fail, no case existed, but the capture still said `outcome: case-opened`.

**Capability mint**

`h_poc1_verify_decision` commits the `capability-mint` transition before admitting the new capability into the live-secret index (`1156-1178`). When secret-index admission was forced to fail, no capability remained and the token remained unspent, but a committed record still stated `final_status: MINTED`.

**Required correction**

- Reserve all required capacity—including secret-index capacity—before writing committed success evidence.
- Treat case creation as an authority-bearing transition with prepared/provisional/committed semantics, or write only a refusal/aborted record when token minting fails.
- Make committed evidence describe the final effective state, not an intermediate state that may still be rolled back.
- Add fault injection after every prerequisite/reservation boundary, not only after the six named capture writes.

---

### SEC-R3-04 — High — State mutations occur outside the prepared/committed transition contract

**Problem**

At least two operational state changes can occur without matching transition evidence.

**Expiry**

`_expire_if_due` changes a capability to `EXPIRED` and discards its secret directly (`stub_server.py:892-896`). The independent probe observed no expiration transition or expiration-named capture.

**POC-3 stage attempt**

`h_stage_deliver` increments the attempt counter before writing its capture (`1745-1756`). When the capture failed, the request returned `capture-failed`, but the counter remained incremented; the next successful call reported attempt 2.

**Required correction**

- Route expiry through an explicit evidence-backed transition, or define it as a derived state whose source time/expiry record is authoritative and whose reconciliation is deterministic.
- Move stage-attempt mutation behind successful evidence commit or roll it back on capture failure.
- Inventory every mutable field and prove it is either derived, non-authoritative telemetry, or governed by the A.7 transition contract.

---

### SEC-R3-05 — High — Capture writes are not crash-atomic and leak quota on failure

**Problem**

`write_capture` reserves quota first (`stub_server.py:497-505`) and pre-creates the final path as an empty file (`537-551`) before writing a separate temporary file and replacing it (`552-562`).

A forced I/O failure while opening/writing the temporary path left:

```text
one zero-byte final .json file
one general-pool quota unit consumed
```

The record is neither valid committed evidence nor absent. The counter is not rolled back.

**Required correction**

- Allocate a unique temporary file with exclusive creation.
- Write, flush, and fsync the temporary file.
- Atomically rename it to a final path that did not previously exist.
- Fsync the directory.
- Remove any temporary artifact on failure.
- Increment the pool counter only after successful publication, or roll the reservation back on failure.
- Add crash/fault tests at filename allocation, open, write, flush, fsync, rename, and directory-fsync boundaries.

---

### SEC-R3-06 — High — Route-policy entity quotas are not uniformly enforced

**Problem**

The route table declares entity quotas, but enforcement is handler-specific rather than guaranteed by dispatch. Several handlers accept work after the declared store has already reached its ceiling.

Independent probes set the relevant counters/stores to their maximums and observed:

```text
/poc1/refusal with receipt_count == MAX_RECEIPTS
→ 200 recorded

/poc3/receipt with receipt_count == MAX_RECEIPTS
→ 200 recorded

/poc2/triage with len(ideas) == MAX_IDEAS
→ 200 staged
```

`_quota_ok` defines the ceilings (`stub_server.py:686-701`), but dispatch does not enforce the route's `quota` value centrally (`1800-1855`), and the affected handlers omit the check or do not increment the authoritative count.

**Required correction**

- Enforce each route-policy entity quota centrally before handler execution, unless the policy explicitly declares `none`.
- Reserve capacity atomically with the state transition and release it on failure.
- Define what is being counted for evidence-only receipts/refusals and POC-2 staged ideas.
- Add one over-capacity negative test per non-`none` route-policy quota.

---

### SEC-R3-07 — Medium — Outcome coverage is label coverage, not branch correctness

**Problem**

The self-test's outcome guard proves only that every source-emitted outcome code appears somewhere in the suite. It cannot prove that:

- The intended case produced that outcome.
- The transition occurred exactly once.
- The caller-visible HTTP result matches the in-process result.
- Concurrency preserves the same semantics.

The entire suite and outcome guard passed while the Critical races above remained reachable.

**Required correction**

Keep the label-coverage guard as a completeness aid, but do not count it as security correctness evidence. For security-relevant routes, bind each scenario to:

```text
starting state
request and authenticated caller
expected status
expected outcome
expected state delta
expected evidence delta
forbidden state/evidence outcomes
concurrency cardinality
```

The gate should compare the observed branch-specific result with that oracle.

## 5. Required Rework Packet

Fable should disposition `SEC-R3-01` through `SEC-R3-07` and issue one narrow Builder rework packet covering:

1. Linearizable registration, case, token, capability, and run transitions.
2. Revocation/execute ordering and final authority recheck.
3. Truthful commit ordering for case creation and capability minting.
4. Evidence-backed expiry and rollback-safe stage attempts.
5. Crash-atomic capture publication and quota rollback.
6. Central route-policy quota enforcement.
7. Branch-specific, live-HTTP, concurrent acceptance tests.

The rework acceptance suite must include deterministic barriers; probabilistic stress tests alone are insufficient.

## 6. Gate State

```text
Packet integrity:                      PASS
Builder self-test reproduction:        PASS
Pinned witness reproduction:           PASS
Measurement-validator reproduction:    PASS
Current Disclose implementation:        PASS
A.4 amendment:                          PASS
A.7 evidence contract:                  FAIL
Caller-visible concurrent boundary:     FAIL
R2+R3 stub security gate:               FAIL
Owner hands-on POC session:             BLOCKED
Provider selection:                     NOT MADE
Release-1 definition:                   UNCHANGED
Decision Engine / v1.4 baseline:        NOT REOPENED
Hunter action required now:             NONE
Next actor:                              FABLE
```

The standing separation remains unchanged: Fable owns architecture, dispositions, and project management; the Builder implements the bounded correction; ChatGPT independently re-verifies; Hunter retains final authority.
