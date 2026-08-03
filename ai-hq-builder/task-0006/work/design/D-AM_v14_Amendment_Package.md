# D-AM — v1.4-Proposed Amendment Package (for the build gate)

**Status:** Proposed amendments only. **Nothing here modifies the accepted v1.3 files** — the v1.3 Manual and register remain byte-identical until a GOV-03 release the owner later accepts (plan §12 rollback rule). This package is the exact change set TASK-0003+ applies at build time, plus the Item 0 execution record.

## 1. Item 0 — standing-role refresh (plan §3 method, P2A-10-compliant)

### 1.1 GOV-01 replacement text (register row; verifier's form, verbatim from plan §3)

> **GOV-01** — Standing program roles: Fable (architect/designer, project manager, integration owner, stage-gate approver), ChatGPT (independent verifier), Builder role currently assigned to Claude Opus 5 under APP-01 provider portability, Sonnet (reader/context librarian), and owner (final authority), with the boundaries of Manual §20A.1.

Status marker on the row: **`Amended v1.4 (CP-P2-A Item 0; trail entries 69/82)`** — applied to `05_Requirements_Register_v1.1.md` line 72 and the `.csv` line 61 GOV-01 row at build time.

### 1.2 ADR-019 — dated amendment note (appended; original text stays byte-intact)

Append immediately after the ADR-019 row/entry (Manual line 1796):

> *Amendment (v1.4, CP-P2-A Item 0):* the Builder assignment changed from Claude Opus 4.8 to **Claude Opus 5** at trail entry 69 (owner-authorized standing substitution, ratified at trail entry 82); role boundaries unchanged. The 2026-07-25 decision text above is preserved as written.

### 1.3 Current-facing table updates (each tagged *(v1.4 — CP-P2-A Item 0; trail entries 69/82)*)

| Manual location | Change |
| --- | --- |
| §12.1 mapping table (lines 189, 190, 192) | "Claude Code Opus 4.8" → "Claude Code Opus 5" (Execution row: "Opus 5 managing Sonnet agents") — **presented as current**, so in scope per P2A-10 |
| §12.1.1 role table (lines 1017, 1018, 1020) | Same substitution, three rows |
| §20A.1 Builder row (line 1534) | "**Claude Opus 4.8**" → "**Claude Opus 5**" |

### 1.4 Included/excluded-path scan report (executed 2026-07-29; no unqualified zero-count claim)

Scan: `grep -rn "Opus 4.8"` over all `*.md/*.csv/*.json`. **26 files contain the string; classification:**

- **Included paths (current-facing — the complete Item 0 change set):** `04_Proposed_Operating_Manual_v1.1.md` (8 occurrences: 3× §12.1, 3× §12.1.1, 1× §20A.1, 1× ADR-019 — the first seven substituted, ADR-019 handled per §1.2), `05_Requirements_Register_v1.1.md` (1, GOV-01), `05_Requirements_Register_v1.1.csv` (1, GOV-01), `fable/phase1-audit-v1.0/manifest.json` (1 — the `builder` field describes the historical TASK-0001 build; **excluded as historical** on inspection, retained verbatim). Post-application acceptance check: zero current-facing occurrences within the included set.
- **Excluded paths (historical/time-of-event records, retained byte-identical, with reason):** `baseline/**` (2 files — immutable received baseline); byte-preserved verifier records (`01_/09_/18_` v1.2-pass, `VERIFIER_ChatGPT_response.md`, `14_` phase 2 — external documents); frozen authority trail `06_Frozen_Authority_Trail_41-75.md` (frozen snapshot); decision-trail addendum + TASK-0001/0002 release/build records + change plans + peer-review/idea-register/parked-research docs (time-of-event history; P2A-10 requires their preservation); `bootstrap_id_registry.md` (TASK-0001 row is a historical allocation record); this plan and its records (quote the substitution itself).

## 2. Proposed Decision Engine amendments (applied at build, accepted with v1.4)

1. **Register additions:** DE-R1..DE-R8 as new rows, texts **byte-identical to plan §5** (the verifier-confirmed block; machine-comparable copies travel in every packet), status `Proposed v1.4 → Accepted on v1.4 acceptance`.
2. **Manual addition:** a Decision Engine chapter carrying, by reference to the committed design set: the field-authority contract (D-B2), identity/dedup (D-B3), concurrency boundaries (D-B4), degraded-operation matrix (D-B5), tier/policy function + autonomy caps (D-B6), attention/quiet hours (D-B7), policy objects/precedence composite (D-B8, as selected at the gate), event model/replay (D-B9), partitioned queues (D-B10), rituals (D-B11), owner surfaces (D-B13), schema (D-B14).
3. **Change log:** `07c_Change_Log_v1.3_to_v1.4.md` enumerating 1–2 plus Item 0, per the N-03 pattern.
4. **WF-09 note:** the PROVISIONAL marker resolves — the taxonomy is fixed by D-B6 §2.4 (dimension → authority-class assignment); register row annotated accordingly at v1.4.

## 3. Application rule

This package executes only after: verifier design-gate review → Fable dispositions → scoped re-verification → owner design acceptance → build change plan authorization (plan §10). No step is claimed by this document.
