# D-B7 — Attention Band Function and Quiet-Hour Scheduling (DE-R5; OD-1)

**B-item:** B7 (plan §4). **Status:** Complete. **Authority:** proposed DE-R5 (verbatim, plan §5); ATT-01..03, SCH-01; OD-1 as ratified (owner gate record `12_`, trail 82 — content not modifiable here). **Depends on:** D-B6 (tier/risk/blocking outputs), D-B8 (policy-object schema — OD-1 encodes as instances), D-B5 (system health/degradation state input). **Feeds:** B10 (bands order queue presentation), B12 (re-execution), B13 (band determines card surfacing).

## 1. Objective

Design the deterministic attention-band function over the full DE-R5 dimension set — tier, action-class risk, blocking, aging, **domain partition, current owner mode, system health/degradation state** (the three dimensions P2A-06 added), and the versioned interrupt/quiet-hour policy — with Critical reachable only through owner-ratified policy on verified evidence, and OD-1 encoded as versioned policy objects.

## 2. The band function

### 2.1 Bands and signature

Bands (owner-facing vocabulary unchanged from the accepted walkthrough experience): **Critical** (interrupt now) · **Needs-Owner** (queue admission, next natural session) · **Briefing** (scheduled digest) · **Record-only** (filed, findable). `band(inputs) → (band, reason-trace)` — deterministic over: tier and authority ceiling (D-B6 §2.3) · action-class risk · blocking state (derived links) · aging state (per-partition ladder events, B10) · **domain partition** (Business/Personal — separate policy instances, PER-02) · **current owner mode** (available / quiet-hours / away — a policy-plane state, owner-set or scheduled, never model-inferred) · **system health** (D-B5 F-mode active ⇒ its own notice class; degradation never *suppresses* a qualifying Critical — F-rows keep C8/notice paths open) · the versioned interrupt/quiet-hour policy (§3). Every output carries a reason-trace naming which rule fired — no unexplained bands (INT-01 discipline, feeds B13 cards).

### 2.2 Structural rules (DE-R5 verbatim, made mechanical)

- **Critical is policy-gated:** the band function contains *no* path to Critical except through an owner-ratified interrupt-policy object (§3) mapping **verified evidence** into the accepted ATT-01 boundary (immediate physical, legal, financial, security, or comparably consequential danger). Model output can neither qualify an event as Critical nor suppress a qualifying one — model fields are not inputs to the Critical predicate at all (they are absent from its signature, not merely down-weighted).
- **Recalibration only via PolicyVersionEvents:** band thresholds, quiet-hour windows, and aging escalation points are policy parameters (D-B8 objects); no learning process mutates them directly — LRN observations propose, the governed workflow disposes (hypothesis check 2 applies to attention exactly as to tiers).
- **No recalibration may weaken a non-overridable protection floor** — floor policies (D-B8 §2) bound the reachable policy space itself.

## 3. OD-1 encoded as policy objects (content as ratified — instantiation only)

`interrupt.business.v1` / `interrupt.personal.v1` (per partition), each carrying, per ATT-01 category (physical / legal / financial / security / comparable): **trigger condition** — verified-event triggers only (conservative posture as ratified); **corroboration bar** — the verification/confidence requirement per category.

**Two distinct rules, never conflated (P2G-07 correction — the prior text wrongly narrowed the first rule to physical/security):**

1. **Verified-critical rule:** an event that is *verified* as qualifying ATT-01 danger — immediate physical, legal, financial, security, or comparably consequential — **interrupts through quiet hours in every category.** The quiet-hour window suppresses lower bands only; it can never narrow an already-qualified ATT-01 Critical (the accepted OD-1 statement: *qualifying danger interrupts through quiet hours; everything else holds for the morning brief*).
2. **Ambiguous-urgency fallback:** when qualification is *ambiguous* (corroboration bar not met, category assessment uncertain), the ratified fallback applies — physical-danger and security ambiguity fails **toward interrupting**; legal/financial/comparable ambiguity holds to the next briefing.

