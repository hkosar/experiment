# Builder Delivery Record — TASK-0007 supplemental round R1 (the POC wrapper stub)

**Task:** TASK-0007 R1 — build the throwaway wrapper stub the three workflows already call.
**Builder:** Claude Code session, model `claude-opus-5` (standing authorized substitution, trail entry 69).
**Branch:** `claude/task-0002-builder-handoff-g97x8j` (operator-designated; see §8).
**Instruction authority:** `08_TASK-0007_R1_Wrapper_Stub_Packet.md`. Scenario context read but **not acted on**: `09_` and `10_` — see §2.
**Returned to:** **Fable.**
**Status:** **Stub complete, adversarially reviewed, and self-tested at 66 cases. No POC has been run; no provider was contacted.**

**Snapshot integrity (H-06):** `EXPORT_MANIFEST.json` validated **41/41 entries, 0 mismatched, 0 missing, 0 unexpected** before anything was read as authority. The relay's `poc/` copy is **byte-identical to the accepted R0 return, 36/36**, so the work tree is the accepted baseline rather than my own copy of it.

---

## 1. What was built

A single-file service, `poc/stub/stub_server.py` — **653 lines, Python standard library only, zero third-party imports** (verified by AST scan). Starts with one command, no database, no Docker:

```
cd poc/stub && python3 stub_server.py --port 8787
curl -s http://127.0.0.1:8787/health
python3 selftest_stub.py            # 66 cases
```

**THROWAWAY marker** in the module header, in `/health`'s response body, in an `X-Throwaway` response header on every request, in every capture record it writes, and in the README section. It states plainly that it is not the AI OS wrapper, earns no Track B credit, and must not survive into production — and names the four things it deliberately lacks that `13B_` requires of the real wrapper (authentication, cryptography, persistence, clock authority).

**Every endpoint the shipped workflows call resolves.** Checked mechanically rather than by eye: the workflow JSON references **9 wrapper paths**, the stub exposes those 9 plus `/health`, `/owner/cases`, `/owner/decide` and `/sink` (**13** total) — **0 called-but-missing, 0 orphaned routes**. The Zapier build spec's 7 paths are a subset.

## 2. Scope — what I did not do, and why

`09_` re-aims the D3 scenarios to the Release 1 App-Building Management Platform, and `10_` returns **PASS WITH CHANGES**. Both are explicit that this does not touch R1:

- `09_` §4: *"TASK-0007 **R1 (wrapper stub) continues unchanged** — its endpoints are scenario-agnostic by design."*
- `10_` gate state: `TASK-0007 R1 generic stub: MAY CONTINUE` · `TASK-0007 R2 scenario work: BLOCKED UNTIL CORRECTIONS` · `Provider POC execution: BLOCKED UNTIL CORRECTIONS`.

So I built the stub scenario-neutral and **did not re-aim any workflow, runbook scenario, or the cost model** — that is R2, and it is blocked. The stub's endpoints carry no scenario assumption: `/poc1/review-case` takes an enveloped payload with metadata and returns a token; nothing in it knows or cares whether the artifact is a call transcript or a Builder return.

**Zapier MCP tools appeared in this session.** I did not use them. Running any provider POC is blocked by `10_`, and the sequencing in `08_` puts the owner session after Fable's verification of this round. I also did not call the read-only connection-listing tools: that would be contacting a provider and reading the owner's account outside an authorized session. **Flagged as a change request in §7** because it materially changes what the owner session may need.

## 3. The two mandatory refusals, shown failing

`08_` §R1 names two refusals that must ship demonstrated. Both do, in `poc/stub/out/stub_selftest.json`:

**Refusal 1 — missing / forged / replayed resume token.** Seven cases: no token, forged token, empty string, non-string (object) token, a valid token with no owner decision yet, the replay after a legitimate use, and a token from a different case. All refused with distinct reasons.

**Refusal 2 — an approval decision arriving from the provider side.** Twelve field spellings — the five obvious ones plus `Approved`, `APPROVED`, `approve`, `result`, `status`, a Cyrillic-homoglyph `decisоn`, and `target_endpoint` — each rejected **while accompanying an otherwise-valid token**, plus the same rejection at case-open time. This is now an **allowlist** (`token` and nothing else), which is why the homoglyph and casing variants an attacker used to slip past a name check are all refused. The check runs **before** the token is examined, and a control case proves the refused attempt **did not burn the owner's token** — a refusal that consumed the token would be a denial-of-service on the owner's own approval. **And the decision must reach the owner surface through the owner key**, which is §4a #1.

The rest of the 66: envelope required before classification (missing envelope, wrong trust class, envelope-without-partition); partition control (personal refused at both entry points, absent partition refused); **no Personal route exists at all** (404, and the route table is enumerated in the self-test rather than asserted); POC-3 flow including a checkpoint for an unannounced run; secret redaction with a **non-vacuity check** that the redactor actually fired; `synthetic: true` on capture records; capture path-traversal refusal; and the eight §4a regressions.

## 4. The defect the live path caught that the unit path did not

I ran the self-test first — 36/36 — and then ran the server over real HTTP with curl. **The live run failed.**

