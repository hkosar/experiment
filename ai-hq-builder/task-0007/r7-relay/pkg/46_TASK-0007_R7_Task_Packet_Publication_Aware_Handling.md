# 46 — TASK-0007 Round R7: publication-aware handling, scoped quarantine, restart posture

**Scope: five narrow items in `write_capture`, `_rollback_capture`, their callers, and startup.** Do **not** reopen concurrency, the `25_` contract, provider contracts or the POC architecture — all remain closed and accepted. Every R6 behaviour the verifier confirmed must re-run unchanged.

## Context

R6 closed the four named `OSError` boundaries and its quarantine genuinely fails the current process closed — independently confirmed. Three items remain. One is the same authority contradiction displaced into the post-durability tail; two are the strict-fsync rule being applied **beyond its scope**, which is an availability defect and, in practice, a risk of the stub locking up on the owner mid-session for no reason.

## Required corrections

1. **Make exception handling publication-aware.** Once the publication directory fsync has succeeded and `published` is true, **no later exception may be converted into an ordinary `CaptureError`, and no caller may remove provisional live state on its account.** A durably committed capture is committed. Today a non-`OSError` from the post-publication tail reaches `except BaseException`, becomes `CaptureError`, and `h_owner_artifact_register` then tears down the registration and reports it "not effective" beside a durable `committed` record saying `REGISTERED`.

2. **Add the exact red-before-green probe.** The corrected build must **fail first against R6** and then pass: raise a **non-`OSError` interruption immediately after the real committed directory close**, and require that no ordinary ineffective claim appears beside a committed record.

3. **Do not quarantine when no artifact was ever created.** Track whether a temp or final name ever existed. If neither did, there is **nothing to prove** — release the capture reservation and return an ordinary capture failure. Today a failure before any name exists (e.g. `os.makedirs` failing) still attempts the rollback directory fsync, reports "rollback directory fsync failed (ENOENT)" and hard-quarantines with `surviving_final_path: null` and `surviving_temp_path: null`.

4. **Give the rollback path a durability boundary, mirroring publication.** Mark rollback **proven immediately after the rollback directory fsync returns**. A subsequent directory-**close** error is a **recorded soft anomaly**: it must not retain quota and must not hard-quarantine. The publication path already has a true-durability flag before close; the rollback path must have the same.

5. **Resolve the restart posture.** Quarantine currently lives only in `STORE.storage_quarantine`, which a fresh process initialises empty — so a restart with the same candidate and data directory silently clears it while the ambiguous committed record remains on disk. Either **persist a quarantine/startup marker** that a new process must find and require reconciliation for, **or** bind the runbook/start command so a restart cannot bypass manual reconciliation. State which, and why.

6. **Re-run unchanged and report:** verifier rollback probe **5/5**, capture-fault suite **9/9**, oracle **7/7 / 33 clauses**, concurrency barriers **6/6**, and the accepted prepared-record/quota behaviour (the legitimate `prepared` record and its single reserved-owner unit must still survive a failed committed registration).

## Method and constraints

Pin R6 as `r6_reference/` exactly as prior pins are done. **Red-before-green is mandatory** — every criterion must be shown failing against the pinned R6 before it is claimed green; that rule has caught a vacuous test and several injection-evasions across this workstream. Immutable denylist unchanged (`r1_`–`r5_reference`, harness code, `authority_manifest.json`); allowlists unchanged; THROWAWAY markers preserved; no `13B_` obligation.

**Anti-evasion caution, restated:** if a correction stops one of the verifier's probes from landing its fault, that is an evasion, not a pass — say so and stop.

**Stop and report** if any item cannot be done without touching concurrency or a `25_` clause. It should not need to; all five are confined to capture publication, rollback, their immediate callers, and startup.

## After R7

Builder → Fable structural verification → verifier re-check → **owner hands-on POC session.** Nothing else is open in the gate.
