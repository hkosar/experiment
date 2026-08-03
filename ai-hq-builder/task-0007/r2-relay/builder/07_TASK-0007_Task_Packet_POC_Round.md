# 07 — Task Packet: TASK-0007 — Capability Portfolio POC Round (D3)

**Task ID:** TASK-0007 (allocated `bootstrap_id_registry.md`, trail 120 — row committed with this packet). **Builder:** Claude Opus 5. **Authority chain:** plan `02_` Rev 2 (verifier PASS `03_`; owner approval trail 119) → D1–D2 verifier PASS (`06_`) → this packet. **Returned to:** Fable. **Standing constraint:** `01_` sequencing ruling — this is bounded discovery evidence-gathering; it is NOT Track B implementation, selects nothing, and hardens nothing.

## 1. Scope

> **SCENARIO SUPERSESSION (addendum, trail 125 — R1P-01):** the scenario set below is superseded by the owner's Release-1 ruling and the verifier's scoped ack (`09_` §2 is the ONE authoritative D3 scenario definition: POC-1 Builder-return pipeline with the bound idempotency identity and its five required tests; POC-2 idea capture & staging with two trust-envelope cases; POC-3 durable nightly integrity sweep; POC-4 optional). The R1 stub round already in flight is scenario-neutral and continues; the R2 round implements `09_` §2. Everything else in this packet (execution model, constraints, measurements discipline, return requirements) stands.

Implement ~~POC-1 (call review & delegation), POC-2 (read-only email triage), POC-3 (durable overnight workflow)~~ **the `09_` §2 scenario set** — measure lists per `00_` §10 as amended by `09_` §2 — on **both** primaries: **Zapier** (managed slot) and **n8n** (self-hosted slot, Mac Studio or equivalent owned host). Identical success criteria per candidate. **POC-4 (on-demand MCP action) is optional**: run it if, after POC-1..3, tool-scoping/revocation behavior remains undiscriminated between the candidates — state the decision either way.

## 2. Execution model (the part that involves the owner)

The owner performs all account creation, credential grants, and app connections **personally**, following runbooks you author — you never hold or request the owner's passwords; OAuth grants happen on the owner's screen. Your deliverables are: per-candidate setup runbooks (numbered steps, owner-friction expected at each), workflow definitions/exports, measurement harnesses, and the working sessions' recorded results. Where a candidate needs code (n8n nodes, transforms), you write it within this packet's scope.

## 3. Binding constraints (from `05_` §2 — violations are findings, not judgment calls)

- **Business partition only. No Personal-partition data enters any provider in this round.**
- External-untrusted envelope on all inbound content (email bodies, transcripts) before any model classification.
- Providers receive workflow payloads and OAuth-scoped access — **never** policy artifacts, evidence contracts, journal contents, or step-up secrets.
- Raw restricted content is minimized/redacted wherever a metadata path suffices; where content must flow, say so and log it — that observation is itself B-2-relevant evidence.
- Approval *authority* stays with the owner surface (Discord/AI OS card); a provider human-in-loop feature may carry the pause, never decide it.
- Kill/revoke: each POC must demonstrate connection-level revocation actually severing the provider's access, measured (POC-1 minimum; POC-4 if run).
- Secrets never in prompts, code, logs, or the return zip.

## 4. Measurements (the deliverable is numbers plus observations, not impressions)

Per candidate per POC: the `00_` §10 measure list, plus setup wall-clock time, owner-friction log (every step the owner had to perform, with time), failure/retry behavior actually induced (kill a run mid-flight in POC-3 — do not simulate the failure in prose), receipt/evidence quality against the D-EC_ shape (what fields a provider result actually carries vs what the wrapper must synthesize), actual costs incurred + the billing-unit arithmetic verified against the `05_` §3 model (correct V1..V5 with measured values), and per-axis notes for the fourteen `02_` §4 axes where this round produces evidence. Every claim of the form "provider X supports Y" must carry a demonstrated instance or be marked NOT TESTED — the `00_` §13 partial-mechanism rule applies to you too.

## 5. Return requirements

APP-06 Delivery Record with reflexive falsifier element; per-POC per-candidate results; runbooks; workflow exports (Zapier zap definitions / n8n workflow JSON); measurement data as machine-readable files; the corrected cost model; incidents and surprises named. One zip; `RETURN_MANIFEST.json` self-verified; H-06 discipline on this snapshot before starting.

## 6. What this task is NOT

No provider selection or recommendation (that is D5, Fable + verifier + owner). No production wiring: nothing built here becomes load-bearing without a Track B packet after portfolio approval. No AI OS core code. No `13B_` obligation implementation. If a candidate cannot express a required flow at all, stop that flow, record it as a capability finding, and continue the rest — a blocked flow is a result, not a failure of the task.

## 7. Snapshot

`EXPORT_MANIFEST.json` lists every input with hashes (H-06): this packet, plan `02_` Rev 2, `04_` (incl. Ownership Matrix v2), `05_` (boundaries + cost frame), `06_` (the D1–D2 verdict), `00_`/`01_` for authority context. Validate 100% before reading anything as authority.
