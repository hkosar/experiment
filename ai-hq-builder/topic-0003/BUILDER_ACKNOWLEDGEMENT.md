# Builder Acknowledgement — TOPIC-0003 (Provider & Capability Adoption Review)

**Received:** `Provider_Adoption_Plan_Verifier_Relay.zip` — `00_ChatGPT_Provider_Adoption_Handoff.md`, `01_Fable_Disposition_and_Sequencing_Ruling.md`, `02_Provider_Adoption_Discovery_Plan.md`, `SHA256SUMS.txt`.
**Relay integrity:** `SHA256SUMS.txt` verified **3/3 OK** before anything was read as authority.
**Builder status:** **HOLDING. No work performed and none authorized.**
**Returned to:** **Fable**, not the verifier.

---

## 1. Why this is an acknowledgement and not a delivery

The relay contains **no Task Packet**, and three separate instruments say the Builder does not act yet:

- `00_` §13 (Claude Opus 5): *"No provider implementation authority yet. After an approved Task Packet, build only bounded POCs and integration adapters."*
- `01_` §3: *"The Builder has no provider implementation authority until an approved Task Packet issues under the approved plan (handoff §13, adopted verbatim)."*
- `01_` §2.2: *"The only Builder work this topic itself authorizes, after plan approval, is bounded POC packets."*

`01_` §4 sets the route: `02_` → **verifier audit** → **owner approval** → POC Task Packets under TASK-0007+ allocations → Builder. Three gates ahead of me. `02_` §6 confirms this plan does not authorize Builder work beyond D3's bounded POC packets, and D3 itself requires prior owner approval.

I have therefore filed the relay, verified it, read it, and stopped. Nothing was installed, evaluated, or built. No provider was tried. No document was altered.

## 2. Standing constraints I am now under, recorded so they are not re-derived later

1. **Adopt before build** (`00_` §4) is a standing rule for all build-phase work.
2. **Design contracts govern providers, not the reverse** (`01_` §2.3). Where a candidate cannot honor an accepted contract, that is a finding against the candidate — not a reason to bend the contract. If a POC packet ever reaches me containing an instruction that would relax an accepted design semantic to fit a vendor, that is a change request back to Fable, not work.
3. **No core architecture changes to match a preferred provider** without an accepted change (`00_` §13).
4. **POC ceiling** (`02_` §2): bounded, throwaway-eligible, no production credentials beyond the minimum, Business/Personal separation and external-untrusted rules applied from day one.

## 3. Two observations offered to D1/D4 — reference only, use or discard

These are volunteered because `02_` §3 D4 says the interface contract starts from already-ratified material, and I built the closest thing to it. **They are not work product and they assert no disposition.** Fable owns the matrix.

**(a) The TASK-0005 external-basis contract is already provider-boundary shaped.** What R2–R5 built separates three parties that the provider boundary will also have to separate: the **evidence source** (`ExternalManifest.source_id`), the **attestation authority** (`ReceiptRegistry.authority_id`), and the **governance authority** (`EvidencePolicy.authority_id`), each independently bound, with refusal when any two collide. When an adopted provider executes an action and returns a receipt, the provider is the attestation authority — which means the §4.1 separation rule already answers a question D4 would otherwise have to open: *a provider may not also author the policy that says which of its own receipts authorize an action.* Whether that survives contact with a real provider's receipt format is exactly what a POC would measure.

**(b) The two open items I filed may land squarely in this topic, and both get worse at a provider boundary.**

- **B-12** (`48_` §5, already in `13B_`): `ActionContext` classification keys are trusted as declared, not bound to the canonical payload. At an adopted provider this becomes *the provider's* action-classification fidelity.
- **The R5 record §7 change request**: *which* policy artifact a fold should have been given is not modelled. With one internal policy plane this is theoretical; with a provider portfolio and per-provider policy versions it is operational.

Both map to `01_` §2.4's §6.5 class (secrets/identity/evidence/observability). I raise them here only so the mapping work does not have to rediscover them.

**A possible use for existing evidence, offered as a suggestion Fable may reject:** `02_` §4 requires POC claims to be machine-measured rather than testimonial, and `01_` §2.4 maps B-7/B-8 to the §6.2 durable-execution class. The seventeen schedule-liveness behaviors in `run_p2s04.py` are already machine-runnable statements of what durable scheduling has to do — missed-run detection, version-bound horizons, transaction invariants, occurrence windows, durable retirement. If Fable wants, they could serve as a conformance frame for POC-3 rather than being restated in prose. **This is a suggestion about reusing existing evidence, not a request for work and not a claim that any provider would pass.** Adapting them to a provider would itself need a packet.

## 4. What I need before I can act

A Task Packet issued under the approved plan, carrying: the POC's bounded scope, the governing accepted contracts it must honor, the allowlist, the measurement definitions `02_` §4 requires, and the credential ceiling. Until that arrives I am holding.

---

*Builder acknowledgement — not evidence, not a deliverable, and not a disposition on any capability (APP-06). No provider was evaluated, contacted, installed, or recommended in producing this document.*
