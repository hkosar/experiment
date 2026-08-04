# 12 — ChatGPT Independent Security Review: TASK-0007 R1 Wrapper Stub

**Reviewer:** ChatGPT, independent verifier/security reviewer  
**Review target:** `stub_server.py` and its supplied security evidence  
**Packet:** `ChatGPT_Security_Review_Request_TASK0007R1.zip`  
**Packet SHA-256:** `c973cbcf88f185bcfcc3c1833272d3025c1027453548ffc68d40d516baaf316e`  
**Target SHA-256:** `ecdaae6716c52379f8871b406c738618f359fb3d3d9e1941d764dc4b376328ac`

## 1. Verdict

### Narrow R1 refusal verdict

| Required refusal | Independent result |
| --- | --- |
| Missing, forged, or replayed resume token is refused | **PASS** |
| Provider-supplied decision fields are refused by `/poc1/verify-decision` | **PASS** |
| A caller without the owner key cannot use `/owner/decide` | **PASS** |
| Concurrent use of one approved token authorizes at most once | **PASS** — 1 authorization and 49 refusals in a 50-thread probe |

### End-to-end security verdict

**FAIL — the stub is not cleared for the owner POC session yet.**

The endpoint-level refusal checks work, but the represented side effect does not enforce them end to end. `/sink` accepts an arbitrary direct request with no ActionRequest, capability, owner decision, or token. A provider can therefore bypass the entire approval flow and obtain `{"delivered": true}` without ever calling `/poc1/verify-decision`.

This is a defect in the POC's evidence value, not a claim that a production system has been compromised. The service is correctly marked throwaway, binds to loopback, uses no real account, and claims no production authentication. Nevertheless, POC-1 is intended to demonstrate that the provider can carry a pause but cannot decide or execute the protected action by itself. The current stub does not demonstrate that property.

## 2. Independent verification performed

### Packet and supplied evidence

```text
Archive opened successfully
SHA256SUMS: 7 / 7 passed
Python compilation: passed
Supplied self-test: 66 / 66 passed
Freshly generated self-test output: byte-identical to supplied stub_selftest.json
```

### Independent probes

```text
Probe count: 14
Expected controls that passed: 5
Residual defects reproduced: 9
```

Machine-readable evidence is supplied as:

```text
12A_ChatGPT_Security_Probe_Evidence_TASK-0007_R1.json
```

## 3. Findings

### SEC-R1-01 — Gate-blocking: direct side-effect bypass

**Affected code:** `ACTION_TARGET`, `h_sink`, and the public `("POST", "/sink")` route.

**Observed:**

```text
POST /sink with an attacker-selected payload
→ HTTP 200
→ {"delivered": true, "sink": "local throwaway"}
→ capture record written
```

No owner key, resume token, ActionRequest ID, execution capability, payload binding, or one-time authorization is required.

**Why it matters:** The provider can skip the owner-decision and token-exchange path entirely. The two mandatory refusals therefore pass only at the guarded endpoints, not at the represented action boundary.

**Required correction:** Mint a single-use execution capability only after a valid owner acceptance. Bind it to at least:

```text
ActionRequest ID
case ID
fixed target
canonical payload digest
single-use state
short POC lifetime
```

`/sink` must fail closed without that capability, reject mismatched payloads, and reject replay. A simpler acceptable POC design is to remove the public sink and have the stub perform the local synthetic side effect inside the authorized exchange, but that would no longer test provider relay as directly.

---

### SEC-R1-02 — High: arbitrary capture payloads defeat the redaction claim

**Affected code:** `redact()`, `h_poc1_receipt`, `h_poc1_refusal`, `h_poc3_reconcile`, `h_poc3_receipt`, and other handlers that persist caller-controlled dictionaries.

**Observed:** A real minted resume token placed under the benign field name `opaque` was written verbatim to a capture record.

The redactor works for recognized key names and selected value shapes, but a resume token is deliberately opaque random text. The system cannot infer that every arbitrary string is a secret.

**Required correction:** Do not persist arbitrary inbound payloads. Use endpoint-specific capture schemas and allowlist only the fields needed for the POC evidence. In addition, redact exact active token values by digest comparison and redact the exact owner key by constant-time equality before any logging or capture. Unknown fields should be omitted or represented only by field name, type, byte count, and a non-reversible digest.

---

### SEC-R1-03 — High: terminal owner decisions remain mutable

**Affected code:** `h_owner_decide` and the decision read/spend sequence in `h_poc1_verify_decision`.

**Observed:**

```text
Owner records accept
Provider verifies and receives authorized ActionRequest
Owner records reject for the same case
Second owner write returns HTTP 200
Stored decision now says reject
```

The record can therefore say “rejected” after the represented action was authorized under “accept.” Concurrent decision replacement can also race with token spending because the decision read and token spend are not one atomic operation.

**Required correction:** Treat the first valid owner decision as terminal for this POC, or implement a versioned replacement/revocation protocol. The simplest fix is to return `409 Conflict` for a second decision and perform decision lookup plus token consumption under one lock using the immutable decision record.

---

### SEC-R1-04 — High: capture failure leaves a live uncaptured authorization

**Affected code:** `h_owner_decide` writes `STORE.decisions` before calling `write_capture`.

**Observed:** With an invalid/unwritable capture destination:

```text
Decision inserted into memory
capture write raises NotADirectoryError
owner request receives no valid completion response
provider subsequently verifies the token
authorization succeeds
```

