# 44B — R6 reproduction notes

All commands below were run against the extracted packet at:

```text
/mnt/data/r6_recheck_work/pkg
```

## 1. Packet integrity

```bash
sha256sum /mnt/data/R6_Final_Recheck*.zip
cd /mnt/data/r6_recheck_work/pkg
sha256sum -c SHA256SUMS.txt
```

Both input archives produced:

```text
abc0e6fcae6843fb0e46c6a6bfb12f56ce1020cf3e2bab5ab96c2f141c173dbb
```

`SHA256SUMS.txt` verified 123 entries. `authority_manifest.json` independently verified 122 listed files.

The base tree was reproduced with:

```bash
mkdir /tmp/r6-base
cd /tmp/r6-base
tar -xf /mnt/data/r6_recheck_work/pkg/base_snapshot.tar
git init -q
git add -Af .
git write-tree
```

Result:

```text
845b5ee34b53979d565cbf09c719a3a649e03429
```

## 2. Existing verifier rollback probe

```bash
cd /mnt/data/r6_recheck_work/pkg
python3 40_security_probes/chatgpt_r5_cleanup_rollback_probe.py \
  poc/stub/stub_server.py > /tmp/r6.json
python3 40_security_probes/chatgpt_r5_cleanup_rollback_probe.py \
  poc/stub/r5_reference/stub_server_r5.py > /tmp/r5.json
```

Applying the packet's unchanged `_c_rollback` criterion:

```text
R6:       5/5 scenarios
pinned R5: 0/5 scenarios
```

## 3. Existing capture-fault regression

```bash
cd /mnt/data/r6_recheck_work/pkg/poc/stub
python3 capture_fault_suite.py stub_server.py
python3 capture_fault_suite.py r5_reference/stub_server_r5.py
```

Results:

```text
R6:       9/9
pinned R5: 5/9
```

## 4. Independent R6 quarantine-integrity probe

```bash
python3 44_security_probes/chatgpt_r6_quarantine_integrity_probe.py \
  /mnt/data/r6_recheck_work/pkg/poc/stub/stub_server.py
```

Summary:

```json
{
  "current_process_fail_closed": true,
  "ordinary_failure_with_durable_committed_evidence": true,
  "post_rollback_fsync_spurious_quarantine": true,
  "preartifact_spurious_quarantine": true,
  "restart_bypasses_explicit_recovery": true
}
```

The raw result is included at:

```text
44_raw_evidence/chatgpt_r6_quarantine_integrity_r6.json
```

## 5. R5-versus-R6 post-durable comparison

```bash
python3 44_security_probes/post_durable_interrupt_compare.py \
  /mnt/data/r6_recheck_work/pkg/poc/stub/r5_reference/stub_server_r5.py \
  /mnt/data/r6_recheck_work/pkg/poc/stub/stub_server.py
```

Pinned R5 leaves only `prepared-artifact-register` and one owner-pool unit. R6 leaves both `prepared-artifact-register` and `committed-artifact-register`, returns the same ordinary 500 claim, removes all live registration state, retains two owner-pool units, and does not quarantine.

The deterministic fault wrapper calls the real directory close before raising `KeyboardInterrupt`; it does not bypass or weaken file publication.

## 6. Oracle and concurrency regressions

```bash
cd /mnt/data/r6_recheck_work/pkg/poc/stub
python3 oracle_suite.py stub_server.py
python3 barrier_suite.py stub_server.py
```

Results:

```text
oracle:  7/7 scenarios, 33 clauses
barrier: 6/6 scenarios
```
