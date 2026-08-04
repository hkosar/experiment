# Builder Delivery Record — TASK-0007 Round R2 (stub rework + Release-1 re-aim)

**Task:** TASK-0007 R2 — security and evidence-integrity rework of the POC wrapper stub, merged with the Release-1 scenario re-aim.
**Builder:** Claude Code session, model `claude-opus-5` (standing authorized substitution, trail entry 69).
**Branch:** `claude/task-0002-builder-handoff-g97x8j` (operator-designated; see §9).
**Instruction authority:** `14_TASK-0007_R2_Task_Packet_Stub_Rework_and_Release1_Reaim.md`, whose §2 contract governs where it disagrees with any earlier document. `13_` read first, as instructed.
**Returned to:** **Fable.**
**Status:** **Rework complete and self-tested. No POC has been run; no provider was contacted.**

**Snapshot integrity (H-06):** `SHA256SUMS.txt` validated **48/48 OK, 0 mismatched** before anything was read as authority. The relay's `poc/` copy is **byte-identical to the accepted R1 return, 40/40**.

---

## 1. What changed, in one paragraph

The stub is rebuilt against `14_` §2's corrected contract: **1,324 lines, Python standard library only, zero third-party imports, 14 routes.** The POC-1 side effect moved from an unguarded `/sink` to `/relay/deliver` behind a single-use capability bound to the action id, case, resolved target and payload digest; POC-3 got its own retry-tolerant `/stage/deliver`. Owner decisions are terminal and atomic. Every capture is written — temp file, flush, fsync, atomic rename — **before** the state it records is committed, carries a stub-minted timestamp, candidate, run instance, route and `authored_by`, and cannot overwrite a prior run. Boundary checks moved to dispatch. The three workflows and the Zapier specs are re-aimed to `09_` §2's Release-1 scenarios.

**Self-test: 56/56.** **R1 witnesses: 21/21** reproduced against the pinned R1 artifact.

## 2. How "demonstrated failing against the unfixed behaviour" is met

`14_` §3 requires it and R1 met it with defect probes. **I did not use defect switches** — a switch that can turn a control off is itself a finding (P2V-01), and R2 is a round about not shipping controls that can be reached around.

Instead `stub/r1_witnesses.py` runs the probes **against the superseded build itself**, held byte-identical at `stub/r1_reference/stub_server_r1.py`. Its **SHA-256 is checked at run time against `ecdaae67…76328ac`** — the fingerprint `13_`'s chain-of-custody table records for the target the verifier reviewed — and the witness run **refuses to continue** if it does not match. So the "unfixed behaviour" shown is the artifact the review actually examined, not a reconstruction of it.

**21/21 witnesses reproduce**, covering SEC-R1-01, -02, -03, -06 and FAB-01, -02, -05, -06, -07, -08, -09, -13, -14, -15. A sample of what R1 actually did, quoted from `out/r1_witnesses.json`:

- `POST /sink {"anything": "at all"}` → **200 `delivered: true`** — the represented side effect, with no capability, no case, no authorization.
- A **reject overwritten by an accept**, then `verify-decision` → **`authorized: true`**: an ActionRequest minted for a case the owner had rejected.
- `redact({"opaque": <live token>})` → **the token, verbatim**; and `authority_id`/`authority_version`/`tokens_used` → **`[REDACTED:key-name]`**, a bare constant the harness scores PRESENT.
- The pending branch and the owner-key refusal → **captures 1 → 1**: no record of either.
- **7 routes** accepted a provider-authored `decision` field.
- A duplicate run declaration → **checkpoints 1 → 0, `started_at` changed, status 200**.
- `reconcile` on a run that does not exist → **200, `side_effect_certain: true`, citing ACT-01**.
- `metadata: []` → **200** while `metadata: [1]` → **AttributeError**, which is precisely `13_` VC-01's point: a test written to the review's literal repro passes against unfixed code.

## 3. Security corrections — `SEC-R1-01..08`, `DOC-01`

