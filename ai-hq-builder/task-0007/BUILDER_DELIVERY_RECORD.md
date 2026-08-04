# Builder Delivery Record — TASK-0007 Round R5 (capture-publication correction)

**Task:** TASK-0007 R5 — one defect: SEC-R4-01, capture publication marked durable before the directory fsync.
**Builder:** Claude Code session, model `claude-opus-5` (standing authorized substitution, trail entry 69).
**Branch:** `claude/task-0002-builder-handoff-g97x8j` (operator-designated; see §8).
**Instruction authority:** `38_TASK-0007_R5_Task_Packet_Capture_Publication_Fix.md` (governing). `25_` unchanged; the R4 concurrency architecture accepted and **not reopened**. `36_`/`36A_`/`36B_`/`37_` and the shipped probes are authoritative inputs.
**Returned to:** **Fable.**
**Status:** **Built and self-tested. Independent verification pending.** No POC has been run; no provider was contacted. **Nothing is outstanding and nothing needed a ruling this round.**

**Snapshot integrity (H-06), before anything was read as authority:**

| Check | Result |
| --- | --- |
| `SHA256SUMS.txt` | **105/105 OK** |
| `authority_manifest.json` | **104/104 verified, 0 mismatched, 0 missing**; one unlisted file on disk, `SHA256SUMS.txt` itself |
| `BASE_BINDING.txt` tree, independently reproduced | **`4b0874f66d10c2fda06e5f87024372862397637a`** — matches |
| Relay's `poc/` against my R4 return | **69/71 byte-identical**; the two that differ are `stub/out/selftest.json` and `stub/out/r1_witnesses.json`, both regenerate-by-running |
| `r4_reference/stub_server_r4.py` | **`2876522bec584678c2326d002e58e9fa388b64ac9be9092c2ba1a18022450f79`** — the R4 build the verifier examined |

---

## 1. The defect, and that it was mine

`37_` §3 and `38_` describe it exactly. `write_capture` set `published = True` immediately after `os.link` succeeded, **before** the directory fsync. A failure at the directory open or fsync then left the `finally` block believing the capture had landed: it kept the reserved quota unit and left the final file on disk, while the caller rolled the transition out of live state. The survivor read `phase: committed`, `outcome: committed`, `final_status: REGISTERED` — durable evidence asserting authority for a transition that never became effective, which is the precise failure A.7 exists to prevent. Separately, a temp-unlink failure after a successful link left the final hard link, because cleanup retried only the temp name.

I wrote that ordering at R4 while fixing SEC-R3-05, and I wrote the comment above it claiming "any failure removes the temp artifact and RELEASES the pool unit" — which was true of every boundary I had thought about and false of the two I had not. The `published` flag conflated two different facts, *the link succeeded* and *the record is durable*, and the bug lived exactly in the gap between them.

## 2. The correction

Three states are now tracked separately, because conflating them is what produced the defect:

| | meaning |
| --- | --- |
| `tmp` | the temp file exists, until it is unlinked |
| `linked_path` | the final path exists, from the moment `os.link` returns |
| `published` | the record is durable — set **only after the directory fsync returns** |

The `finally` releases the pool unit and removes **both** `linked_path` and `tmp` whenever `published` is false. The final path is removed first: it is the one that would otherwise be read as durable evidence, so if only one cleanup can succeed, that is the one that matters. This also closes the temp-unlink case — when that unlink fails, `tmp` is still set *and* `linked_path` is set, so both are cleaned.

`os.link` is kept, as `38_` §5 requires; the no-overwrite property was confirmed correct and is not touched. **The concurrency model is untouched** — the change is confined to the publication ordering inside `write_capture`, exactly as the packet predicted, so there was nothing to stop and report.

## 3. My own fault suite passed against the defective build before it worked

`capture_fault_suite.py` injects at all four post-link boundaries and asserts the three properties `38_` names. Its first draft went **5/5 against the pinned R4 build** — a build that must fail three of them.

The cause: `mod.os` *is* the process-wide `os` module, so patching it is global rather than local to the loaded stub, and the draft never restored what it patched. The first injector broke `os.link` for every probe after it, so each later boundary failed at the *link* instead of at its own boundary, left nothing behind, and passed vacuously. The suite is now snapshot-and-restore around every injection, and the fault names it in a comment rather than being quietly corrected.

This is the second time in two rounds that a test of mine passed vacuously, and both times the only thing that caught it was **requiring red against the pinned defective build before accepting green against the fixed one**. That check is worth more than any individual test in this package, and it is the one habit from this program I would carry into the production wrapper unchanged.

The suite also carries a **control**: an unfaulted capture must still publish and still consume its unit. Four "nothing survived" assertions are otherwise satisfiable by a build that never publishes anything.

## 4. Verification — every figure from a command run after the last edit

