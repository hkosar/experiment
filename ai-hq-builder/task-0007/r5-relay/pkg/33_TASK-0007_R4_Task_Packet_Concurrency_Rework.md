# 33 — TASK-0007 Round R4: concurrency and evidence-ordering rework of the R2+R3 stub

**Context.** The independent security review of the completed R2+R3 stub returned **FAIL** (`31_`), concurred in full (`32_`). The `Disclose` exemption and the A.4 amendment passed; the Builder's 167/167 / 34/34 / 160/160 were independently reproduced. The failure is a single systemic defect: **the stub's authority transitions are not linearizable under the threaded HTTP server a provider actually meets** — every transition reads state under a short lock, releases it, works, and commits later, so two concurrent requests both pass the precondition and both become effective. This is the R3 analogue of DEF-R2-01: the tested (single-threaded, in-process) layer differs from the caller-met (concurrent HTTP) layer.

**This is bounded rework on the integrated R3 baseline, not a redesign.** No contract clause in `25_` changes. Throwaway POC apparatus, no Track B credit, every THROWAWAY marker preserved. **Read `32_` and `31_` first; the reviewer's per-finding "Required correction" bullets and its probe scripts (shipped at `31_security_probes/`) are authoritative inputs.**

## 0. Snapshot, manifest, allowlists — unchanged from `25_` §0

Same allowlists, same immutable denylist (now including both `r1_reference/` and `r2_reference/`), same Fable-published authority manifest, same snapshot-only base binding with the tree-reproduction recipe. `authority_manifest.json` is not Builder-editable. `poc/data/validate_measurements.py` remains allowlisted. **`25_` is the governing contract and is unchanged; this packet is a build instruction against it.**

## 1. The one architecture decision (made here, not delegated)

**SELECTED: one linearizable transition per subject identity, enforced by a single global transition lock held across the entire critical path** — precondition check, capacity/secret reservation, evidence preparation, state publication, and terminal result. The reviewer explicitly authorized this for a throwaway stub (*"A global lock is acceptable… Production scalability is not required at this gate"*). Do **not** implement per-shard or lock-free schemes; a throwaway POC wants the simplest thing that is provably correct, and a single lock held for the whole transition is that.

The rule, binding on every handler that changes authority state:

> A transition holds the global lock continuously from the moment it reads its precondition to the moment it has published its new state and written its `committed` evidence. Nothing that another concurrent request could observe or race against happens outside that held lock. If any step inside can fail (a capture write, a quota reservation, a secret-index admission), it is attempted while holding the lock and either completes the transition or rolls the whole transition back with no observable effect and no consumed resource.

Where a capture write must not hold the global lock for its full fsync duration, the permitted pattern is: **reserve** (under lock) → **prepare/fsync the evidence** (may release the lock for I/O) → **re-acquire the lock, re-check the precondition still holds, publish, commit**. A precondition that changed while the lock was released aborts the transition. This preserves linearizability without holding the lock across disk I/O.

## 2. Per-finding corrections (all required)

**SEC-R3-01 — linearize registration, case, token, capability, run.**
- **Insert-if-absent under one held lock** for: artifact registration (`reg_by_identity`), review-case (`by_identity` → case + token published atomically), and run declaration (`(schedule_id, occurrence)`). The duplicate check and the publish must be the same critical section; a loser returns the winner's suppressed-duplicate result, not a second artifact.
- **Atomic token claim-and-spend before minting an ActionRequest:** the token is marked consumed in the same held lock that reads it valid, before any capability is minted. A second concurrent verify sees it already consumed.
- **Atomic capability claim/lease before execution:** `/relay/deliver` claims the capability (marks it in-use / leases it) under the held lock at the start, so a second concurrent delivery on the same capability cannot also pass the precondition.
- Deterministic two-request barrier tests (per §4) must show **exactly one winner** and a truthful loser for each of the five identities.

**SEC-R3-02 — revoke vs deliver ordering.**
- Give each capability a **revocation epoch or lease generation**. `/relay/deliver` claims a lease/epoch at the start (under the held lock); `/owner/revoke` atomically increments the epoch / cancels an uncommitted lease. **The delivery re-validates authority at the terminal commit point**: if the capability was revoked (epoch advanced) after the claim, the delivery does not become effective and returns a truthful non-delivery. **Once `/owner/revoke` has returned success, no later delivery may commit under the revoked generation.**
- Barrier tests for revoke-before-claim, revoke-after-claim-before-commit, and revoke-after-delivery.

**SEC-R3-03 — evidence must describe only effective state.**
- **Reserve all capacity before writing committed success evidence** — including secret-index capacity for a capability mint. If secret-index admission can fail, reserve the slot before the `capability-mint` `committed` record, and roll the record back (or never write it) on failure.
- **Case creation is an authority-bearing transition:** either give `/poc1/review-case` prepared/provisional/committed semantics, or — the simpler acceptable form — write the `case-opened` capture **only after** the token is successfully minted and the case published, and on token-mint failure write a refusal/aborted record instead of `case-opened`. A committed record must never describe a case that does not exist.

