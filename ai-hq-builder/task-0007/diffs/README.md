# Diffs — TASK-0007 R8

Changed files diffed against **the R7 baseline the relay shipped**
(`r8-relay/pkg/poc/`), verified **102/102 byte-identical to my R7 return** before
any editing.

- `stub_stub_server.py.diff` — `51_`'s four gating items. **A**: two independent
  durable marker locations plus a write-free disk fact (a surviving `.tmp`), and
  truthful disclosure when none of them lands. **B**: `_restart_posture()` — one
  function that produces every operator-facing statement about restart
  behaviour, called from `/health` and both 503 bodies, so the sentence cannot
  disagree with the field beside it. **C**: the temp prefix is reserved and bound
  *before* any create, and `_existing_temp_artifacts` asks the directory instead
  of the local variable; the early return may run only once absence is
  established. **D**: every handler in `_rollback_capture` catches
  `BaseException`, so the rollback tail is exception-type complete and the quota
  release still runs. Plus the **§1 fourth instance**: the capture-path
  containment check was lexical (`abspath` + `startswith`) and is now real
  (`realpath`).
- `stub_probe_runner.py.diff` — `_retarget_pair`, which rewrites the two absolute
  path bindings in the verifier's R8 probe and proves line by line that nothing
  else moved; and `_c_r7_adversarial`, whose criteria come from `51_` items A/C/D
  and each of which asserts the injected fault fired as well as the outcome.
- `stub_selftest_stub.py.diff` — the R8 block: the R7 pin, the probe red against
  it and green against this build, and all five `51_` §4 mandatory cases —
  including the both-locations-fail case the verifier's probe does not cover,
  which is what shows the fallback is a second mechanism and not a moved
  goalpost.
- `runbooks_*.diff` — the operator instruction `51_` item A requires for the
  no-durable-record case, in all three runbooks.

**Not changed:** `stub/capture_fault_suite.py` is byte-identical to R7 — `51_`
requires its 9/9 to re-run unchanged, so it is this round's regression proof, and
it passes 9/9 against the pinned R7 build too, which is exactly why R8 needed the
verifier's new probe to find these three defects.

**`PROPOSED-NOT-APPLIED-item-E-run_all.sh.txt`** — item E requires editing a file
the same packet's denylist forbids editing. The patch is written out and verified
but **not applied**; see the Delivery Record §5, CR-R8-01. `.txt`, not `.diff`, so
it cannot be mistaken for one of the applied diffs.

Not diffed: `stub/r7_reference/stub_server_r7.py` is a byte-identical copy of the
R7 build (`sha256 69b98fb0…f6b0ac91`) — verify with `sha256sum`, as the suites do
before loading it. `stub/security_probes/chatgpt_r7_adversarial_recheck.py` is
the verifier's own file, copied byte-identical from `49_security_probes/`
(`sha256 b7db68d4…08436c366`). `harness/out/**` and `stub/out/**` regenerate by
running.
