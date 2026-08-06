# 56 — TASK-0007 Round R9: marker state as facts, complete inventories, enforced invariants

**Context.** The executed R8 re-check returned **FAIL** (`54_`), concurred in full (`55_`). Items C and D are **closed on their required boundaries** and every R6/R7 regression held. What failed is the layer R8 added: the marker machinery classifies its own function returns instead of disk facts, its recovery inventories are incomplete or unsafe, the scan-once single-process assumption was **executed and disproven**, and the containment fix has an ordering leak and a root-symlink gap. **Read `54_` first; its eight "Required narrow correction" items are the authoritative inputs and this packet instantiates them.** The verifier's probe ships at `54_security_probes/chatgpt_r8_adversarial_recheck.py` and is part of the acceptance set.

**Bounded rework on the integrated R8 baseline.** No clause of `25_` changes. Concurrency, provider contracts, the POC architecture, the `47_` §3 publication-tail ruling and the R8-closed items C/D are **closed and not reopened**. Throwaway POC apparatus; every THROWAWAY marker preserved.

## 0. Snapshot, manifest, allowlists — unchanged from `25_` §0

Same allowlists; immutable denylist now includes `r1_`–`r7_reference/`; `authority_manifest.json` Fable-published and not Builder-editable; snapshot-only base binding with the executed tree recipe. **One denylist amendment, already granted:** CR-R8-01 (trail 162) — apply your item-E edit to `poc/harness/run_all.sh` in **this** return, achieving exactly the behaviour you verified (FAIL/1; INCOMPLETE/2 when every check that ran passed but one or more were NOT RUN; PASS/0; status-preserving; no vendoring, no network). That file, that change, this return only.

## 1. The organising requirement, unchanged — and now it applies to the fix of the fix

`51_` §1's rule stands: **every control must establish the fact it exists for, not a proxy.** R8 removed three proxies and introduced two new ones *inside the remedy*: "the marker function returned cleanly" standing in for "a record exists / is durable", and "no marker was found by a scan that errored" standing in for "no record exists". The §1 self-search caught one of these classes in draft; the shipped code still carried the other. **The instruction is therefore sharpened: after implementing the items below, re-run the §1 search over every function you added or modified in R8 and R9 — the last two rounds prove the pattern concentrates in new remediation code, so that is where to look first. Report the result either way.**

## 2. Required corrections — `54_`'s eight items, made concrete

**Item F — marker state is a tri-state fact, not a success Boolean.** (`54_` correction 1; findings 1.1, 1.2.)
Track each marker attempt as one of:
- **`DURABLE`** — file fsync *and* parent-directory fsync both returned. A later exception (directory close included) is a recorded soft anomaly and **cannot erase `DURABLE`** — this is the same post-durability boundary you built twice already (publication, R5/R7; rollback, R8 item D) applied a third time, to the marker writer.
- **`PRESENT_OR_UNKNOWN`** — the path was created (or may have been) but durability was not established: partial write, post-create failure, any state where the file can exist. Presence is the signal — your own docstring already says a partial marker is still a marker; the classification must honour it.
- **`ABSENT_KNOWN`** — the failure occurred before creation *and* absence was verified as a filesystem fact (the item-C method: ask the directory, and an unlistable directory establishes nothing).
`restart_protection` derives from the **best** surviving fact across both locations and the live temp facts (item G), never from exception-freeness.

**Item G — live disk facts feed the live posture.** (`54_` correction 2; finding 1.3.)
A `surviving_temp_path` in the live incident **is** a restart signal — the write-free mechanism you built for restarted processes must be visible to the posture of the raising process. While any temp or `PRESENT_OR_UNKNOWN`/`DURABLE` marker exists, the service must not emit `restart_protection: "none"`, `survives_restart: false`, or any "nothing on disk" sentence.

**Item H — one incident, one ID, one complete inventory.** (`54_` correction 3; findings 2.1, 2.2.)
Stamp each quarantine event with a stable incident ID; write the **same ID and the complete sibling-path inventory into both markers**; merge and deduplicate by ID on scan. `/health` and both 503 bodies must expose **every** incident and a `durable_records` list containing **every actual evidence record needed for reconciliation** — a durable primary must appear there even when its close tail anomalied (2.2), and both siblings must survive a restart (2.1). Acceptance: the verifier's executed sequence — write both markers, restart, delete exactly what the service names, restart again — must end **clean**, and the same sequence against pinned R8 must end quarantined.

**Item I — a scan error is never a durable record.** (`54_` correction 4; finding 2.3.)
An unlistable directory fails the current process closed with persistence classified **unknown** — it does not mint `restart_protection: "durable"`, does not put any directory path into `durable_records`, and never presents unlistable or nonexistent paths as removable evidence. `durable_records` may contain only actual marker/temp files. The transient-`EIO` sequences in `54_` §2.3 — including the one that named the whole data directory as deletable — are mandatory red-before-green cases.

