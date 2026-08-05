# Builder Delivery Record — TASK-0007 Round R6 (capture rollback and quarantine)

**Task:** TASK-0007 R6 — SEC-R4-01, final: a failure of the rollback itself was swallowed.
**Builder:** Claude Code session, model `claude-opus-5` (standing authorized substitution, trail entry 69).
**Branch:** `claude/task-0002-builder-handoff-g97x8j` (operator-designated; see §8).
**Instruction authority:** `42_TASK-0007_R6_Task_Packet_Rollback_Quarantine.md` (governing). `25_` unchanged; the concurrency architecture closed and not reopened; R5's accepted post-link paths preserved.
**Returned to:** **Fable.**
**Status:** **Built and self-tested. Independent verification pending.** No POC has been run; no provider was contacted. No change requests; nothing needs a ruling.

**Snapshot integrity (H-06), before anything was read as authority — all counts below describe THIS relay** (`TASK0007_R6_Rollback_Quarantine_Builder.zip`), which is the labelling correction `41_` §3 asked for:

| Check | Result |
| --- | --- |
| `SHA256SUMS.txt` | **122/122 OK** |
| `authority_manifest.json` | **121/121 verified, 0 mismatched, 0 missing**; one unlisted file on disk, `SHA256SUMS.txt` itself |
| `BASE_BINDING.txt` tree, independently reproduced | **`34888d5a188248ed5fab594ba21ac5064632dc73`** — matches |
| Relay's `poc/` against my R5 return | **89/91 byte-identical**; the two that differ are the regenerate-by-running evidence outputs |
| `r5_reference/stub_server_r5.py` | **`972c30d532a957a94a8e7200c9385e387f7508673335acdc8652eb6e3dd15e68`** — the R5 build the verifier examined |

---

## 1. The defect, and why it is the same one twice

`stub_server.py:735` was `except OSError: pass`. If removing the final link failed after a publication failure, the success-named `committed` record survived on disk while the service returned the ordinary `capture-failed / not effective` response. The caller was told the transition was ineffective while durable evidence said it committed.

That is SEC-R4-01 again — the same authority contradiction, displaced from the first-order path into the recovery path. I fixed the first-order path at R5 and wrote a bare `except OSError: pass` in the cleanup two lines below it, which means I treated the rollback as bookkeeping rather than as part of the guarantee. **The rollback is not housekeeping. It is the half of the transaction that decides whether the service is allowed to say "this did not happen."**

`41_` §2 is right that this needs two cascading filesystem failures and is close to unreachable on a healthy localhost disk. I am not going to argue it is more dangerous than it is. What makes it worth the round is that "the cleanup failed silently" is the exact mechanism by which an evidence guarantee dies without anyone noticing.

## 2. The correction — the verifier's seven

| # | Required | Implemented |
| --- | --- | --- |
| 1 | Quota released only when rollback is proven | `_rollback_capture` removes the final link and any temp, **fsyncs the directory to make the removal durable**, and only then calls `_release_pool` |
| 2 | Cleanup failure is a distinct storage-uncertain result | new `CaptureQuarantine`, **deliberately not a subclass of `CaptureError`** so the handlers' `except (CaptureError, QuotaError)` cannot convert it back into the ordinary claim |
| 3 | Quarantine and fail closed | the incident is registered on `STORE.storage_quarantine`; dispatch then refuses **every** further authority transition with `503 refused-storage-quarantine`; `GET /health` still serves and reports why |
| 4 | Durable publication at the true boundary | `published = True` sits immediately after `os.fsync(dfd)` returns, inside the `try`, so the later `os.close` cannot downgrade an already-durable record |
| 5 | Publication separated from temp housekeeping | a directory-close error after a successful fsync is recorded as a **soft anomaly** that blocks nothing and rolls nothing back |
| 6 | Tests red against R5, green against the fix | §4 |
| 7 | The verifier's rollback probe green | **5/5 against R6, 0/5 against pinned R5** |

The quota unit is retained on quarantine deliberately: while a record may still exist, the reservation is the only remaining accounting for it. Releasing it would be a second false statement on top of the first.

**One judgement call, flagged for Fable.** When the removal *succeeds* but its directory fsync cannot be performed, I treat the rollback as not established and quarantine. Item 1 sequences the fsync before the release and item 3 says quarantine "when rollback cannot be established", so this reads as required — but it is the strictest available reading, and it is why the `directory_open_after_link_failure` scenario now ends in quarantine where R5 ended in an ordinary failure. If Fable prefers "removed but undurable" to be a soft anomaly instead, that is a two-line change.

## 3. Nothing routed around an injection point

`42_` cautions against evasion, and I checked for it specifically because I did it three times at R4. Every fault the verifier's probes inject still lands: `os.open`, `os.unlink`, `os.fsync` and `os.close` are all called through the module-level `os` the probes patch, and the new rollback path deliberately calls the **same** `os.open`/`os.fsync` the publication path uses, so a probe blocking the directory also blocks the rollback's fsync. That is why `directory_open_after_link_failure` quarantines rather than quietly succeeding — the injection reaches the recovery path too, which is the honest outcome rather than the convenient one.

## 4. Verification — every figure from a command run after the last edit

