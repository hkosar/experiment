# Change Log — Phase 1 Baseline v1.0 to Version 1.1 (accepted)

**Process:** 7-role independent audit (six packet-prescribed roles + Claude-capability reality check) → adversarial verification of every Critical/High finding → consensus synthesis (49 entries) → owner realignment (concept framing, LLM-speed timelines, staged activation) → 10-scenario experience walkthrough → ChatGPT peer verification (zero dissents; findings G-01/G-02/G-03) → merge. **Accepted by the owner 2026-07-25 (decision-trail entry 53).**

## Added

- **Canonical state model** (Manual 4.4): five dimensions — stage / work_status / attention / focus / health — with deterministic display-label mapping; "Needs Attention" retired as a term. (C-07)
- **Protection layer** (new section 11A): identity above the channel with step-up confirmation, kill switch, recovery, emergency read-only (C-01); five-field input trust envelope and the external-content-is-data rule (C-02); data classes with per-class Discord render policy and stricter notification previews (C-20); append-only tamper-evident action log (C-21); backups with verified restores, independent watchdog, degraded mode (C-22); idempotent consequential actions with uncertain-outcome halt (G-02); per-stage security gates (C-19).
- **Ownership matrix and global identifier contract** (5.2.1), including `schema_version` on all persistent objects (C-06, G-03).
- **Typed-role arbitrary-depth tree** with task-leaf default and promotion rule (6.1) reconciling hierarchy and recursion (C-09).
- **Derived hub rollups** with intrinsic parent state (9.3 note) (C-10).
- **Correction primitives** and the "Wrong place" gesture (7.6) (C-11); **Rejected (no-build)** terminal state (7.7) (C-47).
- **Staged adaptive routing** honoring decision trail 28, unlocked by measured correction rates (8.2.1) (C-11/D4).
- **Recall-by-description** as a required navigation direction (9.2) (C-13).
- **Harness governance**: risk tiers, mandatory minimums, named owner, tamper-evident evidence store, coverage disclosure (11.2) (C-14); merge action class with interim one-branch rule (11.3) (C-18).
- **Operationalized reviewer independence** and scope-change loop (12.4) (C-15, C-31).
- **Starting role configuration** (Coordinator + Planner/Builder/Independent Auditor + Reader) with role-to-stage map and per-transition artifact contracts (12.1.1) (C-17, C-30/D3).
- **Checkpoint hardening** (15.3.1): cadence triggers, worker-session records, reconciliation-on-resume, protected vs generated fields (C-16, G-01).
- **Staged Activation Plan** replacing Waves 0–5 (17): baseline capture, per-stage gates with stop/continue, capacity model, adopt-before-build, early read-only email brief behind the protection slice (C-03/04/05, D1/D2/D6).
- **Cost-side and load success measures** (18.1) (C-05, C-12).
- **Program governance** (20A): Fable/ChatGPT/Opus/Sonnet/owner roles with boundaries and the eleven-item stage-gate packet (owner-directed; verifier-refined).
- New requirement families in `05_Requirements_Register_v1.1`: IDN, TRS, DAT, LOG, RES, MEM-05/06/07, ACT, SCH, CAP, COR, EX-11, QUE, GOV, SEC. New ADRs 013–019; new design principles DP-021–025; glossary additions.

## Changed

- Fold-back gains a defined actor and trigger (7.4) (C-25). Blocker overrides log consequences and habituation opens a review after repeated same-class overrides (8.3) (C-36).
- WF-09 marked provisional with dimensional routing model (C-08). ORG-01/02, WF-03, ATT-02, HW-01 amended (Appendix A.1).
- Hardware framed as always-on body, purchase owner-timed (20.1, 17.6 note) (C-45/D7); HW-01 register/ADR contradiction resolved as Provisional.
- D9 resolved: one visible coordinator ratified by owner; per-category agent assignment is configuration (16.4).
- Audit-gate section updated to current status; both reviewers recommend Phase 2 stays gated until owner acceptance (19.1).

## Preserved

- The entire operating philosophy and every v1.0 strength named by the auditors: capture without classification, stage-as-state, checkpoints, governed learning, split truth ownership, harness-based approval, Discord-thin-layer, attention model, INT-01 decision-prompt standard, memory-contract-before-provider.
- All deliberately provisional items (HQ taxonomy, Discord channel map, Gbrain selection, mailroom detail, personal HQ structures) remain provisional.
- Deferred to build backlog (not concept defects): full merge policy (C-18), gateway/OpenClaw vendor governance detail (C-27), scope-change mechanics (C-31), delegation wiring (C-32), learning telemetry (C-33), date synchronization (C-43).

## Scenario regression check (verifier merge-order step 9)

| Walkthrough scenario | Mechanism it depends on | Present in v1.1 |
| --- | --- | --- |
| 1 Morning reconnect | Executive Desk + canonical state + watchdog-backed silence | 4.2, 4.4, 11A.5 ✓ |
| 2 Word-vomit capture | Reception + kickoff records + adjust escape hatch | 4.1, 7.3, 7.6 ✓ |
| 3 Interjection routing | Staged adaptive routing + corrections | 8.2.1, 7.6 ✓ |
| 4 Blocker override | Consequence friction + habituation review | 8.3 ✓ |
| 5 Overnight failure | Checkpoint cadence + worker sessions + reconciliation | 15.3.1 ✓ |
| 6 Consequential approval | Harness evidence + coverage disclosure + step-up identity | 11.2, 11A.1 ✓ |
| 7 Email triage | Trust envelope + read-only brief stage + render classes | 11A.2, 17.4, 11A.3 ✓ |
| 8 Bad week return | Unified review queue + aging/consolidation + parked context | QUE-01, C-12 changes, 7.6 ✓ |
| 9 Recall-by-description | EX-11 navigation direction | 9.2 ✓ |
| 10 Fold-back momentum | Fold-back actor/trigger + To-Did + Rejected state | 7.4, 7.7, 9.4 ✓ |

All ten scenarios are supported by the revised baseline text.
