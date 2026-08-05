# Builder Delivery Record — TASK-0007 Round R7 (publication-aware handling, scoped quarantine, restart posture)

**Task:** TASK-0007 R7 — the five corrections in `46_`.
**Builder:** Claude Code session, model `claude-opus-5` (standing authorized substitution, trail entry 69).
**Branch:** `claude/task-0002-builder-handoff-g97x8j` (operator-designated; see §8).
**Instruction authority:** `46_TASK-0007_R7_Task_Packet_Publication_Aware_Handling.md` (governing), with `44_`/`44A_`/`44B_` as the findings behind it. `25_` unchanged; concurrency, provider contracts and the POC architecture closed and not reopened.
**Returned to:** **Fable.**
**Status:** **Built and self-tested. Independent verification pending.** No POC has been run; no provider was contacted. No change requests; nothing needs a ruling.

**Snapshot integrity (H-06), before anything was read as authority — all counts below describe THIS relay** (`TASK0007_R7_Builder.zip`):

| Check | Result |
| --- | --- |
| `SHA256SUMS.txt` | **109/109 OK** |
| `authority_manifest.json` | **108/108 verified, 0 mismatched, 0 missing**; two unlisted files on disk, `SHA256SUMS.txt` and the manifest itself |
| `BASE_BINDING.txt` tree, independently reproduced | **`22e85dd16b646acb45e623c7f7b96896b2a9ed68`** — matches |
| Relay's `poc/` against my R6 return | **96/97 byte-identical**; the one that differs is `stub/out/selftest.json`, a regenerate-by-running output |
| `r6_reference/stub_server_r6.py` | **`d0fd4c449e797be422c78b2c283d6c7b0232dfbcb96a286821279c49b0d19ac0`** — the R6 build the verifier examined |

---

## 1. The defect, and what is actually new about it

Item 1 is **SEC-R4-01 for the third time**, displaced again — first the publication path (R5), then the recovery path (R6), now the tail *after* durability. `write_capture`'s inner handler catches `OSError` around the directory close, so a **non**-`OSError` there escaped to `except BaseException`, became a `CaptureError`, and `h_owner_artifact_register` tore the registration back out of live state and answered "not effective" beside a durable `committed` record reading `REGISTERED`. The shape is identical every time: *a caller is told a transition did not happen while this service's own evidence says it did.*

What I got wrong is worth naming precisely, because it is not the same mistake as R5 or R6. Those were places I had not looked. This one I **had** looked at — R6 added the `published` flag and used it correctly in the `finally` to suppress the rollback. I then left three `except` clauses converting unconditionally two lines above it. I gated the *rollback* on durability and not the *claim*, which means I treated the flag as being about cleanup when it is about what the service is entitled to say.

Items 3 and 4 are a different class and I want to be honest that they are **my over-correction**, not a gap. R6's Delivery Record §2 flagged the strict-fsync reading as a judgement call and offered to soften it; `46_` §Context is right that applying it beyond its scope is an availability defect. Item 3 quarantined on `os.makedirs` failing — nothing had been created, so there was nothing on disk to be ambiguous about, and the service locked itself up over an empty directory. Item 4 quarantined after the rollback fsync had already returned, which is precisely the mistake the publication path's durability boundary exists to prevent, made again one function over.

Item 5 is the one with the widest blast radius and the least drama: the quarantine lived only in memory, so restarting the process cleared it while the ambiguous record stayed on disk. A control that expires when someone reboots is not a control.

## 2. The correction — `46_`'s five, item by item

| # | Required | Implemented |
| --- | --- | --- |
| 1 | Once published, no exception becomes an ordinary `CaptureError` and no caller removes provisional live state | all three `except` clauses in `write_capture` are gated on `published`; after durability the exception goes to `_absorb_post_durable`, which records a soft anomaly and lets the capture return its path. No caller sees an exception at all, so no caller can roll anything back |
| 2 | The exact red-before-green probe | the verifier's `post_durable_interrupt_compare.py` and `chatgpt_r6_quarantine_integrity_probe.py`, byte-identical, wired into `probe_runner.py` with criteria from `46_` — §4 |
| 3 | No quarantine when no artifact was ever created | `_rollback_capture` returns early when both `linked_path` and `tmp` are empty: release the reservation, ordinary capture failure |
| 4 | A durability boundary on the rollback, mirroring publication | `rollback_durable = True` immediately after the rollback directory fsync returns, inside the `try`; a later close error is a recorded soft anomaly, releases the quota, and does not quarantine |
| 5 | Persist a marker **or** bind the runbook — state which and why | **persisted marker.** §3 |
| 6 | Re-run the confirmed R6 results unchanged | §4 |

**Item 1, the judgement call, stated rather than buried.** `_absorb_post_durable` absorbs `KeyboardInterrupt` and `SystemExit` too. Re-raising them would satisfy the letter of item 1 — they are not `CaptureError`, and the callers' `except (CaptureError, QuotaError)` would not roll anything back — but it would leave the transition stranded mid-commit with durable evidence and no in-memory record, which is a worse contradiction than the one being fixed, and it would abort the verifier's own probe rather than answer it. The scope is one `os.close` on a directory fd, after durability; there is no other work in that tail for an interrupt to be protecting. **If Fable disagrees, this is a two-line change and the probe expectation moves with it.**

