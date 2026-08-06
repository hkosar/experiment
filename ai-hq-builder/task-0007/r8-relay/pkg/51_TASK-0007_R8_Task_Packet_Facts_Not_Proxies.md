# 51 — TASK-0007 Round R8: replace the proxies with the facts they stand for

**Context.** The executed re-check of R7 returned **FAIL** (`49_`), concurred in full (`50_`). R7 is incomplete, not wrong: every R6 behaviour re-executed unchanged, all four R7 defect flags are genuinely fixed on the inputs they were written for, and the settled publication-tail interrupt ruling holds. Three controls remain, each correct on the input it was shown and blind one step over.

**Bounded rework on the integrated R7 baseline.** No clause of `25_` changes. Concurrency, the provider contracts, the POC architecture and the `47_` §3 publication-tail ruling are **closed and not reopened**. Throwaway POC apparatus, no Track B credit, every THROWAWAY marker preserved. **Read `49_` first; its per-finding "Required R8 correction" bullets are authoritative inputs, and its probe at `49_security_probes/chatgpt_r7_adversarial_recheck.py` is part of the acceptance set.**

## 0. Snapshot, manifest, allowlists — unchanged from `25_` §0

Same allowlists, same immutable denylist (now including `r1_`–`r6_reference/`), same Fable-published `authority_manifest.json` (not Builder-editable), same snapshot-only base binding with the tree-reproduction recipe. **`25_` is the governing contract and is unchanged; this packet is a build instruction against it.**

## 1. The organising requirement — read this before the item list

The three findings are one habit. Each control tests a **cheap proxy** instead of the **fact it exists to establish**:

| Control | Proxy it currently tests | Fact it must establish |
| --- | --- | --- |
| no-artifact early return | a local variable is empty | no temp or final name **ever existed on disk** |
| rollback close tail | the exception is an `OSError` | **anything at all** went wrong after durability |
| restart quarantine | no marker file is present | the previous process **did not quarantine** |

**Every correction below must establish the fact, not a better proxy for it.** And the specific instruction that matters more than the three fixes: **before returning, search the stub for a fourth instance of this pattern** — any place where a control's test is a stand-in that is correct on the failure it was shown and silent on a neighbouring one. Report what you find, including "I looked here and here and found none." A fourth instance found by the Builder is worth more to this program than the three fixed ones.

## 2. Required corrections

**Item A — an unpersisted quarantine marker must not be only diagnostic.** (`49_` §2; gate-blocking.)

`_persist_quarantine` may still not raise — that constraint was right and stands. But `marker_persisted: false` currently ends the story, and `_scan_quarantine_markers` reopens clean because an absent marker is indistinguishable from never-quarantined. Establish the fact. Acceptable resolutions, **state which you took and why**:

- a **second durable control location** attempted when the first fails (a different directory, a differently-named sentinel, a marker beside the ambiguous record itself), with the same fail-closed scan treatment; and/or
- **inverting the write** so the durable signal is created *before* the operation that can fail and removed only on proven success — a failed removal then leaves a spurious marker, which is the safe direction, and it removes the structural absurdity of recording a storage failure using the storage that just failed; and/or
- **binding the start path** so the same candidate and data directory cannot reopen without explicit reconciliation, per item 5's second permitted remedy.

If, after a genuine attempt, no durable record can be made — a wholly read-only filesystem is the honest case — then the service must **say so truthfully and prominently** and the runbook must carry the operator instruction. What it must not do is claim a protection it does not have.

**Item B — the `/health` and 503 text must be conditional and true.** (`49_` §2.)

`stub_server.py:1360-1365` emits `reconcile_by: "…restarting does not clear it"` unconditionally, in the same object as `marker_persisted`. When the marker did not land, that sentence is false, and it sits one key from the field the Builder added specifically so an operator could tell the difference. Make every operator-facing statement about restart behaviour conditional on whether a durable record actually exists. **Audit the 503 body and the runbooks for the same sentence**; fix wherever it appears.

**Item C — track temp creation as a filesystem fact.** (`49_` §3.)

`fd, tmp = tempfile.mkstemp(...)` binds `tmp` only on return, so an exception between the exclusive create and the assignment leaves an artifact with `tmp is None`, and the no-artifact early return then declares nothing was created. Select and assign the temp pathname **before** the create, or otherwise make a post-create/pre-return exception discoverable. **The early return may run only after establishing that neither a temp nor a final name ever existed.** The ordinary `os.makedirs`-failed case that motivated item 3 must stay fixed — it is a real availability defect and must not regress into a spurious quarantine.

