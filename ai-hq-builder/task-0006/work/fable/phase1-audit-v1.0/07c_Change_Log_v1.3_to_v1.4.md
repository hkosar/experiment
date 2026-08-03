# Change Log — Version 1.3 (accepted) to Version 1.4 (proposed)

**Successor identity (verifier N-03, adopted):** change-plan ID **CP-P2-A** is historical and unchanged; the baseline layer it produces is **v1.4** (proposed until the owner event). The accepted v1.2→v1.3 change log (`07b`) is historical and receives no successor content.

**Status:** **BUILT by TASK-0006 (closure round C1) — complete as a build; not yet verified, released, or owner-accepted.** All four change-set items are applied. The DE-R1..DE-R8 texts, absent from the original TASK-0006 snapshot, were supplied in the C1 relay from `13_CP-P2-A_Design_Phase_Change_Plan.md` §5 and are now in the register. Body sections record the TASK-0006 build and describe the pre-acceptance state.

---

# CP-P2-A — Decision Engine design integration (built by TASK-0006, completed at closure round C1)

**Process:** Decision Engine design executed under CP-P2-A → independent verification across ten packets → Fable dispositions and scoped re-verification each cycle → machine design gate green with zero open findings (trail entry 114) → owner design acceptance with five decisions recorded (trail entry 116) → Fable authorizes build-phase work in `52_v1.4_Proposed_Build_Change_Plan.md` and allocates Track A as TASK-0006 → Builder applies `design/D-AM_v14_Amendment_Package.md` to the accepted baseline → Fable verifies the return, unblocks the missing requirement texts and dispositions three instruction defects in `54_TASK-0006_C1_Closure_Note.md` → Builder completes the change set (this build).

**Authoritative instructions:** `53_TASK-0006_Task_Packet_v1.4_Integration.md`, `design/D-AM_v14_Amendment_Package.md` (the change set), and `54_TASK-0006_C1_Closure_Note.md` (closure round). **Requirement-text source:** `13_CP-P2-A_Design_Phase_Change_Plan.md` §5 Part C. **Reference-only (no instruction authority):** `52_v1.4_Proposed_Build_Change_Plan.md`, `05_Design_Phase_Change_Plan_Proposal.md`, `design/D-B6_Tier_Policy_Function_and_Autonomy.md`.

**Scope:** documentation-only / no runtime code. No accepted decision is reopened; no ID is renumbered; no lifecycle state is changed; the gate/control set remains Fable-only. Nothing in the accepted v1.3 text is removed — every change is an amendment or an addition.

## Amended — Item 0, standing-role refresh (D-AM §1)

- **GOV-01 (register MD line 72 + CSV line 61):** requirement text replaced with D-AM §1.1's verbatim replacement, naming the Builder role as **currently assigned to Claude Opus 5 under APP-01 provider portability**. Status note `Amended v1.4 (CP-P2-A Item 0; trail entries 69/82)` **appended**; the trail-53 acceptance of the base requirement is preserved.
- **Manual current-facing tables — seven substitutions**, "Claude Code Opus 4.8" → "Claude Code Opus 5" and "**Claude Opus 4.8**" → "**Claude Opus 5**": §3.2 stage-mapping table (3 rows), §12.1 role-based lifecycle table (3 rows), §20A.1 Builder row (1 row). Each of the three locations is tagged *(v1.4 — CP-P2-A Item 0; trail entries 69/82)*.
- **ADR-019 (Manual Appendix D):** the original 2026-07-25 decision row is **byte-intact**; a dated amendment note is appended recording the Opus 4.8 → Opus 5 assignment change at trail entry 69, ratified at trail entry 82, role boundaries unchanged.
- **Historical and time-of-event records are untouched**, per D-AM §1.4's excluded-path classification and P2A-10.

## Amended — WF-09 PROVISIONAL marker resolved (D-AM §2.4)

