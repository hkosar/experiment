# 40B — R5 reproduction notes

## Target hashes

```text
R5 stub: 972c30d532a957a94a8e7200c9385e387f7508673335acdc8652eb6e3dd15e68
R4 pin:  2876522bec584678c2326d002e58e9fa388b64ac9be9092c2ba1a18022450f79
```

## Run the omitted-boundary probe

From this return directory:

```bash
python3 40_security_probes/chatgpt_r5_cleanup_rollback_probe.py \
  /path/to/pkg/poc/stub/stub_server.py
```

For comparison against the defective pin:

```bash
python3 40_security_probes/chatgpt_r5_cleanup_rollback_probe.py \
  /path/to/pkg/poc/stub/r4_reference/stub_server_r4.py
```

The decisive R5 object is `committed_final_link_cleanup_failure`.

Unsafe result:

```text
status = 500
registrations = 0
identity_index = 0
transition_mirror = []
records contains committed-artifact-register with phase=committed
```

The `prepared-artifact-register` record and one reserved-owner unit are expected to remain. Their presence is not the failure. The failure is the additional committed record for state the response and live indexes say did not become effective.

## Re-run the prior verifier probes

```bash
python3 40_security_probes/chatgpt_capture_publication_fault_probe.py \
  /path/to/pkg/poc/stub/stub_server.py

python3 40_security_probes/chatgpt_capture_postlink_cleanup_probe.py \
  /path/to/pkg/poc/stub/stub_server.py
```

Both should be green on R5. They are included to show that the FAIL verdict does not dispute the ordinary paths they cover; it arises at the explicitly required cleanup-failure and rollback-durability boundaries they do not cover.

## Probe behavior by scenario

### `standalone_final_link_cleanup_failure`

1. Fully writes and file-fsyncs the temp record.
2. Links the final name.
3. Forces publication directory-open failure.
4. Forces the rollback attempt to unlink the final name to fail.
5. Records files and pool counters after restoring the real OS functions.

### `committed_final_link_cleanup_failure`

1. Allows the prepared registration record to publish normally.
2. Forces the committed record's publication directory-open failure.
3. Forces rollback removal of `committed-artifact-register-*.json` to fail.
4. Records HTTP result, live registration indexes, transition mirror, capture files, and pool counters.

### `rollback_directory_fsync`

1. Allows the temp-file fsync.
2. Forces the publication directory fsync to fail.
3. Counts whether a later rollback directory fsync is attempted.

R5 reports `rollback_directory_fsync_observed: false`.

### `post_fsync_close_plus_cleanup_failure`

1. Allows the publication directory fsync to succeed.
2. Forces directory-fd close to fail.
3. Forces rollback removal of the final record to fail.

This isolates the fact that `published=True` is assigned after close rather than at the successful directory-fsync boundary.

### `persistent_temp_cleanup_failure`

Forces both the initial temp unlink and the rollback retry to fail. R5 leaves a hidden temp artifact and releases the pool reservation.

## Files in this return

- `40_ChatGPT_R5_Single_Finding_Recheck.md` — formal verdict.
- `40A_ChatGPT_R5_Probe_Evidence.json` — structured findings and observations.
- `40_security_probes/chatgpt_r5_cleanup_rollback_probe.py` — independent omitted-boundary probe.
- `40_security_probes/*_r5.json` and `*_r4*.json` — raw outputs.
- `40_source_evidence/` — source excerpts, R4-to-R5 diff, and packet integrity evidence.
- `40_regression_logs/` — completed corroborating regressions and disclosed environment-limited runs.
