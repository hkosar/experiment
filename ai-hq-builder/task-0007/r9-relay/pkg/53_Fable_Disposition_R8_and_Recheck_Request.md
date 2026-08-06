# 53 — Fable Disposition: R8, and the re-check request

**Input:** `TASK0007_R8_Builder_Return.zip`, SHA-256 `262c58852991c21cd8bc7ae8fd496274b91f86544b9679eae8e322a472c20ff6`, 117 members, archive-safety clean.

## 1. Structural verification (static only, per the trail-127 practice)

| Check | Result |
| --- | --- |
| `RETURN_MANIFEST.json`, re-hashed entry by entry | **106/106 exact — 0 missing, 0 mismatch, 0 undeclared** (paths rooted at `poc/`) |
| Immutable denylist (harness code incl. `run_all.sh`, `r1_`–`r6_reference/`) | **byte-identical, every file** |
| New `r7_reference/stub_server_r7.py` | **byte-identical to the integrated R7 stub** (`69b98fb0…0ac91`) — the pin is genuine |
| Verifier's probe under `stub/security_probes/` | **byte-identical to `49_security_probes/`** |
| Stdlib-only | **confirmed at the AST level** (the two grep hits are docstring prose) |
| Secret-shaped scan | clean |
| Change set on integration | **exactly 8 modified + 4 added, matching the declared counts** |

The second consecutive clean manifest, and the Builder's own H-06 block independently re-verified this relay's `SHA256SUMS` (113/113), authority manifest (112/112) and base tree (`69ca5043…`) before reading anything as authority. **No suite was run by Fable**; every figure in the Delivery Record §6 is a Builder self-claim pending the executed re-check.

## 2. The four gating items, confirmed by reading

**Item A** — three mechanisms, layered by what each needs from a failing disk: the R7 primary marker; a **fallback marker in the data directory itself**, which already exists and so needs neither of the two things the verifier's reproductions broke; and the **write-free fact** — any `.tmp` that outlived its process under `captures/<candidate>/` is an unproven artifact by construction (`42_`'s settled policy read from the other side) and needs no successful write at all. **Both marker locations are attempted every time**, with the stated reason that a fallback exercised only on primary failure is an untested path — which is exactly how the primary's own gap survived R7. When nothing lands, the service claims nothing: `restart_protection: "none"` plus an explicit DO-NOT-RESTART warning, surfaced at the top level of `/health`, not only in the nested block.

**Item B** — `_restart_posture()` is now the **single source** of every operator-facing restart statement, called from `/health`, the dispatch-gate 503 and the raising request's 503, derived from what actually landed. The R7 contradiction — the true field and the false sentence one key apart — is structurally impossible to reintroduce without editing one function. The runbook audit found the false sentence in no runbook; all three runbooks gained the conditional table instead.

**Item C** — the temp prefix is **reserved and bound before any create**; `_existing_temp_artifacts` asks the directory, not the variable. The early return now requires three facts: no final link, no temp on disk, **and absence actually established** — a directory that cannot be listed establishes nothing and falls through to the proof path, while a directory that does not exist does establish absence, which is precisely how the ordinary `os.makedirs` case stays fixed. Confirmed by tracing that path: `makedirs` fails → no directory → `FileNotFoundError` on the listing → absence established → ordinary failure, pools released. The unique-per-attempt prefix also means concurrent captures cannot cross-match each other's temps.

**Item D** — every handler in `_rollback_capture` (unlink, directory open, fsync, close) now catches `BaseException` via one `_why()` helper, split on `rollback_durable` exactly as before; `_release_pool` is reached on the durable path R7 dropped. The comment names the fact that made this non-optional: `KeyboardInterrupt`/`SystemExit` are `BaseException` and not `OSError`.

**Anti-evasion, stated before being asked:** item C's tempting implementation — selecting the name and calling `os.open(O_CREAT|O_EXCL)` directly — would be correct **and** would stop the verifier's `mkstemp` patch from ever firing. The Builder kept the create where the probe can reach it and established the fact another way, with `mkstemp_faults: 1` asserted on both builds. That is the discipline this workstream demanded after three evasions, applied at the exact point where evasion would have been most natural.

## 3. The §1 fourth-instance search — two found, and the second is the valuable one

**Instance 1 (fixed):** the capture-path containment check used `os.path.abspath` + `startswith` — a **lexical** test standing in for the filesystem fact "the bytes land inside the captures tree", divergent the moment a path component is a symlink. Fixed with `realpath` on both sides plus a planted-symlink self-test. Severity honestly scoped (not reachable from any owner or provider request; requires a pre-placed symlink under `--data`) and a **named residual**: a swap *between* check and `makedirs` still lands outside; closing it needs `O_NOFOLLOW`/openat design work. **Ruling: the residual is accepted for the throwaway and carried forward to `13B_`** alongside the AUDIT-R4-2 reserve requirement — the production wrapper's capture path must hold containment against symlink swaps, not only against lexical traversal.

