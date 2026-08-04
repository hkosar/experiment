# 32 — Fable Disposition: independent security review of the R2+R3 stub

**Input:** `31_` + `31A_` + `31B_` + the 9 probe scripts and their outputs (bundle SHA-256 `cceb1fbf1dd7a0bfb97bf35adecaab09825d80a0604dc0e72895d098a827059f`; internal `SHA256SUMS` 21/21 valid — verified per basename, the bundle's list uses `./`-prefixed paths). The reviewer's target hash `7f13494e…5b90f572` matches the integrated stub exactly; it reviewed the file this repository holds.

**Verdict: FAIL — CONCURRED IN FULL on all seven findings.** The two Criticals are confirmed by Fable's own static reading of the cited code; the review is correct, well-evidenced, and its central conclusion is sound: **the POC's core claim fails under concurrent HTTP requests.**

## 1. What passed, and the one that matters most

Three of the four requested attack surfaces held: the `Disclose` response-only exemption (the deliberate hole Fable most wanted attacked — the reviewer confirmed only two construction sites, both service-minted, that provider JSON cannot instantiate, and that capture/log paths use `disclose=False`), the A.4 `UNCERTAIN` amendment (provider-reported uncertain moves no state), and the Builder self-test / witness / validator reproductions (167/167, 34/34, 160/160 — the reviewer ran them, so they are now independently confirmed, not merely Builder-authored).

**But the review found exactly the thing Fable asked it to hunt: the R3 analogue of the R2 layer mismatch.** DEF-R2-01 was "a control whose tested layer differs from the layer a caller meets." The reviewer's §3.2: *"The sequential in-process tests pass, but the caller-visible ThreadingHTTPServer permits concurrent requests. The tested sequential layer therefore differs materially from the concurrent HTTP layer a provider actually meets."* Same shape, one layer up — the tests exercise single-threaded request handling; the server is threaded. This is the vindication of routing adversarial verification to an independent reviewer: three parties (Builder self-test, Fable static reading, and the prior security review) all worked at a layer where the defect is invisible, and only live concurrent probing surfaced it.

## 2. Fable's own confirmation of the two Criticals

Per the trail-127 practice, **Fable ran no concurrency probes.** It confirmed the *mechanism* of the two Critical findings by static reading, which is sufficient to concur and is what the practice permits:

- **SEC-R3-01** (`h_poc1_review_case`, lines 1039-1084 as cited): `with STORE.lock: prior = STORE.by_identity.get(ikey)` — then **the lock is released** — then the new case is minted and `STORE.by_identity[ikey] = case_id` is published in a **separate later critical section**. Two concurrent requests with one identity both read `prior is None` and both proceed. A textbook check-then-act gap, and the same pattern recurs at registration, verify-decision, relay, and run-started exactly as the finding states.
- **SEC-R3-02** (`h_relay_deliver`): the capability status is read and the `EXPIRED/REVOKED` check runs near the top; the flow then proceeds through multiple steps and sets `b["status"] = DELIVERED_WITH_RECEIPT` at the end **with no revocation re-check between the initial read and the terminal commit**. A concurrent `/owner/revoke` that lands in that window is silently overwritten — an acknowledged owner revocation lost to an in-flight delivery.

Both are real. The reviewer's deterministic two-request barrier method (not stress; `31B_`) is the right way to have found them, and it is more convincing than the 50-thread probe it correctly set aside as corroborating-only.

## 3. Dispositions

| ID | Sev | Disposition |
| --- | --- | --- |
| **SEC-R3-01** authority/idempotency transitions not linearizable | Critical | **CONCUR** — mechanism confirmed statically; systemic across 5 handlers |
| **SEC-R3-02** acknowledged revoke lost to in-flight delivery | Critical | **CONCUR** — confirmed statically; no terminal-state recheck at the delivery commit |
| **SEC-R3-03** evidence asserts transitions that never became effective | High | **CONCUR** — single-phase `case-opened` capture before token mint; `capability-mint` committed before secret-index admission |
| **SEC-R3-04** state mutations outside the prepared/committed contract | High | **CONCUR** — `_expire_if_due` mutates with no transition evidence; stage-attempt counter increments before its capture |
| **SEC-R3-05** capture writes not crash-atomic; leak quota on failure | High | **CONCUR** — quota reserved and the final path pre-created empty before the temp write; a failure leaves a zero-byte final file and a consumed quota unit |
| **SEC-R3-06** route-policy entity quotas not uniformly enforced | High | **CONCUR** — enforcement is per-handler, not central at dispatch; refusal/receipt/triage accept work past ceiling |
| **SEC-R3-07** outcome coverage is label coverage, not branch correctness | Medium | **CONCUR** — the guard the Builder introduced (and Fable praised at trail 139) is a completeness aid, not security evidence; a 167/167 suite coexisted with reachable Criticals |

SEC-R3-07 is worth naming honestly: at trail 139 Fable adopted the outcome-coverage guard as a pattern for the real wrapper. The reviewer's correction stands — it proves each outcome label is *produced by some case*, not that the *right branch* produced it for the *right scenario*, and it passed green while the Criticals were live. **Adjusted position:** the guard stays as a completeness aid, but the acceptance oracle for security routes must bind each scenario to a starting state, expected status/outcome/state-delta/evidence-delta, forbidden outcomes, and a concurrency cardinality — as the reviewer specifies.

## 4. Root cause, stated plainly

This is not seven unrelated bugs. Six of the seven are one defect: **the stub's authority transitions are not linearizable, because every one of them reads state under a short lock, releases it, does work, and commits later without holding a single critical section across the whole check→reserve→commit.** The seventh (SEC-R3-07) is why that survived testing. The correction the reviewer specifies is correspondingly single: **one linearizable transition per subject identity, a global lock held across precondition, reservation, evidence preparation, state publication, and terminal result** — which the reviewer explicitly authorizes for a throwaway stub (*"A global lock is acceptable… Production scalability is not required at this gate"*). That is the architecture decision, and `33_` makes it rather than delegating it.

## 5. Rework issued, and sequencing

**`33_` (the R3 stub security rework packet) issues to the Builder**, making every correction concrete per §5 of the review. This goes **directly to the Builder**, not through another plan-gate confirmation, for a specific reason: unlike the six R3 contract revisions — where Fable was inventing architecture and the verifier rightly gated each draft — here the **verifier has already specified the fix**, per finding, with a named model (global-lock linearization) it pre-authorized. `33_` codifies that prescription; it does not originate it. The returned build then goes back to ChatGPT for the concurrency re-verification the review already schedules (§5: *"deterministic barriers; probabilistic stress tests alone are insufficient"*), and the reviewer's own probe scripts — shipped in this bundle and integrated at `31_security_probes/` — become part of the acceptance suite so the re-verification runs the same barriers that found the defects.

Nothing accepted reopens: Release-1, the Capability Portfolio work, provider selection, the Decision Engine design, the v1.4 baseline, and the production-wrapper architecture all stand. **Owner POC session remains BLOCKED** until the reworked stub passes the concurrency re-verification. This is the productive direction at last — a bounded, well-specified build, not another contract revision.

## 6. A note on what this validates

Six plan-gate revisions hardened the *contract*; this review hardened the *build* against the one thing no amount of contract precision or single-threaded testing could catch. The escalation practice the owner established at trail 127 — route adversarial verification to an independent party with an execution sandbox — is the only reason this defect was found before the owner sat down to a live session where a single approval could have fanned out into multiple real side effects. It is worth carrying, unchanged, into the production wrapper's own security gate.
