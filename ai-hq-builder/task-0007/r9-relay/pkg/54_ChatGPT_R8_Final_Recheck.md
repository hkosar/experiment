# 54 — ChatGPT R8 Final Executed Re-check

**Integrity block**

- **Attached ZIP SHA-256:** `c06588ad99b39eb9cc3ec1c76c7c5e0a65ecaffc645a03b6bc654fb77ec83cbf`
- **`SHA256SUMS.txt`:** `118/118` entries valid
- **`authority_manifest.json`:** `117/117` listed files present and SHA-valid
- **Tree reproduced from `base_snapshot.tar`:** `1e7825af3406e974899ebe1ffd0b311683d2dd71`

The archive arrived intact. I extracted it, reproduced the base tree independently, compared the packet probe to the in-tree executable copy, ran the required R8-versus-pinned-R7 cases, reran the accepted R6/R7 regressions, and then ran an independent adversarial probe against the extracted R8 implementation.

# Verdict

**FAIL — the security gate remains open. The hands-on n8n-versus-Zapier session remains blocked.**

R8 genuinely fixes the exact Item C and Item D failures reported at R7. Its fallback marker is also a real second write location, not a sham relocation. All required R6/R7 regression checks remained green.

However, Items A and B are not closed. The new marker layer still substitutes “the marker-writing function returned without an exception” for the disk facts it is meant to establish. I reproduced cases where a marker is already present or durably committed, but the live process reports `restart_protection: "none"` and says a restart **will** clear quarantine. A fresh process then finds that same disk fact and refuses authority transitions. I also reproduced incomplete and unsafe recovery inventories and the open scan-once multi-process bypass.

The settled post-publication Ctrl-C ruling was not reopened. Its exact comparison remains green on R8 and pinned R7.

## Disposition by requested item

| Item | Disposition | Executed result |
|---|---|---|
| A — unpersisted marker must not be merely diagnostic | **FAIL** | Primary-failure fallback works, and the genuine no-record control is truthful. But partial markers, post-durable close errors, and a surviving write-free temp are all misclassified in the live process. |
| B — health/503/runbook restart claims conditional and true | **FAIL** | Claims are false in both directions; `durable_records` can omit a real sibling marker or identify an entire directory as a record to delete. |
| C — temp creation tracked as a filesystem fact | **PASS** | Post-create/pre-return temp is discovered; rollback proof is attempted; failure quarantines and retains quota. The ordinary pre-artifact `makedirs` case remains ordinary. |
| D — rollback post-durable tail exception-complete | **PASS** | A non-`OSError` after real deletion, rollback fsync and real close becomes a soft anomaly; quota releases; no hard quarantine. |
| E — optional harness distinction | **DEFERRED / NON-GATING** | `n8n-workflow` remains unavailable in this environment. This is not a basis for the gate verdict. |
| R6/R7 confirmed behavior | **PASS** | Required regressions and the settled interrupt comparison remained green. |

# Gate-blocking findings

## 1. The marker writer still classifies exceptions, not disk facts

The controlling code is `poc/stub/stub_server.py:709-731` and `734-797`.

`_write_marker()` returns an error for **any** exception through the directory-close tail. `_persist_quarantine()` then treats only `why is None` as evidence that a record landed. That is not equivalent to “no record exists” or “no durable record exists.”

### 1.1 Post-durability directory-close exception produces a false `none` claim

I induced a genuine committed-record rollback failure, then allowed both quarantine marker writes to complete through:

- JSON write and flush;
- marker file fsync;
- parent directory fsync;
- the real directory close.

After each real close, the probe raised `RuntimeError` from the wrapper. The injected fault fired twice, once for each marker location.

Executed result:

- initial status: `503 refused-storage-quarantine`;
- primary marker exists as valid JSON;
- fallback marker exists as valid JSON;
- both marker files were fsynced;
- both parent directories were fsynced;
- live incident: `marker_persisted: false`, `restart_protection: "none"`, `durable_records: []`;
- live warning: restart **WILL** clear quarantine and **WILL** accept authority transitions;
- fresh process: quarantined;
- fresh registration: `503`.

The durable fact and the operator statement directly contradict each other. This is the same post-durability classification error R7 fixed in the publication and rollback tails, reintroduced in the new marker writer.

### 1.2 Partial marker files are present, but the live process says nothing exists on disk

The source explicitly says at `stub_server.py:712-714` that a partial marker is still a marker and that presence is the signal. The implementation does not honor that statement in the raising process.

I allowed `open(..., "w")` to create each marker, wrote 28 bytes, then raised `ENOSPC` during JSON output. Both primary and fallback marker files survived. The live process reported:

- `marker_persisted: false`;
- `restart_protection: "none"`;
- `durable_records: []`;
- “nothing on disk will tell a new process what happened here.”

A fresh process treated the unreadable files as quarantine signals and refused registration with `503`.

