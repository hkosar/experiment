# 36 — ChatGPT Concurrency Re-verification: TASK-0007 R4 Wrapper Stub

**Reviewer:** ChatGPT, independent verifier  
**Review target:** `poc/stub/stub_server.py`  
**Governing request:** `35_ChatGPT_Concurrency_Reverification_Request_R4.md`  
**Review type:** Scheduled concurrency and evidence-ordering gate before Hunter's hands-on POC session  
**Review date:** August 4, 2026  
**Packet SHA-256:** `0baf7e605dc54a493565f13181d020df12d1bb08a37a46177359bcdacd66285d`  
**R4 target SHA-256:** `2876522bec584678c2326d002e58e9fa388b64ac9be9092c2ba1a18022450f79`  
**Pinned R3 target SHA-256:** `7f13494ee510ef6e863f7324680832a582fb075f6d6ccf4442b379345b90f572`

## 1. Verdict

**FAIL — the owner POC session remains blocked.**

The concurrency rework itself is accepted. **AUDIT-R4-5 is resolved in the Builder's favor**, and the original concurrency findings SEC-R3-01 and SEC-R3-02 are closed against this R4 target. The selected global-lock model does serialize the authority transitions, produces one effective winner for each identity, prevents a successful revoke from being overtaken by an in-flight delivery, and continues to hold in a supplemental eight-request test.

The overall security gate nevertheless remains open because the requested `os.link` failure-path review found a separate, independently reproduced High-severity defect:

> **SEC-R4-01 — post-link capture failures can leave a success-named final record for a transition the service rolled back, while also leaking capture quota.**

A forced failure at the required directory-fsync boundary returned HTTP 500 and removed the registration from live state, yet left a final `committed-artifact-register` file whose fields say `phase: committed`, `outcome: committed`, and `final_status: REGISTERED`. That is false durable/visible authority evidence. It also retained the failed committed record's reserved-owner quota unit.

| Gate item | Disposition |
|---|---|
| AUDIT-R4-5: five original probes versus the global-lock model | **CONCUR; criterion amended** |
| SEC-R3-01: registration/case/token/capability/run races | **CLOSED for R4** |
| SEC-R3-02: revoke versus delivery | **CLOSED for R4** |
| Current deadlock posture | **No present lock cycle found; structural and unenforced** |
| More than two concurrent requests | **Supplemental 8-way R4 check passed** |
| SEC-R4-01: post-link capture publication/cleanup | **OPEN — High, gate-blocking** |
| Overall security gate | **FAIL** |
| Hands-on POC session | **BLOCKED** |

The required next action is one narrow capture-publication correction. The global-lock architecture does not need to be reopened.

## 2. AUDIT-R4-5 — explicit ruling

### 2.1 Ruling

**CONCUR.** The acceptance statement in `33_` §4 requiring the five internally synchronized legacy probes to run green is amended for this global-lock implementation.

Those probes place their rendezvous inside work that `33_` expressly requires one request to hold exclusively:

- `http_race_probes.py:23-28` blocks both requests in a monkeypatched `write_capture` after the review-case pre-check.
- `http_authority_races.py:21-38` blocks in `Transition.prepare` for capability mint and attempt start.
- `http_revoke_race.py:11-17` pauses delivery in `Transition.prepare` while issuing revoke.
- `more_race_probes.py:10-28` blocks both registration and run declaration in `Transition.prepare`.
- The race portions of `security_probes.py:50-145` use the same internal-barrier shape.

R4 takes `STORE.lock` around the entire POST dispatch at `stub_server.py:2160-2180`. Therefore a second request cannot reach `write_capture` or `Transition.prepare` until the first request leaves the lock. The first request waits for a participant that the architecture correctly prevents from arriving, the barrier breaks, and the probe reports an internal failure rather than the one-winner result it was intended to measure.

I cannot produce a conforming implementation of the selected model in which both requests simultaneously reach those points. Making that happen would require at least one of the following, each of which invalidates the proposed falsifier:

1. release the global lock before the injected point;
2. move or bypass the monkeypatched function;
3. special-case the probe; or
4. change the probe.

The first changes the selected architecture; the next two are probe evasions; the fourth concedes the criterion needs amendment. The Builder's structural analysis is therefore correct.

