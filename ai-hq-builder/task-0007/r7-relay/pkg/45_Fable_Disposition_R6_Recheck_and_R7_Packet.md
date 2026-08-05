# 45 — Fable Disposition: R6 re-check, and the R7 correction

**Input:** `44_`/`44B_` + probes (bundle SHA-256 `b9d9a39dc59419172c1acd8c0815e778015d716049a33fdd74925062bbd79fcc`; internal checksums **26/26 valid**). **FAIL — SEC-R4-01 remains OPEN.** Concurred.

## 1. What R6 closed, independently confirmed

Verifier's rollback probe **5/5 against R6, 0/5 against pinned R5**; Builder capture-fault suite **9/9 vs 5/9**; oracle **7/7 / 33 clauses**; concurrency barriers **6/6**. The verifier also directly confirmed the new quarantine works: a real rollback failure returns `503 refused-storage-quarantine`, `GET /health` stays up and reports `storage_quarantined: true`, subsequent owner *and* provider POSTs both get 503, and neither state nor evidence changes while quarantined. **The concurrency architecture and the strict-fsync rule both remain accepted and closed.**

## 2. Where Fable's own ruling landed — precisely

The verifier is explicit: *"This is not a disagreement with Fable's strict-fsync ruling. I concur that a deletion whose directory fsync did not complete is not a proven rollback and should quarantine."* The ruling stands.

But two of the three findings (§4.1, §4.2) are that the ruling was **applied beyond its scope** — the service quarantines when *no artifact was ever created* (nothing to roll back), and when the rollback fsync **already succeeded** and only a later directory *close* reported an error. Fable's structural review confirmed `_rollback_capture` did what `42_` asked and did not ask the next question: *does it also fire when there is nothing to prove?* That is a real gap in Fable's review, distinct from the ruling itself, and it is recorded as one. The corrective is in the packet: a durability boundary on the rollback path mirroring the one the publication path already has, and an explicit "no artifact ever existed" case.

**Both are availability defects, not evidence defects** — and correcting them makes the apparatus *less* likely to lock up spuriously during the owner's session, which is a practical benefit, not only a formal one.

## 3. The High finding

Real, and narrow. Moving `published = True` to the directory-fsync boundary was correct, but the **outer exception handler was not moved with it**: after publication is durable, a non-`OSError` exception (e.g. an interruption) still reaches `except BaseException`, is converted to `CaptureError`, and the caller then removes provisional live state and reports the registration "not effective" — while a durable `committed` record says `REGISTERED`. The original authority contradiction, displaced once more, now into the post-durability tail. Fable concurs: *the true durability boundary was moved, but the meaning of the outer exception handler was not moved with it.*

## 4. The restart gap, and why it is worth taking

Quarantine lives only in `STORE.storage_quarantine`, which a fresh process initialises empty. The verifier restarted with the same candidate and data directory after a genuine quarantine and got `storage_quarantined: false` plus an accepted new registration — while the ambiguous committed record was still on disk. It deliberately did **not** make this the decisive finding, since the POC keeps other authority state in memory by design. But it correctly qualifies `42_`'s claim that "explicit recovery" is required: R6 enforces that only for the current process. Fable concurs and takes the fix.

## 5. Test-accounting, recorded again

The verifier **did not** treat the shipped `190/190` and `34/34` as independent verification. Its independent results are the targeted probes and suites named in §1 only. Those Builder counts remain self-claims and are recorded as such — the second consecutive round in which Fable records this rather than repeating a Builder number as verified.

## 6. R7 issued (`46_`), and an honest read on the trajectory

Five corrections, all narrow: publication-aware exception handling; the exact red-before-green interruption probe; no quarantine when no artifact ever existed; a rollback durability boundary so a post-fsync close error is a recorded soft anomaly rather than a hard quarantine; and a resolved restart posture (persisted marker or a bound runbook rule). All existing R6 results must re-run unchanged.

**Trajectory, stated plainly for the owner.** Seven rounds. The findings have moved from a real concurrency defect that would have corrupted his session (R4), through genuine but rarer disk-failure paths (R5, R6), to this: an interruption landing in a microsecond window, plus two over-strictness defects Fable's own review let through. That is convergence, not a treadmill — each round the remaining risk is materially smaller and the fixes are smaller. **But it is the seventh round on apparatus that gets deleted after one session**, and the owner has already chosen the higher-assurance path once (trail 151). Fable's recommendation remains to finish it — two of the five items directly reduce the chance of the stub locking up on him mid-session — while noting the residual-risk option stays available on his word at any point.