This is a direct Item A/Item B failure: path presence is a disk fact, but the live classification uses function success as its proxy.

### 1.3 The “write-free” temp mechanism is not reflected in the live posture

R8 correctly discovers surviving temps during a fresh-process scan at `stub_server.py:799-859`. But `_restart_posture()` at lines `961-1010` recognizes only `recovered_from_disk_fact`, which exists **after a restart scan**. It does not recognize the live incident’s `surviving_temp_path` or `surviving_temp_paths`.

I created a real temp, raised before `mkstemp` returned the pathname, forced temp rollback to fail, and forced both marker writes to fail before creating markers. The live incident contained the exact surviving temp path, yet reported:

- `restart_protection: "none"`;
- `survives_restart: false`;
- `durable_records: []`;
- restart **WILL** clear quarantine;
- “nothing on disk will tell a new process.”

The temp existed. A fresh process found it as `recovered_from_disk_fact`, reported it in `durable_records`, and refused registration with `503`.

That independently fails Fable’s requested write-free-temp check.

### 1.4 Positive control: genuine no-record failure is reported truthfully

To ensure the probe was not merely rejecting every `none` result, I also forced both marker writes to fail before either path was created and left no temp artifact. In that control:

- no primary marker existed;
- no fallback marker existed;
- no surviving temp existed;
- the live process reported `restart_protection: "none"`;
- a fresh process started clean and accepted registration with `200`.

So R8’s `none` branch is valid for a real no-record case. The defect is that materially different disk states are collapsed into that same branch.

## 2. Recovery inventory is incomplete and can be unsafe

The relevant code is `stub_server.py:889-936`, `961-1010`, and `1697-1714`; the operator instruction is in `poc/runbooks/RUNBOOK-n8n.md:50-59` and the corresponding owner runbook.

### 2.1 Restart loses the sibling relationship between the two markers

When both normal marker writes succeed, the raising process lists both paths. On restart, the scanner reads them as two independent incidents. `/health` exposes only the first incident and derives `durable_records` only from that incident.

Executed result:

- initial durable records: 2;
- restart incidents: 2;
- restart `durable_records`: 1;
- I deleted every path the restart response instructed the operator to delete;
- another fresh process remained quarantined on the unreported sibling marker.

The R8 split criterion therefore did not preserve an actionable reconciliation property. “Delete every path in `durable_records`” is insufficient after the restart that the mechanism exists to protect.

### 2.2 A fully durable primary marker can be omitted when only the fallback returns success

I allowed the primary marker through file fsync, parent-directory fsync and real close, then raised from the close wrapper. The fallback completed without error.

The live response listed only the fallback under `durable_records`; the real primary marker appeared only inside the failed-attempt diagnostics. Deleting every listed durable record left the primary marker, and the next process remained quarantined.

A post-durable tail anomaly must not remove a real marker from the recovery inventory.

### 2.3 Scan errors are mislabeled as durable records

At `stub_server.py:905-912` and `924-931`, a directory-listing error is represented by putting the directory path into `recovered_from_marker` and setting `restart_protection: "durable"`.

That creates two contradictions:

1. A transient primary-directory `EIO` produced `survives_restart: true` and a purported durable record whose path did not exist. Once the injected fault disappeared, a fresh process started clean and accepted registration with `200`.
2. A transient fallback-directory `EIO` reported the **entire data directory** as the durable record. It was a directory containing unrelated operator data. The runbook says to delete every path in `durable_records`.

A scan failure is a reason to fail the current process closed, but it is not itself a durable record. The posture is “unknown/unprotected unless another real disk signal exists,” and a directory that was merely unlistable must never be presented as the marker file to delete.

## 3. The scan-once multi-process bypass is real and should not be accepted

`_ensure_quarantine_scanned()` at `stub_server.py:940-958` scans once per process. `dispatch()` calls it on every request, but after the first call the Boolean gate makes later calls no-ops.

I executed the open challenge Fable explicitly sent to the verifier:

1. Process A used a candidate/data directory and completed its clean first scan.
2. Process B used the same candidate/data directory and generated a genuine quarantine with both durable markers.
3. Process A then reported healthy and accepted a new authority transition with HTTP `200`.
4. Fresh process C found the markers and refused with `503`.

The marker text says every process using the data directory refuses authority transitions. Process A disproved that statement.

Fable’s concurrence relied on an implied one-process POC usage pattern, but the runbooks did not state that as a binding invariant and the implementation does not enforce it with a lock, lease or PID ownership. A safety claim may rely on a single-process invariant only if the launch path enforces it or the operating contract states it unambiguously and prevents the second process. Neither is true here.

This finding concerns quarantine persistence across processes—the exact mechanism under review—not the already-closed request linearization or provider-contract concurrency work.

# Secondary containment findings

These are not required to reach the FAIL verdict, but they answer the requested realpath review.

## Candidate-directory symlink