### 2.2 Important qualification: the shipped socket barrier is corroborating, not controlling

Fable accepted `barrier_suite.py` as equivalent evidence. Its `race()` helper uses a client-side `Barrier(2)` immediately before each thread sends (`barrier_suite.py:106-127`). That aligns client intent, but it does **not deterministically force both requests to reach the same server-side precondition or lock boundary**. Operating-system scheduling may still serialize the sends.

I therefore do not rely on that client barrier alone as the substitute acceptance proof. It remains useful corroboration because it produced:

```text
R4 target:       6 / 6 scenarios hold
Pinned R3 target: 0 / 6 scenarios hold
```

The controlling replacement evidence in this review is an independent live-HTTP handler-entry release gate. It wraps the real route handler without bypassing authentication, route policy, preconditions, transition code, capture code, or final state checks. The first handler pauses without throwing; the second request starts; the probe records whether the second handler can enter before release; then both requests complete normally.

- In R4, handler entry occurs **inside** the global dispatch lock, so exactly one handler enters before release.
- In pinned R3, there is no outer transition lock, so both handlers enter before release and the old duplicate-authority behavior reproduces.

### 2.3 Independent two-request results

| Identity/property | Pinned R3 | R4 |
|---|---:|---:|
| Same registration identity | 2 handlers entered; 2 registration records | 1 entered; 1 record; loser `already-registered` |
| Same submission identity | 2 entered; 2 cases; 2 tokens | 1 entered; 1 case; 1 token; loser `duplicate-suppressed` |
| Same resume token | 2 entered; 2 ActionRequests; 2 capabilities | 1 entered; 1 ActionRequest; 1 capability; loser `refused-token` |
| Same capability | 2 entered; both returned delivered | 1 entered; one delivered; one replay with no second side effect |
| Same schedule occurrence | 2 entered; 2 runs | 1 entered; 1 run; loser `duplicate-run-declaration` |

The R4 responses are not merely cardinality-correct; the loser responses truthfully describe the winner's already-effective state.

### 2.4 Revoke versus delivery

The original revoke probe requires revoke to return success while delivery is paused inside `Transition.prepare`. Under the selected lock, that ordering is unavailable: if delivery entered the transition first, revoke cannot return until delivery leaves it. The resulting R4 outcome was:

```text
Delivery: 200 / delivered
Revoke:   409 / refused because status is already DELIVERED_WITH_RECEIPT
Final:    DELIVERED_WITH_RECEIPT with one receipt
```

That is a valid delivery-before-revoke linearization, not a successful revoke losing to a later delivery.

A separate independent epoch probe paused delivery inside `attempt-start` preparation without injecting a transition exception:

```text
Pinned R3
- revoke returned 200 while delivery was paused
- delivery then returned 200
- final status became DELIVERED_WITH_RECEIPT
- receipt present

R4
- revoke could not return while delivery was paused
- delivery returned 200
- revoke then returned 409
- one final receipt
```

This closes the actual SEC-R3-02 property: **once revoke returns success, no later delivery commits under that revoked authority.**

### 2.5 Beyond two requests

The Builder correctly disclosed that its required barriers were two-request tests. Because the implementation uses one outer mutex rather than a pairwise mechanism, the safety argument should generalize, but I checked it rather than relying only on inference.

A supplemental eight-request handler-entry probe against R4 produced one effective object for every tested identity:

- 1 registration and 7 `already-registered` results;
- 1 review case/token and 7 `duplicate-suppressed` results;
- 1 ActionRequest/capability and 7 `refused-token` results;
- 1 delivery receipt and 7 replay/no-second-side-effect results;
- 1 run and 7 duplicate-run-declaration results.

Only one of the eight route handlers entered before the external release in every scenario.

## 3. Packet and evidence integrity

An untouched extraction produced:

```text
Packet SHA-256
0baf7e605dc54a493565f13181d020df12d1bb08a37a46177359bcdacd66285d

SHA256SUMS.txt
84 / 84 passed

Authority manifest
83 / 83 file hashes passed
Exactly one governing instruction: 35_ChatGPT_Concurrency_Reverification_Request_R4.md

Declared base tree
d9b529a7a82465c2bb068d74774f724ed3b17bba

Independently reconstructed base tree
d9b529a7a82465c2bb068d74774f724ed3b17bba

R4 target stub
2876522bec584678c2326d002e58e9fa388b64ac9be9092c2ba1a18022450f79

Pinned R3 target
7f13494ee510ef6e863f7324680832a582fb075f6d6ccf4442b379345b90f572
```