| Suite | Against R5 | Against pinned R4 | Meaning |
| --- | --- | --- | --- |
| **Verifier's `chatgpt_capture_publication_fault_probe`** | **green** | **red** | SEC-R4-01, both sub-cases |
| **Verifier's `chatgpt_capture_postlink_cleanup_probe`** | **green** | **red** | link / temp-unlink / directory-open |
| **`capture_fault_suite.py`** (mine) | **5/5** | **2/5** | all four boundaries + control |
| Stub self-test | **178/178** | — | 170 from R4, plus 8 for SEC-R4-01 |
| Reviewer's full probe set (11) | **6 green** | 4 green | the five barrier-class remain per AUDIT-R4-5, ruled on in `37_` §1 |
| Superseded-build witnesses | **34/34** | — | R1 21, R2 13, both pins digest-checked |
| Deterministic barriers | **6/6** | — | corroborating, per `37_` §2 |
| Acceptance oracle | **7/7, 33 clauses** | — | branch-specific, live HTTP |
| Measurement validator | **160/160, 0 violations** | — | unchanged |
| Structural harness | **PASS** | — | harness code byte-identical, `out/**` regenerated |

On the committed-registration case the expected reading is **not** "nothing survives": the `prepared` record published successfully and legitimately remains, holding its own quota unit. A.7 is explicit that an orphan `prepared` is reported uncertain, never complete. What must not survive is the `committed` record — and it does not. Observed: `steps=['prepared-artifact-register']`, `registrations=0`, `identity_index=0`, `reserved-owner=1`.

## 5. Fable's correction to its own ruling, accepted

`37_` §2 downgrades `barrier_suite.py` from **equivalent** to **corroborating**: its `race()` helper aligns two clients immediately before sending, which aligns intent but does not deterministically force both requests to the same server-side precondition. That is right, and I accept it without reservation — I called it equivalent in the R4 record and it was not. The controlling instrument is the verifier's live-HTTP handler-entry release gate, which wraps the real handler without bypassing auth, route policy, preconditions, transition code or capture code.

I have **not** adopted that gate into my own suite this round, because `38_` says "Scope: one defect" and building new concurrency instrumentation is not that. It is the obvious first improvement if a later round reopens the area, and I would rather flag it than smuggle it in. `barrier_suite.py` stays and is labelled corroborating in this record.

## 6. Falsifier element (APP-06 / CPB-14, reflexive)

| # | Claim | Who would have to be wrong, and how | Status |
| --- | --- | --- | --- |
| 1 | SEC-R4-01 is fixed | **The verifier, with its own probes.** Both ship in this return and both go green here and red against the pin. The narrow risk is that a boundary exists that neither the verifier nor I injected at — the write, the flush, the file fsync, the mkstemp — all of which are *pre*-link and already covered by the R4 work, but "already covered" is what I believed about the post-link path too | **Built to spec; independent verification pending** |
| 2 | Nothing else regressed | **The regression battery, which I also wrote.** 178/178, 34/34, 6/6, 7/7, 160/160 and a green harness. Every one of those numbers has been green in a round that was later returned FAIL, so their value is in the delta, not the total | Not disconfirmed; **same author as the thing tested** |
| 3 | My fault suite can actually fail | **It could not, in draft, and I nearly shipped it.** It now goes 2/5 against the pin and 5/5 here, and carries a publish-control so it cannot pass by breaking everything. That is evidence it discriminates — not proof it discriminates on every property it claims | **Demonstrated in both directions** |
| 4 | The fix is confined to publication ordering | **The diff.** One function changed; the concurrency model, the lock discipline, `Disclose`, the pools and the quota accounting are untouched. If a reviewer finds a behavioural change outside `write_capture`, this claim is wrong | Not disconfirmed; **diff shipped** |
| 5 | My record matches my code | **Me.** Every figure in §4 came from a command run after the last edit. The number to distrust hardest remains the one I authored both sides of | **Self-authored; independently unverified** |

## 7. Return contents

Complete `poc/` tree, Delivery Record, self-verified `RETURN_MANIFEST.json`, `proposed_classifications.json` (**suggestion only**), and `diffs/`.

Changed: `stub/stub_server.py` (the `write_capture` publication ordering only), `stub/selftest_stub.py` (the SEC-R4-01 block), `stub/probe_runner.py` (the two new probes and their criteria).
Added: `stub/r4_reference/` (permitted by `38_`), `stub/capture_fault_suite.py`, and the verifier's two probe scripts plus their recorded outputs under `stub/security_probes/`.
Regenerated by running: `harness/out/**`, `stub/out/**`.

## 8. Open items and deviations

- **No change requests this round.** Nothing in `38_` was internally inconsistent, nothing required touching `25_` or the concurrency model, and nothing needs a ruling.
- **Immutable denylist unchanged** — `r1_/r2_/r3_reference`, harness code, `authority_manifest.json`; proven per-file in the manifest.
- **`barrier_suite.py` is corroborating, not controlling** — §5.
- **Inherited and still open:** n8n node types and parameters remain NOT TESTED (`n8n-nodes-base` blocked by the egress proxy, 403), fifth round unchanged.
- **No POC run, no provider contacted. No `13B_` obligation implemented.** Every THROWAWAY marker kept.
- **Branch deviation (unchanged, disclosed):** operator-designated branch.
- **Recommended reviewer focus:** §3 — the vacuous-pass draft is the most instructive thing in this return, and the red-before-green discipline is what I would want checked hardest.

---

*Builder-authored completion claim and evidence index — not independent evidence (APP-06). SEC-R4-01 is claimed corrected against `38_`; **no POC is claimed run, and no security property is claimed independently verified.** Per `38_` the next steps are Fable structural verification and the verifier's re-check of this one finding, after which the owner session is unblocked. That gate closes when the verifier says so, not when I do.*