**SEC-R3-04 — no state mutation outside the transition contract.**
- **Expiry:** route `_expire_if_due` through an explicit evidence-backed `EXPIRED` transition, **or** make `EXPIRED` a *derived* state computed from an authoritative `expires_at` with no in-place mutation and no secret discard outside a recorded transition. Pick one and state which; a silent status flip with a discarded secret and no capture is not acceptable.
- **Stage attempt:** move the `stage_attempts` increment **behind** the successful capture commit, or roll it back on capture failure. A `capture-failed` response must not leave the counter advanced.
- **Inventory every mutable field** on `STORE` and prove each is one of: derived, non-authoritative telemetry, or governed by the A.7 transition contract. Ship that inventory in the Delivery Record.

**SEC-R3-05 — crash-atomic capture with quota rollback.**
- **Do not pre-create the final path.** Allocate a unique temp file with exclusive creation; write, flush, fsync; atomically rename onto a final path that did not previously exist; fsync the directory; remove any temp artifact on failure.
- **Increment the pool counter only after successful publication**, or roll the reservation back on failure. A failed capture must leave **no** zero-byte final file and **no** consumed quota unit.
- Fault tests at each boundary: filename allocation, open, write, flush, fsync, rename, directory-fsync.

**SEC-R3-06 — central entity-quota enforcement.**
- Enforce each route-policy **entity quota at dispatch, before the handler runs**, unless the route's policy is `none`. Reserve capacity atomically with the transition; release on failure.
- Define precisely what is counted for the evidence-only receipt/refusal routes and for POC-2 staged ideas (the counter that gates them must be the one that actually increments).
- One over-capacity negative test per non-`none` route-policy quota — including `/poc1/refusal`, `/poc3/receipt`, `/poc2/triage`, which the probes showed accepting work past ceiling.

**SEC-R3-07 — a branch-specific acceptance oracle.**
- Keep the outcome-coverage guard as a **completeness aid**; it is no longer counted as security evidence.
- For every security-relevant route, bind each test scenario to an oracle: `{starting_state, request + authenticated caller, expected_status, expected_outcome, expected_state_delta, expected_evidence_delta, forbidden_state/evidence_outcomes, concurrency_cardinality}`. The gate compares the observed branch-specific result against that oracle, over **live HTTP**.

## 3. What must NOT change

- No `25_` contract clause. The authority model, the `Disclose` mechanism, the A.4 amendment, the three capture pools, the measurement contract — all stand. This round makes them hold under concurrency; it does not alter them.
- The immutable denylist: `r1_reference/` and `r2_reference/` stay byte-identical with their run-time pins; harness code untouched; `authority_manifest.json` Fable-owned.
- The `Disclose` exemption passed and is not to be broadened. If a correction adds a new `Disclose` construction site, it must be justified and regression-tested (the Builder's own standing caveat).

## 4. Required tests — deterministic barriers over live HTTP

The acceptance suite must include, and demonstrate failing against the current build (via the pinned R3 artifact, the witness method):

- **The reviewer's own probe scripts** (`31_security_probes/`) run green against the reworked build: `http_race_probes`, `http_authority_races`, `http_revoke_race`, `more_race_probes`, `security_probes`, `stage_precise_probe`, `capture_atomicity_probe`, `quota_enforcement_probe`, with `control_probes` still green.
- **Deterministic two-request barrier tests** (not stress) for each of: one registration identity → one record; one submission identity → one case + one token; one resume token → one ActionRequest + one capability; one capability → one delivery receipt; one schedule occurrence → one run; revoke-vs-deliver in all three orderings.
- **Fault-injection** at every reservation/prerequisite boundary named in SEC-R3-03/04/05, not only the six original capture boundaries.
- **Over-capacity** negative test per non-`none` entity quota.
- The branch-specific oracle (SEC-R3-07) for every security route.

Probabilistic stress alone is insufficient (reviewer §5); barriers are required. Pin the R3 artifact the same way `r2_reference/` is pinned so "demonstrated failing" runs against the exact build the review examined.

## 5. Allowlist, return, stop-and-report

Allowlist and denylist per `25_` §0 (unchanged). The concurrency rework is confined to `poc/stub/stub_server.py` and its tests (`selftest_stub.py`, `r1_witnesses.py`, plus a new pinned `r3_reference/` mirroring the `r2_reference/` pattern if §4's "demonstrated failing against R3" needs it — that is a **permitted allowlist addition** under the same AUDIT-4 precedent Fable already accepted, listed explicitly in the return manifest). `harness/out/**` and `stub/out/**` regenerate by running. No `13B_` obligation; no workflow re-aim (the workflows are unchanged this round).

Return: Delivery Record with the reflexive falsifier; the mutable-field inventory (SEC-R3-04); the self-test covering §4 with mandatory cases shown failing first; the reviewer's probe scripts run green; `RETURN_MANIFEST.json` self-verified plus optional `proposed_classifications.json`; H-06 first.

**Stop and report** if any correction cannot be made without changing a `25_` contract clause (it should not need to), if the global-lock model creates a deadlock you cannot resolve within the stub (report the cycle rather than working around it), or if any clause here is internally inconsistent. The stop-and-report discipline has caught a real defect in every prior round; keep using it.

## 6. After R4

R4 return → Fable structural verification (static, per the trail-127 practice) → **ChatGPT concurrency re-verification** using its own barrier probes (the review scheduled this; the probes ship in the packet) → owner hands-on POC session. The security gate closes when the reworked stub passes the same deterministic barriers that failed it.
