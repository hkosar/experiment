# Builder Delivery Record — TASK-0007 Round R9 (marker state as facts, complete inventories, enforced invariants)

**Task:** TASK-0007 R9 — `56_`'s items F–K, the carried item E, and the §1 re-search over all R8+R9 remediation code.
**Builder:** Claude Code session, model `claude-opus-5` (standing authorized substitution, trail entry 69).
**Branch:** `claude/task-0002-builder-handoff-g97x8j` (operator-designated; see §9).
**Instruction authority:** `56_TASK-0007_R9_Task_Packet_Marker_Facts_and_Enforcement.md` (governing), with `54_` — read first, as `56_` §3 directs — as the authoritative findings and `55_` as Fable's concurrence. `25_` unchanged; concurrency, provider contracts, the POC architecture, both settled rulings and the R8-closed items C/D are closed and not reopened.
**Returned to:** **Fable.**
**Status:** **Built and self-tested. Independent verification pending.** No POC has been run; no provider was contacted. No change requests — CR-R8-01 was authorized in `56_` §0 and is applied.

**Snapshot integrity (H-06), before anything was read as authority — all counts describe THIS relay** (`TASK0007_R9_Builder_2.zip`):

| Check | Result |
| --- | --- |
| `SHA256SUMS.txt` | **118/118 OK** |
| `authority_manifest.json` | **117/117 verified, 0 mismatched, 0 missing**; two unlisted on disk, `SHA256SUMS.txt` and the manifest itself |
| `BASE_BINDING.txt` tree, independently reproduced | **`64bf6c8f6e0187865fca22c82094863755e96879`** — matches |
| Relay's `poc/` against my R8 return | **106/106 byte-identical** |
| `r8_reference/stub_server_r8.py` | **`5df1408fdf2fd5dbcb5d2577a20c14699009493c32de1ba7c0d6c347c44bf7a1`** |
| Verifier's probe, against `54_security_probes/` | **`282a654e2ea2ae62e4f4c892c3728b7b50b50a53fa0051bf70ebdacf8c1426e6`** — byte-identical |

---

## 1. What R8 did, stated without softening

R8 removed three proxies and put two new ones **inside the remedy**. `_write_marker` returned an error for any exception anywhere in its body — including one raised after the marker file *and* its parent directory had both been fsynced — and `_persist_quarantine` counted a marker as landed only on a clean return. **"The function returned without an exception" stood in for the disk facts "a record exists" and "a record is durable."** That is the third time this workstream has applied a post-durability boundary correctly in one place and missed it in the next (publication R5/R7, rollback R8, marker R9).

Two things I want on the record rather than buried:

**The scan-once judgement was mine, Fable concurred, and the verifier disproved it by execution.** I wrote in the R8 record that scan-once was "formally the pattern" and judged the gap unreachable because two processes on one data directory is not the supported configuration. `55_` §3 identifies the exact defect in that reasoning, and it is not "the assumption was wrong" — it is that **I never checked the assumption against the sentence the service ships.** The marker text says *"every process using this data directory refuses authority transitions"*, unconditionally. A claim that exceeds its enforcement is itself a proxy-for-fact instance. I had the §1 table in front of me and did not apply it to the sentence.

**The `durable_records` finding is the one that could have caused real harm.** A transient `EIO` on the fallback scan put the entire data directory into `durable_records`, next to a runbook telling the operator to delete every path in it. An operator following the written instruction in good faith would have destroyed the evidence tree. Nothing else this round is in that category, and I am not going to describe it as a reporting defect.

## 2. The corrections — `56_`'s items

| # | Required | Implemented |
| --- | --- | --- |
| **F** | tri-state marker fact, not a success Boolean | `_write_marker` returns `{path, state, error, anomaly}`; `state` comes from `_path_fact`, which **asks the filesystem**. `DURABLE` is set the instant the parent-directory fsync returns and nothing after it may lower it — the close tail records a soft anomaly instead. `PRESENT_OR_UNKNOWN` when the path exists or cannot be shown absent; `ABSENT_KNOWN` only when absence is verified the item-C way |
| **G** | live disk facts feed the live posture | `_restart_posture` counts `surviving_temp_paths` from the **live** incident, and every real record raises the level. While any temp or present/durable marker exists, `none` / `survives_restart: false` / "nothing on disk" cannot be emitted |
| **H** | one incident, one ID, one complete inventory | a stable `incident_id` stamped at construction; the **same ID and the complete sibling inventory written into both markers**; `_merge_incidents` deduplicates by ID on scan; `_quarantine_summary` exposes **every** incident and the union of every real record on `/health` and both 503 bodies |
| **I** | a scan error is never a durable record | `_scan_error_incident` — `restart_protection: "unknown"`, the location reported under `unlistable_location` with an explicit "this is NOT a record to delete", nothing added to `durable_records`. `_classify_records` admits only **stat-verified regular files**; a directory never qualifies |
| **J** | enforce the one-process invariant | **both mechanisms** — `flock(LOCK_EX \| LOCK_NB)` on `<data_dir>/.stub-<candidate>.lock` held for the process lifetime, **and** `_refresh_quarantine` before every authority transition. §4 |
| **K** | complete the containment check | (a) containment now runs **before** `_reserve_pool`, so a refusal cannot leak a unit; (b) the canonical root is compared against its physical location under the resolved data directory, so a root symlink is **refused** rather than resolved through by both sides |
| **E** | the authorized `run_all.sh` edit | applied. `NOT RUN` is distinct from ran-and-failed: FAIL/1, INCOMPLETE/2, PASS/0. Verified with the dependency absent (exit 2) and present (exit 0). No vendoring, no network |

