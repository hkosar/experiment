# 36B — Reproduction Notes: TASK-0007 R4 Concurrency Re-verification

## 1. Environment

The independent probes use Python 3 and the standard library only. They import the target stub by filesystem path and replace its process-local globals with a clean `Store`, `SecretIndex`, descriptor key, and temporary capture directory.

The commands below assume this return's `36_security_probes/` directory is the current directory and the R4 packet has been extracted elsewhere.

```bash
R4=/path/to/R4_PACKET/poc/stub/stub_server.py
R3=/path/to/R4_PACKET/poc/stub/r3_reference/stub_server_r3.py
```

## 2. Controlling concurrency probe

```bash
python chatgpt_r4_prelock_probe.py "$R4" > chatgpt_r4_prelock_r4.json
python chatgpt_r4_prelock_probe.py "$R3" > chatgpt_r4_prelock_r3.json
```

The probe installs an external release gate at route-handler entry. It does not throw inside the transition and does not bypass dispatch, authentication, route policy, preconditions, evidence, or state publication.

Expected controlling distinction:

```text
R4: handler_entries_before_release = 1 for every identity
R3: handler_entries_before_release = 2 for every identity
```

R4 must finish with one registration, one case/token, one ActionRequest/capability, one receipt, and one run. R3 should reproduce duplicate effective objects.

## 3. Revoke-generation probe

```bash
python chatgpt_r4_revoke_epoch_probe.py "$R4" > chatgpt_r4_epoch_r4.json
python chatgpt_r4_revoke_epoch_probe.py "$R3" > chatgpt_r4_epoch_r3.json
```

Expected:

```text
R4: revoke_returned_while_delivery_paused = false
R3: revoke_returned_while_delivery_paused = true
```

The R3 output should show revoke 200 followed by delivery 200 and a final receipt. R4 may validly linearize delivery first, with revoke subsequently returning 409 because the capability is already terminal.

## 4. Supplemental eight-request check

```bash
python chatgpt_r4_nway_probe.py "$R4" > chatgpt_r4_nway_r4.json
```

Expected: `handler_entries_before_release` is 1 in all five scenarios, with one effective winner and seven truthful losers.

This is supplemental rather than a replacement for the required two-request old/new witness.

## 5. Gate-blocking capture-publication probe

```bash
python chatgpt_capture_publication_fault_probe.py "$R4" \
  > chatgpt_capture_publication_fault_r4.json
python chatgpt_capture_publication_fault_probe.py "$R3" \
  > chatgpt_capture_publication_fault_r3.json
```

The current R4 target is expected to fail this test:

```text
standalone_directory_fsync
- returns CaptureError
- leaves one final JSON record
- leaves one capture quota unit consumed

committed_registration_directory_fsync
- returns HTTP 500 / capture-failed
- registrations = 0
- identity_index = 0
- transition_mirror = empty
- committed-artifact-register file remains
- committed record says final_status = REGISTERED
- reserved-owner pool = 2
```

The known-defective R3 target also fails, satisfying the requirement that the criterion can go red. A corrected R5 target must instead remove the failed committed record and release its quota while preserving only any intentionally retained prepared-attempt evidence.

## 6. Post-link cleanup boundaries

```bash
python chatgpt_capture_postlink_cleanup_probe.py "$R4" \
  > chatgpt_capture_postlink_cleanup_r4.json
```

The current R4 target produces:

- link failure: no file, no quota — control passes;
- temp-unlink failure after link: final file remains — fails;
- directory-open failure after link: final file remains and quota remains — fails.

## 7. Legacy probe handling

The packet's nine legacy scripts and nine archived outputs were compared byte-for-byte with the verifier originals. The archived outputs are the original R3 FAIL evidence, not post-R4 outputs.

Four non-race legacy probes were retargeted by changing only their single `SRC=` line and ran green individually. The five internally synchronized race probes remain red for the reason adjudicated in the main report. Some of the direct-dispatch scripts emitted their complete red JSON but did not terminate cleanly during interpreter shutdown against R4; their emitted JSON was captured after the script body completed. No claim relies on treating a hang or timeout as a pass.

## 8. Evidence files

- `chatgpt_r4_prelock_r4.json` / `chatgpt_r4_prelock_r3.json` — controlling two-request old/new evidence.
- `chatgpt_r4_epoch_r4.json` / `chatgpt_r4_epoch_r3.json` — revoke ordering evidence.
- `chatgpt_r4_nway_r4.json` — supplemental eight-request evidence.
- `chatgpt_capture_publication_fault_r4.json` / `_r3.json` — directory-fsync and false-commit evidence.
- `chatgpt_capture_postlink_cleanup_r4.json` — link/unlink/directory-open boundaries.
- `chatgpt_r4_legacy_nonrace_results.json` — four green unchanged legacy controls.
- `legacy_more_race_r4.json` / `legacy_security_probe_r4.json` — emitted red legacy race results.
- `r4_barrier_*.log` / `r4_oracle_*.log` — independent reruns of the Builder suites.