| ID | Correction | Witness / test |
| --- | --- | --- |
| **SEC-R1-01** | `/sink` is gone. The POC-1 side effect is `/relay/deliver`, gated on a single-use capability bound to action id, case, resolved endpoint and canonical payload digest, with a short TTL. Implemented **per `13_` VC-03, not per `12_`'s literal text**: POC-3's staging is a separate retry-tolerant path with no capability, because a blanket single-use rule would fail the round's own mandated mid-flight kill and mis-score the provider retry POC-3 exists to measure | direct call, altered action/case/payload/capability, expired capability — all refused; replay returns the prior receipt |
| **SEC-R1-02** | Redaction gained **exact-value scrubbing**: live token and key values are compared, **including as substrings**, by constant-time comparison before anything reaches a log or capture. Corrected **jointly** with FAB-05, which pulls the other way | live token under `opaque`, `note`, `ｔｏｋｅｎ`, `tоken` and a 40-char key — absent from every capture |
| **SEC-R1-03** | The first valid owner decision is **terminal**; a second is a captured 409. Decision lookup and token consumption happen in **one critical section** against an immutable record — R1 read `STORE.decisions` unlocked and locked only for the spend | second decision → 409 |
| **SEC-R1-04** | Capture-before-commit everywhere, **including the token-spend path** (FAB-04) | capture failure during a decision → neither decision nor authorization survives; capture failure at spend → **token still unspent**, and the next verify succeeds |
| **SEC-R1-05** | Logging emits a **route-matched constant plus the status and nothing else**, per `13_` VC-04 — `log_message`, `log_request` and `log_error` are all silenced, so neither a secret in the path, nor a query string, nor a malformed request line reaches stderr | secret in the path, in a query, and in a garbage request line — absent from the captured stderr |
| **SEC-R1-06** | Handler-level exception boundary returning a structured refusal with no traceback; nested types validated before use; **the test uses a truthy non-dict**, per `13_` VC-01 | truthy list/str/int/bool metadata → no crash; deeply malformed JSON → 400, service still healthy |
| **SEC-R1-07** | `Content-Length` bounded `0 ≤ n ≤ MAX_BODY`; negative refused; conflicting duplicate headers refused; non-identity transfer encodings refused; **socket timeout** added, which is what actually closes connect-and-send-nothing | all four, over real sockets |
| **SEC-R1-08** | `application/json` required, and a **per-process provider credential** on every provider-facing route, distinct from the owner key and conferring no owner authority. **Paired with the runbook correction** `13_` §2.2 names | browser-simple POST → 415; missing provider credential → 403 |
| **DOC-01** | The banner prints the keys as **bare values with no copyable command**, and **all three runbook sites** moved to `read -rs` shell variables — `13_` §2.2 is right that fixing only the banner would close the finding falsely | banner contains no `curl`; no request line logged at all |

## 4. Evidence integrity — `FAB-01..17`

