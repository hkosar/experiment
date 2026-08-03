# 01 — Fable Disposition and Sequencing Ruling on the Provider Adoption Handoff

**Input:** `00_ChatGPT_Provider_Adoption_Handoff.md` (SHA-256 `b5775f61763bb6bfa3ff169ff0ff49d4722a537ea539b7b071abddb50d66cc55`), authored by the verifier as a proposed change request, dated 2026-07-30, received from the owner 2026-08-02 with the directive: *"let's ensure we are leveraging tools that already exist vs reinventing them, to ensure speeds to completion."* **Disposition: ACCEPTED as a new topic (TOPIC-0003) with the timing corrections below.** The core policy — **adopt before build** — is adopted as a standing rule for all build-phase work.

## 1. Timing reconciliation (the one thing the handoff could not know)

The handoff predates the design-gate outcome: its §15 asks for insertion "before the design gate claims that the execution architecture is complete." Between its authoring and its receipt, the design gate **passed** (`51_`, trail 114) and the owner **accepted the design** (trail 116). Ruling: **nothing in that acceptance is reopened, and nothing in it conflicts with this review.** The gate that passed proved the **provider-neutral core** — authority/policy semantics, trust and data envelopes, evidence independence, event identity, fold/replay invariants, protection floors, kill/revoke — which is precisely the handoff's own §15 "continue and complete as core design" list, now complete. The handoff's §15 "hold as provisional" list (scheduler, connector framework, credential infrastructure, watchdog *implementation*, receipt extraction, observability, cost assumptions) maps almost one-for-one onto `13B_Build_Gate_Obligations_Register.md` — the register of build work the design gate explicitly did **not** perform. The design campaign's outcome is therefore already in the shape the handoff asks for: core proven, implementation deferred. What was missing — and what this topic supplies — is the rule that the deferred implementation gets an **adopt/wrap/build classification before any custom build task is cut**.

## 2. Sequencing ruling (binding on Fable's own task issuance)

1. **TASK-0006 (v1.4 baseline integration) PROCEEDS unchanged.** It integrates accepted provider-neutral design text into the baseline documents — squarely in the handoff's §5 "work that may continue." No provider assumption is hardened by it.
2. **All Track B build allocations (TASK-0007+) are BLOCKED pending this review's owner-approved provider portfolio.** No `13B_` obligation may be issued as a custom-build Task Packet until its capability row carries an Adopt/Wrap/Build/Defer/Reject disposition the owner has approved. The only Builder work this topic itself authorizes, after plan approval, is **bounded POC packets**.
3. **Design contracts govern providers, not the reverse.** An adopted provider implements the accepted design contracts (D-EC_, D-B9, D-KR, D-B6 …); where a candidate cannot honor a contract, that is a finding against the candidate — or, if the owner wants the candidate anyway, a **governed design change** under the standing reopening rule. No silent bending of accepted semantics to fit a vendor (this restates the handoff's own §13 Builder instruction as a Fable-enforced rule).
4. **`13B_` rows acquire a provider-class mapping** as this review's first deliverable — e.g., B-7/B-8 (scheduling/watchdog) → §6.2 durable-execution class; B-3 (attestation) and secrets/step-up → §6.5; B-5/B-6/B-9 (journal persistence) → §6.4 operational state; B-1 (live model runs) → §6.6 model gateway (contract-first). The register itself is unchanged — the mapping is additive.

## 3. Role and integrity notes

- The verifier authored this proposal and will audit the plan derived from it (§13). That is a mild self-review coupling, disclosed here for the record; it is acceptable because the owner holds final approval and the POC evidence is required to be machine-measured, not testimonial.
- The Builder has **no provider implementation authority** until an approved Task Packet issues under the approved plan (handoff §13, adopted verbatim).
- Owner decisions in this topic are limited to genuine tradeoffs (hosted vs self-hosted, cost vs maintenance, exposure vs coverage, portfolio vs single provider) — never technical certification without verifier evidence (§13, adopted; consistent with P2G-14).

## 4. What happens next

`02_Provider_Adoption_Discovery_Plan.md` (issued with this ruling) goes to the verifier for audit. On verifier PASS and owner approval of the plan, discovery executes; POC Task Packets follow under new TASK allocations. TOPIC-0003 tracks it all; trail entry 117 records the opening.
