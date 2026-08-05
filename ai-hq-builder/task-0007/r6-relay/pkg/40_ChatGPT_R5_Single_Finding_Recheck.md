# 40 — ChatGPT R5 single-finding re-check

**Input:** `R5_Single_Finding_Recheck.zip`  
**Input SHA-256:** `2609d21df38f4dce965aa3b95cfc6a2ce7e6d2635b4e41b95da911a623c59c9f`  
**Scope:** SEC-R4-01 only. The R4 concurrency architecture remains accepted and was not reopened.  
**Verdict:** **FAIL — SEC-R4-01 remains OPEN (High, gate-blocking). The owner hands-on POC session remains blocked.**

## 1. Executive ruling

R5 materially improves the ordinary post-link failure paths:

- `published` is no longer set immediately after `os.link`;
- the final link is tracked separately as `linked_path`;
- the verifier's two unchanged R4 probes are green against R5 and red against the pinned R4 build;
- the Builder's four named fault boundaries are 5/5 against R5 and 2/5 against R4; and
- the legitimate `prepared` record and exactly one reserved-owner quota unit correctly survive a failed committed registration.

That is real progress, but it does not complete the acceptance requirement previously issued in `36_` §4. The R5 rollback path **releases quota before proving cleanup, silently swallows final-link cleanup errors, and never fsyncs the directory after rollback deletion**. When final-link cleanup is faulted, R5 returns the ordinary claim that the registration was “not effective,” removes all live registration state, yet leaves a final JSON record saying:

```text
step:         committed-artifact-register
phase:        committed
outcome:      committed
final_status: REGISTERED
```

That is the same authority contradiction SEC-R4-01 was opened to eliminate. R5 fixes the first-order failure but not the required failure of the rollback itself.

## 2. What independently passed

### Packet and pin integrity

- `SHA256SUMS.txt`: **103/103 OK**.
- `authority_manifest.json`: **102/102 OK**, no missing or mismatched listed files.
- `base_snapshot.tar` independently reproduces tree **`36fcd20d7d612b39801dbe90a700d84823f51284`**, matching `BASE_BINDING.txt` and the authority manifest.
- Pinned R4 digest: **`2876522bec584678c2326d002e58e9fa388b64ac9be9092c2ba1a18022450f79`**, matching the build examined at R4.
- R5 stub digest: **`972c30d532a957a94a8e7200c9385e387f7508673335acdc8652eb6e3dd15e68`**.
- The two prior verifier probes are byte-identical to the R4-return originals:
  - `chatgpt_capture_publication_fault_probe.py`: `2f37ef5c98144b7f654ca11050b216ecc2e0dbfb449b7138660e9eee21fb506c`
  - `chatgpt_capture_postlink_cleanup_probe.py`: `3cb4df24c10390f52c57a2ab04344bb6b631a96b873001835bd55232de518b8d`

### Named R5 acceptance probes

The unchanged publication-fsync probe produced the correct ordinary-fault result against R5:

```text
HTTP status:       500 / capture-failed
registrations:     0
identity index:    0
transition mirror: empty
surviving records: prepared-artifact-register only
reserved-owner:    1
```

The unchanged post-link probe also found no file and no consumed quota at link failure, one-shot temp-unlink failure, and directory-open failure. The same probes remain red against pinned R4.

The Builder's `capture_fault_suite.py` independently reproduced as:

```text
R5: 5/5 (control + link + temp-unlink + directory-open + directory-fsync)
R4: 2/5 (control and link only; the three defective boundaries remain red)
```

The targeted R5 self-test block completed **8/8**. Broader corroborating regression checks completed as **34/34 witnesses**, **6/6 barrier scenarios**, and **7/7 oracles / 33 clauses**. These do not cure the cleanup-state defect below.

## 3. SEC-R4-01 remains open — rollback cleanup can still leave false committed evidence

### Severity

**High — gate-blocking.** The impact is false authority evidence and recovery ambiguity. The quota leak is improved in this branch, but the more important contradiction remains: disk evidence can say committed while HTTP and live state say ineffective.

### Source evidence

The relevant R5 path is:

```text
stub_server.py:694-696   os.link succeeds; linked_path is recorded
stub_server.py:699-705   temp is unlinked; directory is opened, fsynced, and closed
stub_server.py:707       published = True
stub_server.py:728-729   on failure, quota is released first
stub_server.py:730-736   final/temp unlink errors are silently ignored
```

Three defects remain in that ordering:

1. **Cleanup is not proven before quota/state rollback is claimed.** `_release_pool(pool)` runs before either unlink attempt.
2. **A failed final-link removal is swallowed.** The `except OSError: pass` path leaves the success-named final record and propagates only the original publication failure.
3. **Rollback deletion is not made durable.** There is no directory open/fsync after removing the final link and temp name.

Additionally, `published = True` is set only after `os.close(dfd)` returns, not immediately after the directory fsync succeeds. A close error after successful directory fsync therefore enters rollback even though publication has already reached its stated durability boundary.

The registration handler then catches the resulting `CaptureError`, deletes the provisional registration and identity index, and returns:

```text
registration not recorded, and therefore not effective
```

There is no distinct storage-uncertain/quarantined branch for a rollback that could not be established.

### Direct registration reproduction