## 3. §1 — the re-search over all R8 and R9 code, reported either way

`56_` §1 sharpened the instruction: the pattern concentrates in new remediation code, so look there first. I enumerated the surface mechanically — every function whose text differs from the pinned R7 build (R8's changes) or from the pinned R8 build (R9's) — **25 functions**. Four instances found, all fixed.

| # | Where | The proxy | How it was found |
| --- | --- | --- | --- |
| 1 | `_surviving_temp_artifacts` | *"a `.tmp` exists under `captures/`"* standing in for *"a `.tmp` **outlived** the process that created it"*. At R8 the scan ran once at startup, before any capture existed, so the two were the same statement. Item J made it run before every transition and they came apart instantly: **every normal capture has a real `.tmp` on disk between `mkstemp` and the unlink**, so a concurrent request quarantined a perfectly healthy service | **The regression suites, not reading.** Barriers went 3/6 and the oracle 6/7 the moment the rescan landed. Fixed by registering the reserved temp prefix on the Store *before* the create and excluding in-flight prefixes — a fact about this process's own state, which is authoritative for its own temps |
| 2 | `_existing_only` | `os.path.isfile(p)` returning False stood in for *"this is not a record"*. `isfile` swallows every `OSError`, so a marker that could not be **stat'ed** — a real record, still on disk — vanished silently from the operator's inventory. **That is finding 2.2's exact shape inside the code written to fix finding 2.3** | Reading, against the §1 table. Now `_classify_records` splits *proven absent* (dropped) from *cannot resolve* (reported as `unverifiable_records`, never deleted and never presented as deletable) |
| 3 | `_path_fact` | *"the directory listing succeeded"* standing in for *"the name is not in it"* — I returned `ABSENT_KNOWN` as soon as `listdir` did not raise, without checking membership | Reading. Now the basename must actually be absent from the listing |
| 4 | `_rollback_capture` | the incident ID was stamped inside `_persist_quarantine`, which runs **after** the incident is appended to the register. Between those two lines the incident had no ID, and `_merge_incidents` keys on it — a concurrent `_refresh_quarantine` would have merged it under `None` with any other ID-less incident. *"It will get an ID in a moment"* is not *"it has one"* | Reading, while checking item H's merge key |

**Instance 1 is the one worth the round.** It is the same shape as the scan-once finding one level down: a statement that was true under an unstated condition (the scan only ever ran at startup), shipped as though it were unconditional. It was found because item J removed the condition and the suites broke loudly — which is an argument for the regression set, not for my reading.

**Looked and found none**, with the ground named so the negative result means something: authentication (`compare_digest` against the stored value), route policy (the table *is* the policy), field allowlisting, entity quota (SEC-R3-06 already removed the parallel-counter proxy), pool selection, token spend under the held lock, revocation epoch at terminal commit, publication durability (R5/R7), rollback durability (R8), temp-as-filesystem-fact (R8 item C), transport refusals, `_merge_incidents`' union semantics, `_acquire_candidate_lock` (the lock *is* the enforcement), and `_quarantine_summary`'s per-incident iteration. Redaction remains partly heuristic **by necessity** and is named again here so "found none" is not read as "looked only where it was easy".

## 4. Item J — why both mechanisms, and not just the one `56_` selected

`56_` selects `flock` and pre-authorizes the rescan alternative. **This build ships both, and neither is decoration.**

- **The lock** stops the accidental second launch — the real operational risk, an operator starting a second stub on the same data directory — before it can do anything at all. A second process on the same `(data_dir, candidate)` refuses to start and names the holder's PID.
- **The rescan** makes the marker's *"every process"* sentence true for **any** process, including one that never went through the startup path. That is precisely the configuration the verifier's probe constructs, and it is the configuration in which the sentence would otherwise still exceed its enforcement — one layer down, which is the finding itself.

