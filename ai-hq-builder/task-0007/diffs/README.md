# Diffs — TASK-0007 R4

Changed files diffed against **the R3 baseline the relay shipped**
(`r4-relay/pkg/poc/`), verified 45/47 byte-identical to my R3 return before any
editing (the two that differ are the regenerate-by-running evidence outputs).

New this round, diffed against `/dev/null`: `stub/probe_runner.py`,
`stub/barrier_suite.py`, `stub/oracle_suite.py`, `stub/security_probes/README.md`.

Not diffed, and why:

- `stub/r3_reference/stub_server_r3.py` — a byte-identical copy of the build the
  reviewer examined (`sha256 7f13494e…5b90f572`, the hash `32_` records). A diff
  against its own source is empty by construction; verify with `sha256sum`, as
  `r1_witnesses.py` and `probe_runner.py` both do before loading it.
- `stub/security_probes/*` — the reviewer's own nine scripts and nine recorded
  outputs, copied byte-identically from the relay's `31_security_probes/`.
- `harness/out/**`, `stub/out/**` — regenerate by running.
