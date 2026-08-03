# 04 — D1: Capability Inventory, Adopt/Wrap/Build/Defer/Reject Classification, and Ownership Matrix (draft)

**Stage:** D1 of the approved plan (`02_` Rev 2; owner approval trail 119). **Status:** draft for the combined D1–D2 verifier review. Dispositions marked **(pre-POC)** are preliminary — D3 evidence can change them; per the plan, no custom-build Task Packet issues from a row until its disposition is owner-approved at D5.

**Classification key:** ADOPT (provider satisfies the requirement) · WRAP (provider executes; AI OS applies policy/identity/evidence controls around it) · BUILD (custom, justified per row) · DEFER (not needed for first useful release) · REJECT (conflicts with an accepted requirement). **Owner key:** AI OS · Provider · Provider + AI OS wrapper · Custom service. Provider classes per handoff §6.

## 1. The invariant core (BUILD, owner: AI OS — the handoff's §15 "continue" list, all design-accepted)

| Capability | Disposition | Rationale |
| --- | --- | --- |
| Topic graph, hierarchy, checkpoints, fold-back | BUILD | The operating model itself — the thing that is unique to the owner; no product implements it |
| Decision Engine semantics (authority, tier/policy function, attention bands, quiet hours) | BUILD | Design-accepted (trail 116); provider-neutral by construction |
| Evidence contracts (`design/D-EC_`) and evidence-independence rules | BUILD (contract) | The AI OS owns what counts as evidence; providers only supply raw material for it |
| Business/Personal partition enforcement | BUILD, then WRAP provider actions | Partition policy is core; every provider action crosses it through the wrapper |
| Protection floors, kill/revoke (D-KR), owner override | BUILD | Non-negotiable floors cannot be outsourced to a vendor's feature set |
| Owner identity + step-up authorization (IDN-02) | BUILD (policy) | Step-up is AI OS policy rendered at the owner surface; provider auth features are transport at most |
| Purpose taxonomy + governed purpose mapping (B-4, B-13) | BUILD | The P2Y-01 campaign outcome — policy-plane authority is precisely what must not be caller- or vendor-defined |
| ActionContext-to-payload binding (B-12) | BUILD | Lives in the wrapper boundary the AI OS owns by definition |
| Release governance / dual-verification git system | KEEP CUSTOM (current) | Handoff §8 concurs; it built this very review |

## 2. Integration and action fabric (handoff §6.1) — the adopt-heavy zone

| Capability | Disposition (pre-POC) | Owner | Rationale |
| --- | --- | --- | --- |
| SaaS connector coverage (email, calendar, CallRail, Meta, CRM, forms, messaging) | ADOPT | Provider | Thousands of maintained connectors is exactly the commodity not to rebuild |
| OAuth + credential onboarding/refresh for common SaaS | ADOPT | Provider | Mature managed auth (class §6.3); custom only for unsupported/sensitive systems |
| Webhook intake, routine triggers/schedules | ADOPT | Provider | Commodity; POC-3 measures reliability |
| Routine retries, branching, duplicate suppression (transport level) | ADOPT | Provider | Commodity; AI OS keeps *semantic* idempotency (event identity is core, §1) |
| Application action execution | WRAP | Provider + AI OS wrapper | Provider executes; every consequential action enters via provider-neutral ActionRequest and returns a receipt through the wrapper — the accepted architecture diagram (`00_` §4) |
| Human-approval mechanics | WRAP | AI OS (authority) + provider (transport at most) | Approval *authority*, step-up, and the card surface are AI OS/Discord; a provider's human-in-loop feature may carry the pause signal, never the decision |
| Execution receipts / run history | WRAP | Provider + AI OS wrapper | Provider results transform into D-EC_-conformant receipts; provider run history is corroborating, never the authoritative journal |
| Connector-health monitoring | ADOPT + thin WRAP | Provider, surfaced to AI OS | Provider-native health feeds a degradation event into the AI OS (D-B5 ladder stays core) |

## 3. Durable execution and scheduling (handoff §6.2; `13B_` B-7/B-8)

| Capability | Disposition (pre-POC) | Owner | Rationale |
| --- | --- | --- | --- |
| Ordinary scheduled/overnight workflows | ADOPT | Provider | POC-3's subject |
| High-assurance durable workflows (checkpoint/replay/recovery) | ADOPT-or-BUILD, decided by POC-3 | Provider or custom service | If the fabric's durability measures pass POC-3, Temporal-class escalation is unnecessary; if not, escalate the narrow class only |
| Watchdog / missed-run detection (D-KR two-leg, B-8) | WRAP | AI OS logic on independent infrastructure | The design contract requires independence from the thing being watched; the watchdog's *logic* is core, its *host* can be an adopted scheduler distinct from the primary executor |
| Temporal receipt validity (B-7) | WRAP | Provider timestamps + AI OS validation | Providers supply timing; the accepted validity policy judges it |

## 4. Operational state (handoff §6.4; `13B_` B-5/B-6/B-9)

