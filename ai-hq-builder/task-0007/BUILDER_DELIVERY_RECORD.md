# Builder Delivery Record — TASK-0007 (Capability Portfolio POC Round, D3)

**Task:** TASK-0007 — POC-1/2/3 on Zapier and n8n per packet `07_`.
**Builder:** Claude Code session, model `claude-opus-5` (standing authorized substitution, trail entry 69).
**Branch:** `claude/task-0002-builder-handoff-g97x8j` (operator-designated; see §7).
**Instruction authority:** `07_TASK-0007_Task_Packet_POC_Round.md`; standing constraint `01_` §2; boundaries `05_` §2; measure lists `00_` §10; receipt shape `D-EC_`.
**Returned to:** **Fable.**
**Status:** **THE POC ROUND HAS NOT BEEN RUN. Every measure is NOT TESTED.** The apparatus the round requires is complete, self-tested, and delivered. No provider was contacted, no account exists, no credential was requested or held.

**Snapshot integrity (H-06):** `EXPORT_MANIFEST.json` validated **8/8 entries, 0 mismatched, 0 missing, 0 unexpected** before anything was read as authority.

---

## 1. What I could not do, stated before what I did

Packet §2 defines the execution model: *"The owner performs all account creation, credential grants, and app connections **personally**, following runbooks you author."* Packet §4 defines the deliverable: *"the deliverable is numbers plus observations, not impressions."*

Those numbers require a working session that has not happened. Concretely, in this environment:

- **No Zapier account and no n8n host exist**, and neither can be created without the owner.
- **No OAuth grant is possible** — every grant in this design happens on the owner's screen by construction.
- **`api.zapier.com` is unreachable** — the egress proxy refuses CONNECT (403).
- **`n8n-nodes-base` cannot be installed** — same proxy, 403. This bounds even my offline validation; see §3 F-6.
- Setup wall-clock, owner-friction minutes, induced-failure recovery, revocation time-to-effect, and actual billing units are all **properties of that session**, not of any artifact I can author.

So I built every deliverable packet §2 assigns to me — runbooks, workflow definitions, measurement harnesses — and **left every measurement empty and explicitly marked `NOT TESTED`.** Packet §4 binds me to the same rule it binds the review to: *"Every claim of the form 'provider X supports Y' must carry a demonstrated instance or be marked NOT TESTED."* **This record makes no claim about either candidate's capabilities.**

I am not scaling the task down on my own authority — §6 already establishes that an unrunnable flow is "a result, not a failure of the task," and this is that case at the level of the whole round rather than one flow.

## 2. What is delivered

| Deliverable (packet §2/§5) | State | Evidence |
| --- | --- | --- |
| Per-candidate setup runbooks | **Complete.** `RUNBOOK-owner-session.md` (the session script, ordering and rationale), `RUNBOOK-n8n.md` (23 numbered steps), `RUNBOOK-zapier.md` (13). Owner-action steps flagged; each names the friction expected and the value to record | `runbooks/` |
| Workflow definitions / exports | **n8n: three importable JSON workflows**, 9 / 4 / 7 nodes, structurally validated against the real `n8n-workflow` library. **Zapier: build specs**, because Zapier has no import format — finding F-1 | `workflows/` |
| Measurement harnesses | **Four, each with its own self-test**: structural validation (10 cases), boundary compliance (9), cost model (14), receipt conformance (6). One driver, `run_all.sh` | `harness/`, `harness/out/` |
| Corrected cost model | **Arithmetic complete and self-proved**; every rate slot `NOT MEASURED` and returning `None` rather than a fabricated zero | `harness/cost_model.py`, F-5 |
| Machine-readable measurement data | **Templates only.** Both candidates × three POCs × every `00_` §10 measure, all `NOT TESTED`; plus the owner-friction CSV | `data/` |
| Incidents and surprises | Six findings, each labelled by how it was produced | `FINDINGS.md` |
| POC-4 decision | **Not run, and the reason stated**: §1 conditions it on POC-1..3 leaving tool-scoping undiscriminated. POC-1..3 have not run, so the condition cannot be evaluated. Recorded as pending, not skipped | §5 row 4 |

## 3. Findings produced by building, not by running

Full text in `FINDINGS.md`; the two that change the shape of the decision:

**F-2 — a provider can supply only 4 of the 16 D-EC_ receipt fields.** Derived mechanically from the ratified contract: 4 provider-owned, 9 the wrapper must mint, 3 that must come from a structurally distinct authority. **Whatever fabric is adopted, the wrapper carries three quarters of the receipt.** This bounds the adoption question before any candidate is measured, and it narrows what "provider evidence quality" can even mean as a criterion. The checker also refuses to count a provider-supplied *authority* field as conformance — a provider attesting to its own execution under its own purpose is P2Y-01 in a new location.

**F-1 — Zapier has no public import format.** n8n workflows are files; Zaps are editor state. `04_` §7 lists "workflow definitions exported per run" as an exit strategy and `02_` §4 makes portability an axis — the two candidates are not equally exitable, and that surfaced from trying to produce the deliverable rather than from any measurement.

