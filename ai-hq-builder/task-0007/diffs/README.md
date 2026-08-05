# Diffs — TASK-0007 R7

Changed files diffed against **the R6 baseline the relay shipped**
(`r7-relay/pkg/poc/`), verified **96/97 byte-identical to my R6 return** before
any editing; the one that differs is `stub/out/selftest.json`, a
regenerate-by-running evidence output.

- `stub_stub_server.py.diff` — the `46_` corrections. Item 1: every conversion
  in `write_capture`'s outer handler chain is now gated on the `published`
  durability flag, and `_absorb_post_durable` records a post-durability tail
  failure as a soft anomaly instead of turning it into a `CaptureError`. Item 3:
  `_rollback_capture` returns early when no temp and no final name ever existed
  — nothing created, nothing to prove. Item 4: the rollback gets the same true
  durability boundary the publication path has, so a close error after its
  directory fsync is a soft anomaly rather than a hard quarantine. Item 5:
  `_persist_quarantine` / `_scan_quarantine_markers` / `_ensure_quarantine_scanned`
  and the `/health` reporting that goes with them.
- `stub_probe_runner.py.diff` — the verifier's two R7 probes, and criteria taken
  from `46_` items 1-5. Each criterion is paired with a check that the probe's
  injected fault actually fired, because "no spurious quarantine" is trivially
  satisfiable by an injection that never lands.
- `stub_selftest_stub.py.diff` — the R7 block: the R6 pin, both probes shown red
  against it and green against this build, and items 1, 3, 4 and 5 driven
  in-process, including a genuinely fresh `Store` over the same data directory.

**Not changed:** `stub/capture_fault_suite.py` is byte-identical to R6. `46_`
item 6 requires its 9/9 to re-run unchanged, so it is the regression proof for
this round rather than evidence of this round's corrections — and it passes 9/9
against the pinned R6 build too, which is exactly why R7 needed the verifier's
new probes to find these five defects.

Not diffed: `stub/r6_reference/stub_server_r6.py` is a byte-identical copy of the
R6 build (`sha256 d0fd4c44…b0d19ac0`) — verify with `sha256sum`, as the suites do
before loading it. `stub/security_probes/chatgpt_*` and
`stub/security_probes/post_durable_interrupt_compare.py` are the verifier's own
files, copied byte-identical from `44_security_probes/`. `harness/out/**` and
`stub/out/**` regenerate by running.
