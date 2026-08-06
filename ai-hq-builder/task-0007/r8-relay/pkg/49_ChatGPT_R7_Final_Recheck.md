# 48 — ChatGPT final re-check of R7 publication-aware handling and restart posture

## Integrity block

- **Attached ZIP SHA-256:** `673109fbc06fa0851dc8eb7efe36bc1971080fea7cb5340282c95b0628982062`
- **`SHA256SUMS.txt`:** **115/115 valid**
- **`authority_manifest.json`:** **114/114 listed files present and hash-valid**
- **Tree independently reproduced from `base_snapshot.tar`:** `4134d968755f623cc358eac1c58caa66706f98c8`

The archive arrived intact and matches the relay hash recorded by Fable/Claude. The pinned R6 source is SHA-256 `d0fd4c449e797be422c78b2c283d6c7b0232dfbcb96a286821279c49b0d19ac0`; the R7 source is `69b98fb09ae94d4f38b30e3e2d2179045fe4e50b529033940a7ad1ccf6b0ac91`. The two copied R6 verifier probes are byte-identical to the packet-level copies.

## Verdict

**FAIL — the security gate remains open. The hands-on n8n-versus-Zapier session remains blocked.**

R7 passes the supplied happy-path corrections for items 3 and 4 and preserves every R6 behavior I re-executed. It does not, however, make restart quarantine reliable when the marker cannot be created, and item 3's new early-return test can classify an existing temp artifact as “nothing created.” Item 4 also repeats the prior exception-type blind spot for a non-`OSError` after the real rollback directory close.

The settled post-durable Ctrl-C ruling was not reopened. Its exact red-before-green probe is green on R7 and red on the pinned R6 build.

## 1. What independently passed

The packet's exact R7 probe produced the intended summary:

- Pinned R6: all four R7 defect flags `true`; current-process fail-closed `true`.
- R7: all four supplied defect flags `false`; current-process fail-closed remains `true`.
- The injected faults landed on both builds.

The narrow supplied item-3 case passes: a forced `os.makedirs` failure before any artifact exists returns ordinary `capture-failed`, leaves no record, releases all capture quota, and creates no quarantine.

The narrow supplied item-4 case passes: publication fsync fails; rollback deletion and rollback directory fsync succeed; a real directory close followed by injected `OSError` is recorded as soft, leaves no records, releases quota, and creates no quarantine.

The R6 regression results are unchanged:

| Check | Pinned R6 | R7 |
|---|---:|---:|
| Verifier rollback probe | 5/5 | 5/5 |
| Capture-fault suite | 9/9 | 9/9 |
| Acceptance oracle | 7/7, 33 clauses | 7/7, 33 clauses |
| Deterministic barriers | 6/6 | 6/6 |
| Current-process quarantine fail-closed | true | true |

The accepted committed-registration rollback failure remains semantically identical: HTTP 503 `refused-storage-quarantine`; pools `{general: 0, reserved-owner: 2, security-refusal: 0}`; one registration; one identity-index entry; and the same committed plus prepared capture records. R7 adds only the quarantine marker outside `captures/` when marker persistence succeeds.

Additional executions: R7 stub self-test **215/215**, superseded-build witnesses **34/34**, and measurement validation **160/160 with zero violations**.

## 2. Gate finding: marker-write failure still permits restart bypass

### Source

`poc/stub/stub_server.py:649-705` explicitly makes marker persistence best-effort. Any exception during directory creation, marker-file creation/write/fsync, directory open/fsync, or close is converted to:

```text
marker_persisted: false
marker_error: <exception>
```

The current process remains quarantined, but no second persistence mechanism or startup binding is installed. Startup only refuses when `_scan_quarantine_markers` finds a marker file or cannot list an existing marker directory (`stub_server.py:708-755`). A missing directory or an empty directory is interpreted as no quarantine.

### Deterministic reproductions

I first induced the already-accepted genuine quarantine condition: committed publication failed, rollback of the success-named committed record failed, the ambiguous committed record survived, and the raising process returned 503 and failed closed.

I then independently forced two marker failures before any marker file existed:

1. `os.makedirs(<data>/storage_quarantine/<candidate>)` raises `EROFS`.
2. Marker-file `open(..., "w")` raises `EACCES` after the marker directory exists.

Both produced the same result, repeated three times:

```text
initial response:                 503 refused-storage-quarantine
ambiguous committed record:       survives
marker_persisted:                 false
current-process health:           storage_quarantined = true
fresh-process health, same path:  storage_quarantined = false
fresh-process registration:       200 registered
fresh-process quarantine count:   0
```