**Instance 2 (fixed):** the first draft of the Builder's **own R8 remedy** wrote `except OSError: continue` on a per-directory listing — reporting *"I could not look"* as *"there is nothing here"*, the identical substitution, inside the function whose job is to establish the fact. Found by re-reading its own new code against the §1 table, not by any test, and reported anyway. That report is worth more than either fix: it demonstrates the pattern is a **default under `try:`**, not a historical artifact — which is the strongest argument that `51_` §1's check must become standing practice in the production build.

The looked-and-found-none table names its ground control by control, and calls redaction's heuristic half an **irreducible** proxy rather than claiming it as a fact — which is the honest way to say "found none".

## 4. Rulings

**CR-R8-01 — GRANTED, and the defect is Fable's.** `51_` item E requires editing `poc/harness/run_all.sh`; `51_` §3/§5 and `25_` §0 forbid touching it. The packet was internally inconsistent, the Builder's resolution was exactly right — stop the one non-gating item, finish everything else, ship the change unapplied with its verification — and the stop-and-report discipline has now caught a Fable packet defect for the second time. **The grant is behaviour-bound, not hash-bound:** Fable attempted mechanical application of the shipped diff to a copy and **only the first hunk applied** — the hunk arithmetic is malformed, so the text is not a mechanically appliable patch (a process observation, not a build defect; the Builder verified behaviour on an edited copy, not via `patch(1)`). Authorization: **in its next return, whichever round that is, the Builder applies its own item-E edit** achieving exactly the verified behaviour — FAIL/1 for any check that ran and failed, INCOMPLETE/2 when every check that ran passed but one or more were NOT RUN, PASS/0 otherwise; exit-status-preserving for every check that runs; no vendoring, no network. The denylist is amended for that one file, that one change, that one return.

**The scan-once judgement — CONCUR, with the ground named.** `_ensure_quarantine_scanned` tests "was this directory quarantined at first request" as a stand-in for "is it quarantined now" — formally the §1 pattern, as the Builder itself says. The gap requires a second process sharing the same data directory concurrently. Fable checked the runbooks: they instruct **one stub, restarted with a different `--candidate`** to switch corpora — the single-process configuration is what they describe, though no runbook states it as a *rule*. Ruling: the judgement stands for the POC; the in-process case is covered by the in-memory register, so a process always fails closed on its own quarantine. **Two consequences:** the owner runbook gains one sentence in the next authorized edit round making single-process-per-data-directory an explicit rule rather than an implication; and the item goes to the verifier as an open challenge, since the Builder asked to be overruled rather than guessed.

**§6.2's changed criterion — accepted as disclosed, flagged for the verifier.** The R7 "exactly one marker" assertion now fails for the right reason (item A requires a second location). The Builder split it rather than loosening it: the R7 property is still checked verbatim, the fallback is asserted to be in a **different** directory, and reconciliation must remove every durable record. It flagged this unprompted as the move that deserves suspicion. It does — `50_` §2.2 is the live example of one getting through — so it is on the re-check list.

## 5. Disposition and the re-check

**R8 is STRUCTURALLY ACCEPTED and INTEGRATED** (8 modified, 4 added; `r7_reference/` added to the immutable denylist on the established precedent). **Security posture NOT independently verified** — that is the re-check's job, and per the trail-158 rule the gate moves only on an executed return carrying the input archive's SHA-256 and reproduction notes.

**Requested reviewer focus, in order:**

1. **The Builder's own §8 row 2, its stated first target: is the fallback marker a second mechanism or a relocated goalpost?** Your probe faults only the primary; a sham fallback would pass it. The Builder's distinguishing evidence — both locations attempted every time, `marker_attempts` reporting the failed primary, and a shipped both-locations-fail case that asserts the service *discloses* rather than claims — is exactly what needs independent execution.
2. **The both-locations-fail disclosure path**: on a disk that accepts no marker at all, does the response genuinely contain no sentence claiming a restart will be stopped (the Builder asserts this by whole-body search), and does the write-free `.tmp` fact carry the restart protection it claims?
3. **The scan-once judgement** (§4 above) — Fable's concurrence is open to challenge exactly as the Builder requested.
4. **The split criterion in §6.2** — confirm the R7 property survived the split unweakened.
5. **The realpath fix and its named TOCTOU residual** — confirm the fix holds for the planted-symlink case and that the residual's scoping (operator-placed symlink only) is accurate.
6. **Every R6- and R7-confirmed behaviour unchanged**, including the `47_` §3 interrupt probe and the prepared-record/quota tables.

**On this re-check the owner's hands-on n8n-versus-Zapier session unblocks.** Nothing else in the gate is open. Item E's authorized application is deliberately **not** gated on it.