| ID | Correction |
| --- | --- |
| **FAB-01** | Every refusal path captures, including the pending branch, the owner-key refusal and the boundary 400s. Key material is never recorded — the capture says a decision was *attempted without owner authority*, not what was presented |
| **FAB-02** | `--candidate` is **required and name-validated**; the service refuses to start without it. It threads into every path and every record body |
| **FAB-03** | A per-process `run_instance` in every filename, files created **`O_EXCL`**, never truncating |
| **FAB-04** | The authorization capture lands before the token is spent |
| **FAB-05** | Key-name matching is now **whole-segment**, with an explicit non-secret allowlist covering the D-EC_ REQUIRED names, `tokens_used` and `session_id`. A withheld value is a **structured marker** (name, type, bytes, digest), never a bare constant |
| **FAB-06** | The provider-decision refusal and the partition/envelope checks run **at dispatch**, with a commented exemption list. Verified across **all 11 persisting routes** |
| **FAB-07** | Run identity is **stub-minted**; a duplicate declaration is a captured 409 preserving the prior `started_at` and checkpoint count. Provider correlation is a separate, provider-marked field that anchors nothing |
| **FAB-08** | `reconcile` reports exactly what it compared and states plainly `external_post_state_checked: false`; the ACT-01 citation is removed. `triage` no longer asserts `links_followed`/`actions_taken` — provider conduct is measured at the provider |
| **FAB-09** | Every capture carries `recorded_at` plus a note that it is a local wall clock with **no authority** |
| **FAB-10** | Atomic writes; no `.tmp` survives; every capture parses |
| **FAB-11** | POC-3 stage posts file under **POC3** |
| **FAB-12** | Endpoints derive from the **bound port**, with `--advertise` for the container case. No second literal |
| **FAB-13** | `_ct_eq` handles non-ASCII rather than raising before a verdict |
| **FAB-14** | The extra-fields refusal records the **count**, never the rejected key names |
| **FAB-15** | The five-component identity tuple, all required, malformed → captured 400; the idempotency key derives from all five and **travels in the ActionRequest payload to the target** |
| **FAB-16** | `/health` no longer exposes `captures_written` |
| **FAB-17** | Token lookup is a dict hit; `receipts` is a bounded count; case/receipt/run/capture ceilings added |

## 5. Release-1 re-aim (work item D)

The three n8n workflows are replaced with `09_` §2's scenarios — **POC-1 Builder-return pipeline** (11 nodes: envelope + five-component identity binding with the digest **computed here rather than trusted**, duplicate/rejection branch, pause, token-only verify, capability relay, receipt), **POC-2 idea capture and staging** (Case A owner-authored vs Case B imported, with an assertion node that fails if external origin ever acquires instruction authority), **POC-3 nightly integrity sweep** (stub-minted run id, retry-tolerant stage, checkpoint, reconcile). Every provider-facing HTTP node carries `X-Provider-Key` and `Content-Type` — **6/6, 1/1 and 5/5**.

The Zapier build specs are re-aimed to the same three scenarios and carry the R1P-05 artifact-handling measures. All three runbooks updated, including both `13_` §2.2 corrections.

**Reported, not absorbed:** the three R0 workflow files are **replaced, not edited in place** — their Release-2 scenarios live on in `00_` §10 and `09_` §2's parking statement, so nothing is lost, but the file names change and I am flagging it rather than letting a diff look like deletion.

## 6. Two places the contract could not be satisfied as written — reported per `14_` §5

**(a) `harness/**` is excluded from the allowlist, but §5 requires the structural harness re-run — and running it rewrites `harness/out/`.** Four output files changed: `structural.json`, `structural.log`, `boundary.json`, `boundary.log`. **No harness code file changed** — verified by hash against the relay for all six. I shipped the regenerated outputs because reverting them would ship evidence naming workflow files that no longer exist, which is worse than the tension. **If Fable wants `harness/out/` reverted, it is a copy of four files** — but then the shipped structural report describes the R0 workflows.

**(b) The secret scan returns 2 hits, neither mine to fix and neither a credential.** `harness/check_boundaries.py` carries the synthetic `"Authorization: Bearer abc"` fixture flagged at R1 — still outside the allowlist. `stub/r1_reference/stub_server_r1.py` carries `password: hunter2` in a docstring example; that file **must stay byte-identical** to the reviewed target or the witness pin fails by design. Everything R2 wrote scans clean.

## 7. Verification

- **Stub self-test 56/56**: R1P-04 9 · `12_` §5 14 · `13_` §4 17 · boundary 6 · **live-HTTP transport 10**.
- **R1 witnesses 21/21**, pin verified against the reviewed target's SHA-256.
- **Harness PASS**: structural 3/3 on the re-aimed workflows, boundary clean 3/3, 39 harness self-test cases.
- **All 9 workflow-declared endpoints resolve**; the relay and stage targets are server-supplied by design.
- **Stdlib-only** across all three stub files (AST scan). **pyflakes clean.**
- **Allowlist:** 13 modified + 6 added + 3 replaced; the only paths outside are the four `harness/out/` artifacts in §6(a).
- **`RETURN_MANIFEST.json`** self-verified by re-hashing every entry from the unpacked zip.

