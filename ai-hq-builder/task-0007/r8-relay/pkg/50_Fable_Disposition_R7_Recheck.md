# 50 — Fable Disposition: the executed R7 re-check

**Input:** `R7_ChatGPT_Final_Recheck_Return.zip`, SHA-256 `72e9d10ba245d08f2daf044c093edebef135097541d5617f1190411b4885a965`, 17 members, archive-safety clean (no absolute paths, no traversal, no symlinks, no hard links).

**Numbering note:** the verifier's report is internally headed `# 48`, which collided with `48_` (the declination disposition issued before it arrived). It is integrated **verbatim, content untouched**, under the filenames `49_ChatGPT_R7_Final_Recheck.md`, `49A_ChatGPT_R7_Probe_Evidence.json`, `49_security_probes/` and `49_execution_logs/`. Filenames are Fable's to assign on integration; verifier content is never rewritten.

## 1. This one is a verdict, and the integrity block proves it

Every number the verifier reported reconciles against what this repository sent, checked independently here:

| Claim | Fable's check | Result |
| --- | --- | --- |
| Input zip SHA-256 `673109fb…82062` | vs. trail 157 relay fingerprint | **exact** |
| `SHA256SUMS.txt` 115/115 | `wc -l` of the sent packet's list | **115** |
| `authority_manifest.json` 114/114 | manifest's own `files` count | **114** |
| Base tree `4134d968755f623cc358eac1c58caa66706f98c8` | `git rev-parse 1110bf90…^{tree}` | **exact** |
| R7 source `69b98fb0…0ac91` | `sha256sum` of the integrated stub | **exact** |
| R6 pin `d0fd4c44…19ac0` | `sha256sum r6_reference/stub_server_r6.py` | **exact** |

The base tree is the decisive one: `4134d968…` is the real tree object of the commit recorded at trail 157, and the verifier produced it by extracting `base_snapshot.tar` and reconstructing it — a value that cannot be guessed, inferred from prose, or copied from the packet. **The archive was extracted and the code was executed.** The standing rule adopted at `48_` §5 is satisfied, and this return moves the gate.

`49_execution_logs/` ships stderr from the self-test, witnesses, both capture-fault runs, both oracle runs and both barrier runs — the raw material for re-running the result, which is the second half of that rule.

## 2. Verdict: FAIL — CONCURRED IN FULL on all three findings

Per the trail-127 practice **Fable ran no probes**. All three mechanisms were confirmed by reading the integrated source.

### 2.1 Marker-write failure permits restart bypass — CONCUR, gate-blocking

`_persist_quarantine` (`stub_server.py:687-703`) wraps the whole write in `except BaseException`, sets `marker_persisted: False`, and returns. No second control is installed.

`_scan_quarantine_markers` then reopens clean in both failure shapes:
- `os.makedirs` failed → the directory does not exist → line 721-722 `except FileNotFoundError: return []`, commented *"never quarantined; nothing to recover."*
- the file write failed → the directory exists and is empty → the loop at 729 finds nothing → `found` is empty.

**The docstring at 711-714 claims the scan "Fails closed on every ambiguity."** It does — on every ambiguity it can *observe*: an unreadable marker and an unlistable directory both count as incidents, which is good design. But an **absent marker after a failed write is byte-for-byte indistinguishable from never-quarantined**, so the one ambiguity the scan cannot observe is the one it fails *open* on. That is the recurring shape of this entire workstream, and §3 says so.

**The contradictory `/health` text is confirmed and is worse than a cosmetic slip.** At `stub_server.py:1360-1365` the Builder added `marker_persisted` with an explicit comment — *"an operator has to be able to tell the difference between 'a restart will still be stopped' and 'the marker could not be written, so it will not be'"* — and then left `reconcile_by` asserting *"restarting does not clear it"* **unconditionally, in the same JSON object**. An operator reading that object gets the true field and the false sentence side by side. The Builder identified the exact operator need and then contradicted it one key later.

### 2.2 Item 3 loosened past its stated boundary — CONCUR

`tmp = None` at line 1018; `fd, tmp = tempfile.mkstemp(...)` at line 1023. The name binds only when `mkstemp` **returns**. Anything raising between the file's exclusive creation inside `mkstemp` and the completion of that assignment leaves the artifact on disk with `tmp is None`. `_rollback_capture`'s new guard — `if not linked_path and not tmp: _release_pool(pool); return` (831-835) — then classifies that as "no artifact ever existed."

**The guard tests a local variable as a proxy for a filesystem fact, and the proxy is wrong precisely in the window where the fact matters.** The verifier's own comparison table is the proof that this is a genuine loosening and not a rewritten requirement: pinned R6 quarantines and retains quota on this input; R7 returns an ordinary `CaptureError` and releases it.