Also: **F-3** the approval-authority constraint forced a specific POC-1 shape (the provider's pause carries an opaque token; the wrapper verifies it and returns the ActionRequest or refuses) and gives the session a concrete stop-and-record point if either product's HIL cannot be configured that way; **F-4** the `05_` §2 boundary rules are now machine-checked with each rule shown firing; **F-5** the Zapier/n8n crossover reduces to one number, `n8n_price_per_execution / zapier_price_per_task` steps per run, and this workload sits in the region where the rates decide it; **F-6** the environment's proxy blocks the node-type registry, so parameter correctness is settled at import time on the owner's host — which is why that step is a recorded measurement in the runbook.

## 4. Verification

- **Harness PASS**, re-run from a clean copy of the return payload: structural validation 3/3 workflows, boundary check clean 3/3, and **39 self-test cases across four checkers, all passing** (10 + 9 + 14 + 6).
- **Every checker is demonstrated failing.** Each self-test feeds deliberately broken input and requires rejection: duplicate node ids, dangling connections, orphaned nodes, missing triggers, Personal-partition paths, policy artifacts crossing to a provider, secrets in a definition, classification before the envelope, a provider deciding an approval, unpriced inputs returning `None` rather than `0`.
- **Secret scan over the entire return payload: 0 hits** across seven credential-shaped patterns. Packet §3: secrets never in code, logs, or the return zip.
- **Allowlist:** the manifest names "POC workspace of the Builder's choosing — nothing in the ai-hq repo is writable under this task." Nothing outside `ai-hq-builder/task-0007/` was written. **No ai-hq file was touched.**
- **`RETURN_MANIFEST.json`** self-verified by re-hashing every entry from the unpacked zip.

## 5. Falsifier element (APP-06 / CPB-14, reflexive)

| # | Claim | Who would have to be wrong, and how | Status |
| --- | --- | --- | --- |
| 1 | The round genuinely cannot run here | **Me, about the environment.** Falsified by: a provider account already existing that I did not look for, or an owner session I could have driven asynchronously. I verified the two mechanical halves — `api.zapier.com` refuses CONNECT through the proxy, `n8n-nodes-base` returns 403 — but the decisive fact is not technical: **every OAuth grant in this design happens on the owner's screen by construction.** No amount of environment access changes that | **Blocking; falsifiable by producing an account** |
| 2 | The workflow definitions are sound | **The n8n importer, and it has not seen them.** Structural validation is real — they construct as `Workflow` objects and the validator rejects ten classes of defect — but **node types and parameters are NOT TESTED**, because the registry could not be installed. I expect import-time corrections and the runbook treats them as expected findings. If a definition fails to import wholesale, my structural pass will have proved less than it appears to | **Partially verified; the gap is named** |
| 3 | The boundary checker means something | **Me, about scope.** It checks *definitions*, not runtime. A clean definition pointed at a Personal mailbox by whoever attaches the credential violates the same rule the checker just passed. Its nine self-test cases prove the rules fire, not that the round will be compliant | **Verified at definition scope only** |
| 4 | F-2's 4/9/3 split is right | **Me, about the contract.** The field list is my reading of `D-EC_` plus the TASK-0005 encoding it anchors. If `D-EC_` implies a field I omitted, or if a provider legitimately owns something I assigned to the wrapper, the split moves. It is auditable line by line against `D-EC_` §1 and §4, and `--fields` prints the basis for every entry | **Not disconfirmed; transcription auditable** |
| 5 | My record matches my artifacts | **Me.** This has failed in most prior cycles and was caught twice in TASK-0006 — a stale figure and a wrong regex. Here every count in §4 was read from a clean-room re-run of the shipped payload, not from the working copy and not from an earlier draft | **Failed before; re-derived from the shipped copy** |
| 6 | No provider was contacted and no secret exists here | **The scan and the network record.** Zero secret-shaped hits across seven patterns; the only outbound requests this task made were to the npm registry, and one probe each to `api.zapier.com` and `registry.npmjs.org` to establish reachability — no provider account, API, or workspace was accessed | Not disconfirmed |

## 6. What I need to finish the task

An owner working session, run against `runbooks/RUNBOOK-owner-session.md`. It needs: the owner present for account creation and OAuth grants; a host for n8n (Docker); the Business mailbox; an overnight window for POC-3 including a deliberate mid-flight kill; and permission for the revocation test in POC-1. When `data/` comes back populated, `harness/run_all.sh` consumes it and the write-up follows.

**One thing worth deciding before that session:** whether the wrapper endpoints the workflows call (`/poc1/review-case`, `/poc1/verify-decision`, `/poc2/triage`, `/poc3/*`) exist in any runnable form. The flows are written against them because `05_` §2 requires the AI OS to own every decision — but if no wrapper stub exists, the session cannot complete POC-1 or POC-3, only POC-2's provider half. **That is a dependency this packet does not name, and it is the most likely thing to block the session on the day.** A throwaway stub is a small piece of work; I did not build one because it was not in scope and it would sit at the AI OS boundary, not the provider's.

## 7. Open items and deviations

- **The measurement round is un-run** — §1. This is the whole gap between this delivery and the task.
- **Wrapper-stub dependency** — §6. Raised as a change request; I have not assumed it.
- **POC-4 pending, not skipped** — its trigger condition cannot be evaluated until POC-1..3 run.
- **No scope deviations.** Nothing outside the POC workspace; no ai-hq file touched; no `13B_` obligation implemented; no provider selected, recommended, or ranked.
- **Branch deviation (unchanged, disclosed):** operator-designated branch.
- **Recommended reviewer focus:** §6 first — the wrapper dependency is the practical blocker. Then F-2, which is the one result here that would survive unchanged whichever candidate wins.

---

*Builder-authored completion claim and evidence index — not independent evidence (APP-06). The apparatus is claimed complete; no POC is claimed run and no provider capability is claimed at all.*