## 3. Item 5 — why the marker, and not the runbook

**The quarantine is a statement about a directory, not about a process.** The ambiguous record survives the restart, so the thing that says "this directory is ambiguous" has to survive it too, and has to be found by whoever next opens that directory — a different machine, a different operator, a start command nobody read. A runbook binding only holds for people who follow the runbook, and the person this needs to stop is the operator improvising a restart at 2am.

Three consequences worth review:

- **The marker lives beside `captures/`, never inside it** (`<data_dir>/storage_quarantine/<candidate>/`). A file inside the capture tree is a file every reader counts as evidence, and this is not evidence of a transition — it is a statement that the evidence there cannot be trusted.
- **There is no in-service path that clears it.** Reconciliation means an operator inspecting the records and deleting the marker; requiring filesystem access is what makes it explicit. A "clear the quarantine" endpoint or flag would be a production-reachable disable path for the control, which is the defect class this program has already had to remove once (P2V-01). The self-test asserts structurally that `STORE.storage_quarantine` is only ever appended to or extended.
- **Writing the marker is best-effort by construction, and says so.** It only ever runs on a path where the filesystem has already failed, so it cannot raise — losing the quarantine because the marker could not be written would be strictly worse than an unpersisted marker. It records `marker_persisted` on the incident instead, and `/health` and the 503 body report it, so an operator can tell "a restart will still be stopped" from "it will not". The startup scan fails closed on every ambiguity: an unparseable marker and an unlistable directory both count as a quarantine.

The scan runs lazily on the first `dispatch`, not in `Store.__init__`, because every caller assigns `Handler.data_dir` **after** constructing the Store. It takes its own lock and never holds it while acquiring another, so the documented total order (`STORE.lock` → `SECRETS._lock`) is untouched and `GET /health` — deliberately lock-free per A.8 — cannot end up queued behind a POST.

## 4. Verification — every figure from a command run after the last edit

Red-before-green, `46_`'s mandatory method. **Both R7 probes are red against the pinned R6 build and green against this one, with the injected fault firing identically on both** — that last part is the anti-evasion check, not a formality.

| Suite | Against R7 | Against pinned R6 | Meaning |
| --- | --- | --- | --- |
| **Verifier's `chatgpt_r6_quarantine_integrity_probe`** | **5/5 checks** | **1/5** | items 1, 3, 4, 5 + the R6 property preserved |
| **Verifier's `post_durable_interrupt_compare`** | **green** — 200, `registered`, 1 registration beside the committed record | **red** — 500, `capture-failed`, 0 registrations beside the same committed record | item 2 |
| **Verifier's `chatgpt_r5_cleanup_rollback_probe`** | **5/5 scenarios** | 5/5 | item 6: R6's confirmed result, unchanged |
| `capture_fault_suite.py` | **9/9** | 9/9 | item 6: unchanged, and **byte-identical to R6** |
| Acceptance oracle | **7/7, 33 clauses** | — | item 6, branch-specific, live HTTP |
| Deterministic barriers | **6/6** | — | item 6, corroborating per `37_` §2 |
| Prepared-record/quota behaviour | **unchanged** | unchanged | item 6 — §4.1 |
| Stub self-test | **215/215** | — | 190 from R6, plus 25 for R7 |
| Reviewer's full probe set (now 14) | 9 green | 7 green | the same five barrier-class remain per AUDIT-R4-5, ruled on in `37_` §1 |
| Superseded-build witnesses | **34/34** | — | R1 21, R2 13 |
| Measurement validator | **160/160, 0 violations** | — | unchanged |
| Structural harness | **PASS** | — | harness code byte-identical; `out/**` regenerated |

The four R7 defect flags, R6 → R7: `ordinary_failure_with_durable_committed_evidence` true → **false**; `preartifact_spurious_quarantine` true → **false**; `post_rollback_fsync_spurious_quarantine` true → **false**; `restart_bypasses_explicit_recovery` true → **false**. `current_process_fail_closed` is **true on both** — the R6 behaviour did not move.

### 4.1 Item 6, the prepared-record/quota behaviour, side by side

`committed_final_link_cleanup_failure`, R6 and R7: status **503** `refused-storage-quarantine` on both; pools `{general 0, reserved-owner 2, security-refusal 0}` on both; registrations **1**, identity index **1** on both; the surviving capture tree byte-for-byte the same two records (`committed-artifact-register` / `committed`, `prepared-artifact-register` / `prepared`). The **only** difference is one new file at `storage_quarantine/<candidate>/quarantine-*.json` — outside `captures/`, by design.

## 5. One thing I had to fix that was not a code defect

