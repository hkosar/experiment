# Diffs — TASK-0007 R6

Changed files diffed against **the R5 baseline the relay shipped**
(`r6-relay/pkg/poc/`), verified 89/91 byte-identical to my R5 return before any
editing (the two that differ are the regenerate-by-running evidence outputs).

- `stub_stub_server.py.diff` — the SEC-R4-01 correction: `_rollback_capture`
  (proven removal + its own directory fsync, or `CaptureQuarantine`), the
  durability boundary moved inside the `try` so a close error cannot downgrade
  a durable record, the two storage registers, dispatch failing closed while
  quarantined, and `/health` reporting it.
- `stub_capture_fault_suite.py.diff` — the four R6 rollback boundaries, added
  alongside the R5 boundaries which remain as the regression proof.
- `stub_probe_runner.py.diff` — the verifier's rollback probe and its criteria.
- `stub_selftest_stub.py.diff` — the R6 block, including the quarantine driven
  through a real route and the fail-closed check.

Not diffed: `stub/r5_reference/stub_server_r5.py` is a byte-identical copy of the
R5 build (`sha256 972c30d5…3dd15e68`) — verify with `sha256sum`, as the suites do
before loading it. `stub/security_probes/chatgpt_*` are the verifier's own files.
`harness/out/**` and `stub/out/**` regenerate by running.
