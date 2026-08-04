# Diffs — TASK-0007 R5

Changed files diffed against **the R4 baseline the relay shipped**
(`r5-relay/pkg/poc/`), verified 69/71 byte-identical to my R4 return before any
editing (the two that differ are the regenerate-by-running evidence outputs).

- `stub_stub_server.py.diff` — **the whole of the SEC-R4-01 correction.** One
  function, `write_capture`: `linked_path` tracked separately, `published` set
  only after the directory fsync, and the `finally` removing the final path as
  well as the temp. Nothing else in the service changed.
- `stub_selftest_stub.py.diff` — the SEC-R4-01 block (8 cases).
- `stub_probe_runner.py.diff` — the verifier's two new probes and their criteria.
- `stub_capture_fault_suite.py.diff` — new, diffed against `/dev/null`.

Not diffed: `stub/r4_reference/stub_server_r4.py` is a byte-identical copy of the
R4 build (`sha256 2876522b…22450f79`) — verify with `sha256sum`, as the suites do
before loading it. `stub/security_probes/chatgpt_*` are the verifier's own files,
copied byte-identically. `harness/out/**` and `stub/out/**` regenerate by running.