The structural harness came up `VALIDATOR SELF-TEST FAIL — 9/10` on first run in this container: the `well-formed control` case was rejected because `n8n-workflow` was not installed here. It is a JS dev dependency of `validate_n8n_workflows.mjs`, distinct from `n8n-nodes-base`, which remains blocked by the egress proxy. Installing it restored **HARNESS PASS** and made `harness/out/**` byte-identical to R6's. `node_modules/` is **not** in the return. I record it because a Builder who found a red harness and quietly moved on would be doing the thing this program exists to catch.

## 6. Falsifier element (APP-06 / CPB-14, reflexive)

| # | Claim | Who would have to be wrong, and how | Status |
| --- | --- | --- | --- |
| 1 | Publication-aware handling closes the post-durability tail | **The verifier's own probe, red at 500/0-registrations against R6 and green at 200/1 here.** The residual risk is a *fourth* displacement — some other place where a durable fact and a claim about it can diverge. That is what the last three rounds have been, so it is where I would attack next, and I do not claim it is exhausted | **Built to spec; independent verification pending** |
| 2 | The persisted marker makes a restart safe | **This is the claim to check hardest, because it is the one I chose the shape of.** The marker can fail to be written — I made that non-fatal on purpose and surfaced it rather than pretending durability I do not have. If the reviewer thinks an unpersisted marker should itself be fatal, that is a defensible different call and it is a small change | Not disconfirmed; **best-effort, and says so** |
| 3 | Items 3 and 4 narrow the quarantine without weakening it | **Me, and this is a Builder loosening a control after being told it was too strict — exactly the move that deserves suspicion.** The check is that the genuine quarantine paths did not move: `chatgpt_r5_cleanup_rollback_probe` is still 5/5 and `capture_fault_suite.py` is still 9/9 with the file **unedited**, so the four R6 rollback boundaries still quarantine | **Narrowed by the packet; regression proof is an unedited file** |
| 4 | No injection was routed around | **Me, and I have done it three times.** The mechanism: every fault the R7 probes inject fires identically on both builds — `forced=1` on R6 and on R7 for the interrupt, `makedirs_faults=1`, `rollback_close_faults=1` with `rollback_directory_fsync_succeeded=true`. Each criterion in `probe_runner.py` asserts the fault landed *as well as* the outcome, because "no spurious quarantine" is trivially satisfiable by an injection that never fires | Not disconfirmed; **fault-landed assertions shipped** |
| 5 | `capture_fault_suite.py` at 9/9 is evidence for R7 | **It is not, and I am saying so rather than letting the number carry weight it has not earned.** It passes 9/9 against the *pinned R6 build* too. It is the regression proof that R6's accepted boundaries did not move — nothing more. All of the R7 evidence comes from the verifier's two new probes and the self-test block built around them | **Named as regression-only** |
| 6 | My record matches my code | **Me.** Every figure in §4 is Builder-run and none of it is independently confirmed. The only independently confirmed numbers this program has are the ones the verifier states in its own reports | **Self-authored; independently unverified** |

## 7. Return contents

Complete `poc/` tree, Delivery Record, self-verified `RETURN_MANIFEST.json`, `proposed_classifications.json` (**suggestion only**), `diffs/`.

Changed: `stub/stub_server.py` (publication-aware handling, the early rollback return, the rollback durability boundary, marker persistence and the startup scan, `/health`), `stub/probe_runner.py`, `stub/selftest_stub.py`.
Added: `stub/r6_reference/` (permitted by `46_`), the verifier's `chatgpt_r6_quarantine_integrity_probe.py` and `post_durable_interrupt_compare.py` under `stub/security_probes/`, and `stub/out/r7_acceptance.json`.
**Unchanged and deliberately so:** `stub/capture_fault_suite.py`, byte-identical to R6.
Regenerated by running: `harness/out/**` (byte-identical to R6), `stub/out/selftest.json`, `stub/out/r1_witnesses.json`.

## 8. Open items and deviations

- **No change requests.** Nothing in `46_` was internally inconsistent, and nothing needed concurrency or a `25_` clause — the packet predicted that, and it held. One judgement call is flagged in §2 for Fable to reverse if it prefers.
- **Immutable denylist unchanged** — `r1_`–`r5_reference`, harness code, `authority_manifest.json`; proven per-file in the manifest and by directory diff.
- **Inherited and still open:** n8n node types and parameters remain NOT TESTED (`n8n-nodes-base` blocked by the egress proxy, 403), seventh round unchanged.
- **No POC run, no provider contacted. No `13B_` obligation implemented.** Every THROWAWAY marker kept.
- **Branch deviation (unchanged, disclosed):** operator-designated branch.
- **Recommended reviewer focus:** §6 row 3 (a control I loosened after being told it was too strict), then §6 row 2 (the marker's failure mode), then §2's item-1 judgement call.

---

*Builder-authored completion claim and evidence index — not independent evidence (APP-06). `46_`'s five items are claimed corrected; **no POC is claimed run, and no security property is claimed independently verified.** Per `46_` the next steps are Fable structural verification and the verifier's re-check, after which the owner's hands-on session is unblocked. That gate closes when the verifier says so, not when I do.*
