# 42 — TASK-0007 Round R6: capture rollback and quarantine (SEC-R4-01, final)

**Scope: one defect, one function.** The concurrency architecture is **closed and must not be reopened**. `25_` is unchanged. R5's ordinary post-link paths are **accepted** and must not regress — the verifier confirmed them independently, including that the legitimate `prepared` record and its one reserved-owner quota unit correctly survive a failed committed registration. Do not "fix" that; it is correct.

## The defect

A failure of the **rollback itself** is swallowed. `stub_server.py:735` is `except OSError: pass`, so if removing the final link fails after a publication failure, the success-named `committed` record survives on disk while the service returns the ordinary `capture-failed / not effective` response. The caller is told the transition was ineffective while durable evidence says it committed — the exact authority contradiction SEC-R4-01 exists to eliminate, displaced into the recovery path. A persistent temp-cleanup failure similarly leaves a hidden `.tmp` artifact while reporting an ordinary failure.

## Required correction (the verifier's seven, verbatim in substance)

1. **Do not release quota until rollback is proven.** Remove the final link and any remaining temp, fsync the directory, and only then release the reservation and permit the caller to claim the transition ineffective.
2. **Do not swallow cleanup failure.** A failed final unlink, temp unlink, directory open, or rollback fsync must become a **distinct storage-uncertain result** — not `pass`.
3. **Quarantine and fail closed when rollback cannot be established.** Do not return the ordinary ineffective response while a `committed` record may survive. Preserve enough provisional state to reconcile, block further authority transitions as necessary, and require explicit recovery.
4. **Set durable publication at the true boundary.** Once the publication directory fsync succeeds, a later directory-fd **close** error must not turn a durable committed record into an ordinary rollback claim.
5. **Separate publication from temp housekeeping.** A temp-cleanup problem *after* durable publication must not roll back live state while committed evidence is retained.
6. **Tests, red against R5 and green against the corrected build**, for: final-link cleanup failure; persistent temp cleanup failure; rollback directory-open/fsync failure; and directory-close failure after a successful publication fsync.
7. **Re-run `chatgpt_r5_cleanup_rollback_probe.py`** (shipped at `40_security_probes/`): every non-control scenario must produce either **proven cleanup** or an **explicit quarantined/uncertain state** — never a normal ineffective claim alongside surviving committed evidence.

## Method and constraints

Pin R5 as `r5_reference/` exactly as the prior pins are done, and apply the standing rule: **every criterion must be shown red against the pinned defective build before it is claimed green.** That rule has caught a vacuous test and three injection-evasions across previous rounds; it is not optional.

Immutable denylist unchanged (`r1_`–`r4_reference`, harness code, `authority_manifest.json`); allowlists unchanged; every THROWAWAY marker preserved; no `13B_` obligation.

**One caution, learned the hard way:** do not route around an injection point. If a correction makes one of the verifier's probes unable to land its fault, that is an evasion, not a pass — say so and stop.

**Stop and report** if the correction cannot be made without touching the concurrency model or a `25_` clause. It should not need to; the defect is confined to `write_capture`'s failure and rollback handling.

## After R6

Builder → Fable structural verification → verifier re-check of this one finding → **owner hands-on POC session.** Nothing else in the gate is open.