The planted candidate-directory symlink is correctly refused and no outside file is written. However, the general capture pool increments before the containment check at `stub_server.py:1239-1277` and is not released on refusal. One failed containment check therefore leaks one quota unit.

## `captures/` root symlink

A pre-existing symlink at the `data_dir/captures` root is accepted. Because both `root` and `expected` are passed through `realpath`, both resolve through the same external target, and the prefix check succeeds. The probe wrote a JSON capture physically outside the configured data directory.

This still requires local/operator or prior-filesystem influence, so it is lower severity in this throwaway POC. But it is not merely the named check-to-use TOCTOU residual: the symlink exists before the check and is accepted by the check. The stated realpath correction is therefore partial.

# Required R8 and regression execution

| Execution | R8 | Comparator / qualification |
|---|---:|---|
| Shipped self-test | **250/250** | RC 0 |
| Exact R7 adversarial recheck | **4/4 green** | pinned R7 **0/4 red**; injected faults landed on both builds |
| Capture-fault suite | **9/9** | pinned R7 **9/9** |
| Acceptance oracle | **7/7, 33 clauses** | — |
| Deterministic barriers | **6/6** | — |
| R6 quarantine-integrity probe | **5/5** | pinned R7 **5/5** |
| R5 cleanup/rollback probe | **5/5** | pinned R7 **5/5** |
| Post-durable interrupt comparison | **green** | pinned R7 **green**; forced fault count 1 on both |
| Witness reproduction | **34/34** | — |
| Measurement validation | **160/160** | zero violations |
| Independent R8 adversarial probe | **10 scenarios + 1 positive control** | failure summary reproduced identically in 4 executions |

The post-durable interrupt comparison preserved the accepted behavior on both R8 and pinned R7:

- status `200 registered`;
- one registration and one identity-index entry;
- pools `{general: 0, reserved-owner: 2, security-refusal: 0}`;
- one prepared and one committed record;
- zero quarantine incidents;
- injected post-durable fault fired exactly once.

Current-process fail-closed behavior and the previously accepted prepared-record/quota behavior also remained intact.

# Harness qualification

`poc/harness/run_all.sh` returned `1` because `n8n-workflow` was not installed. The Node structural validator could not load its module, and its self-test reported 9/10 because the well-formed control was rejected under that missing dependency. The Python boundary, cost and receipt checks ran as logged.

Per the R8 disposition, Item E is deferred and non-gating. This environment issue is not used as evidence for the FAIL verdict.

# Required narrow correction

1. **Represent marker state as facts, not one success Boolean.** At minimum distinguish:
   - `DURABLE`: file and parent-directory fsync completed;
   - `PRESENT_OR_UNKNOWN`: path exists, was created, is partial, or may exist after a later failure;
   - `ABSENT_KNOWN`: failure occurred before creation and absence was verified.
   A directory-close exception after parent fsync is a soft anomaly and cannot erase `DURABLE`.

2. **Include live temp facts in restart posture.** A surviving `surviving_temp_path` is itself a restart signal. Do not emit `none`, `survives_restart: false`, or “nothing on disk” while it exists.

3. **Give each quarantine event a stable incident ID and preserve the full record set.** Persist the same incident ID and complete sibling-path inventory in both markers; merge/deduplicate them on scan; expose every incident and every actual record needed for reconciliation.

4. **Never treat a scan error’s directory as a durable marker record.** Fail the current process closed, but classify persistence as unknown unless a real marker/temp fact is observed. `durable_records` must contain actual removable evidence records, never an entire data directory or a merely unlistable/nonexistent path.

5. **Enforce the one-process invariant or remove the scan-once assumption.** Use an exclusive lock/lease for each `(data_dir, candidate)`, or observe marker-generation changes/rescan before every authority transition. A future runbook sentence alone is weaker than the marker’s “every process” claim and does not stop accidental second launch.

6. **Complete containment handling.** Validate the canonical captures root itself, reject a pre-existing root symlink, perform containment before reserving quota or release quota on refusal, and carry `dirfd`/`openat`/`O_NOFOLLOW` into the production design.

7. Add red-before-green probes for:
   - partial marker creation/write failure;
   - marker directory-close failure after real file and directory fsync;
   - surviving temp plus failure at both marker locations;
   - restart reconstruction of both sibling marker paths;
   - transient primary and fallback scan failures, including an assertion that no directory enters `durable_records`;
   - two processes sharing one candidate/data directory;
   - captures-root symlink and no quota leak on containment refusal.

8. Re-run the unchanged R6/R7 regression set.

# Gate disposition

- **R8:** FAIL
- **Security gate:** OPEN
- **Hands-on n8n-versus-Zapier session:** BLOCKED
- **Items C and D:** CLOSED on their required boundaries
- **Items A and B:** OPEN
- **Settled publication-tail Ctrl-C ruling:** NOT REOPENED; regression remains green
- **Concurrency linearization, provider contracts, `25_`, and the wider POC architecture:** NOT REOPENED
