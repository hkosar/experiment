# 02 — Provider & Capability Adoption Review: Bounded Discovery Plan (for verifier audit)

**Topic:** TOPIC-0003. **Status:** proposed plan, awaiting verifier audit then owner approval — nothing here selects a provider or authorizes implementation. **Source scope:** the handoff (`00_`) §§5–12, adopted with the bounds below; Fable's sequencing ruling (`01_`) is a standing constraint on this plan.

## 1. Objective

Classify every provider-dependent capability the AI OS contemplates (Adopt / Wrap / Build / Defer / Reject), test the serious candidates against identical proof-of-capability workflows, and deliver an owner-approvable provider portfolio plus a revised build plan — so Track B builds only what genuinely must be built.

## 2. Scope bounds (what makes this plan bounded)

- **In scope — provider classes §6.1–6.5:** integration/action fabric; durable workflow execution; managed authentication/embedded connections; operational state confirmation (Supabase/Postgres hypothesis); secrets/identity/evidence/observability.
- **Deferred — §6.6 classes** (semantic memory, local-model runtime, model gateway, browser automation, voice, dashboard, search, vector storage, document processing): provider-contract-first only; no evaluation work unless one becomes blocking, and then only by plan amendment.
- **Candidate set for evaluation:** Zapier, n8n, Pipedream, Make, Activepieces, Temporal (durability class), direct MCP servers, custom-controlled-service baseline for comparison. Shortlisting (D2) narrows this to the POC set; the handoff's §14 portfolio hypothesis is a hypothesis under test, not a default.
- **POC set:** POC-1 (call review & delegation), POC-2 (read-only email triage), POC-3 (durable overnight workflow) required; POC-4 (on-demand MCP action) optional if D2 shows it discriminates. **At least two candidates run identical POCs; at least one managed and one self-hosted/developer-controlled.**
- **Implementation ceiling:** POC packets are the only Builder implementation in this topic — bounded, throwaway-eligible, no production credentials beyond what a POC minimally needs, Business/Personal separation and external-untrusted rules applied from day one.

## 3. Stages and deliverables (mapped to handoff §11)

| Stage | Work | Deliverables (§11 #) |
| --- | --- | --- |
| D1 — Inventory & classification | Map every accepted requirement + planned mechanism (incl. all 13 `13B_` rows and the §15 hold-list) to provider classes; draft Adopt/Wrap/Build/Defer/Reject matrix with rationale per row | 1, 2 |
| D2 — Shortlist & boundaries | Candidate shortlist with reasons; security/data boundary matrix (what data may enter each provider, what stays local, what needs the AI OS wrapper); cost & capacity model at 1x/3x/10x from real workload estimates | 3, 5, 6 |
| D3 — Proof of capability | POC Task Packets (TASK-0007+ allocations, Builder under standard discipline) run identical workflows on the shortlist; results measured against §9 criteria and §10 measures — machine-measured where possible, owner-friction observed, costs actual | 4 |
| D4 — Interface contract | Provider-neutral ActionRequest / capability declaration / execution result / receipt / error / retry / revocation contract — **starting from the already-ratified D-EC_ evidence contracts and D-B9 event model**, extended to the provider boundary; this is a head start the handoff predates | 7 |
| D5 — Portfolio & revised plan | Recommended portfolio (default, fallback, custom exceptions); revised Decision Engine design impact (core / wrapper / removed-from-custom-scope per mechanism); revised development & deployment plan incl. Mac Studio topology; owner decision package (P2G-14 form: genuine tradeoffs only) | 8, 9, 10, 11 |

Stage gates: D1–D2 are Fable document work reviewed by the verifier together; D3 requires prior owner approval of this plan (it spends money and Builder time); D4–D5 complete before the owner package presents.

## 4. Evaluation and evidence discipline

The §9 criteria (capability, governance/security, reliability, economics, operations, portability) are adopted as the scoring frame, with this project's standing evidence rules on top: no claim from reputation or documentation alone where a POC can measure it; every "provider satisfies requirement X" claim names the evidence or is marked untested; partial mechanisms are never recorded as full satisfaction (the verifier's own §13 challenge duty); cost figures come from the measured POC runs extrapolated, with the extrapolation method stated.

## 5. Acceptance criteria

The handoff's §12 list is adopted **verbatim** as this topic's completion condition, with one addition: the sequencing ruling's provider-precedence rule (design contracts govern providers) is confirmed honored in the final portfolio recommendation, or every exception is surfaced as a governed design-change proposal.

## 6. What this plan does not do

Select a provider; install anything; alter any accepted design or baseline text; unblock Track B custom builds; authorize Builder work beyond D3's bounded POC packets; ask the owner to certify anything technical.
