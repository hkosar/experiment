# 55 — Fable Disposition: the executed R8 re-check

**Input:** `R8_ChatGPT_Final_Recheck_Return.zip`, SHA-256 `e352783a36e8c3782fc9b9772a7155c1feb7d2133bcd2b3e00f7cb9cd8d02ed4`, 47 members, archive-safety clean; internal `SHA256SUMS.txt` self-verified with 0 failures. Integrated verbatim as `54_`, `54A_`, `54B_`, `54_security_probes/`, `54_execution_logs/`, `54_repeat_runs/`.

## 1. The return is a verdict under the trail-158 rule

Input zip `c06588ad…3cbf` = the trail-163 relay fingerprint; `SHA256SUMS` 118/118 = the sent list; manifest 117/117 = the sent count; base tree `1e7825af…dd71` = the real tree object of commit `6a25c2bb…`, reproducible only by extracting the snapshot. The failure summary was reproduced identically in **four** executions (`54_repeat_runs/`), and every regression carries an exit-code log. This is the most complete verifier return of the workstream.

## 2. Verdict: FAIL — CONCURRED IN FULL

Per the trail-127 practice Fable ran no probes; every cited mechanism was confirmed by reading the integrated source at the cited lines.

**Items C and D are CLOSED on their required boundaries** — the temp-as-filesystem-fact and exception-complete rollback fixes held under independent adversarial execution, and every R6/R7 regression stayed green, including the settled interrupt ruling. The round genuinely fixed what R7's re-check found. What it did not fix is the layer it added.

**Items A and B FAIL, and the root cause is the program's own named habit, relocated once more.** `_write_marker` returns "failed" for *any* exception anywhere in its body — including after the marker file and its directory are both durably fsynced — and `_persist_quarantine` counts a marker as landed only on a clean return. **"The function returned without an exception" is a proxy standing in for the disk facts "a record exists" / "a record is durable."** Confirmed statically:

- `stub_server.py:975` — `_restart_posture`'s durable test looks at `restart_protection` / `marker_persisted` / `recovered_from_marker` / `recovered_from_disk_fact`. A live incident whose markers failed but whose **surviving temp is sitting right in the incident** (`surviving_temp_paths`) matches none of them: the write-free mechanism R8 built is invisible to the posture function R8 built, in the same round.
- `stub_server.py:905-912` (and the fallback twin) — a directory-listing error is recorded with the **directory path** in `recovered_from_marker` and `restart_protection: "durable"`, which flows into `durable_records`. With the runbook instructing *"delete every path in `durable_records`"*, a transient `EIO` on the fallback scan presents **the whole data directory** as a record to delete. That is the sharpest finding of the round: an operator following the written instruction in good faith would destroy the evidence tree.
- Restart collapses the two sibling markers into two incidents and exposes only the first's inventory — so deleting everything the service names leaves the sibling, and the next process is quarantined with the operator having done exactly what was asked. Reconciliation as shipped is not completable from the service's own instructions.

**An honest asymmetry, stated because it is true and not because it softens the verdict:** findings 1.1–1.3 all fail in the *safe* direction — the service under-claims protection, and the fresh process still quarantines off the real disk facts. The gate-relevant dangers are 2.2 (a durable primary omitted from the inventory), 2.3 (false `durable` off a transient scan error, plus the delete-the-directory instruction), and finding 3. The verdict needs no softening; it needs the fix.

## 3. The scan-once ruling: Fable OVERRULED, by execution

`53_` §4 concurred with the Builder's scan-once judgement. **The verifier executed the exact challenge and disproved it**: process A, healthy first scan; process B quarantines the shared directory with both markers durably written; process A goes on accepting authority transitions at 200. The marker's own text says *"every process using this data directory refuses authority transitions"* — process A is a counterexample.

**The defect in Fable's reasoning, recorded precisely:** the concurrence rested on the runbooks describing a single-process configuration — but the *service's claim* is written in the marker text, and the claim says "every process", unconditionally. **A claim that exceeds its enforcement is exactly a proxy-for-fact instance** — the marker asserts a fact ("all processes refuse") whose actual ground is an unstated, unenforced usage pattern. Fable checked whether the assumption was plausible and never checked the assumption against the sentence the service ships. Same review-method gap as trails 152, 154 and 159, and this time it produced a wrong ruling rather than a missed defect. The verifier's standard is adopted verbatim as a standing rule:

> **A safety claim may rely on a single-process invariant only if the launch path enforces it, or the operating contract states it unambiguously and prevents the second process.**

## 4. The containment findings

Both confirmed by reading. The **quota leak** (`_reserve_pool` at line 1240, containment check at 1274-1277, `CaptureError` raised with no release) is a plain ordering defect. The **captures-root symlink** is the more instructive one: `realpath` on *both* sides resolves through the same pre-existing link, so the prefix check passes and bytes land outside the data directory — the R8 fix moved the blind spot from "symlink below the root" to "symlink at the root". The verifier is right that this is not the disclosed TOCTOU residual; it is a gap in the check as shipped. Severity honestly low (requires operator-placed state), gate-relevant because R9 is touching this code anyway.

## 5. Disposition

**R8 FAIL, concurred in full. Security gate OPEN. Owner POC session BLOCKED** (his trail-161 election). Items C and D closed; items A and B, the inventory findings, the scan-once enforcement and the containment completion go to **R9** (`56_`). The verifier's eight required corrections are adopted as the packet's spine; CR-R8-01's authorized item-E application is folded into the same return. Concurrency, the `25_` contract, the POC architecture and both settled rulings are **not reopened**.

**Trajectory, stated plainly for the owner.** Nine rounds. The last three have each closed everything the previous round opened and opened something narrower: R7's three findings are now one classification layer plus an enforcement gap, all inside the quarantine/recovery machinery, none reachable from any provider request, none able to double-fire an action or corrupt the comparison. The gate is converging on the reporting of failures, not the handling of them. The owner's residual-risk option (trail 151) remains available on his word, unchanged; his trail-161 election to finish stands unless he says otherwise.