- **WF-09 (register MD + CSV):** the PROVISIONAL marker resolves. The interjection-routing taxonomy is fixed by `D-B6_` §2.4 — placement and relationship are model-proposed recommendations, blocking is deterministic derived, disposition and attention are function outputs (attention via D-B7's band function), authority is a function output and never model-writable, and confidence is model-proposed metadata that is displayable but never an authority input. All seven dimensions carry an authority class. Status note appended in the C1-ruled form `Amended v1.4 (CP-P2-A; design accepted trail 116 — final on v1.4 owner acceptance)`; the v1.1 amendment record is preserved.

## Added — Decision Engine manual chapter (D-AM §2.2)

- **Manual §22 — Decision Engine Design**, carrying the committed design set **by reference**, not by inlining. Fourteen documents cited by full file name as they stand in the `design/` directory (C1 §C-4): `D-B2_Field_Authority_Contract.md`, `D-B3_Identity_and_Deduplication.md`, `D-B4_Concurrency_and_Ordering.md`, `D-B5_Degraded_Operation_Matrix.md`, `D-B6_Tier_Policy_Function_and_Autonomy.md`, `D-B7_Attention_and_Quiet_Hours.md`, `D-B8_Policy_Objects_and_Precedence.md`, `D-B9_Event_Model_and_Replay.md`, `D-B10_Partitioned_Queues.md`, `D-B11_Ritual_Integration.md`, `D-B13_INT01_Card_and_Owner_Templates.md`, `D-B14_Operational_DB_Schema.md`, `D-EC_Evidence_and_Schedule_Contracts.md`, `D-ODP_Owner_Decision_Package.md`. Section numbers are cited only for `D-B6_`, the one design file supplied to the Builder. §22.1 additionally names the design-gate test record and the gate-closure verdict (C1 §C-3). The chapter records status and authority, states that the design documents are normative where they differ from it, closes the §19.2 forward reference, and confirms that the gate proved the provider-neutral core without certifying production readiness.

## Added — DE-R1..DE-R8 requirement rows (D-AM §2.1)

- **Eight new register rows (MD + CSV):** DE-R1 identity and deduplication · DE-R2 concurrency and ordering · DE-R3 degraded operation · DE-R4 tiers and deterministic policy evaluation · DE-R5 attention · DE-R6 policy objects and precedence · DE-R7 events, evidence linkage, and replay · DE-R8 automatic T2 volume expansion. Texts are byte-identical to `13_CP-P2-A_Design_Phase_Change_Plan.md` §5 Part C — the Revision 2 block in which the verifier's replacement texts were adopted verbatim (P2A-03..P2A-09). Inserted in register order immediately after DEC-02.
- **Status form**, per the C1 ruling: `Proposed v1.4 (CP-P2-A; design accepted trail 116) — Accepted on v1.4 owner acceptance`. These are new normative requirements whose acceptance completes at the v1.4 release, not at the trail-116 design acceptance; a receipt-commit restamp finalizes the cells at owner acceptance, following the v1.2/v1.3 pattern.
- **WF-09's status fragment harmonized** to the same distinction: `Amended v1.1; Amended v1.4 (CP-P2-A; design accepted trail 116 — final on v1.4 owner acceptance)`.

## Register arithmetic

| Measure | Before (v1.3) | After (this build) |
| --- | --- | --- |
| Register data rows (MD) | 125 | 133 |
| Register data rows (CSV) | 125 | 133 |
| New IDs added | — | 8 (DE-R1..DE-R8) |
| Existing rows amended | — | 2 (GOV-01, WF-09) |
| Rows renumbered or otherwise changed | — | 0 |
| MD / CSV ID sets identical | yes | yes |

125 accepted rows + 8 DE-R additions = **133 current rows**, of which the 8 DE-R rows are proposed and carry no acceptance until the v1.4 owner event.

## Preserved

- The entire product concept, executive experience, and every non-targeted v1.1, v1.2 and v1.3 mechanism.
- The five universal canonical dimensions; the four-way role separation plus the constrained Release Executor.
- ADR-019's original decision text byte-intact; all historical and time-of-event records byte-intact per D-AM §1.4.
- No ID renumbering; no acceptance marking for CP-P2-A; the accepted v1.3 baseline is amended, never rewritten.

## Regression matrix (semantic)

| Baseline mechanism | Effect of the CP-P2-A layer | Result |
| --- | --- | --- |
| Provider portability (APP-01) | GOV-01 now names the Builder assignment *as an assignment under* APP-01 rather than as a fixed identity | Reinforced ✓ |
| Role separation (§20A.1, APP-03) | Role boundaries unchanged; only the assigned model name changes | Preserved ✓ |
| History preservation (P2A-10) | ADR-019 original preserved; excluded historical paths untouched | Preserved ✓ |
| Independent evidence authority (APP-06, 11.2) | §22 records that the gate proved the provider-neutral core and did not certify production readiness | Not weakened ✓ |
| Phase 2 deferrals (§19.3) | Decision Engine schema and routing logic are designed; §22 closes the forward reference | Advanced ✓ |
| Protection layer and staged activation (§11A, §17) | Untouched by the Decision Engine design and continue to bind it | Preserved ✓ |
| Requirements register authority (§Appendix A) | Register remains authoritative; §22 creates no requirement of its own | Preserved ✓ |

## Open against this log

Nothing blocking. The four items raised at first delivery are closed by `54_TASK-0006_C1_Closure_Note.md`:

1. **DE-R1..DE-R8 texts** — supplied from `13_` §5 and applied (above). The original packet cited "plan §5" while the snapshot shipped the nonbinding draft `05_Design_Phase_Change_Plan_Proposal.md`; recorded as a packaging defect, corrected.
2. **Status-form conflict** — resolved by the C1 ruling in favour of D-AM §2.1's form; packet `53_` §1.2's wording is superseded.
3. **D-B12** — exists (`D-B12_Design_Gate_Test_Report.md`) and is correctly absent from the §22.2 operating-mechanism list; it is gate evidence, and §22.1 now names it alongside the gate-closure verdict.
4. **D-AM §1.3's section labels and the design filenames** — the corrected section citations are ratified; §22.2 now carries full filenames read from the live `design/` directory. `D-AM_v14_Amendment_Package.md` stays byte-intact as a historical instruction document, with its label error recorded as an erratum in `54_`.

The ADR-019 note placement is ratified as applied.

**Remaining before v1.4 is accepted:** Fable verification of this closure round, then the owner v1.4 acceptance event and its receipt-commit restamp of the eight proposed status cells.