| Suite | Against R6 | Against pinned R5 | Meaning |
| --- | --- | --- | --- |
| **Verifier's `chatgpt_r5_cleanup_rollback_probe`** | **5/5 scenarios** | **0/5** | item 7 |
| `capture_fault_suite.py` — R6 rollback boundaries | **4/4** | **0/4** | final-link, persistent temp, rollback fsync, close-after-fsync |
| `capture_fault_suite.py` — R5 boundaries (regression) | **5/5** | **5/5** | `42_` §3: R5's accepted paths did not move |
| Stub self-test | **190/190** | — | 178 from R5, plus 12 for the rollback/quarantine work |
| Reviewer's full probe set (12) | 7 green | 6 green | the five barrier-class remain per AUDIT-R4-5, ruled on in `37_` §1 |
| Superseded-build witnesses | **34/34** | — | R1 21, R2 13 |
| Deterministic barriers | **6/6** | — | corroborating, per `37_` §2 |
| Acceptance oracle | **7/7, 33 clauses** | — | branch-specific, live HTTP |
| Measurement validator | **160/160, 0 violations** | — | unchanged |
| Structural harness | **PASS** | — | harness code byte-identical; `out/**` regenerated |

The five rollback scenarios, R5 → R6: `standalone_final_link_cleanup_failure` ordinary error with the record surviving → **quarantine**; `committed_final_link_cleanup_failure` `capture-failed` → **`refused-storage-quarantine`**; `rollback_directory_fsync` two fsyncs and no durable removal → **three fsyncs, nothing surviving**; `post_fsync_close_plus_cleanup_failure` ordinary error discarding a durable record → **published and retained**; `persistent_temp_cleanup_failure` ordinary error with a hidden `.tmp` → **quarantine**.

## 5. Two corrections to my own record, from `41_` §3

- **I over-reported what was independently confirmed.** The verifier's runner hit a 240-second limit partway through and confirmed only the R5 capture-publication block, **8/8** — not my full 178/178. My R5 record's verification table did not distinguish "the verifier ran this" from "I ran this", and it should have. Every figure in §4 above is **Builder-run**; the only independently confirmed numbers this program has are the ones the verifier states in its own reports.
- **My snapshot counts were ambiguously labelled.** `105/105` and `4b0874…` in the R5 record described the relay *I* received, while the outer re-check packet carried different figures. Both were true of different artifacts and neither was wrong, but I did not say which artifact each described. §"Snapshot integrity" above now names the relay explicitly.

## 6. Falsifier element (APP-06 / CPB-14, reflexive)

| # | Claim | Who would have to be wrong, and how | Status |
| --- | --- | --- | --- |
| 1 | The rollback is now proven or quarantined | **The verifier's probe, which ships here and goes 5/5 vs 0/5.** The residual risk is a *third* level: something in `_rollback_capture` itself failing in a way I have not injected — and that is precisely the shape of the last two rounds, so I would attack it there first | **Built to spec; independent verification pending** |
| 2 | Quarantine fails closed | **The blocking rule is coarse on purpose.** Every POST is refused once quarantined, including read-only listings. That is deliberate — a service that cannot describe its own evidence should not be answering questions about it — but it is stricter than "as necessary", and if that is wrong it is wrong in the safe direction | Not disconfirmed; **deliberately coarse** |
| 3 | R5's accepted paths did not regress | **The R5 boundary block, still 5/5 on both builds.** Two criteria did change — `directory_open_after_link_failure` and the post-link probe — and I changed them because `42_` items 1 and 7 supersede `38_`'s "no quota consumed", not because my build failed them. That is exactly the move a Builder makes when weakening a criterion to fit, so it is the claim to check hardest, and the ordinary-failure branch of both criteria is unchanged and still strict | **Changed by supersession; stated, not buried** |
| 4 | No injection was routed around | **Me, and I have done it three times.** §3 gives the mechanism rather than the assurance; the check is that every patched `os` call is still on the live path, and the quarantine at `directory_open_after_link_failure` is the visible proof that the probe still reaches the recovery path | Not disconfirmed; **mechanism stated** |
| 5 | My record matches my code | **Me**, and §5 records two places it did not. Every figure in §4 is Builder-run and none of it is independently confirmed | **Self-authored; independently unverified** |

## 7. Return contents

Complete `poc/` tree, Delivery Record, self-verified `RETURN_MANIFEST.json`, `proposed_classifications.json` (**suggestion only**), `diffs/`.

Changed: `stub/stub_server.py` (the rollback path, the durability boundary, the quarantine registers, dispatch fail-closed, `/health`), `stub/selftest_stub.py`, `stub/capture_fault_suite.py`, `stub/probe_runner.py`.
Added: `stub/r5_reference/` (permitted by `42_`) and the verifier's `chatgpt_r5_cleanup_rollback_probe.py` plus its recorded outputs under `stub/security_probes/`.
Regenerated by running: `harness/out/**`, `stub/out/**`.

## 8. Open items and deviations

- **No change requests.** Nothing in `42_` was internally inconsistent; nothing needed the concurrency model or a `25_` clause. One judgement call is flagged in §2 for Fable to soften if it prefers.
- **Immutable denylist unchanged** — `r1_`–`r4_reference`, harness code, `authority_manifest.json`; proven per-file in the manifest.
- **Inherited and still open:** n8n node types and parameters remain NOT TESTED (`n8n-nodes-base` blocked by the egress proxy, 403), sixth round unchanged.
- **No POC run, no provider contacted. No `13B_` obligation implemented.** Every THROWAWAY marker kept.
- **Branch deviation (unchanged, disclosed):** operator-designated branch.
- **On proportionality (`41_` §5):** the owner holds that call, not me. If he takes the accept-the-residual-risk option instead, this round's work does not need to be unwound — the quarantine path simply never fires on a healthy disk.
- **Recommended reviewer focus:** §6 row 3 — the two criteria I changed — then §2's flagged judgement call.

---

*Builder-authored completion claim and evidence index — not independent evidence (APP-06). SEC-R4-01 is claimed corrected against `42_`; **no POC is claimed run, and no security property is claimed independently verified.** Per `42_` the next steps are Fable structural verification and the verifier's re-check of this one finding, after which the owner session is unblocked. That gate closes when the verifier says so, not when I do.*