**Item J — enforce the one-process invariant.** (`54_` correction 5; finding 3; supersedes `53_` §4's overruled concurrence.)
The adopted standard: *a safety claim may rely on a single-process invariant only if the launch path enforces it, or the operating contract states it unambiguously and prevents the second process.* **Selected mechanism, not delegated: an exclusive advisory lock (`fcntl.flock`, `LOCK_EX | LOCK_NB`) on `<data_dir>/.stub-<candidate>.lock`, acquired at startup and held for the process lifetime.** A second process on the same `(data_dir, candidate)` refuses to start with a truthful message naming the holder. This makes the marker's "every process" sentence true by construction — the sentence you ship must still be checked against what is enforced, per §1. If `flock` is genuinely unworkable, the verifier's alternative (rescan/generation-check before every authority transition) is pre-authorized — state which you took and why. Localhost, one operator: stop-and-report if you believe neither fits.

**Item K — complete the containment check.** (`54_` correction 6; secondary findings.)
(a) Reserve quota **after** the containment check passes, or release it on refusal — one failed check must not consume a unit (mandatory red-before-green: the verifier's exact case). (b) Validate the canonical `captures/` root itself: a pre-existing symlink at the root must be refused, not resolved through — compare the realpath of the root against the expected physical location under `--data`, don't let both sides resolve through the same link. (c) The `O_NOFOLLOW`/`openat` design carry-forward to `13B_` stands (trail 162) and is **not** an R9 obligation.

**Item E (carried) — apply the authorized `run_all.sh` edit** per §0. Non-gating, but due in this return.

## 3. What must NOT change

- No `25_` clause. Items C and D as shipped in R8 — the verifier closed them on their boundaries; do not refactor them except where item G touches the incident dict.
- Both settled rulings (publication-tail interrupts, `47_` §3; and the R8-established rollback analogue) — extended if needed, never reopened.
- `_persist_quarantine` still cannot raise.
- The immutable denylist (now through `r7_reference/`), except the single authorized CR-R8-01 edit.
- Every R6/R7/R8-confirmed regression must re-run unchanged — including the four verifier probes, the oracle, barriers, witnesses, and measurement validation.

## 4. Required tests — red-before-green against pinned R8, faults landing on both builds

Pin R8 as `r8_reference/stub_server_r8.py` (permitted addition, same precedent; add to the denylist). Every criterion shown failing against pinned R8 before claimed green, **with the injected fault asserted firing identically on both builds**. Mandatory cases, from `54_` correction 7:

1. partial marker creation (`ENOSPC` mid-JSON) → live posture must claim `PRESENT_OR_UNKNOWN`-grade protection, never "nothing on disk";
2. marker directory-close failure **after** file and directory fsync → `DURABLE` survives as a soft anomaly;
3. surviving temp plus both marker locations failing → live posture reflects the temp (item G);
4. both-sibling restart reconstruction → delete-what-the-service-names ends clean (item H);
5. transient primary **and** fallback scan failures → no directory ever enters `durable_records` (item I);
6. two processes, one `(data_dir, candidate)` → the second refuses to start (item J), and the `54_` §3 sequence cannot be reproduced;
7. captures-root symlink → refused, and containment refusal leaks no quota (item K);
8. the positive control stays green: genuine no-record failure still reports `none` truthfully and a fresh process starts clean.

Run the verifier's own `chatgpt_r8_adversarial_recheck.py` and report its result on both builds. Re-run and report unchanged: R7 adversarial probe 4/4, R6 quarantine-integrity 5/5, R5 rollback 5/5, capture-fault 9/9, oracle 7/7/33, barriers 6/6, interrupt comparison, witnesses 34/34, measurement 160/160, self-test.

## 5. Allowlist, return, stop-and-report

Per `25_` §0 plus: `stub/r8_reference/`, new probe modules under `stub/`, and the single CR-R8-01 edit. Return: Delivery Record with the reflexive falsifier; the §1 re-search over R8+R9 code, reported either way; red-before-green evidence with fault-landed assertions; `RETURN_MANIFEST.json` regenerated after the final run; H-06 first. **Stop and report** if any correction cannot be made without touching a `25_` clause, if the flock mechanism conflicts with anything the harness does, or if any clause here is internally inconsistent — the discipline has caught a real defect (twice a Fable defect) in every round it has run.

## 6. After R9

R9 return → Fable structural verification (static, trail-127) → **executed verifier re-check** under the trail-158 rule → owner hands-on session (his trail-161 election). The verifier's four-execution reproducibility standard from this round is the bar the R9 evidence should meet.
