# Owner Session Runbook — TASK-0007 POC round

**Read this one first.** It is the session script. The two candidate runbooks are the detail.

**Who does what.** You create every account, grant every credential, and click every OAuth consent — personally, on your screen. The Builder never holds, requests, or receives a password, token, or API key. If any step in any runbook seems to ask you to send a secret somewhere, **stop** — that is a defect in the runbook, not an instruction to follow.

**What this session is for.** Producing numbers. Packet `07_` §4: *"the deliverable is numbers plus observations, not impressions."* Everything in `data/measurements.template.json` currently reads `NOT TESTED`. The session's job is to replace those with measured values and evidence references. A measure you could not run stays `NOT TESTED` — that is a result, and a truthful one.

---

## 0. Before you start

| Check | Why |
| --- | --- |
| You are using the **Business** mailbox/accounts only | Packet §3: no Personal-partition data enters any provider this round. This is binding, not a preference |
| You have a throwaway-eligible mindset about everything built here | Packet §6: nothing built here becomes load-bearing without a Track B packet |
| A timer you can start and stop per step | Setup wall-clock and owner-friction minutes are themselves measures |
| `data/owner_friction_log.template.csv` open | One row per step **you** had to perform, with its time |

**Cost exposure.** Both candidates have free tiers adequate for this round. If any step asks for a paid plan before a POC can complete, stop and record it — "the free tier cannot express this flow" is a genuine economics finding, not an obstacle to work around by spending.

## 1. Order of work, and why this order

1. **n8n first, POC-2 first.** n8n self-hosted is the slower setup and POC-2 is read-only — so the first thing you do is the lowest-risk flow on the higher-effort candidate. If self-hosting is going to be painful, you learn it early, on a flow that cannot touch anything.
2. **Then Zapier POC-2.** Same flow, other candidate — the first genuine like-for-like comparison.
3. **Then POC-1 on both.** This one sends something. It also carries the revocation test, which is the only place a kill/revoke measure exists (packet §3).
4. **Then POC-3 on both.** This one needs an overnight window and a deliberate mid-flight kill.
5. **POC-4 only if needed.** Packet §1: run it only if tool-scoping/revocation is still undiscriminated after POC-1..3. **State the decision either way** — "we did not run POC-4 because X" is a required output, not an omission.

## 2. The three rules that override convenience

1. **Approval authority never moves to the provider.** Both fabrics have a human-in-the-loop feature. It may carry the *pause*. The decision is made on your AI OS/Discord surface and verified by the wrapper before anything is sent. If you find yourself approving something inside Zapier's or n8n's own UI and that approval directly causes the send, the flow is wired wrong — record it and fix the wiring.
2. **The provider never receives the rulebook.** No policy artifacts, no evidence contracts, no journal contents, no step-up secrets. Workflow payloads and OAuth-scoped access only.
3. **Content minimisation is measured, not assumed.** Where a metadata path suffices, use it. Where raw content must flow to make the flow work at all, **say so and log it** — packet §3 says that observation is itself B-2-relevant evidence. Do not quietly widen the data path to make a step succeed.

## 3. What to capture at every step

- **Time.** Start/stop per step, into the friction log.
- **Every click you had to make.** The measure is owner friction, and it is invisible unless recorded as it happens.
- **The raw provider result JSON**, whenever a step produces one. Save it under `data/captures/<candidate>/<poc>/`. These feed `harness/receipt_conformance.py`, which computes what each provider can and cannot supply against the D-EC_ shape.
- **Actual costs and billing units consumed.** Not the plan price — the metered units the run actually burned. These correct the cost model.
- **Surprises.** Packet §5 requires incidents and surprises named. A surprise you explain away is the one worth recording.

## 4. The induced failure (POC-3) is mandatory

Packet §4: *"kill a run mid-flight in POC-3 — do not simulate the failure in prose."* Start the overnight run, then kill it between the bounded stage and the checkpoint. Record what each fabric actually did: retried, replayed from the top, resumed, or lost the run. Then check whether the AI OS side detected a missed run independently, and how long that took.

**This is the measure most likely to separate the candidates**, and it is the one that cannot be inferred from any documentation.

## 5. The revocation test (POC-1) is mandatory

Packet §3: kill/revoke must demonstrate **connection-level revocation actually severing the provider's access, measured**. Revoke the connection from the app side, then attempt the action again, and record whether it failed and how quickly. A provider that keeps working for some interval after revocation is a finding with direct bearing on `04_` §7's exit-strategy column.

## 6. When you are done

Run `harness/run_all.sh`. It re-validates the workflow definitions, re-checks the boundary constraints, recomputes the cost model against your measured values, and runs the receipt-conformance analysis over your captures. Then hand the whole `poc/` directory back — the Builder writes it up, and nothing gets a disposition here. Packet §6: **no provider selection or recommendation in this round.**
