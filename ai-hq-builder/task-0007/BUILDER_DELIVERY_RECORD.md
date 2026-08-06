# Builder Delivery Record — TASK-0007 Round R8 (facts, not proxies)

**Task:** TASK-0007 R8 — `51_`'s four gating items, the §1 fourth-instance search, and one non-gating item.
**Builder:** Claude Code session, model `claude-opus-5` (standing authorized substitution, trail entry 69).
**Branch:** `claude/task-0002-builder-handoff-g97x8j` (operator-designated; see §8).
**Instruction authority:** `51_TASK-0007_R8_Task_Packet_Facts_Not_Proxies.md` (governing), with `49_` — read first, as `51_` §5 directs — as the authoritative findings behind it and `50_` as Fable's concurrence. `25_` unchanged; concurrency, provider contracts, the POC architecture and the `47_` §3 publication-tail ruling closed and not reopened.
**Returned to:** **Fable.**
**Status:** **Built and self-tested. Independent verification pending.** No POC has been run; no provider was contacted. **One change request: CR-R8-01, §5** — item E cannot be done inside the packet's own denylist.

**Snapshot integrity (H-06), before anything was read as authority — all counts below describe THIS relay** (`TASK0007_R8_Builder.zip`):

| Check | Result |
| --- | --- |
| `SHA256SUMS.txt` | **113/113 OK** |
| `authority_manifest.json` | **112/112 verified, 0 mismatched, 0 missing**; two unlisted files on disk, `SHA256SUMS.txt` and the manifest itself |
| `BASE_BINDING.txt` tree, independently reproduced | **`69ca5043f0e844f5c81caef7b5eae38bf52ec91d`** — matches |
| Relay's `poc/` against my R7 return | **102/102 byte-identical** |
| `r7_reference/stub_server_r7.py` | **`69b98fb09ae94d4f38b30e3e2d2179045fe4e50b529033940a7ad1ccf6b0ac91`** — the digest `49_` and `50_` both independently report for the executed build |
| Verifier's probe, against `49_security_probes/` | **`b7db68d4f43a725ac9e460446640b975362c33fa5ce94a80b508dd408436c366`** — byte-identical |

---

## 1. The habit, named accurately

`50_` §3 and `51_` §1 are right, and the framing is better than "three bugs". Each control tested a **cheap proxy** for the fact it existed to establish, and each was correct on the input it was shown and blind one step over:

| Control | What it tested | What it had to establish |
| --- | --- | --- |
| no-artifact early return | `tmp` is `None` | no temp or final name **ever existed on disk** |
| rollback close tail | the exception is an `OSError` | **anything at all** went wrong after durability |
| restart quarantine | no marker file is present | the previous process **did not quarantine** |

What makes this worth stating rather than just fixing: I wrote the R7 `/health` block with an explicit comment saying an operator must be able to tell "a restart will still be stopped" from "the marker could not be written, so it will not be" — **and then asserted "restarting does not clear it" unconditionally, one key later, in the same JSON object.** I identified the exact operator need and contradicted it in the next statement. That is not a blind spot; it is a failure to check my own output against the requirement I had just written down. The countermeasure this round is `_restart_posture()`: **one function** produces every operator-facing restart statement, called from `/health` and both 503 bodies, so there is exactly one place for it to be wrong and it is derived from what actually landed.

## 2. The corrections — `51_`'s items