| Capability | Disposition (pre-POC) | Owner | Rationale |
| --- | --- | --- | --- |
| Storage engine for journal/state | ADOPT (Supabase/Postgres, confirmation pending POC-3 interplay) | Provider (infrastructure) | Do not build a database |
| Journal semantics: transaction invariants, recurrence admission, per-entry identity, replay | BUILD (logic layer on the adopted store) | AI OS | The eight invariants and admission rules are the design-gate's proven core; they run *on* Postgres, they are not *provided by* it |
| Tamper-evident action log | WRAP | AI OS hash-chain on adopted store + adopted signing primitives | B-3 pairing |

## 5. Secrets, identity, evidence, observability (handoff §6.5; `13B_` B-3)

| Capability | Disposition (pre-POC) | Owner | Rationale |
| --- | --- | --- | --- |
| Secrets storage/rotation | ADOPT (candidate class at D2; vault-grade product) | Provider | Commodity with dangerous build-it-yourself economics |
| Cryptographic attestation of evidence (B-3) | BUILD-SMALL on adopted primitives (KMS/signing) | AI OS + adopted crypto | The *policy* (what must be signed by whom) is the accepted design; the primitives are adopted, never hand-rolled |
| Error monitoring / operational health | ADOPT | Provider | Commodity observability, feeding D-B5 degradation events |

## 6. Deferred classes (handoff §6.6 — contract-first, no evaluation now)

Semantic memory/knowledge (Gbrain candidacy noted), local-model runtime, model gateway/routing, browser automation, voice/telephony, companion dashboard, search/research, vector storage, document processing — **DEFER**, each behind a provider-neutral contract when first needed. `13B_` B-1 (live two-model run) and B-2 (real-input sample) stay what they are: build-gate *verification obligations*, not infrastructure — BUILD (test harnesses) when their gate arrives.

## 7. Capability Ownership Matrix **v2** (per the verifier's `06_` D1–D2 review recommendation: primary + fallback + lock-in + exit strategy per row; migration-cost entries marked est. until D3 measures)

| Capability | Primary owner | Fallback | Lock-in risk | Exit strategy |
| --- | --- | --- | --- | --- |
| OAuth + SaaS connections | Fabric provider (POC decides) | The other primary (Zapier↔n8n) | Medium — re-consenting accounts is the real cost (est.) | Connections enumerated in the ownership record; re-auth runbook per app |
| Routine schedules + triggers | Fabric provider | The other primary; OS-level cron as floor | Low (est.) | Schedules are versioned specs in the AI OS journal (D-KR P2S-04) — the provider only *hosts* them, so they re-materialize anywhere |
| Durable high-assurance execution | POC-3 decides (fabric vs escalation) | Temporal-class engine or custom service | Medium (est.) | Contract-first scheduler/durability interface; workflow definitions exported per run |
| Watchdog / missed-run detection | AI OS logic | Second independent host (never the primary executor) | None by design | The independence contract *is* the exit strategy |
| Topic graph + checkpoints + fold-back | AI OS | None | None | Core invariant — never delegated |
| Decision Engine + policy + attention | AI OS | None | None | Core invariant |
| Evidence contracts + purpose governance | AI OS | None | None | Core invariant (the P2Y-01 campaign is why) |
| External execution | Fabric provider | Custom executor for the narrow class that needs it | Medium (est.) | Wrapper around the provider-neutral ActionRequest contract — replace the executor, keep the contract |
| Execution receipts | Provider + AI OS wrapper | Direct-API receipts via custom adapter | Low — receipts are transformed into D-EC_ form on arrival | The AI OS ledger is authoritative; provider history is corroboration only |
| Partition + protection floors + kill/revoke | AI OS | None | None | Kill reaches providers as connection-level revocation (POC-tested) |
| Operational state storage | Supabase/Postgres (confirmation pending) | Any Postgres host | Low — standard Postgres | pg_dump-restorable; schema is D-B14's conceptual types |
| Journal semantics on that store | AI OS | None | None | Logic layer, provider-independent by construction |
| Secrets | Adopted vault-class provider (D2 class; product at D3/D5) | Second vault product | Low–Medium (est.) | Standard secret-export ceremony; rotation on migration |
| Attestation policy (B-3) | AI OS on adopted crypto primitives | Alternate KMS/signing provider | Low — primitives are commodity | Trust roots held by AI OS; re-anchor on provider swap |
| Knowledge / memory | Deferred (contract-first; Gbrain a candidate, not a selection) | TBD at its own review | Medium if adopted naively (est.) | Memory contract abstraction precedes any adoption |
| Release governance / dual-verification git | AI OS (current custom system) | None | None | Keep custom — it built this very review |

## 8. The headline (for the verifier and the owner)

Classifying all thirteen `13B_` obligations and the handoff's §3 mechanism list yields: **the custom-build surface shrinks to the AI OS's genuine core** — operating model, policy/authority, evidence governance, partition/floors, journal semantics, wrapper boundary — while connectors, auth, scheduling transport, retries, storage engines, secrets, monitoring, and crypto primitives all adopt. Nothing in the accepted design is contradicted by any adoption above; where a POC shows a provider cannot honor a design contract, the sequencing ruling (`01_` §2.3) governs.
