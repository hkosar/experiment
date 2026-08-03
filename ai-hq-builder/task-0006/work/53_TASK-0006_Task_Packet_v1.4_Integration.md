# 53 — Task Packet: TASK-0006 — v1.4 Baseline Integration

**Task ID:** TASK-0006 (allocated `bootstrap_id_registry.md`, trail 116). **Builder:** Claude Opus 5 (standing authorized substitution, trail entry 69). **Task authority:** `52_v1.4_Proposed_Build_Change_Plan.md` Track A; the change set itself is `design/D-AM_v14_Amendment_Package.md`, already verifier-confirmed and included verbatim in the snapshot. **Returned to:** Fable. Not the verifier — this is Fable's integration to verify; the design-gate verifier's role ended with `51_`.

## 1. Scope — apply D-AM_v14 exactly as written, nothing else

`D-AM_v14_Amendment_Package.md` fully specifies the change set. Do not improvise beyond it; where it says "by reference," reference — do not inline design text into the Manual.

1. **Item 0 — standing-role refresh** (§1 of D-AM): apply the GOV-01 replacement text, the ADR-019 amendment note, and the three current-facing table substitutions ("Opus 4.8" → "Opus 5") to `fable/phase1-audit-v1.0/04_Proposed_Operating_Manual_v1.1.md`, `05_Requirements_Register_v1.1.md`, and `05_Requirements_Register_v1.1.csv`, exactly at the included paths D-AM §1.4 names. Excluded paths (historical/time-of-event records) stay byte-untouched — do not touch anything D-AM §1.4 lists as excluded.
2. **DE-R1..R8 register additions** (D-AM §2.1): new rows in `05_Requirements_Register_v1.1.md` and the `.csv`, texts byte-identical to `05_Design_Phase_Change_Plan_Proposal.md` §5's block (included in the snapshot), status `Amended v1.4 (CP-P2-A; owner acceptance trail 116)`.
3. **Decision Engine manual chapter** (D-AM §2.2): a new chapter in `04_Proposed_Operating_Manual_v1.1.md` carrying, **by reference** (not by inlining), the committed design set — D-B2 through D-B14 as D-AM lists them, plus `D-EC_` and `D-ODP_` since those postdate D-AM's original drafting; cite file names and section numbers, do not duplicate their content into the Manual.
4. **Change log** (D-AM §2.3): author `07c_Change_Log_v1.3_to_v1.4.md` enumerating items 1–3 above plus Item 0, following the N-03 pattern used by prior change logs in this repo (locate and match their format; do not invent a new one).
5. **WF-09 note** (D-AM §2.4): annotate the WF-09 register row — the PROVISIONAL marker resolves per D-B6 §2.4's dimension → authority-class assignment.

## 2. What this is not

Not new design work, not build engineering, not a reopening of anything decided in trail 116 — the DE-R8 hard-maximum value (5,000/day) and expansion-armed-at-go-live are already applied to `design/D-B6_`; this task carries that already-updated design text into the baseline by reference, it does not re-derive it. If applying D-AM's text literally produces a contradiction with the current repository state (e.g., a line D-AM expects to find has already moved), stop and report — do not paper over it with a judgment call.

## 3. Return requirements

Standard Delivery Record (APP-06, reflexive falsifier element). Per-item disposition: which D-AM section, what changed, exact before/after for text substitutions. A full diff of every touched baseline file. Confirmation that every D-AM §1.4 excluded path is untouched (grep re-run, count reported). `checksums.sha256` regenerated for touched directories. One zip; `RETURN_MANIFEST.json` self-verified before relay (the standing H-06 discipline — snapshot integrity confirmed before anything is read as authority).

## 4. Allowlist

Writable: `fable/phase1-audit-v1.0/04_Proposed_Operating_Manual_v1.1.md`, `fable/phase1-audit-v1.0/05_Requirements_Register_v1.1.md`, `fable/phase1-audit-v1.0/05_Requirements_Register_v1.1.csv`, a new `fable/phase1-audit-v1.0/07c_Change_Log_v1.3_to_v1.4.md`. Nothing else. `D-AM_v14_Amendment_Package.md` and `design/D-B6_` etc. are read-only inputs, not writable targets.

## 5. Snapshot

`EXPORT_MANIFEST.json` in this zip lists every input file with its hash, per H-06 (packet and snapshot issued together — the trail-92 lesson). Validate 100% before reading anything as authority.