All nine legacy probe scripts are byte-identical to the verifier originals. Their nine archived result files are also byte-identical to the original R3 FAIL evidence. The packet disclosed that these files are checkable inputs rather than post-R4 outputs, so they were not misread as new pass evidence.

The four legacy probes that do not depend on the incompatible internal race rendezvous ran green individually against R4:

```text
stage_precise_probe        green — failed capture leaves attempt 0; next success is attempt 1
capture_atomicity_probe    green — its pre-link open fault leaves no file and no quota
quota_enforcement_probe    green — all three over-capacity requests refused
control_probes             green — Disclose and A.4 controls preserved
```

The green `capture_atomicity_probe` is not sufficient for SEC-R3-05 closure because it faults only `builtins.open` before `os.link`; it never exercises the required post-link or directory-fsync boundaries.

## 4. Finding

### SEC-R4-01 — High — Post-link capture failures leave false committed evidence and leak quota

**Status:** Gate-blocking residual of SEC-R3-05, with direct SEC-R3-03 evidence-integrity impact.

#### Requirement

`33_TASK-0007_R4_Task_Packet_Concurrency_Rework.md:42-45` requires:

- publication onto a previously nonexistent final path;
- directory fsync;
- removal of temporary artifacts on failure;
- rollback of capture quota on failure; and
- fault tests at directory-fsync and the other publication boundaries.

The architecture rule at `33_:15-19` also requires a failed step to roll back with no observable effect and no consumed resource.

#### Code evidence

`write_capture` performs these steps:

```text
stub_server.py:647-670  create/write/fsync temp, then os.link(temp, final)
stub_server.py:674      unlink temp
stub_server.py:676      set published = True
stub_server.py:677-681  open and fsync directory
stub_server.py:693-704  release quota/clean up only when not published; removes only temp
```

The no-overwrite property is correct: `os.link(tmp, path)` fails if `path` already exists. The defect is what happens **after that link succeeds**.

The final name exists at line 670, but `published` is set before directory fsync. If directory open/fsync then fails, the `finally` block sees `published == True`, retains the quota, and does not remove the final path. If temp unlink fails after the link, `published` remains false and quota is released, but cleanup retries only the temp name; the final hard link still remains.

#### Independent standalone fault results

**Forced directory-fsync failure after successful link:**

```text
result: CaptureError / EIO
final JSON files left: 1
pool: general = 1
```

**Forced directory-open failure after successful link:**

```text
result: CaptureError / EIO
final JSON files left: 1
pool: general = 1
```

**Forced first temp-unlink failure after successful link:**

```text
result: CaptureError / EIO
final JSON files left: 1
pool: general = 0
```

The link-failure control behaved correctly: no final file and no consumed quota. The defect is specifically the post-link state.

#### Independent authority-transition result

The directory-fsync fault was then injected on the **committed** capture of `POST /owner/artifact/register`:

```text
HTTP response:             500 / capture-failed
response says:             registration not effective
live registrations:        0
registration identity map: 0
transition mirror:         empty
```

Yet the capture directory contained:

```text
prepared-artifact-register
committed-artifact-register
  phase:        committed
  outcome:      committed
  final_status: REGISTERED
```

The reserved-owner pool count was `2`: one valid prepared record plus the failed committed record. A correct rollback would retain at most the prepared attempt record, remove the false committed record, and release the failed commit's quota unit.

This is a direct contradiction between caller-visible result, live state, and evidence. A later reader can conclude that a registration became effective when the service explicitly rolled it back.

#### Why the prior green probe missed it

`capture_atomicity_probe.py:5-18` monkeypatches `builtins.open` and fails before the temp content is written and before the final hard link exists. R4 deliberately restored that injection point, so the probe now passes. It does not fault:

- `os.link`;
- temp unlink after link;
- directory open;
- directory fsync; or
- cleanup of an already-created final link.

This is the fourth false-green blind spot requested in `35_` §3, although it is more precise to call it an **uncovered required boundary** than a fourth literal bypass of the original monkeypatch.