This is the finding `47_` §5 asked for by name — *"a control relaxed after being told it was too strict is exactly where an over-relaxation would hide."* It was there, and Fable's structural review at `47_` §2 did not find it, because that review confirmed the branch existed and did what it said, and did not ask **what the branch's test actually establishes**. Same review-method gap as trail 152 and 154, third instance, now recorded against the method rather than the round.

### 2.3 Item 4 exception-type incomplete — CONCUR, and it is the settled ruling one function over

Line 877: the `os.close(dfd)` inside the `finally` is guarded by `except OSError`. A non-`OSError` escapes the `finally`, propagates out of `_rollback_capture`, and never reaches `_release_pool(pool)` at line 906 — so the quota unit is retained and no soft anomaly is recorded, exactly as the verifier's execution shows.

**Fable adds the point the verifier left implicit, because it makes the fix non-optional.** `KeyboardInterrupt` and `SystemExit` are `BaseException`, not `OSError`. `47_` §3 ruled that absorbing an interrupt after durability is established is correct, and that ruling is settled and independently concurred. **It was applied to the publication tail and not to the rollback tail, which has the identical shape** — a close-after-durability with no remaining work to protect. So R7 shipped the ruling and its own counterexample in one file. The verifier reproduced it with a plain `RuntimeError`, which is the cleaner probe; the interrupt case is the one that makes it reachable in an owner session that ends with Ctrl-C.

## 3. Root cause: three proxies standing in for the facts they represent

These are not three unrelated patches. Each is a **cheap proxy substituted for the fact the control is supposed to establish**, and each is correct on the input it was shown and blind one step over:

| Control | Proxy it tests | Fact it must establish |
| --- | --- | --- |
| no-artifact early return | a local variable is empty | no temp or final **name ever existed on disk** |
| rollback close tail | the exception is an `OSError` | **anything at all** went wrong after durability |
| restart quarantine | no marker file is present | the previous process **did not quarantine** |

That framing is the useful thing to hand the Builder, because it says where a fourth instance would live rather than only naming three. `51_` §1 makes it the organising requirement.

## 4. What genuinely holds

Everything else re-executed clean, and this is the part that keeps the round narrow. R6's confirmed results are unmoved: verifier rollback probe 5/5 on both builds, capture-fault suite 9/9 on both, acceptance oracle 7/7 across 33 clauses, deterministic barriers 6/6, current-process quarantine still fails closed. The accepted committed-registration rollback-failure behaviour is semantically identical down to the pool figures. Self-test 215/215, witnesses 34/34 and measurement validation 160/160 — **now independently executed, not Builder self-claims**, for the first time on this build.

**The four R7 defect flags are genuinely fixed** on the inputs they were written for, with the faults landing on both builds. The Ctrl-C ruling's own probe is green on R7 and red on pinned R6. R7 is a real improvement that did not regress anything; it is incomplete, not wrong.

## 5. The n8n harness gap — not a security finding, and not R8's gate

The verifier could not run the Node structural harness: `n8n-workflow` is not vendored and its sandbox's internal npm mirror returned 404 for it. **Fable confirms this is a verifier-environment limitation, not a product defect** — the log shows a request to an internal artifact gateway, and the package resolves normally from the public registry the owner's machine will use. It is correctly excluded from the verdict.

One consequence is worth fixing anyway, for the owner rather than for the gate: `run_all.sh` printed **`=== HARNESS FAIL ===`** in that run, with the security-relevant Python checks all passing. A missing optional Node dependency must not render as a harness failure during the owner's own session — he would reasonably read it as something being broken. Carried into `51_` as a **non-gating** item.

## 6. Disposition

**R7 FAIL, concurred in full. Security gate OPEN. Owner POC session BLOCKED.** `51_` (R8) issues to the Builder: three narrow corrections, the truthfulness fix, the mandatory red-before-green set, and one non-gating usability item. Concurrency, the `25_` contract, the POC architecture and the settled publication-tail ruling are **not reopened**.

**Residual-risk position, stated for the owner rather than for the gate.** The verifier's finding severities are correct and Fable does not soften them. But the owner's standing option to run on stated residual risk (trail 151, restated 154) deserves a current reading, because the calculus has moved: all three findings require a genuine storage failure or a fault landing in a sub-millisecond window, none can double-fire a real provider action, and the apparatus is deleted after one supervised localhost session. At R4 the open defect could have fanned one approval into multiple real side effects; at R8 the open defects leak one capture quota unit out of 5,000 and lose a restart guard on a disk that has already failed. **Fable's recommendation is still to finish** — R8 is three small fixes, two of which reduce the chance of the stub locking up mid-session — but the owner may run the session on R7 at any time on his word, and `52_` puts that choice to him plainly rather than leaving it implied.