**Quiet hours** — 10:00 PM–6:30 AM, tunable by policy version (owner-only change, one-tap proposal path fine, but always a PolicyVersionEvent); **emergency contacts** — a scrutiny signal contributing to category assessment, never identity-proof and never a sufficient condition (the A8-oracle boundary). **Contacts list:** to be named at activation (as recorded in OD-1) — the policy object carries an explicitly empty, explicitly marked contact set until then; an empty set cannot widen any trigger (absence semantics per D-B3's discipline).

**Explicit band mappings (ATT-03, made mechanical):** verified successful background completion → hub update (Record-only with hub-visibility flag); safe automatic retry → Briefing; first overdue reminder → Briefing; subsequent overdue steps follow the per-partition aging ladder (B10).

**Quiet-hour boundary traces (P2G-07 acceptance set — verified + ambiguous per category, at 2 AM inside quiet hours):**

| Category | Verified qualifying event | Expected | Ambiguous signal | Expected |
| --- | --- | --- | --- | --- |
| Physical | Corroborated intrusion/danger alert | **Critical — interrupts** (rule 1) | Uncorroborated third-party claim | **Interrupts** (rule 2 fails toward interrupt) |
| Security | Verified account-takeover event | **Critical — interrupts** (rule 1) | Single anomalous login signal below bar | **Interrupts** (rule 2) |
| Legal | Verified service-of-process with same-night deadline effect | **Critical — interrupts** (rule 1) | Unverified "legal threat" email (external-untrusted) | **Holds to briefing** (rule 2) |
| Financial | Verified unauthorized large outbound transfer in progress | **Critical — interrupts** (rule 1) | Model-flagged "unusual" invoice, unverified | **Holds to briefing** (rule 2) |
| Comparable | Verified event of equivalent immediate consequence per ratified policy mapping | **Critical — interrupts** (rule 1) | Uncertain comparable-severity claim | **Holds to briefing** (rule 2) |

All ten traces: the reason-trace names which rule fired and the evidence IDs; model output alone can neither qualify (rule 1 requires verified evidence per the corroboration bar) nor suppress (no model field feeds the suppression path) — the DE-R5 invariant.

## 4. Quiet-hour scheduler

A SCH-01-governed schedule object per partition: quiet-window boundaries evaluate in the owner's local time zone (stored on the policy object, not inferred per-event); transitions emit schedule events (auditable, replayable); the band function reads the *recorded* owner-mode state — so replay reproduces attention decisions across DST shifts and travel (basis includes the mode state, not wall-clock arithmetic at replay time). Ritual scheduling (B11) reuses this same envelope mechanism — the shared seam is deliberate and noted for B11.

## 5. Required tests — executed (recorded traces)

**Reproduction record (P2A-13):** procedure = deterministic line-cited traces against §2–§4 over the attention-relevant fixtures (`03F_`, SHA-256 `77efff5c051c4c31ddbe8768d4d06027076641b923704d8b28483216d8fcb784`: S1 morning reconnect, S4/S8 attention cases, A8 interrupt oracle) plus the boundary scenarios below; B12 re-executes. Coverage limit: fixture set + named boundary cases, not exhaustive band-space enumeration; the reason-trace requirement makes any live misband diagnosable, which is the operational safety net ATT-03 review then consumes.

| Test | Scenario | Outcome | Verdict |
| --- | --- | --- | --- |
| ATT-01 boundary — qualifying event | Verified security event (account-takeover signal, corroborated per policy bar) at 2 AM | Critical; quiet-hour exception (security fails toward interrupting); reason-trace cites the ratified policy object + evidence IDs | **PASS** |
| ATT-01 boundary — non-qualifying urgency | "Urgent" vendor email (unverified external claim of consequence) | Cannot reach Critical: no verified evidence mapping through the policy object; Needs-Owner or Briefing per tier/risk; the *claim* of urgency is model-visible semantic content with zero band authority | **PASS** |
| Model cannot qualify | Model proposes maximum risk/urgency on a routine item | Critical predicate has no model inputs (§2.2) — band unchanged from control/derived computation; suggestion surfaces as display metadata only | **PASS** |
| Model cannot suppress | Qualifying verified physical-danger event; model summarizer scores it low-importance | Critical fires regardless — suppression path structurally absent | **PASS** |
| A8 oracle — contacts as signal | Message claiming to be an emergency contact, unverified identity | Contact match raises scrutiny (category assessment weight) but is not identity-proof and not sufficient; without verified evidence, holds per ambiguity rule (physical-danger phrasing → fails toward interrupt per ratified fallback — exactly the ratified conservative/interrupt split) | **PASS** |
| Quiet hours — ordinary item | T3 Needs-Owner item arrives 11 PM | Held to morning queue admission; no notification; aging clock still runs (B10) | **PASS** |
| Owner-mode change replay | Same event replayed against recorded mode `available` vs `quiet` | Different bands, each deterministic from its recorded basis — mode is basis, not ambient state | **PASS** |
| Degradation interplay | Qualifying Critical during D-B5 F7 (evidence services down) | If the *triggering evidence is already verified and recorded*, Critical fires; if verification is unattainable due to F7, the item cannot meet the corroboration bar — it holds with an explicit degraded-verification notice to the owner (never a silent drop; the degradation itself is owner-visible per D-B5) | **PASS** |
| Aging escalation | Needs-Owner item ages past the ladder threshold | Band escalates only along the policy-versioned ladder (to stronger *presentation*, never to Critical — aging is not an ATT-01 category) | **PASS** |

## 6. Acceptance criteria — met

Deterministic bands across replays (mode/health in the recorded basis); OD-1 objects reproduce the ratified policy exactly (§3 — instantiation, no content change); no recalibration path outside PolicyVersionEvents (§2.2); Critical unreachable except via owner-ratified policy on verified evidence (traced from both directions — cannot-qualify and cannot-suppress).

## 7. Falsifier / reopen condition

Reopens if any trace shows Critical reachable from unverified evidence (design-gate blocker per plan §4 B7), or a band change without a policy-version event. Not triggered. Post-activation, ATT-03's review trigger (urgent-item burial with business cost) remains the standing operational falsifier, feeding governed recalibration — never silent retune.
