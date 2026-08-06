# Diffs — TASK-0007 R9

Changed files diffed against **the R8 baseline the relay shipped**
(`r9-relay/pkg/poc/`), verified **106/106 byte-identical to my R8 return** before
any editing.

- `stub_stub_server.py.diff` — `56_`'s items F–K.
  **F**: `_write_marker` returns a tri-state DISK FACT (`DURABLE` /
  `PRESENT_OR_UNKNOWN` / `ABSENT_KNOWN`) via `_path_fact`, which asks the
  filesystem instead of reading the exception; a close-tail failure after the
  parent-directory fsync is a recorded soft anomaly and cannot erase `DURABLE`.
  **G**: `_restart_posture` counts the live incident's `surviving_temp_paths`,
  so the write-free mechanism is visible to the raising process and not only
  after a restart. **H**: a stable `incident_id` and the complete sibling
  inventory written into *both* markers, `_merge_incidents` deduplicating by ID
  on scan, and `_quarantine_summary` exposing every incident and the union of
  every real record. **I**: `_scan_error_incident` — an unlistable directory
  fails closed as `unknown`, mints no durable claim, and never enters
  `durable_records`; `_classify_records` admits only stat-verified regular
  files. **J**: `_acquire_candidate_lock` (`flock`, `LOCK_EX | LOCK_NB`) at
  startup **and** `_refresh_quarantine` before every authority transition —
  both, for the reason given in the Delivery Record §4. **K**: containment
  moved ahead of the pool reservation, and the canonical `captures/` root
  compared against its physical location so a root symlink is refused rather
  than resolved through by both sides.
- `stub_probe_runner.py.diff` — `_c_r8_adversarial`, whose eleven checks come
  from `54_`/`56_` and each of which asserts the injected fault fired as well as
  the outcome. The verifier's **positive control** is one of the eleven and must
  stay `True`: without it, all ten defect flags are satisfiable by a build that
  simply never says `none`.
- `stub_selftest_stub.py.diff` — the R9 block: the R8 pin, the probe red against
  it and green against this build, and all eight `56_` §4 mandatory cases, run
  in-process so the fault ordinals are visible.
- `runbooks_*.diff` — the four-state `restart_protection` table and the
  one-stub-per-`(--data, --candidate)` rule, in all three runbooks.
- **`harness_run_all.sh.diff`** — CR-R8-01, **authorized in `56_` §0 for this
  return only**. `run_all.sh` is otherwise on the immutable denylist; it was
  supplied unapplied at R8 and is applied here. `NOT RUN` is now distinct from a
  check that ran and failed: FAIL/1, INCOMPLETE/2, PASS/0. No vendoring, no
  network requirement.

**Not changed:** `stub/capture_fault_suite.py` is byte-identical to R8 — `56_`
§3 requires every prior confirmed regression to re-run unchanged, so it is this
round's regression proof, and it passes 9/9 against the pinned R8 build too,
which is why R9 needed the verifier's new probe to find these findings.

Not diffed: `stub/r8_reference/stub_server_r8.py` is a byte-identical copy of
the R8 build (`sha256 5df1408f…c44bf7a1`) — verify with `sha256sum`, as the
suites do before loading it. `stub/security_probes/chatgpt_r8_adversarial_recheck.py`
is the verifier's own file, copied byte-identical from `54_security_probes/`
(`sha256 282a654e…8c1426e6`). `harness/out/**` and `stub/out/**` regenerate by
running.