Shipping only the lock would have left `54_` §3's mechanism closed and `55_` §3's *rule* still violated. The cost is two or three `os.listdir` calls per authority transition on a localhost throwaway apparatus, and merging is by incident ID so re-observing the same facts is a no-op rather than a growing register.

**Stated as a limitation:** `flock` is advisory. It binds cooperating processes, which every process running this file is; it does not stop a different program from writing into the data directory. On a platform without `fcntl` the stub now **refuses to start** rather than claim a protection it cannot enforce.

## 5. Verification — every figure from a command run after the last edit

Red-before-green against the SHA-pinned R8, with the injected fault asserted firing identically on both builds.

| Suite | Against R9 | Against pinned R8 | Meaning |
| --- | --- | --- | --- |
| **Verifier's `chatgpt_r8_adversarial_recheck`** | **11/11 checks** | **1/11** | items F–K |
| — F, post-durable marker close | `durable`, both markers listed | `none`, `durable_records: []` | 2 file fsyncs, 2 dir fsyncs, 2 close faults on both |
| — F, partial marker (ENOSPC mid-JSON) | `present_unverified`, both listed | `none` | 2 partial-write faults on both |
| — G, surviving temp, both markers refused | `durable`, temp listed | `none` | `mkstemp_faults: 1` on both |
| — H, durable primary with close-tail anomaly | listed; delete-and-restart **clean** | primary omitted; restart **503** | 1 close fault on both |
| — H, sibling restart reconstruction | 1 incident, 2 records, **ends clean** | 2 incidents, 1 record, still quarantined | — |
| — I, transient primary scan `EIO` | `unknown`, **no** records | `durable`, a nonexistent path | 1 fault on both |
| — I, transient fallback scan `EIO` | `unknown`, **no** records, sentinel intact | the **whole data directory** named as deletable | 1 fault on both |
| — J, two processes one directory | A refuses at **503** after B quarantines | A accepts at **200** | — |
| — K, containment refusal | **no** pool unit consumed | one unit leaked | — |
| — K, captures-root symlink | **refused**, nothing outside | accepted, JSON written outside | — |
| — **verifier's positive control** | **`none`, truthfully; fresh process clean at 200** | same | must stay green — §8 row 2 |
| **Verifier's `chatgpt_r7_adversarial_recheck`** | **4/4** | 4/4 | R8-closed items C/D, unchanged |
| **`chatgpt_r6_quarantine_integrity_probe`** | **5/5** | 5/5 | unchanged |
| **`post_durable_interrupt_compare`** | **green** | green | the `47_` §3 ruling, unchanged |
| **`chatgpt_r5_cleanup_rollback_probe`** | **5/5** | 5/5 | unchanged |
| `capture_fault_suite.py` | **9/9** | 9/9 | unchanged, and the file is **byte-identical to R8** |
| Acceptance oracle | **7/7, 33 clauses** | — | unchanged |
| Deterministic barriers | **6/6** | — | unchanged |
| Stub self-test | **285/285** | — | 250 through R8, plus 35 for R9 |
| Reviewer's full probe set (now 16) | 11 green | 10 green | the same five barrier-class remain per AUDIT-R4-5, ruled on in `37_` §1 |
| Superseded-build witnesses | **34/34** | — | R1 21, R2 13 |
| Measurement validator | **160/160, 0 violations** | — | unchanged |
| Structural harness | **PASS**, exit 0 | — | and **INCOMPLETE, exit 2** with `n8n-workflow` absent — item E |

## 6. Two criteria changed, stated rather than quietly widened

Both were forced by behaviour `56_` requires, and both are checked *more* strictly now:

- **R7 block, "naming the marker it recovered".** Item H replaced the single `recovered_from_marker` with a merged inventory, because R8's version named one marker and left the operator quarantined by its sibling. The check now requires **every** recovered record to be listed and each to be a real file.
- **R8 block, "the fallback location carried the quarantine".** Item F replaced the `marker_paths` success list with per-attempt tri-state disk facts, because a success list was the proxy. The check now reads the states and requires the surviving attempt to be the fallback at `DURABLE`.

## 7. Return contents

Complete `poc/` tree, Delivery Record, self-verified `RETURN_MANIFEST.json` (regenerated **after** the final run), `proposed_classifications.json` (**suggestion only**), `diffs/`.

Changed: `stub/stub_server.py`, `stub/probe_runner.py`, `stub/selftest_stub.py`, all three runbooks, and **`harness/run_all.sh`** — the single authorized denylist exception (CR-R8-01, `56_` §0).
Added: `stub/r8_reference/` (permitted by `56_` §4), the verifier's `chatgpt_r8_adversarial_recheck.py` under `stub/security_probes/`, `stub/out/r9_acceptance.json`.
**Unchanged and deliberately so:** `stub/capture_fault_suite.py`, and every other denylisted file including `r1_`–`r7_reference/`.
Regenerated by running: `harness/out/**` (byte-identical to R8), `stub/out/selftest.json`, `stub/out/r1_witnesses.json`.

