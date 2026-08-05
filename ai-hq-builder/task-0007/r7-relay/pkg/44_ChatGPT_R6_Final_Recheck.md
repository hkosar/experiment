# 44 — ChatGPT final re-check of R6 rollback/quarantine

**Input:** `R6_Final_Recheck.zip` and `R6_Final_Recheck(1).zip`  
**Input SHA-256:** `abc0e6fcae6843fb0e46c6a6bfb12f56ce1020cf3e2bab5ab96c2f141c173dbb` for both archives; they are byte-identical.  
**R6 source SHA-256:** `d0fd4c449e797be422c78b2c283d6c7b0232dfbcb96a286821279c49b0d19ac0`  
**Pinned R5 source SHA-256:** `972c30d532a957a94a8e7200c9385e387f7508673335acdc8652eb6e3dd15e68`

## Verdict

**FAIL — SEC-R4-01 remains OPEN at High severity. The hands-on POC session remains blocked.**

R6 correctly closes the four named `OSError` rollback/publication boundaries and its hard quarantine genuinely fails the current process closed. However, moving `published = True` to the directory-fsync boundary without making the outer exception handling publication-aware introduced a remaining post-durability path that recreates the original authority contradiction:

> the service returns the ordinary `capture-failed / not effective` result and removes live registration state while a durable `committed` record remains on disk saying the registration is `REGISTERED`.

This is not a disagreement with Fable's strict-fsync ruling. I concur that a deletion whose directory fsync did not complete is not a proven rollback and should quarantine. The failure is later: an exception after publication is already durable can still be mislabeled as a pre-publication capture failure.

## 1. Packet and verifier integrity

The packet is structurally usable:

- Both uploaded R6 archives are byte-identical.
- `SHA256SUMS.txt`: **123/123 valid**.
- `authority_manifest.json`: **122/122 valid**, with no missing or mismatched file.
- `base_snapshot.tar` independently reproduces tree `845b5ee34b53979d565cbf09c719a3a649e03429`.
- The R5 pin matches the reviewed R5 source at SHA-256 `972c30d5…15e68`.
- `chatgpt_r5_cleanup_rollback_probe.py` is byte-identical to the probe delivered in the R5 verifier return, SHA-256 `8a359438…91cd4`.

No integrity issue is the basis for this verdict.

## 2. What R6 successfully fixes

The required first-order and rollback-failure tests now behave as intended:

- Verifier's R5 rollback probe: **R6 5/5; pinned R5 0/5** under the packet's scenario-by-scenario criterion.
- Builder capture-fault suite: **R6 9/9; pinned R5 5/9**.
- Previously accepted publication probe remains green: committed registration publication failure leaves only the legitimate `prepared` record, zero live registration/index entries, and exactly one `reserved-owner` capture unit.
- Independent oracle suite: **7/7 scenarios, 33 clauses**.
- Independent concurrency barrier regression: **6/6 scenarios**.

I also directly confirmed the new current-process quarantine behavior. A real committed-registration rollback failure returns `503 refused-storage-quarantine`; `GET /health` remains available and reports `storage_quarantined: true`; subsequent owner and provider POSTs both return the same 503; and neither state nor evidence changes while quarantined.

Therefore the global-lock concurrency architecture remains accepted and closed. The strict rule that an undurable rollback deletion must quarantine is also accepted.

## 3. SEC-R4-01 remains open: post-durable `BaseException` becomes ordinary `CaptureError`

### Source ordering

In `poc/stub/stub_server.py`:

1. The publication directory is fsynced at line 786.
2. `published = True` is correctly set immediately afterward at line 791.
3. The inner close handler catches only `OSError` at lines 793–803.
4. Any other exception from that post-publication tail reaches the outer `except BaseException` at lines 809–814 and is converted to `CaptureError`.
5. Because `published` is already true, the `finally` block at lines 815–831 does not remove the durable final record.
6. `h_owner_artifact_register` catches `CaptureError` at lines 1126–1133, removes the provisional registration and identity entry, and returns the ordinary statement that the registration was “not effective.”

The true durability boundary was moved, but the meaning of the outer exception handler was not moved with it.

### Deterministic reproduction

`44_security_probes/post_durable_interrupt_compare.py` wraps the second publication-directory close—the committed registration capture—so that it:

1. performs the **real** `os.close(fd)`;
2. then raises `KeyboardInterrupt` immediately afterward.

The probe does not weaken the write, link, file fsync, directory fsync, or live-state code. It deterministically models an interruption delivered after the committed record is already directory-fsynced and the directory FD has actually been closed.

### R6 result

```text
HTTP status:              500
outcome:                  capture-failed
response claim:           registration not recorded, and therefore not effective
registrations:            0
registration index:       0
transition mirror:        0
storage quarantine:       0
reserved-owner captures:  2
```

Disk evidence contains both:

```text
prepared-artifact-register
  phase: prepared

committed-artifact-register
  phase:        committed
  outcome:      committed
  final_status: REGISTERED
```