**Why it matters:** This is evidence apparatus. A state transition that survives while its mandatory capture fails undermines the artifact's purpose and can cause an operator retry against an already-effective decision.

**Required correction:** Make the transition fail closed when its capture cannot be durably written. For the stub, write a temporary capture, flush/close it, atomically rename it, then commit the in-memory decision; or roll back the decision on any capture exception. Return a structured `500` refusal and never leave an authorization live without the required capture.

---

### SEC-R1-05 — High: secrets in URL queries are logged verbatim

**Affected code:** `Handler.log_message`, `do_GET`, and `do_POST`.

**Observed:** A request such as:

```text
GET /health?resume_token=<opaque-secret>
```

caused the opaque secret to appear unchanged in stderr because `BaseHTTPRequestHandler` logs the full request target and the value does not match the selected value-shape regexes.

**Required correction:** These endpoints do not need query parameters. Reject any request with a query component, or override logging to record only the normalized path and status. Never pass the raw request target into a general regex redactor. Add `Cache-Control: no-store` to owner-sensitive responses.

---

### SEC-R1-06 — Medium: malformed input can crash a request thread instead of refusing

**Affected code:** `h_poc2_triage` assumes `metadata` is a dictionary; the HTTP handler does not catch exceptions raised by a route handler.

**Observed:** `metadata: []` raises `AttributeError`. Through HTTP, the client receives `RemoteDisconnected` rather than a structured refusal.

**Required correction:** Validate nested object types before use and wrap route dispatch in a narrow exception boundary. Return a generic structured refusal without exposing a traceback. Preserve tracebacks only in a local reviewer log that cannot contain raw request values.

---

### SEC-R1-07 — Medium: negative Content-Length is not rejected

**Affected code:** `Handler.do_POST`.

**Observed:** `Content-Length: -1` reaches `read(-1)` and waits for connection EOF instead of returning promptly. Repeated local connections can consume unbounded request threads.

**Required correction:** Enforce:

```text
0 <= Content-Length <= MAX_BODY
```

Reject missing-body ambiguity, negative lengths, unsupported transfer encodings, and duplicate/conflicting length headers. Add a short socket/request timeout suitable for the throwaway POC.

---

### SEC-R1-08 — Medium: browser-simple local requests are accepted without a provider-session control

**Affected code:** all provider-facing POST routes.

**Observed:** `/poc1/review-case` accepted a valid JSON body sent as `Content-Type: text/plain`, which is a browser-simple cross-origin request shape. A malicious page cannot read the returned token under normal browser controls, but it can create cases and capture files, and repeated calls can exhaust memory or disk.

**Required correction:** Require `application/json`, reject browser-originated requests unless explicitly allowed, and give provider-facing routes a separate per-process POC key or unguessable session path. This provider key must not confer owner authority. Add bounded case/capture counts or a short session lifetime.

## 4. Owner-key assessment

The per-process owner key is proportionate only for the stated throwaway, single-operator, loopback-only POC. It is **not** real authentication and must not be described as such.

Acceptable scope conditions:

- Bind only to loopback.
- Do not expose this exact service through a public tunnel.
- Use no production credentials, sensitive artifacts, or real business data.
- Rotate the owner key on every process start.
- Keep the key out of provider configuration.
- Delete the service and captures after the POC evidence is collected.

One documentation correction is advisable: the startup example prints the literal owner key inside a curl command. Copying that command places the key in shell history. Use a small owner helper command or a silent shell prompt that stores the value only in a temporary shell variable.

## 5. Additional tests required after correction

The next security packet should include machine-runnable cases for:

1. Direct `/sink` call without a capability — refused.
2. Valid capability with altered action ID, target, payload, or case — refused.
3. Valid capability replay — refused or returns the exact prior idempotent receipt without a second side effect.
4. Resume token placed under arbitrary and Unicode-confusable keys — absent from every capture and log.
5. Second owner decision for the same terminal case — refused.
6. Capture-write failure during owner decision — no decision or authorization survives.
7. Malformed nested metadata and deeply malformed JSON — structured refusal, server remains healthy.
8. Negative length, unsupported transfer encoding, and slow-body request — prompt refusal/timeout.
9. Query strings containing owner or resume secrets — rejected and absent from logs.
10. Browser-simple cross-origin-shaped POST without provider-session credential — refused.

## 6. Gate state

```text
Packet integrity:                         PASS
Supplied 66-case self-test:               PASS
Mandatory token refusal at verify path:   PASS
Owner-key refusal at owner endpoint:      PASS
Provider decision-field allowlist:        PASS
End-to-end approval/execution boundary:   FAIL
Secret non-persistence claim:             FAIL
Malformed-input fail-closed posture:      FAIL
Owner POC session security clearance:     BLOCKED
Production-readiness claim:               NOT MADE / OUT OF SCOPE
Builder rework required:                  YES, narrowly scoped
Next actor:                               Fable
Hunter action required now:               NONE
```

## 7. Required disposition

Fable should disposition `SEC-R1-01` through `SEC-R1-08` and issue a narrow rework packet. `SEC-R1-01` through `SEC-R1-05` should block the owner session. The Medium hardening findings may be corrected in the same round; if any are deferred, the owner-session runbook must explicitly preserve the loopback-only, synthetic-data, short-lived operating constraints and record the accepted residual risk.

No provider-selection decision, Release 1 re-aim decision, Decision Engine design, or production-wrapper architecture is reopened by this review.