## 8. Falsifier element (APP-06 / CPB-14, reflexive)

| # | Claim | Who would have to be wrong, and how | Status |
| --- | --- | --- | --- |
| 1 | The corrected contract is implemented | **An independent reviewer, again.** R1 shipped with 66 green self-test cases, two mandatory refusals working, and my own adversarial pass behind it — and an independent review still found a gate-blocking bypass, because everyone had tested the guarded endpoints and nobody had asked whether the guarded thing was reachable another way. **I have no basis to believe R2 is different in kind**, only that this round's brief was wide enough to name what R1's missed. `14_` §6 sends it back to ChatGPT; that is the right disposition and I am not pre-empting it | **Built to spec; independent verification pending** |
| 2 | The witnesses prove the unfixed behaviour | **The pin, and it is checked.** If `r1_reference/stub_server_r1.py` were a variant, the witnesses would describe a build nobody reviewed — so the run verifies its SHA-256 against `13_`'s recorded fingerprint and refuses to continue on mismatch. What the witnesses do **not** prove is that R2's fixes are complete: they show 21 specific behaviours changed, not that no twenty-second exists | Not disconfirmed; **scope stated** |
| 3 | Redaction is now correct in both directions | **Me, about the allowlist.** The two directions genuinely pull against each other, exactly as `13_` warns. I protected the D-EC_ REQUIRED names, `tokens_used` and `session_id` by name — **a field the harness needs that I did not enumerate would still be destroyed**, and the structured marker means the loss would at least be visible rather than scored PRESENT. That is a real improvement and not a proof | **Improved; enumeration is mine and could be short** |
| 4 | Capture-before-commit holds everywhere | **The ordering.** Tested at the two sites `13_` names — the decision path and the token-spend path — by forcing `write_capture` to raise. Other handlers follow the same shape by construction, and construction is not a test. `14_` C-6 also warns that a generic exception boundary added *before* this fix makes the failure quieter rather than safer; the boundary went in **after**, and the two capture-failure tests are what says so | Not disconfirmed; **two sites tested, others by construction** |
| 5 | My record matches my code | **Me.** Every figure in §7 was produced by a command run after the last edit. The one number I want checked hardest is "56/56", because a self-test I wrote passing a contract I also wrote is the weakest evidence in this package — which is why §2 exists and why `14_` §6 sends the result to an independent reviewer | **Self-authored; independently unverified** |
| 6 | The re-aimed workflows express `09_` §2 | **The n8n importer, still.** Structural validation and boundary checks pass, but node types and parameters remain **NOT TESTED** — `n8n-nodes-base` is still blocked by this environment's proxy. This is R0's falsifier row 2, inherited unchanged for the third round, and it closes at import time on the owner's host | **Open, inherited** |

## 9. Open items and deviations

- **Contract tensions reported, not absorbed** — §6(a) `harness/out/`, §6(b) the two secret-shaped fixtures.
- **Workflow files replaced rather than renamed in place** — §5.
- **R0 falsifier row 2 still open** — node types/parameters NOT TESTED.
- **No POC run, no provider contacted.** The Zapier MCP tools that appeared last round are gone from this session; they were unused then and are unavailable now.
- **No scope deviations.** Nothing outside the `14_` §4 allowlist except §6(a). No `13B_` obligation implemented. No provider selected or ranked. Every THROWAWAY marker kept, and the header still names the four things the real wrapper needs that this deliberately lacks.
- **Branch deviation (unchanged, disclosed):** operator-designated branch.
- **Recommended reviewer focus:** §2 first — the witness method is what makes the rest checkable. Then §6(a), which needs a ruling.

---

*Builder-authored completion claim and evidence index — not independent evidence (APP-06). The rework is claimed complete against `14_` §2; no POC is claimed run, and no security property is claimed independently verified.*