That is the exact SEC-R4-01 contradiction: the ordinary response and live state say ineffective; durable evidence says committed and registered; no quarantine warns the operator that the two disagree.

### Same probe against pinned R5

Pinned R5 also returns 500, but it leaves only the legitimate `prepared` record and one `reserved-owner` unit. The committed record is absent. R6 therefore introduced this specific ordering regression when it correctly moved `published = True` earlier but left `except BaseException` publication-blind.

### Severity

**High.** This is not merely a noisy or unnecessary refusal. It restores false authoritative evidence while issuing the ordinary negative claim SEC-R4-01 exists to forbid.

## 4. The quarantine path can still be entered spuriously

These do not create false committed evidence, so they are lower severity than §3, but they directly fail Fable's requested check that quarantine cannot be entered spuriously.

### 4.1 Failure before any artifact exists

I forced `os.makedirs` to fail before a temp or final name was created. R6 returned:

```text
503 refused-storage-quarantine
problem: rollback directory fsync failed (ENOENT)
surviving_final_path: null
surviving_temp_path:  null
records on disk:      0
reserved-owner pool:  1
```

`_rollback_capture` always attempts to open and fsync the capture directory when its `problems` list is empty, even when both `linked_path` and `tmp` are `None`. A missing directory is therefore treated as an unprovable rollback despite there being no artifact to roll back.

**Severity: Medium — availability/fail-closed correctness.** The safe result is an ordinary capture failure with the reservation released, not a global hard quarantine.

### 4.2 Directory close after a successful rollback fsync

I forced publication-directory fsync to fail, allowed rollback to remove every name, allowed the rollback directory fsync to succeed, then made the rollback directory close report `EIO` after the real close. R6 quarantined, retained quota, and reported “rollback directory fsync failed,” although:

- the rollback directory fsync had returned successfully;
- no temp or final artifact remained; and
- the directory FD had actually been closed.

The publication path has a true-durability flag before close; the rollback path does not. The same boundary rule should apply to both.

**Severity: Medium — availability/fail-closed correctness.** Once rollback fsync succeeds, a later close error is a soft anomaly, not proof that rollback failed.

## 5. Restart qualification

The hard quarantine is stored only in `STORE.storage_quarantine`, initialized as an empty list in `Store.__init__` (`stub_server.py:430–483`). Startup creates a fresh `Store` at lines 2591–2593 and does not load or require reconciliation of prior quarantine state.

Using the same candidate and data directory after a genuine rollback quarantine, a fresh process reported `storage_quarantined: false` and accepted a new registration with HTTP 200 while the old ambiguous committed record remained on disk.

I do **not** use this as the decisive High finding because the governing POC intentionally keeps other authority state in memory across a single run. It does, however, qualify the packet's claim that “explicit operator recovery” is required: the implementation enforces that only for the lifetime of the current process. R7 should either persist a quarantine/startup marker or explicitly enforce a no-restart-before-reconciliation operating rule for this POC.

## 6. Required R7 correction

Keep the correction narrow. Do not reopen concurrency, provider contracts, or the POC architecture.

1. **Make exception handling publication-aware.** Once the directory fsync has succeeded and `published` is true, no later exception may be converted into ordinary `CaptureError` or cause a handler to remove provisional live state. A durably committed capture must be treated as committed.
2. **Add the exact red-before-green probe.** The corrected build must fail the current R6 comparison first, then pass when a non-`OSError` interruption is raised immediately after the real committed directory close. Required result: no ordinary ineffective claim beside a committed record.
3. **Do not quarantine when no artifact was ever created.** Track whether a temp or final name existed. If neither existed, there is no rollback deletion to prove; release the capture reservation and return the ordinary capture failure.
4. **Set a rollback durability boundary.** Mark rollback proven immediately after the rollback directory fsync returns. A subsequent directory-close error is a recorded soft anomaly and must not retain quota or hard-quarantine the service.
5. **Resolve the restart posture.** Persist a quarantine/startup marker or bind the POC runbook/start command so a restart cannot silently bypass the required manual reconciliation.
6. Re-run the existing R6 tests unchanged: verifier rollback **5/5**, capture-fault **9/9**, oracle **7/7 / 33**, barrier **6/6**, and the accepted prepared-record/quota behavior.

## 7. Test-accounting qualification

The shipped `poc/stub/out/selftest.json` reports **190/190**, and the shipped witness file reports **34/34**. I did not treat those generated outputs as independent verification. The independent results claimed in this report are the targeted probes and suites listed above, plus the new R6 probe supplied in this return.

## Gate disposition

- **SEC-R3-01:** closed; unchanged.
- **SEC-R3-02:** closed; unchanged.
- **AUDIT-R4-5:** amended and closed; unchanged.
- **SEC-R4-01:** **OPEN — High**.
- **Hands-on POC session:** **blocked pending the narrow R7 correction and one final re-check.**
