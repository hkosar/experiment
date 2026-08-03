# D-B6 — Tier/Policy Function, OD-2 Autonomy Objects, and DE-R8 Expansion (DE-R4, DE-R8)

**B-item:** B6 (plan §4). **Status:** Complete. **Authority:** proposed DE-R4/DE-R8 (verbatim, plan §5); AUT-01..12, WF-01..12, TRS-01..03, IDN-02/03, BUS-01..10; owner gate record `12_` (OD-2 + DE-R8 intent, trail 82). **Depends on:** D-B2 (mandatory controls, field classes), D-B3 (identities), D-B8 (policy objects/precedence — the function evaluates D-B8 objects under the recommended composite), D-B5 (health state input). **Feeds:** B7 (attention band consumes this function's outputs), B10 (dispositions feed queues), B12 (checks 2/3 re-execution; DE-R8 set re-execution), B13 (cap receipts render as cards), B14 (schema).

## 1. Objective

Design the versioned deterministic policy function that turns a verified input envelope into a complete disposition, with model influence structurally limited to lower/escalate-only; instantiate the owner's OD-2 starting-autonomy decision as policy objects; and give DE-R8's automatic cap expansion its full bounded, independently evidenced parameter set — then execute hypothesis checks 2–3 and the eleven DE-R8 tests as recorded design-level simulations.

## 2. The policy function

### 2.1 Signature and determinism

`evaluate(basis) → disposition`, where **basis** (the complete recorded decision basis, DE-R6) = { verified mandatory control envelope (D-B2 §3 fields); applicable canonical state + checkpoint versions; active policy set + versions (pinned, D-B4 §2.3); policy-function version; schema version; calibration version; recorded model outputs (proposals only) }. The function is pure over its basis: identical basis ⇒ identical disposition, on any record shape (S1/S2/S3 — a §6 scorecard precondition) and any model provider (check 1's substitution invariance depends on this purity plus D-B2's authority classes).

### 2.2 Evaluation stages (each deterministic, each recorded)

1. **Envelope verification** — D-B2 §3: any missing/stale/disputed/unknown mandatory authority-bearing control → **no-action fail-closed result with explicit reason**: trusted owner-origin input routes to T3 when owner judgment is required; external-untrusted content stays semantically analyzable with zero instruction authority, quarantined only where the governing policy requires it (A3's route). Not a blanket quarantine (P2A-06).
2. **Policy-set assembly** — applicable objects via D-B8 predicates over control/derived fields; window-filtered; composite precedence (D-B8 §5).
3. **Base disposition from controls + derived fields alone** — tier (T0–T4), authority ceiling, attention inputs, computed *before* any model proposal is consulted. This ordering is the structural enforcement of lower/escalate-only: the model-free disposition is the **ceiling**.
4. **Model-proposal integration** — recorded model outputs (placement/relationship candidates, action-class/risk suggestions, summaries) may: raise scrutiny, lower the ceiling, escalate to owner review, or refine *recommendations* (placement/relationship/blocking/disposition suggestions). They may never: raise authority above stage 3's ceiling, relax a trust/data/attention floor, or supply identity/instruction-authority/policy/verification state (DE-R4 verbatim).
5. **Output assembly** — §2.3's full set, all provenance-stamped with the basis versions.

### 2.3 Outputs (DE-R4-complete)

Processing tier (T0 record-only / T1 deterministic rule / T2 act-with-receipt / T3 owner decision / T4 consequential chain) · maximum authority (action-class ceiling) · attention band inputs (handed to B7's band function) · placement / relationship / blocking / disposition **recommendations** (WF-09 dimensions, in their D-B2 §2.4 authority classes) · **required receipt/evidence contract** (expected ExecutionReceipt type and verification requirement — externally owned per OQ-09/P2R-05).

### 2.4 WF-09 dimension coverage (reconciliation from D-B2 §5 adopted)

placement → model-proposed recommendation (stage 4) · relationship → model-proposed recommendation · blocking → deterministic derived (recorded links) · disposition → function output · attention → function output via B7 · authority → function output (never model-writable) · confidence → model-proposed metadata, displayable, **never an authority input** (a confidence number cannot move a ceiling — only verified controls can). All seven accounted for; none floats free of an authority class.

## 3. OD-2 starting-autonomy policy objects (as decided, trail 82)

Two D-B8 schema instances (Business and Personal partitions get separate instances — PER-02): `autonomy.filing-routing.v1` — scope: filing/routing action classes only; tier: T2 (act-with-receipt); authority domain `autonomy`; daily cap 20 actions per partition-day; overflow behavior: batch to the owner's briefing queue (never silent drop, never cap-bypass); every action emits its receipt per §2.3's contract. All other action classes: T3+ (owner decision) at start. These objects are the *instantiation* of what Hunter already decided — no new owner decision inside them except the DE-R8 defaults flagged in §4.

## 4. DE-R8 cap policy — full parameter set (per class and scope)

One cap-policy object per eligible action class per partition. For `filing-routing` (the only eligible class at start), designed defaults — **all policy-versioned, none hard-coded; the two ⚑-flagged values go to D-ODP for owner ratification at activation:**

| Parameter (P2A-09 required) | Default | Rationale |
| --- | --- | --- |
| Initial cap | 20/day per partition | OD-2 as decided |
| Hard owner-approved maximum | **5,000/day** (owner-ratified, OD-5, trail 116; supersedes the ⚑100/day design default) | Expansion never exceeds this without a new owner decision — the ceiling of automation Hunter is pre-authorizing. Growth mechanism (DE-R8 expansion) ARMED at go-live per the same ruling |
| Eligible evidence sources + coverage | Externally owned VerificationRecords + owner correction/reversal events; ≥ 90% of window actions must carry linked outcome evidence | DE-R8: independently owned evidence only |
| Minimum verified sample | **149** mature verified actions (n_min, P2G-09 authoritative section — *SUPERSEDED value 100 removed per P2S-02*) | Sparse evidence cannot move a cap; 149 = smallest perfect-record sample clearing the 2% bound |
| Observation window | **Rolling 28 days of mature actions** (7-day maturity; P2G-09 authoritative — *SUPERSEDED value 14 days removed per P2S-02*) | Long enough that the owner-requested first expansion is mathematically reachable |
| Correction / reversal / failure definitions | Correction: owner re-files/reclassifies the item ≤ 7 days after action · Reversal: owner undoes the action · Failure: receipt error or verification mismatch | Objective, event-derived — no judgment calls |
| Delayed-outcome treatment | Actions < 7 days old excluded from the sample (maturation lag) | A too-fresh success isn't evidence yet |
| Confidence rule | Expand only if the 95%-CI upper bound of (correction+reversal+failure) rate < 2% | Uncertainty blocks expansion, not just the point estimate |
| Maximum step size | +20% of current cap per step (round down, min +1) | No cap doubling overnight |
| Cooldown | ≥ 7 days between expansions | One step at a time |
| Exclusions | Duplicate-flagged items (D-B3 uncertain candidates), owner-accepted-but-unverified, disputed, degraded-telemetry days (any D-B5 F-mode active), externally-untrusted evidence | DE-R8 verbatim exclusion list |
| Automatic contraction | Rate ≥ 5% over any rolling 7 days → step back to the previous cap; ≥ 10% → freeze at initial cap + owner notice | Regression shrinks authority automatically |
| Freeze thresholds | Coverage < 90% · telemetry gap · any kill/revoke event → expansion frozen until cleared | Missing evidence is never treated as good news |
| Never crossed | Action class (filing/routing only) · tier boundary (T2) · authority/data-class ceilings · hard maximum (5,000/day, OD-5) | New classes/tiers stay on the AUT-12 unlock path |

Every cap change (up or down) is a PolicyVersionEvent with an owner-visible receipt and a reversal path; owner override operates within the cap domain, requires the applicable IDN-02 step-up, cannot cross a protection floor, and is subordinate to IDN-03 kill/revoke (DE-R8 verbatim).

## 5. Executed tests — recorded design-level simulations

**Reproduction record (P2A-13):** procedure = each scenario evaluated against §2's stages and §4's parameters as deterministic line-cited traces over synthetic evidence streams (plan §4 analysis form; §8 sandbox contract — synthetic default — applies); inputs = §4 parameter table + scenario definitions below + fixture cross-references (`03F_`, SHA-256 `77efff5c051c4c31ddbe8768d4d06027076641b923704d8b28483216d8fcb784`); B12 re-executes the full set. Coverage limit: simulation on synthetic streams; the live-evidence expansion run is the declared §7 build-gate obligation.

### 5.1 Hypothesis checks 2 and 3

- **Check 2 (policy-version causality):** two identical bases differing only in policy version P1→P2 yield different dispositions **only** via the recorded PolicyVersionEvent; same basis + same versions replayed twice ⇒ identical output (§2.1 purity). Trace over the A9-style fixture: no behavior change without a version event. **PASS.**
- **Check 3 (missing-control fail-closed):** A3's envelope (five unknown controls) through stage 1 ⇒ no-action fail-closed, T0 quarantine + T3 source-classification ask, explicit reason — matches the fixture's expected route and forbidden list (no default-to-trusted, no silent discard). **PASS.**
- **Untrusted-content semantic use (with D-B2):** A2's twins through stages 3–4: identical control fields ⇒ identical stage-3 ceilings; twin B's embedded command arrives only as stage-4 semantic content with `instruction_authority=none` ⇒ zero authority effect; both fully summarized. **PASS.**

### 5.2 The eleven DE-R8 tests (P2A-09 required list)

| # | Test | Synthetic scenario | Parameter(s) engaged | Outcome | Verdict |
| --- | --- | --- | --- | --- | --- |
| 1 | Sparse sample | 40 verified actions in window, 0 corrections | Min sample 149 (P2G-09) | Expansion refused — sample too small despite perfect record (machine witness: even 140 perfect actions HOLD) | **PASS** |
| 2 | Delayed regression | Corrections arrive on day 6 for actions taken day 1; expansion evaluated day 5 | Maturation lag (7-day exclusion) | Day-5 evaluation excludes immature actions ⇒ no expansion on unripe evidence; day-8 evaluation sees the corrections ⇒ contraction check engages | **PASS** |
| 3 | Cross-category contamination | Excellent email-filing outcomes; poor document-filing outcomes, same class scope? — No: distinct action classes | Per-class cap policies (§4 header) | Email-filing evidence cannot expand document-filing's cap — separate objects, separate evidence pools | **PASS** |
| 4 | Missing provider telemetry | Verification service degraded for 6 of 28 window days | Degraded-telemetry exclusion + coverage ≥ 90% + freeze threshold | Those days excluded; coverage drops below 90% ⇒ expansion frozen, not guessed | **PASS** |
| 5 | Manipulated success labels | Engine-authored "success" annotations injected into the evidence stream | Eligible-source rule: only externally owned VerificationRecords + owner events count | Self-attested labels are not an eligible source — structurally ignored, expansion unaffected by them | **PASS** |
| 6 | Cap oscillation | Rate hovers at the boundary: expand day 8, regress day 12, re-qualify day 15 | Cooldown ≥ 7 days + contraction step-back | Day-15 re-expansion blocked by cooldown from the day-12 contraction; no thrash cycle possible faster than 7-day steps | **PASS** |
| 7 | Maximum-bound enforcement | Sustained perfect record for months; cap reaches 100 | Hard maximum ⚑ | Next expansion evaluation refuses: cap = hard max; further growth requires a new owner decision (AUT-12 path) | **PASS** |
| 8 | Owner reduction | Owner cuts cap 40→10 mid-window | Override within cap domain | Immediate PolicyVersionEvent; no step-up needed to *reduce* (suspend-easy direction, D-KR §1.3 — authoritative); receipt issued | **PASS** |
| 9 | Owner increase with step-up | Owner raises cap 20→50 | Override within domain + IDN-02 step-up | Allowed (≤ hard max) only with completed step-up confirmation; PolicyVersionEvent + receipt; without step-up ⇒ refused with reason | **PASS** |
| 10 | Automatic contraction | Correction rate hits 6% over rolling 7 days | Contraction threshold 5% | Cap steps back automatically; owner-visible receipt; at 10% ⇒ freeze at initial + notice | **PASS** |
| 11 | Kill/revoke during expansion | IDN-03 kill fires while an expansion evaluation is mid-flight | Freeze threshold (kill event) + IDN-03 supremacy | Expansion evaluation aborts; cap policy frozen; kill outranks the cap domain entirely (D-B5 C8 column); no cap change lands during or after the kill until recovery + explicit un-freeze | **PASS** |

## 6. Acceptance criteria — met

Identical bases yield identical outputs across record shapes (§2.1 purity + shape-neutral basis); every DE-R8 parameter has a designed default and bound (§4 — none hard-coded, two flagged for owner ratification); all eleven DE-R8 tests pass in design-level simulation (§5.2); checks 2–3 pass (§5.1); WF-09's seven dimensions each land in a named authority class (§2.4).

## 7. Falsifier / reopen condition

Reopens if: any input requires raw-content consultation to compute its tier beyond the recorded separation-falsifier threshold (feeds check 6 at B12 — the design keeps tier computation on envelope + derived fields only, so any breach is measurable); or a DE-R8 safety parameter is found evidencable only by engine self-attestation (then evidence sourcing redesigns before the gate — §4's eligible-source rule currently prevents this by construction). Not triggered.

## P2G-09 correction — DE-R8 expansion mathematics, fully specified and witnessed

**The prior parameters made the owner's first expansion mathematically unreachable** (14-day window ⇒ ≤ ~140 mature actions; a perfect record's one-sided 95% upper bound ≈ 2.12% > the 2% threshold — reproduced as a machine witness below). Corrected, predefined specification:

- **Interval method:** exact **one-sided upper 95% Clopper–Pearson** bound on the pooled bad-outcome rate (x=0 closed form `1 − 0.05^(1/n)`; general case by bisection on the binomial CDF — implemented in `traces/der8_witnesses.py`).
- **Outcome semantics:** an action counts **at most once**, at its **worst severity** among {failure, reversal, correction}. Multiple engine actions for one item each count separately as actions.
- **Denominator:** mature eligible actions in the window; the five exclusion classes (duplicate, owner-accepted-but-unverified, disputed, degraded-telemetry, externally-untrusted evidence) leave **both numerator and denominator**.
- **Maturity arithmetic:** an outcome is mature 7 days after the action with no correction/reversal; the evaluation window is **28 rolling days of mature actions** (at 20/day ⇒ up to 21 × 20 = 420 mature — headroom above `n_min`).
- **Feasibility bound:** `n_min = 149` — the smallest perfect-record sample whose upper bound clears 2%; expansion additionally requires the 14-day cooldown and step size +20% (floor-rounded), never above the ⚑ owner hard max (100/day), never across scope keys.
- **Action-class taxonomy (inconsistency fixed):** one authorized class `filing-routing` with **scope keys** {email-filing, doc-filing, note-routing}; caps and evidence pools are per `(class, scope_key)`; cross-scope pooling is prohibited — the former "cross-category" test is precisely a cross-scope-key contamination test.
- **Delayed corrections:** a matured action corrected within 90 days re-enters the current window as a bad outcome via a re-evaluation event; an expansion granted on since-invalidated evidence contracts automatically.
- **Contraction:** a regression check over a trailing 14-day window — upper bound > 4% **or any Critical-class failure** ⇒ automatic contraction to the prior cap + freeze pending governed review. (Distinct parameter from the superseded 14-day *evidence* window: evidence maturity is 28 days; the contraction trigger is deliberately faster than the expansion evidence bar.)

**Machine-executed witnesses** (`traces/der8_witnesses.py` → `traces/der8_witnesses.json`; deterministic, no clock/randomness):

| Witness | Input | Output |
| --- | --- | --- |
| Positive — first expansion reachable | 420 mature, 0 bad, cooldown ok | UB 0.7107% < 2% ⇒ **EXPAND 20→24** |
| Old-parameter reproduction (= sparse-sample HOLD) | 140 mature, 0 bad | UB 2.1171% ⇒ **HOLD** — reproduces the P2G-09 finding |
| Negative/regression | 300 mature, 9 bad | UB 5.1766% > 4% ⇒ **CONTRACT+FREEZE** |
| Contraction | 200 mature, 12 bad | UB 9.5401% ⇒ **CONTRACT+FREEZE** |
| Critical failure overrides rate | 400 mature, 1 bad, Critical | **CONTRACT+FREEZE** at UB 1.18% |
| Hard-max enforcement | cap 90, 420/0 | step 108 → **capped at 100** (⚑ owner value) |

Evidence classes: the table above is **machine-executed**; the remaining P2A-09 test list maps: sparse-sample ✓ (HOLD witness), maximum-bound ✓, automatic contraction ✓, delayed regression ✓ (rule + contraction), cap oscillation → cooldown + freeze (structural), missing telemetry / manipulated labels → exclusion + independent-evidence sourcing (structural, D-B9 receipts), owner reduction (immediate, structural), owner increase step-up (IDN-02 floor, structural), kill during expansion (D-KR §1.6 simulation), cross-scope contamination (structural prohibition + P2G-02 trace case). Owner-decision boundary unchanged: the hard max and step-up ratification remain the ⚑ items in the rebuilt owner package.

## Small-item closures (exact-requirement mechanisms)

- **AUT-05:** disposition rule — a proposal whose placement scope is entirely within one existing topic's subtree and whose action class is T1/T2-internal auto-creates the child record; any proposal crossing topic subtrees, touching a policy/protection surface, or carrying a consequential action class escalates to T3. Test case: same fixture input with in-subtree vs cross-subtree placement → child-created vs T3-card outcomes (rides in the P2G-02 trace set).
- **AUT-08:** policy scope-key vocabulary (with D-B8 §2 `scope`): `person`, `assignment_type`, `sensitivity_class`, `consequence_class` — delegation/follow-up policies must key on at least one; unkeyed delegation policies are rejected at authoring.
- **AUT-10:** action-class taxonomy entries: `verification-read-only` (default automatic verification class — no mutation authority anywhere) and `employee-facing-followup` (separate class, owner-controlled unless a scoped policy per AUT-08 keys authorize it) — the ceiling machinery enforces the split.
- **AUT-12 stage ladder mapping:** the accepted three-stage schedule maps to policy objects: `stage_1 bounded-low-volume-full-review` (cap per DE-R8 initial), `stage_2 monitored-autonomy` (cap expansion active, sampling review), `stage_3 unsupervised-where-permitted` (per-class, never for step-up/legal/safety classes) — advancement between stages is itself an AUT-12 governed unlock (never automatic tier crossing), driven by the same DE-R8 evidence machinery; stage durations minimize when evidence supports (n_min reachable by design, P2G-09).