#### Impact

- **False authority evidence:** a committed record can describe state that does not exist.
- **Quota exhaustion:** repeated directory-fsync failures consume pool capacity despite failed requests.
- **Recovery ambiguity:** capture files, transition mirror, live state, and HTTP response disagree.
- **Gate invalidation:** SEC-R3-05's explicit directory-fsync acceptance boundary was not tested and does not hold.

#### Required correction

Implement an explicit publication state machine that tracks both the temp path and the final link.

1. Do not set `published` until the final directory entry has successfully passed directory fsync.
2. On any error after `os.link` but before successful directory fsync:
   - remove the final link;
   - remove the temp name if it still exists;
   - fsync the directory again so the rollback itself is durable; and
   - release the pool reservation only after the capture is proven ineffective.
3. If rollback cleanup or its directory fsync cannot be established, do not return the ordinary claim that the transition is ineffective. Enter an explicit fail-closed/quarantined storage state requiring reconciliation; the service cannot truthfully choose between “committed” and “rolled back” while the final record may remain.
4. Keep post-publication cleanup semantically separate from publication. Once the final record is durably published, a temp-cleanup problem must not cause the caller to roll back live state while retaining committed evidence.
5. Add branch-specific fault tests for:
   - filename allocation / `mkstemp`;
   - open, write, flush, and file fsync;
   - `os.link`;
   - temp unlink after link;
   - directory open;
   - publication directory fsync;
   - final-link cleanup failure; and
   - rollback directory-fsync failure.
6. For every authority transition, assert that a non-2xx rollback leaves no `committed-*` record for that transition and no extra capture quota. A prepared attempt record may remain if the contract intends it; committed success evidence may not.
7. Run the new tests against this R4 target and require red, then against the corrected target and require green.

The minimal expected result for the reproduced registration fault is:

```text
HTTP 500 / capture-failed
registrations = 0
identity index = 0
transition mirror = empty
no committed-artifact-register file
one prepared-artifact-register file at most
reserved-owner pool = 1 at most
```

## 5. Other requested checks

### AUDIT-R4-1

**CONCUR.** Global quotas can be reserved centrally at dispatch. Subject-scoped attempt/checkpoint limits must use the service-resolved subject inside the held transition rather than a caller-supplied identifier.

### AUDIT-R4-2

**CONCUR WITH DEFERRAL.** Provider crowd-out of an owner-needed shared idea ceiling is a real production-wrapper requirement. It is not a reason to reopen this supervised localhost POC round.

### AUDIT-R4-3

**CONCUR.** Expiry as an evidence-backed transition is consistent with the requirement that unusable secrets leave the live index immediately.

### Deadlock posture

No current server request path was found that acquires `SecretIndex._lock` and then waits for an unheld `STORE.lock` while another request holds `STORE.lock` and waits for the secret lock. POST requests acquire the outer `STORE.lock` first; secret-index methods do not call back into Store; no outbound network I/O occurs inside the transition.

This is a present-code structural observation, not an enforced invariant. The Builder's caveat stands: a future lock or reverse acquisition can silently invalidate it. A lock-order assertion or single synchronization abstraction belongs in the production wrapper, but this is not a new R4 gate blocker.

### Builder oracle

The supplied branch-specific oracle reproduced as:

```text
R4:       7 / 7 routes, 33 / 33 clauses
Pinned R3: 5 / 7 routes
```

This is corroborating evidence. It does not cover the post-link directory-fsync fault found above.

## 6. Gate disposition and bounded next round

**Concurrency adjudication is complete.** Do not spend another round trying to make the five internally synchronized legacy race probes green, and do not release the global lock merely to satisfy their instrumentation.

**Security gate closure is deferred for one narrow R5 capture-publication correction.** The return should contain:

1. the corrected `write_capture` publication/rollback state machine;
2. fault evidence for every post-link and cleanup boundary listed above;
3. a direct registration false-commit regression proving no committed record survives a rolled-back transition;
4. the existing R4 concurrency evidence unchanged or rerun as a regression; and
5. a red-against-current-R4 / green-against-R5 comparison for the new capture tests.

Release-1, Capability Portfolio work, provider selection, Decision Engine design, v1.4, the production-wrapper architecture, and the `Disclose` contract remain outside this bounded correction.
