# Diffs — TASK-0007 R3

Every changed file, diffed against **the R2 baseline the relay shipped**
(`r3-relay/pkg/poc/`), which was verified 43/43 byte-identical to the released
R2 return before any editing began.

Two files have no left-hand side because they are new this round; they are
diffed against `/dev/null`:

- `data_validate_measurements.py.diff` — the §D validator, allowlisted as new
- `stub_r2_reference_README.md.diff` — **AUDIT-4**, outside the enumerated
  allowlist

`stub/r2_reference/stub_server_r2.py` has no diff because it is not new content:
it is a byte-identical copy of the stub returned at R2
(`sha256 a2aea25da2af97368db4eedd9b027da52a84740a9447936c6b50ce0c960900f9`), and
a diff against its own source would be empty by construction. Verify it with
`sha256sum` instead — `r1_witnesses.py` does exactly that before loading it, and
refuses to continue on a mismatch.

`harness/out/**` and `stub/out/**` are not diffed: `25_` §0 marks them
regenerate-by-running, so their content is an artifact of the run rather than an
edit. `harness/out/**` came back byte-identical this round, which is itself the
finding that the structural report does not depend on the node-level edits made
to the workflows.