**Item D — make the rollback post-durable tail exception-type complete.** (`49_` §4.)

Once the rollback directory fsync returns, the removal is durable and nothing later can undo it. Every subsequent close-tail exception — **not only `OSError`** — must be recorded as a soft anomaly, and quota release at line 906 must still occur.

This is the `47_` §3 ruling applied to the tail that did not receive it. **That ruling is settled and is not being reopened**; you are extending it, not revisiting it. Note explicitly that `KeyboardInterrupt` and `SystemExit` reach this tail and are not `OSError`, which is what makes the case reachable in an owner session that ends with Ctrl-C. The verifier's plain `RuntimeError` is the cleaner probe; use it for the red-before-green case.

**Item E — non-gating, for the owner's session rather than the gate.** (`49_` "Harness qualification"; `50_` §5.)

`run_all.sh` printed `=== HARNESS FAIL ===` when the Node structural check could not run because `n8n-workflow` was unavailable, while every security-relevant Python check passed. That is a verifier-environment limitation, not a product defect, and it is **not** part of this gate. But the owner will run this script himself: an unavailable optional dependency must report as **unavailable / not run**, distinctly from a check that ran and failed, and the exit status must reflect that distinction. Do not vendor the dependency; do not add a network requirement.

## 3. What must NOT change

- No `25_` contract clause. Concurrency, the authority model, `Disclose`, the A.4 amendment, the three capture pools, the measurement contract — all closed.
- The immutable denylist: harness code and `r1_`–`r6_reference/` byte-identical; `authority_manifest.json` Fable-owned.
- The `47_` §3 publication-tail interrupt ruling — settled, independently concurred, extended by item D and not reopened.
- `_persist_quarantine` must still never raise. Item A adds durability, not a new failure path into the quarantine handler.
- Every R6- and R7-confirmed result must re-run unchanged.

## 4. Required tests — red-before-green, with the anti-evasion check

Every criterion must be shown **failing against pinned R7** before being claimed green, and — the check you applied unprompted at R7 and which must now be standing practice — **the injected fault must be shown landing identically on both builds**, so a green result cannot come from a build that routed around the injection point.

Mandatory red-before-green cases, at minimum:

1. quarantine-marker **directory** creation fails (`EROFS`), then restart with the same candidate and data directory;
2. quarantine-marker **file** creation fails (`EACCES`) after the directory exists, then restart likewise;
3. temp file **created but an exception raised before the path returns**, with the rollback proof also forced to fail;
4. a **non-`OSError`** raised after the real rollback directory close, with the real deletion and real fsync allowed to complete;
5. the `/health` and 503 text asserted **in both directions** — marker persisted, and marker not persisted.

Pin R7 as `r7_reference/stub_server_r7.py` on the established precedent and add it to the immutable denylist.

**Re-run unchanged and report:** verifier rollback probe 5/5, capture-fault suite 9/9, acceptance oracle 7/7 / 33 clauses, deterministic barriers 6/6, current-process fail-closed, the prepared-record and quota behaviour, self-test, witnesses, and measurement validation. Run `49_security_probes/chatgpt_r7_adversarial_recheck.py` and report its result on both builds.

## 5. Allowlist, return, stop-and-report

Allowlist and denylist per `25_` §0, plus `stub/r7_reference/` and any new probe modules under `stub/` (covered by §5's "and its tests"). `harness/out/**` and `stub/out/**` regenerate by running. No `13B_` obligation.

Return: Delivery Record with the reflexive falsifier; **the §1 fourth-instance search and its result, stated either way**; the red-before-green evidence with fault-landed assertions on both builds; `RETURN_MANIFEST.json` self-verified — regenerated **after** the final run, as R7 correctly did; H-06 first.

**Stop and report** if any correction cannot be made without changing a `25_` clause, if item A cannot be satisfied on a filesystem that has already failed and you believe the honest answer is truthful disclosure rather than a durable control, or if any clause here is internally inconsistent. Stop-and-report has caught a real defect in every prior round; keep using it.

## 6. After R8

R8 return → Fable structural verification (static, per the trail-127 practice) → **executed verifier re-check**, per the standing rule at `48_` §5: a return moves this gate only if it carries the input archive's SHA-256 and reproduction notes sufficient to re-run its result. On that re-check the owner's hands-on n8n-versus-Zapier session unblocks.