| # | Required | Implemented |
| --- | --- | --- |
| **A** | an unpersisted marker must not be only diagnostic | **three mechanisms and truthful disclosure** — §3 |
| **B** | operator text conditional and true | `_restart_posture()`, one definition and three call sites (`/health`, the dispatch-gate 503, the raising request's 503). The runbooks carry the operator instruction; the audit `51_` asked for found the sentence in **no** runbook, so the change there is an addition, not a correction |
| **C** | track temp creation as a filesystem fact | `tmp_prefix` is chosen and bound **before any create**; `_existing_temp_artifacts` lists the directory for it. The early return runs only when there is no final link, no temp on disk, **and** the absence was established — a directory that cannot be listed establishes nothing and falls through to the proof path. A directory that does not exist *does* establish absence, which is how the `os.makedirs` case stays fixed |
| **D** | rollback tail exception-type complete | every handler in `_rollback_capture` — unlink, directory open, fsync, close — now catches `BaseException`, split on `rollback_durable` exactly as before. `_release_pool` runs on the durable path, which R7 skipped entirely because the exception escaped before reaching it |
| **E** | non-gating harness status | **CANNOT BE DONE INSIDE THE DENYLIST — CR-R8-01, §5.** Patch written and verified, not applied |
| **§1** | search for a fourth instance | **two found, both fixed** — §4 |

`51_` item C's warning was specific and I checked it: the ordinary `os.makedirs`-failed case is still an ordinary `capture-failed` with all pools released and no quarantine, asserted directly in the self-test immediately after the item-C case, so the availability defect `46_` item 3 fixed did not regress into a spurious quarantine.

## 3. Item A — what I did, and the option I did not take

**Three mechanisms, because no one of them can establish the fact on a filesystem that is already failing:**

1. **Primary** — `<data_dir>/storage_quarantine/<candidate>/quarantine-*.json`, as at R7.
2. **Fallback** — `<data_dir>/STORAGE-QUARANTINE-<candidate>-*.json`. A different directory, and one that **already exists** (the captures tree lives under it), so it needs no directory creation. The two failure shapes the verifier reproduced break exactly the two things the primary needs and neither of the things the fallback needs. **Both are attempted every time, not the fallback only on primary failure** — a fallback exercised only in the failure case is an untested path, and an untested path is how the primary's own gap survived R7.
3. **Write-free** — any surviving `.tmp` under `captures/<candidate>/`. A temp that outlived its process is an unproven artifact by construction, and `42_` already settled that a temp which cannot be removed is quarantine-worthy. This needs **no successful write at all**, which is the only kind of signal that survives a read-only disk.

**And when none of them lands, the service says so.** `restart_protection: "none"`, `survives_restart: false`, and an explicit `WARNING` beginning "DO NOT RESTART" — surfaced at the **top level** of `/health` as well as inside the quarantine block, because an operator may not open a nested object. `_persist_quarantine` still cannot raise; `51_` §3 keeps that constraint and the reason is unchanged.

**The option I did not take, and why — this is the part to read.** `51_` item A offers **inverting the write** first, and it is the structurally better idea: create the durable signal before the operation that can fail, remove it only on proven success. I could not take it. The inverted write has to happen inside `_rollback_capture`, which is inside the window whose `os.fsync` and directory `os.close` **ordinals** the verifier's probes count — "the second directory close", "the third fsync". Two extra fsyncs and a directory open/close there would relocate every one of those injected faults onto the marker's own I/O. The fault would still fire, at the wrong call, testing nothing. That is an evasion by construction and `51_` §4 forbids exactly it. So: resolution 1 (second durable location), stated as a choice rather than presented as the only option, with the reason the better option is unavailable.

## 4. §1 — the fourth-instance search, and what it found

`51_` §1: *"A fourth instance found by the Builder is worth more to this program than the three fixed ones."* I searched every control in `stub_server.py` against the table's question — **does this control's test establish its fact, or stand in for it?** Two instances, both fixed; the rest of the audit stated either way, because a negative result only means anything if the ground it covers is named.

### FOUND — the capture-path containment check was lexical, not real (fixed)

`write_capture` computed `root` and `expected` with `os.path.abspath` and compared with `startswith`. **`abspath` is purely lexical** — it normalises `..` and makes the path absolute and never touches the filesystem. So the test was *"the path string starts with the captures prefix"*, standing in for the fact *"the bytes land inside the captures directory"*. Those diverge the moment any component is a symlink: `captures/<candidate>` pointing elsewhere passes the string test and writes outside the tree. `SAFE_NAME` blocks `..`, which is the failure this check was shown; a symlink is the one it was silent on. Same shape, one control over.

Fixed with `os.path.realpath` on both sides, and a self-test case that plants a real symlink and asserts both the refusal and that nothing was written outside.

**Severity, stated honestly rather than inflated:** not reachable from any owner or provider request. Every path component is `SAFE_NAME`-matched and the stub creates these directories itself, so it needs an operator or a prior process to have placed a symlink under `--data`. **Residual, named not hidden:** a component swapped for a symlink *between* the check and the `os.makedirs` would still land outside. Closing that needs `O_NOFOLLOW` descriptors and openat-relative writes — a real design change to the publication path, outside `51_`'s items.

### FOUND — in my own R8 code, while writing the fix for this exact class (fixed)

The first draft of `_surviving_temp_artifacts` — the function whose entire job is to establish a fact — wrote `except OSError: continue` on the per-POC directory listing. That reports **"I could not look"** as **"there is nothing here."** It is the identical substitution, committed inside the remedy for it, and I found it by re-reading my own new code against the §1 table rather than by any test. An unlistable capture directory now counts as an incident.

I report this one because it is the more useful of the two. The pattern is not something previous rounds had and this round removed; it is a default I reach for under a `try:` unless I actively check. §1's instruction is the check.

### LOOKED, AND FOUND NONE — with the ground named

| Control | Its test | Verdict |
| --- | --- | --- |
| owner/provider authentication | `hmac.compare_digest` against the stored key | the fact |
| route policy | `ROUTE_POLICY` row; missing ⇒ 404 fail closed | the table **is** the policy |
| capture field allowlisting | membership in the route's `fields` | the fact |
| entity quota | `_entity_live` = the counter the route itself increments | SEC-R3-06 already removed the parallel-counter proxy here |
| capture pools | `_pool_for`, policy-driven | the fact |
| token spend | `consumed` flag set under the held lock | the fact |
| revocation | epoch compared at terminal commit | the fact (SEC-R3-02) |
| publication durability | `published` set after `os.fsync` returns | the fact (R5/R7) |
| rollback durability | `rollback_durable` set after its fsync returns | the fact (R7) |
| transport refusals | Content-Length / Content-Type / JSON shape | facts about the request |
| redaction | `SECRETS.scrub` (exact for minted secrets) + regex patterns (heuristic) | **partly a proxy, and irreducibly so** — see below |

**Redaction is the one honest "proxy" I am not proposing to change.** `SECRET_PATTERNS` is a heuristic for "this blob contains a secret", and no exact test exists for the general case. It is not the defect class: the exact half (`SECRETS.scrub`) covers every value this service minted, which is the only category it has authority over, and the heuristic half is additive. Naming it here so that "found none" is not read as "looked only where it was easy".

### CONSIDERED AND JUDGED NOT AN INSTANCE — stated so the judgement can be overruled

`_ensure_quarantine_scanned` scans **once per process**, so its test is "was this directory quarantined when I first served a request", standing in for "is it quarantined **now**". Formally the pattern. I did not fix it, and the reasoning is: the only gap is a second process sharing the same data directory concurrently, which is not a supported configuration — the runbook starts one stub per candidate — and the in-process case is covered by the in-memory register rather than by the scan, so this process always fails closed on its own quarantine regardless. Re-scanning per request would also need marker-path deduplication to avoid re-appending the process's own incident, which would change `before_state == after_state` in a verifier-confirmed R6 predicate. **If Fable disagrees, it is a contained change and I would rather be told than have guessed.**

## 5. CR-R8-01 — item E cannot be done inside the packet's own denylist

**`51_` §2 item E requires modifying `poc/harness/run_all.sh`. `51_` §3 and §5 both forbid it.** `25_` §0 names it explicitly on the immutable denylist: *"all `poc/harness/*.py`, `*.mjs`, `run_all.sh`"*. Every file in the chain item E names — `run_all.sh`, `validate_n8n_workflows.mjs`, `selftest_validator.mjs` — is denylisted, so there is no allowlisted seam, and `51_` §5's new-file permission is for modules under `stub/`, none of which can change what `run_all.sh` prints.

`51_` §5 says to stop and report on an internally inconsistent clause. Item E is explicitly **non-gating**, so I stopped item E and finished everything else rather than stopping the round.

The patch is written out at `diffs/PROPOSED-NOT-APPLIED-item-E-run_all.sh.txt` and **verified without being applied** — run from `poc/harness/` under a temporary name, dependency absent and then present, temporary copy deleted:

- dependency **absent** → exit **2**, `=== HARNESS INCOMPLETE (every check that ran passed; one or more were NOT RUN) ===`, both Node checks printing `NOT RUN — optional dependency n8n-workflow is unavailable`;
- dependency **present** → exit **0**, `=== HARNESS PASS ===`.

Exit-status-preserving for every check that actually runs. No vendoring, no network requirement. **This working tree ships `run_all.sh` byte-identical**; authorising the patch costs one line.

## 6. Verification — every figure from a command run after the last edit

Red-before-green against the SHA-pinned R7, **with the injected fault shown landing identically on both builds** — `51_` §4 makes that standing practice, and it carries unusual weight this round because two of the three fixes could be faked by a build that simply stopped calling the thing the probe patches. Item C is the live example: selecting the temp pathname myself and calling `os.open(O_CREAT|O_EXCL)` would satisfy the requirement *and* stop the verifier's `tempfile.mkstemp` patch from ever firing. The create therefore stays where the probe can reach it and the fact is established a different way.

| Suite | Against R8 | Against pinned R7 | Meaning |
| --- | --- | --- | --- |
| **Verifier's `chatgpt_r7_adversarial_recheck`** | **4/4** | **0/4** | items A, C, D |
| — item A, marker-`makedirs` (EROFS) | restart **quarantined, 503** | restart clean, **200** | fault fired on both (`marker_makedirs_faults: 1`) |
| — item A, marker-`open` (EACCES) | restart **quarantined, 503** | restart clean, **200** | fault fired on both (`marker_open_faults: 1`) |
| — item C, temp created pre-return | **`CaptureQuarantine`**, quota retained | `CaptureError`, quota released | `mkstemp_faults: 1` on both |
| — item D, `RuntimeError` after real close | **`CaptureError` + 1 soft anomaly**, quota released | `RuntimeError` escapes, **0** anomalies, quota retained | `runtime_close_faults: 1` on both |
| **Verifier's `chatgpt_r6_quarantine_integrity_probe`** | **5/5** | 5/5 | R7-confirmed, unchanged |
| **Verifier's `post_durable_interrupt_compare`** | **green** | green | the `47_` §3 ruling, unchanged |
| **Verifier's `chatgpt_r5_cleanup_rollback_probe`** | **5/5** | 5/5 | R6-confirmed, unchanged |
| `capture_fault_suite.py` | **9/9** | 9/9 | unchanged, and the file is **byte-identical to R7** |
| Acceptance oracle | **7/7, 33 clauses** | — | unchanged |
| Deterministic barriers | **6/6** | — | unchanged, corroborating per `37_` §2 |
| Current-process fail-closed | **true** | true | unchanged |
| Prepared-record / quota behaviour | **unchanged** | unchanged | §6.1 |
| Stub self-test | **250/250** | — | 216 through R7, plus 34 for R8 |
| Reviewer's full probe set (now 15) | 10 green | 9 green | the same five barrier-class remain per AUDIT-R4-5, ruled on in `37_` §1 |
| Superseded-build witnesses | **34/34** | — | R1 21, R2 13 |
| Measurement validator | **160/160, 0 violations** | — | unchanged |
| Structural harness | **PASS** | — | harness code byte-identical, `run_all.sh` included |

**The both-locations-fail case is mine, not the verifier's, and it is the one that matters.** The verifier's probe breaks only the primary; a fallback would pass it whether or not it were a real second mechanism. So the self-test runs each marker failure **twice**: once with the primary broken (the fallback must carry it, and the failed primary attempt must be reported so the fallback is not silently standing in) and once with **every** location broken (the service must report `restart_protection: none`, warn explicitly, and emit **no** sentence claiming a restart will be stopped — asserted by searching the whole response body).

### 6.1 The accepted prepared-record and quota behaviour, side by side

`committed_final_link_cleanup_failure`, R7 and R8: **503** `refused-storage-quarantine` on both; pools `{general 0, reserved-owner 2, security-refusal 0}` on both; **1** registration, **1** identity-index entry on both; the same two capture records (`committed`/`committed`, `prepared`/`prepared`). R8 adds the second marker file outside `captures/`.

### 6.2 One criterion changed, stated rather than widened quietly

The R7 self-test's *"the quarantine is persisted as a marker"* asserted **exactly one** marker and then deleted only the primary to prove reconciliation works. `51_` item A requires a second durable location, so that assertion now fails for the right reason. It is split: the R7 property is still checked verbatim (one primary marker, outside `captures/`), a new check asserts the fallback exists **in a different directory**, and reconciliation now removes every durable record. Flagged here because "a Builder loosening a test after a behaviour change" is the move that deserves suspicion, and `50_` §2.2 is a live example of one getting through.

## 7. Return contents

Complete `poc/` tree, Delivery Record, self-verified `RETURN_MANIFEST.json` (regenerated **after** the final run), `proposed_classifications.json` (**suggestion only**), `diffs/`.

Changed: `stub/stub_server.py`, `stub/probe_runner.py`, `stub/selftest_stub.py`, `runbooks/RUNBOOK-n8n.md`, `runbooks/RUNBOOK-owner-session.md`, `runbooks/RUNBOOK-zapier.md`.
Added: `stub/r7_reference/` (permitted by `51_` §5), the verifier's `chatgpt_r7_adversarial_recheck.py` under `stub/security_probes/`, `stub/out/r8_acceptance.json`, and `diffs/PROPOSED-NOT-APPLIED-item-E-run_all.sh.txt`.
**Unchanged and deliberately so:** `stub/capture_fault_suite.py`, and every file on the immutable denylist including `harness/run_all.sh`.
Regenerated by running: `harness/out/**` (byte-identical to R7), `stub/out/selftest.json`, `stub/out/r1_witnesses.json`.

## 8. Falsifier element (APP-06 / CPB-14, reflexive)

| # | Claim | Who would have to be wrong, and how | Status |
| --- | --- | --- | --- |
| 1 | Item A establishes the fact rather than a better proxy | **The verifier, and the sharpest challenge is that a second location is still a marker write.** It is: on a wholly read-only filesystem both fail, and then the only thing left is the write-free `.tmp` fact and truthful disclosure. I did not claim a durable control there — I made the service say it does not have one. If the reviewer holds that the honest-disclosure branch is insufficient, that is a real disagreement about what is achievable, not about what was built | **Built to spec; independent verification pending** |
| 2 | The fallback is a second mechanism, not a relocated goalpost | **Me, and this is the claim to attack first.** A fallback in a directory the verifier's probe does not fault is *exactly* what an evasion would look like. Three things distinguish it: the primary is still attempted and its failure is reported in `marker_attempts`; the probe's faults still fire (asserted, both builds); and the both-locations-fail case ships and shows the service disclosing rather than claiming | Not disconfirmed; **the disconfirming test ships** |
| 3 | Item C did not stop the verifier's probe from landing | **Me, three times historically.** `tempfile.mkstemp` is still what creates the file, specifically so the probe's patch fires — `mkstemp_faults: 1` on both builds. The tempting fix (select the name, `os.open` it myself) would have been cleaner code and a silent evasion | Not disconfirmed; **mechanism stated** |
| 4 | The §1 search was real and not a formality | **Me.** The strongest evidence that it was real is that one of the two instances it found was **in the code I wrote this round to fix the same class** — a search performed for appearances would not have turned that up, and would certainly not have reported it | **Two found, both fixed, one self-inflicted** |
| 5 | `capture_fault_suite.py` at 9/9 is evidence for R8 | **It is not.** It passes 9/9 against pinned R7 too. It is the regression proof that R6's and R7's accepted boundaries did not move, and nothing more. Every R8 figure comes from the verifier's new probe and the self-test block built around it | **Named as regression-only** |
| 6 | The scan-once judgement in §4 is correct | **Me, and I am least confident of this one.** It is formally the pattern; I judged the gap unreachable in the supported configuration and the fix non-trivial. If that judgement is wrong, it is wrong in the direction of leaving an instance open, which is the direction this workstream has been wrong in before | **Judgement stated, not buried** |
| 7 | My record matches my code | **Me.** Every figure in §6 is Builder-run. The only independently confirmed numbers this program has are the ones the verifier states in its own reports — and `50_` §4 notes that R7 was the first build where the self-test, witnesses and measurement validation were independently executed rather than taken on my word | **Self-authored; independently unverified** |

## 9. Open items and deviations

- **One change request: CR-R8-01 (§5).** Item E requires editing a denylisted file. Patch supplied, unapplied, verified.
- **Immutable denylist unchanged** — `r1_`–`r6_reference/`, all harness code including `run_all.sh`, `authority_manifest.json`; proven per-file in the manifest and by directory diff.
- **Inherited and still open:** n8n node types and parameters remain NOT TESTED (`n8n-nodes-base` blocked by the egress proxy, 403), eighth round unchanged. `n8n-workflow` — a different package — installs normally here and from the public registry; `node_modules/` is **not** in the return.
- **No POC run, no provider contacted. No `13B_` obligation implemented.** Every THROWAWAY marker kept.
- **Branch deviation (unchanged, disclosed):** operator-designated branch.
- **Recommended reviewer focus:** §8 row 2 (is the fallback a real mechanism or a moved goalpost), then §4's scan-once judgement, then §6.2's changed criterion.

---

*Builder-authored completion claim and evidence index — not independent evidence (APP-06). `51_`'s four gating items are claimed corrected and the §1 search reported either way; **no POC is claimed run, and no security property is claimed independently verified.** Per `51_` §6 the next steps are Fable structural verification and an executed verifier re-check; the input archive's SHA-256 is quoted in-channel and every red-before-green result here is reproducible from `stub/out/r8_acceptance.json` and the shipped probe. That gate closes when the verifier says so, not when I do.*