This is the R6 restart bypass narrowed to the exact condition most likely to accompany a storage incident: the filesystem cannot create the new marker. Surfacing `marker_persisted: false` is useful diagnostics, but it is not either remedy permitted by item 5. The marker was not persisted, and the start command/runbook is not bound so restart cannot bypass reconciliation.

There is also a contradictory health instruction at `stub_server.py:1357-1365`: even when `marker_persisted` is false, `/health` says “restarting does not clear it.” The executed restart proves that statement false.

**Disposition:** gate-blocking. Item 5 is not closed.

## 3. Item 3 was loosened past its stated fact boundary

### Source

The new early return is:

```python
if not linked_path and not tmp:
    _release_pool(pool)
    return
```

at `poc/stub/stub_server.py:831-835`.

That tests whether the caller received and assigned a path, not whether a temp or final name ever existed on disk. The task packet required the latter.

### Deterministic reproduction

The independent probe wraps the real `tempfile.mkstemp` so it:

1. creates the real exclusive temp file;
2. closes the real fd;
3. raises before returning the `(fd, path)` pair to `write_capture`;
4. also forces the rollback directory-open proof to fail.

The local `tmp` therefore remains `None`, although the temp file exists.

Pinned R6 and R7 diverge exactly at the new relaxation:

| Result | Pinned R6 | R7 |
|---|---|---|
| Temp artifact survives | yes | yes |
| Rollback proof fault lands | yes | bypassed by early return |
| Returned/raised result | `CaptureQuarantine` | ordinary `CaptureError` |
| Quarantine | 1 | 0 |
| Capture quota | retained | released |

R7 therefore says “nothing created, nothing to prove” while an actual temp artifact exists and the rollback proof is unavailable. This is not a theoretical rewrite of the requirement: R6's accepted policy already treats a persistent temp artifact as quarantine-worthy.

**Disposition:** item 3's ordinary `os.makedirs` case is fixed, but the implementation does not actually track artifact creation. The relaxation is too broad.

## 4. Item 4 is correct for `OSError`, but not exception-type complete

### Source

After rollback directory fsync sets `rollback_durable = True`, the close handler catches only `OSError` (`poc/stub/stub_server.py:868-885`). `_release_pool(pool)` occurs later at line 906.

### Deterministic reproduction

I allowed the real rollback deletion, real rollback directory fsync, and real directory close to complete, then raised `RuntimeError` from the close wrapper. On both R6 and R7:

```text
rollback directory fsync succeeded: true
real close completed:                true
remaining records:                   0
error escaping write_capture:        RuntimeError
storage anomaly recorded:            0
quarantine:                           0
capture quota retained:              1
```

This does not create the authority contradiction from R6—the rollback is durable and no record survives—but it directly misses item 4's required result: a post-fsync close error must be a recorded soft anomaly and must not retain quota. The supplied probe covers only `OSError`, so it does not see this repeated exception-type blind spot.

**Disposition:** not over-loosened for the ordinary operating-system error, but incomplete under the same non-`OSError` tail-fault model that motivated R7 item 1.

## 5. Required R8 correction

Keep the next packet narrow.

1. **Marker failure must have an enforceable fallback.** `marker_persisted: false` cannot be only diagnostic. Use a second durable control location or bind the actual start command/supervisor so a process cannot reopen the same candidate/data directory without explicit reconciliation. The current health text must be conditional and truthful.
2. **Track temp creation as a filesystem fact.** Select and assign the temp pathname before the exclusive create operation, or otherwise make a post-create/pre-return exception discoverable. The no-artifact early return may run only after proving neither a temp nor final name ever existed.
3. **Make the rollback post-durable tail exception-type complete.** Once rollback fsync returns, every later close-tail exception must be recorded as a soft anomaly and quota release must still occur. Add a non-`OSError` red-before-green case; the settled publication-tail ruling need not be revisited.
4. Re-run unchanged: rollback 5/5, capture-fault 9/9, oracle 7/7 / 33, barriers 6/6, current-process fail-closed, and prepared-record/quota behavior.
5. Add the two marker-before-file failures and the post-create/pre-return temp fault to the mandatory red-before-green set, with fault-landed assertions on R6 and R8.

## Harness qualification

The security and regression suites above were executed. The separate structural n8n harness could not be fully rerun because `n8n-workflow` is not bundled and the available internal npm registry returned 404 for it. The Python boundary, cost, receipt, and measurement checks ran; this dependency limitation is not the basis of the FAIL verdict and does not affect the R6-confirmed security behaviors listed above.

## Gate disposition

- **R7:** FAIL.
- **Security gate:** open.
- **Hands-on n8n versus Zapier session:** blocked pending the narrow correction and re-check.
- **Concurrency, provider contracts, the `25_` contract, and the broader POC architecture:** not reopened.
