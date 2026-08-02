# 47 — Owner Arbitration of the Scope Contest + TASK-0005 Rework Packet R4 (Final Design-Gate Cycle)

## 1. The arbitration (recorded; trail entry 110)

The verifier contested the `45_` scope ruling in its one invited round (`46_`, SHA-256 in trail 110), proposing a split: each P2Y finding has a **design-gate BLOCKING portion** (a normative behavioral/authority contract, testable with deterministic logical records) and a **build-gate DEFERRED portion** (cryptography, database semantics, clocks, credentials — matching Fable's `13B_` register). **The owner arbitrated (2026-07-30, verbatim):** *"Chat seems to insist these changes are needed and I'm ok believing them as long as we are working towards an actual resolution and making progress."*

**Ruling adopted:** the verifier's split stands. The four design-gate portions are accepted as DESIGN work (the verifier is right that "who may authorize an evidence purpose" and "what makes a transaction complete" are authority contracts, not plumbing); the deferred portions are confirmed into `13B_`. **The terminal condition, binding both sides:** the four blocking portions below are the CLOSED list. When they close and everything previously preserved still holds, the design gate is judged against the `28_` §8 conditions + this list — nothing else. Any NEW High-or-below finding beyond this list routes to `13B_` by default; only a Critical defect in the design's own claims may extend it. The verifier concurred with exactly this shape in `46_` §45(d): its scope argument is spent; no further scope debate.

## 2. Fable design rulings (adopting the verifier's contract texts as normative design content)

The contract requirements stated per-finding in `46_` §3 are ADOPTED VERBATIM as design rulings — the verifier has, in effect, drafted the missing contracts and Fable ratifies them: (1) an independently governed purpose-validity mapping (action class × scope × policy version × risk/data class → valid evidence purposes; no self-authorization); (2) the eight logical transaction invariants for schedule changes; (3) legal-recurrence admission rules; (4) receipt-occurrence temporal validity. At integration, Fable reflects these into the design corpus (D-B2/D-B9/D-KR anchored additions + D-SM rows as needed) — Fable text work, not Builder.

## 3. TASK-0005 Rework Packet R4 (APP-07) — the final design-gate cycle

**Instruction authority:** `34_` + prior rework packets + this packet; governing texts: **`46_` §3's design-gate-portion specifications, INCLUDED IN THIS ZIP, quoted contracts governing verbatim.** All standing rules carry forward; allowlist unchanged (`design/traces/behavioral/**` + `13V_validate_design_matrix.py`); return to Fable; one zip.

- **RW-42 (P2Y-01 design portion):** encode the governed purpose-validity mapping as policy-plane data (not consumer self-declaration); the verifier's exact negative test ships failing (`delete-production-data` with self-declared `display-monthly-digest` ⇒ refused); a positive case shows a policy-granted purpose resolving.
- **RW-43 (P2Y-02 design portion):** enforce all eight transaction invariants quoted in `46_` §3; each has a failing probe and the well-formed positive control.
- **RW-44 (P2Y-03 design portion):** legal-recurrence admission validation per `46_`'s specification; malformed definitions refuse at admission with named reasons.
- **RW-45 (P2Y-04 design portion):** receipt-occurrence temporal validity per `46_`'s specification — a receipt may satisfy only its own occurrence window; the pre-satisfaction probe ships failing.

**Return requirements:** per-item disposition with shipped-evidence proof; every `44A_` probe relevant to the design portions defeated in exact form; all standing criteria re-proven; APP-06 record with reflexive falsifiers; one zip to Fable. On Fable acceptance: integration, Fable design-text reflection, and the final verdict packet to the verifier under the §1 terminal condition.