## 8. Falsifier element (APP-06 / CPB-14, reflexive)

| # | Claim | Who would have to be wrong, and how | Status |
| --- | --- | --- | --- |
| 1 | Item F classifies disk facts, not control flow | **The verifier.** The residual is `_path_fact` itself: it asks `os.path.exists` and then a directory listing, and on a filesystem where both lie there is no fourth thing to ask. It fails toward `PRESENT`, which over-claims protection rather than under-claiming it — the opposite direction from R8's failures, and the safe one for a quarantine | **Built to spec; independent verification pending** |
| 2 | The fix did not simply delete the `none` branch | **This is the claim to attack first, and the verifier already built the instrument.** Ten of the eleven flags are "does not say `none`"; every one of them is satisfiable by a build that never says `none` at all. The verifier's **positive control** is the eleventh and it is in my criterion as a required green: a genuine no-record failure still reports `none`, warns explicitly, and a fresh process really does start clean at 200 | Not disconfirmed; **the disconfirming test is the verifier's own** |
| 3 | Both item-J mechanisms are load-bearing | **Me.** The rescan alone would pass the verifier's probe — the probe never uses the startup path, so the lock is invisible to it. I shipped the lock anyway because `56_` selects it and because the probe's configuration is not the operator's. The reverse is also true and matters more: the **lock alone would fail the probe**, and a Builder optimising for the acceptance set would have shipped only the rescan | **Both shipped; neither is provable by the probe alone** |
| 4 | The §1 re-search was real | **Me.** Four instances, in code I wrote in the last two rounds. The strongest evidence it was real is instance 1: it was found by the **regression suites breaking**, not by my reading, and I am reporting the mechanism of discovery rather than presenting it as insight. The weakest part is that instances 2–4 came from reading, and reading is what missed them the first time | **Four found, all fixed, one found by tests** |
| 5 | Item K closes the containment gap | **The verifier, and the honest answer is that it closes the gap it was given.** Root symlink refused, candidate symlink refused, no quota leak. The check-to-use TOCTOU remains and is unchanged; `56_` item K(c) carries `O_NOFOLLOW`/`openat` to `13B_` and explicitly excludes it from R9 | **Scoped as the packet scoped it** |
| 6 | `capture_fault_suite.py` at 9/9 is evidence for R9 | **It is not.** 9/9 against pinned R8 as well. Regression proof only | **Named as regression-only** |
| 7 | My record matches my code | **Me.** Every figure in §5 is Builder-run. The only independently confirmed numbers this program has are the verifier's own, and `55_` §1 records that the R8 return met a four-execution reproducibility standard — which `56_` §6 makes the bar for this evidence | **Self-authored; independently unverified** |

## 9. Open items and deviations

- **No change requests.** Nothing in `56_` was internally inconsistent; the one inconsistency from last round (CR-R8-01) was authorized in `56_` §0 and is applied.
- **Immutable denylist unchanged except the single authorized edit** — `r1_`–`r7_reference/` and all other harness files byte-identical; `authority_manifest.json` untouched; proven per-file in the manifest and by directory diff.
- **Inherited and still open:** n8n node types and parameters remain NOT TESTED (`n8n-nodes-base` blocked by the egress proxy, 403), ninth round unchanged. `n8n-workflow` — a different package — installs normally; `node_modules/` is **not** in the return.
- **`flock` is advisory** and the stub refuses to start where `fcntl` is unavailable. Stated in §4 rather than left implicit.
- **No POC run, no provider contacted. No `13B_` obligation implemented.** Every THROWAWAY marker kept.
- **Branch deviation (unchanged, disclosed):** operator-designated branch.
- **Recommended reviewer focus:** §8 row 2 (did the `none` branch survive honestly), then §8 row 3 (which of the two J mechanisms the probe can actually see), then §3 instance 1 — a statement true only under an unstated condition, which is the shape that has now produced findings at two different levels in two consecutive rounds.

---

*Builder-authored completion claim and evidence index — not independent evidence (APP-06). `56_`'s items F–K and the carried item E are claimed corrected and the §1 re-search reported in full; **no POC is claimed run, and no security property is claimed independently verified.** Per `56_` §6 the next steps are Fable structural verification and an executed verifier re-check under the trail-158 rule; the input archive's SHA-256 is quoted in-channel and every red-before-green result here is reproducible from `stub/out/r9_acceptance.json` and the shipped probe. That gate closes when the verifier says so, not when I do.*