The original `consume_token` marked a token consumed at *validation* time. So a provider polling `/poc1/verify-decision` before the owner had decided — which is the normal shape of a paused flow — **burned the token**, and the owner's subsequent approval could never be relayed. The whole POC-1 flow was broken in the one way that matters.

The self-test missed it because it used *two different cases* for "valid token, no decision yet" and "token + decision → authorized". A real provider polls **the same token twice**.

Fixed by splitting `peek_token` (validate, do not consume) from `spend_token` (consume, only once the case is terminally decided either way), and **the missing regression is now a self-test case**: same token, polled before the decision → pending; owner decides; same token → authorized; again → replay refused. Live HTTP confirms the same sequence.

It is a finding about my own verification rather than about the code: **a unit test I wrote passed a contract my code did not honour, because I had unconsciously written the test to the shape my code produced rather than the shape a provider produces.** §4a is the larger version of the same lesson.

## 4a. The adversarial pass, and the eight further defects it found

The two mandatory refusals are exactly the kind of control that passes its own self-test and fails a real attacker, so I ran independent attackers against the stub — each on one lens, each told to attack only the six properties `08_` specifies and to ignore production hardening the packet excludes.

**Two attackers reported before I stopped the run**; I stopped it because my fixes had changed the code out from under the remaining four, so their results would have been against a superseded target. **I then ran the unreported lenses (envelope, partition) against the fixed stub myself**, and found one more defect doing so. I am stating that plainly rather than implying six independent attackers cleared this build.

| # | Defect | Found by | Severity as judged against `08_` |
| --- | --- | --- | --- |
| 1 | **The provider can self-approve.** Nothing distinguished the owner's request to `/owner/decide` from the provider's. The provider opened a case, approved it itself, and walked away with an authorized ActionRequest — mandatory refusal 2 defeated **through the owner door while the field-name check passed the whole time** | me, then independently by attacker 1 | the finding of the round |
| 2 | `/poc1/review-case` handed the provider the `case_id` — the one value `/owner/decide` keys on. The provider was given the address of the door it should not find | attacker 1 | root cause of #1 |
| 3 | **`redact()` could not fire on structured JSON.** Once JSON is decoded, `{"api_key": "..."}` contains no string a value-shape regex can match, so credential *fields* — including a live resume token — persisted verbatim into capture records | attacker 2 (certain) | property 5 broken |
| 4 | **The provider chose the destination of the owner-approved action.** `target_endpoint` in the verify request became the ActionRequest's endpoint, so the provider could redirect an action the owner approved | attacker 2 (certain) | property 2 broken in substance |
| 5 | Capture records used a fixed filename per step and **silently overwrote**, so a session with many runs would ship only the last of each kind — evidence loss disguised as evidence | attacker 2 (certain) | property 6 broken |
| 6 | **Rejections and owner decisions wrote no capture at all**, so the POC-1 rejection path would leave no record | attacker 2 (certain) | property 6 broken |
| 7 | `/owner/decide` **crashed** with an unhandled `TypeError` on a non-hashable `case_id` — no HTTP response from the one endpoint whose failure mode must be a refusal. Crashing is not failing closed | attacker 2 (speculative — confirmed real) | fail-closed posture |
| 8 | A **non-dict `envelope` crashed** the partition check with `AttributeError` — the same fail-closed failure as #7, in a different handler | me, attacking the fixed stub on the unreported envelope lens | fail-closed posture |

**All eight are fixed, and every one has a regression case**: the self-test grew **39 → 66 cases**. The fixes worth naming:

- **A per-process owner key**, printed at startup, never given to a provider, required by `/owner/decide`. It makes "the owner decided" a *checked* fact rather than "something reached the port."
- **`/owner/cases`**, so the owner lists their own pending work instead of being told the case id by the provider — closing #2 at its root rather than only at the door.
- **`verify-decision` became an allowlist**: only `token` is accepted, anything else refused. That subsumes the decision-field denylist for every casing, unicode, and nesting variant attacker 1 slipped past it with — and it is what closes #4.
- **Key-name redaction alongside value-shape redaction**, because neither alone catches both free-text and structured secrets.

**What the attackers tried and could not break** is also evidence: 20 recorded failed attacks across token forgery, truncation/extension, case and whitespace and unicode variants, type confusion, key-name confusion, a 25-trial concurrent double-spend race against the `peek`/`spend` split, and replay in every ordering.

## 5. Verification

