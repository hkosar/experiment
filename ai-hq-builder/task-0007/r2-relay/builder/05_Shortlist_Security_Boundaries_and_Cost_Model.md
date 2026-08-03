# 05 — D2: Candidate Shortlist, Security/Data Boundary Matrix, and Cost & Capacity Model

**Stage:** D2 of the approved plan (`02_` Rev 2). **Status:** draft for the combined D1–D2 verifier review. Per-axis scoring happens at D3 with measured evidence; this document selects who gets measured and fixes the boundaries and the cost frame before anything runs.

## 1. POC shortlist (with reasons; nothing here is a selection)

| Candidate | Role in POC round | Reason |
| --- | --- | --- |
| **Zapier (incl. Zapier MCP)** | POC candidate — the managed/SaaS-first slot (plan requires ≥1) | Broadest connector surface (9,000+ apps claimed), fastest setup, human-in-loop feature to test as approval *transport*, MCP-native — the strongest available test of "how fast can a managed fabric reach a useful system" |
| **n8n** | POC candidate — the self-hosted/developer slot (plan requires ≥1) | Self-host fits the Mac Studio topology; code-level control; execution-based pricing favorable for multi-step workflows; the strongest available test of the ownership/control end |
| **Pipedream** | Named alternate | Enters only if a primary fails a POC gate or if D3 shows embedded/programmatic managed-auth (Connect/MCP) is decisive; strengths overlap the two primaries enough that a three-way first round adds cost, not information |
| **Temporal** | Not a standalone POC | Durability-class complement, not a fabric. POC-3's durability measurements on the primaries decide whether a Temporal-class escalation is needed for a narrow workflow class; evaluating it before that evidence exists would be reputation-driven — the thing §12 forbids |
| **Make** | Documented out (this round) | Same class as Zapier (visual managed automation) with no axis where it plausibly beats Zapier *for this system's needs* (MCP maturity, AI-agent integration); revisitable if Zapier fails |
| **Activepieces** | Documented out (this round) | Same class as n8n (self-hosted) with a smaller ecosystem; open-source licensing noted as a genuine long-term portability argument — revisitable if n8n's fair-code terms or maintenance burden fail a gate |
| **Direct MCP servers / custom controlled services** | Baseline comparator | POC-4 (optional) exercises direct MCP scoping; the custom-service baseline is the cost/control yardstick every adoption must beat |

## 2. Security and data boundary matrix (binding on every POC from day one)

| Data class | May enter a managed provider (Zapier-class)? | May enter self-hosted fabric (n8n on owned hardware)? | Stays only in AI OS control |
| --- | --- | --- | --- |
| SaaS OAuth tokens for connected apps | Yes — that is the adopted service, scoped minimally per connection | Yes — provider-managed credential store, hardened per D2 review | Master secrets, step-up factors |
| Business metadata (senders, timestamps, amounts, statuses, IDs) | Yes — workflow payloads | Yes | — |
| Business content (email bodies, transcripts, documents) | Only the minimum a specific approved workflow requires; external-untrusted envelope applied before any model sees it | Yes, under the same envelope rules | Raw restricted content wherever a metadata/redacted path suffices (the B-2 claim under test) |
| Personal-partition data | No managed-provider transit in the POC round — Personal flows are out of POC scope entirely | POC round: no; post-selection: only under partition rules | Personal raw content |
| Policy artifacts, evidence contracts, journal | Never — providers see ActionRequests and return results; they never hold the rulebook | Never (n8n executes workflows; it does not own state) | Journal, policy plane, receipts ledger (authoritative copies) |
| Owner identity/step-up secrets | Never | Never | AI OS + owner devices |

Standing rules riding on top: every consequential action crosses the wrapper as a provider-neutral ActionRequest with declared authority/limits/evidence requirements (`00_` §4 diagram); provider results are corroborating raw material until transformed into D-EC_-conformant receipts; inbound external content wears the external-untrusted envelope before classification; kill/revoke reaches the provider layer as connection-level revocation (tested in POC-1/POC-4).

## 3. Cost & capacity model (parameterized frame; ACTUALS come from D3 — no number below is a measurement)

**Assumption variables — Release 1 measures (re-based per R1P-03, trail 125; owner can correct any in one line; POCs measure the real values):**

| Variable | Working estimate (labeled, unmeasured) |
| --- | --- |
| V1: artifact returns per day (Builder/verifier zips) | ~3–15 (this program's own relay history is the seed data) |
| V2: average / maximum artifact size | ~0.1–5 MB avg / ~50 MB max |
| V3: manifest/file count per artifact | ~5–60 |
| V4: duplicate-artifact rate | ~5–15% of uploads (observed in this program) |
| V5: owner decision cards per day | ~5–25 |
| V6: relay actions per accepted/rework decision | 1–3 |
| V7: idea captures per day | ~2–10 |
| V8: ideas linked to existing projects vs new topics | ~70/30 split |
| V9: nightly integrity runs / files+checksums inspected | 1 run / ~200–600 files |
| V10: provider tasks/steps/executions per completed workflow | 5–15 (drives the Zapier-per-task vs n8n-per-execution economics directly) |
| V11: owner-attention minutes per workflow | measured at the session (the axis no invoice shows) |

The 1x/3x/10x model recalculates from these as measured. *Parked as Release-2 planning inputs only (not D3 assumptions):* calls/transcripts ~20–60/day; emails triaged ~50–150/day; consequential-action cap growth per DE-R8.

**Billing-unit math to test (from `00_` §17 official-market snapshot, revalidated at POC time):** Zapier bills per task, with an MCP tool call consuming two tasks — cost scales ≈ V×steps (every step meters). n8n bills per execution (one run = one execution regardless of steps) plus self-hosting cost (Mac Studio amortization + electricity + the owner-maintenance hours that are the real price) — cost scales ≈ V, step-insensitive. **Crossover hypothesis to verify at D3:** multi-step volume (V5 high) favors n8n economics; long-tail connector breadth at low per-app volume favors Zapier; the portfolio hypothesis exists because both conditions are true at once in this workload.

**Model deliverable at D3:** measured monthly cost per candidate at 1x (the variables above as measured), 3x, and 10x, including platform fees, model/API costs outside the platform, hosting, and an explicit owner-attention line (hours/month of babysitting) — the axis the verifier's list names as "cost of owner attention," which no vendor invoice shows.

## 4. What D3 will run

*SUPERSEDED at trail 125 (R1P-01):* the one authoritative D3 scenario definition is **`09_` §2** — POC-1 Builder-return pipeline (with the bound idempotency identity and its five required tests), POC-2 idea capture & staging (two trust-envelope cases), POC-3 durable nightly integrity sweep, POC-4 optional. Both primaries, identical inputs, limits, success criteria, and measurement methods; Builder implements only what the packets bound; Business-partition data only, under §2's matrix plus `09_` §3's additive deltas. **No call-review or email-triage scenario is a D3 instruction** — those texts are parked Release-2 planning inputs.