The independent probe forced the committed capture's directory-open failure and then forced removal of its final link to fail. R5 returned:

```text
HTTP:              500 / capture-failed
registrations:     0
identity index:    0
transition mirror: empty
reserved-owner:    1
```

The reserved-owner count of `1` is correct for the legitimately published prepared record. However, the capture directory contained both:

```text
prepared-artifact-register
committed-artifact-register
  phase:        committed
  outcome:      committed
  final_status: REGISTERED
```

The final cleanup fault was actually reached once. The Builder's new cleanup code therefore ran; its error was simply discarded.

### Standalone reproduction

With a publication directory-open failure followed by final-link cleanup failure:

```text
result:        CaptureError / no returned path
pool:          general = 0
survivor:      cleanupfinal-...json
```

R5 released the reservation but left the final record.

### Rollback-fsync reproduction

With a forced publication-directory-fsync failure, the probe observed exactly two fsync calls:

```text
1. temp content file fsync
2. publication directory fsync — forced EIO
```

No third fsync occurred after the rollback unlink. The final file disappeared from the current directory view, but the rollback deletion was not durably committed. A crash-recovery test is filesystem-dependent; the absence of any rollback directory fsync is directly established by both source and call count.

### Post-fsync close boundary

A supporting probe allowed the publication directory fsync to complete, then forced the directory close and final-link cleanup to fail. It observed:

```text
directory fsync successes:       1
forced directory-close faults:   1
forced final-cleanup faults:     1
result:                           CaptureError
surviving final record:           yes
quota retained for failed write: no
```

This confirms that the code can treat an already directory-fsynced record as “unpublished” because `published` is assigned after close.

### Persistent temp cleanup

When both the primary temp unlink and its rollback retry fail, R5 leaves a hidden `.tmp` capture artifact while returning `CaptureError` and releasing quota. This is less severe than the false final record, but it confirms that cleanup failures are generally ignored rather than converted into an explicit uncertain storage state.

## 4. Why the supplied green tests do not close the finding

The supplied R5 tests exercise one initiating fault at a time and assume cleanup succeeds:

- link failure;
- one-shot temp-unlink failure;
- directory-open failure; and
- directory-fsync failure.

They do **not** fault:

- removal of the already-created final link;
- repeated temp cleanup failure;
- rollback directory fsync; or
- the post-fsync directory-close boundary.

Those omissions are not a new expansion of scope. `36_` §4 explicitly required branch-specific tests for **final-link cleanup failure** and **rollback directory-fsync failure**, and required quarantine/fail-closed behavior if rollback could not be established. Fable's R5 request also asked whether a further post-link ordering existed beyond the four named boundaries. It does.

## 5. Required bounded correction

Do not reopen the global-lock concurrency architecture. The next correction remains confined to capture publication and its caller-visible failure state.

1. **Do not release quota until rollback is proven.** Remove the final link and remaining temp name, then fsync the directory, and only then release the reservation and permit the caller to claim the transition is ineffective.
2. **Do not swallow cleanup failure.** A failed final unlink, temp unlink, directory open, or rollback fsync must become a distinct storage-uncertain result.
3. **Quarantine/fail closed when rollback cannot be established.** Do not return the ordinary `capture-failed / not effective` response while a committed record may remain. Preserve enough provisional state to reconcile, block further authority transitions as necessary, and require explicit recovery.
4. **Set durable publication at the actual boundary.** Once publication directory fsync succeeds, a later directory-fd close error must not turn a durable committed record into an ordinary rollback claim.
5. **Separate publication from temp housekeeping.** A temp-cleanup problem after durable publication must not cause live state to be rolled back while committed evidence is retained.
6. Add direct red-against-R5 / green-against-corrected-build tests for:
   - final-link cleanup failure;
   - persistent temp cleanup failure;
   - rollback directory-open/fsync failure; and
   - directory-close failure after successful publication fsync.
7. Re-run the independent `chatgpt_r5_cleanup_rollback_probe.py`; every non-control scenario must produce either proven cleanup or an explicit quarantined/uncertain state—never a normal ineffective claim plus surviving committed evidence.

## 6. Regression and environment notes

- The full supplied self-test did not complete within the independent runner's 240-second command limit; it had progressed through the measurement-validator block. I therefore do not independently claim the Builder's full **178/178** count. The R5-specific capture-publication block completed **8/8**.
- The full legacy probe runner was not used as gate evidence because its five internally synchronized race probes retain the already-adjudicated barrier conflict and impose long barrier timeouts. The accepted concurrency architecture was not reopened.
- The harness's n8n structural checks could not run because `n8n-workflow` is not installed in this environment. This is inherited, disclosed, and unrelated to SEC-R4-01.
- The Builder record's `105/105` and `4b0874...` figures describe the Builder's earlier relay snapshot, whereas this outer Fable recheck packet contains 103 checksum entries and binds to `36fcd20d...`. The current outer packet verifies cleanly; this is a context-labeling note, not evidence of tampering.

## 7. Gate disposition

- **R4 concurrency ruling:** unchanged and closed.
- **Named R5 ordinary post-link paths:** accepted as improved.
- **SEC-R4-01:** **OPEN — High, gate-blocking.**
- **Owner hands-on POC session:** **not released.**
- **Next round:** one narrow capture rollback/quarantine correction, with no concurrency changes.