- **Stub self-test: 66/66 cases**, including both mandatory refusals, the §4 regression, and a case for every one of the eight §4a defects.
- **Live HTTP end-to-end**, not just the dispatch function: health, case open, early poll (pending), owner decision on the owner surface, authorized ActionRequest, replay refused, provider-supplied decision refused.
- **Harness re-run: PASS** — structural validation 3/3, boundary check clean 3/3, and **39 harness self-test cases** (10 + 9 + 14 + 6) on top of the stub's own 39.
- **Workflow definitions: UNCHANGED, all three byte-identical to the accepted R0 return.** `08_` permits corrections if pointing the flows at a real stub surfaces them; **none were needed**, because the stub was written to the paths the workflows already declare. Falsifier row 2 of the R0 record — "node types and parameters are NOT TESTED" — is therefore **still open**, and is closed at import time on the owner's host, not here.
- **Stdlib-only confirmed by AST scan** of both stub files: zero third-party imports. **pyflakes clean.**
- **Secret scan over the whole return payload: 1 hit, and it is not mine to fix.** Eight credential-shaped patterns over every file. The single match is the literal `"Authorization: Bearer abc"` inside `poc/harness/check_boundaries.py` — a **synthetic fixture in that checker's own self-test**, in a file accepted at R0 and **outside this round's allowlist**, so I did not touch it. It is not a credential. My own new files scan clean: the stub self-test's probe values are assembled at runtime precisely so that no credential-shaped literal enters the payload from anything I wrote this round. Offered as a one-line cleanup whenever `harness/` is next writable.
- **Allowlist: everything written is inside `poc/stub/**`, `poc/runbooks/RUNBOOK-n8n.md`, `poc/runbooks/RUNBOOK-owner-session.md`, `poc/README.md`.** No workflow JSON changed. No ai-hq file outside `poc/` touched.
- **`RETURN_MANIFEST.json`** self-verified by re-hashing every entry from the unpacked zip.

## 6. Falsifier element (APP-06 / CPB-14, reflexive)

| # | Claim | Who would have to be wrong, and how | Status |
| --- | --- | --- | --- |
| 1 | The two mandatory refusals hold | **An attacker, and one already did.** My first version relied on a field-name *denylist*, and I wrote in this row's first draft that it was "defence in depth" behind the token+owner-decision join. **That was wrong, and the attackers proved it**: the join itself was defeatable, because nothing stopped the provider recording the owner's decision (§4a #1). The denylist is now an allowlist and the owner surface is key-protected. What remains unproven: the owner key is a shared secret over plain HTTP on loopback — anything that can read the operator's terminal or the process environment has it. For a throwaway stub on the owner's own host that is the right level; it is not authentication | **Attacked, broken, fixed, re-attacked** |
| 2 | The workflow definitions are still sound | **Unchanged and still unproven at the same point.** No correction was needed, so R0's falsifier row 2 is inherited verbatim: node types and parameters remain NOT TESTED because `n8n-nodes-base` is still blocked here. I did not close that gap and do not claim to | **Open, inherited** |
| 3 | The stub cannot be mistaken for production | **Whoever deploys it anyway.** Six independent markers say throwaway (header, `/health`, response header, captures, README, runbook). None of them *prevents* deployment — no technical control stops someone running it behind a real hostname. Marking is the strongest thing an evidence stub can do; it is not an enforcement | **Marked, not enforced** |
| 4 | The POC round is still un-run | **Nobody — deliberately.** No account was created, no OAuth grant made, no provider API contacted, and the Zapier MCP tools now in this session were left unused. Every measure in `data/` remains NOT TESTED | Not disconfirmed |
| 5 | My record matches my code | **Me, twice over this round.** §4: 36/36 green on a contract the code broke, caught only by running real HTTP. §4a row 1 of this table: I asserted a control was sound in a draft of this very record, and an independent attacker refuted it within the hour. **Both failures were in my verification, not my implementation** — the code did what I told it; my tests and my prose agreed with each other and with nothing else. Every count in §5 was produced by a command run after the last edit | **Failed twice here, both caught before shipping** |
| 6 | Nothing outside the allowlist moved | **The diff.** Three workflow JSONs verified byte-identical to the accepted return; changes confined to the four allowlisted paths plus the new `poc/stub/**` | Not disconfirmed |

## 7. Change request to Fable

**Zapier MCP tools are now live in the Builder session.** That was not true when `07_`/`08_` were written, and it changes the shape of the owner session: some of what the runbooks ask the owner to do by hand in the Zapier UI could instead be driven through MCP with the owner's connections. It also raises a governance question worth settling before the session rather than during it — **an MCP-driven action is still a provider action, and `05_` §2's boundary matrix applies to it unchanged.**

I did not use them, did not enumerate the owner's connections, and did not verify what they can do. **If Fable wants the session to use them, that is a scope decision plus probably a runbook revision** — and it belongs in the same round as the R2 re-aim rather than being improvised on the day.

## 8. Open items and deviations

- **R2 re-aim not started** — blocked by `10_`, correctly, and not attempted.
- **Zapier MCP availability** — §7, raised not acted on.
- **R0 falsifier row 2 still open** — node types/parameters NOT TESTED; closes at import time on the owner's host.
- **No scope deviations.** Nothing outside the `08_` allowlist. No POC run, no provider contacted, no `13B_` obligation implemented, no provider ranked.
- **Branch deviation (unchanged, disclosed):** operator-designated branch.
- **Recommended reviewer focus:** §4 — the token-lifecycle defect is the kind that a green self-test hides, and the fix is small enough to check in a minute.

---

*Builder-authored completion claim and evidence index — not independent evidence (APP-06). The stub is claimed complete and self-tested; no POC is claimed run and no provider capability is claimed.*
