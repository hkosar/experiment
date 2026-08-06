# 54B — R8 executed re-check reproduction notes

## Input and working copies

- Input archive: `/mnt/data/R8_Recheck.zip`
- Authoritative extraction used for integrity and reading: `/mnt/data/R8_audit/pkg`
- Disposable execution copy: `/mnt/data/R8_exec`
- Base snapshot reconstruction directory: `/mnt/data/R8_base_repro`
- Verifier logs: `/mnt/data/R8_verifier_logs`

The execution copy was used so generated `out/`, cache and temporary artifacts could not alter the authoritative extraction.

## Integrity procedure

1. Hash the received ZIP with SHA-256.
2. Extract it without using any prose as authority before integrity checks.
3. Parse every nonblank `SHA256SUMS.txt` row and verify the target bytes.
4. Parse all `authority_manifest.json` entries and independently verify file presence and SHA-256.
5. Extract `base_snapshot.tar` to an empty directory.
6. Run:

```bash
git init -q .
git add -Af .
git write-tree
```

The reproduced tree was `1e7825af3406e974899ebe1ffd0b311683d2dd71`, matching `BASE_BINDING.txt` and `authority_manifest.json`.

## Executed target bindings

- R8 `poc/stub/stub_server.py` SHA-256: `5df1408fdf2fd5dbcb5d2577a20c14699009493c32de1ba7c0d6c347c44bf7a1`
- Pinned R7 `poc/stub/r7_reference/stub_server_r7.py` SHA-256: `69b98fb09ae94d4f38b30e3e2d2179045fe4e50b529033940a7ad1ccf6b0ac91`
- Packet copy and executable in-tree copy of `chatgpt_r7_adversarial_recheck.py`: both `b7db68d4f43a725ac9e460446640b975362c33fa5ce94a80b508dd408436c366`
- Independent R8 adversarial probe: `282a654e2ea2ae62e4f4c892c3728b7b50b50a53fa0051bf70ebdacf8c1426e6`

## Required runs

The return bundle contains the stdout/stderr, JSON and return-code records for:

- `selftest_stub.py`
- exact `chatgpt_r7_adversarial_recheck.py` against R8 and pinned R7
- `capture_fault_suite.py` against R8 and pinned R7
- `oracle_suite.py`
- `barrier_suite.py`
- `chatgpt_r6_quarantine_integrity_probe.py` against R8 and pinned R7
- `chatgpt_r5_cleanup_rollback_probe.py` against R8 and pinned R7
- `post_durable_interrupt_compare.py`
- `r1_witnesses.py`
- measurement validation
- `poc/harness/run_all.sh`

## Independent adversarial run

```bash
python 54_security_probes/chatgpt_r8_adversarial_recheck.py \
  /path/to/extracted/poc/stub/stub_server.py \
  > 54_security_probes/chatgpt_r8_adversarial_results.json
```

The probe uses isolated temporary data directories and imports the extracted R8 target directly. It allows the real filesystem operations specified in each case to complete before raising the injected tail fault. It records injection counters and concrete paths so a result cannot become green merely by routing around the fault.

The final Boolean summary was identical across the retained result plus three additional clean executions. In the summary, `true` on a named failure flag means the defect reproduced; `both_marker_fail_truthful_none_control: true` is the positive control and means the genuinely record-free branch behaved correctly.

## Environment

- Python 3.13.5
- Node.js 22.16.0
- Git 2.47.3
- Linux x86_64

No network access was used. The unavailable `n8n-workflow` dependency was not installed or vendored; the resulting harness qualification is recorded separately and is not part of the gate verdict.
