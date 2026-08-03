# Change Log — Version 1.3 (accepted) to Version 1.4 (proposed)

**Successor identity (verifier N-03, adopted):** change-plan ID **CP-P2-A** is historical and unchanged; the baseline layer it produces is **v1.4** (proposed until the owner event). The accepted v1.2→v1.3 change log (`07b`) is historical and receives no successor content.

**Status:** **PARTIALLY BUILT by TASK-0006 — not complete, not verified, not released, not owner-accepted.** One of the four change-set items could not be applied: the DE-R1..DE-R8 requirement texts named by `D-AM_v14_Amendment_Package.md` §2.1 are not present in the TASK-0006 snapshot (see *Not applied* below). **v1.4 is therefore not ready to present for owner acceptance.** Body sections record the TASK-0006 build only and describe the pre-acceptance state.

---

# CP-P2-A — Decision Engine design integration (built by TASK-0006; incomplete)

**Process:** Decision Engine design executed under CP-P2-A → independent verification across ten packets → Fable dispositions and scoped re-verification each cycle → machine design gate green with zero open findings (trail entry 114) → owner design acceptance with five decisions recorded (trail entry 116) → Fable authorizes build-phase work in `52_v1.4_Proposed_Build_Change_Plan.md` and allocates Track A as TASK-0006 → Builder applies `design/D-AM_v14_Amendment_Package.md` to the accepted baseline (this build).

**Authoritative instructions:** `53_TASK-0006_Task_Packet_v1.4_Integration.md` and `design/D-AM_v14_Amendment_Package.md` (the change set). **Reference-only (no instruction authority):** `52_v1.4_Proposed_Build_Change_Plan.md`, `05_Design_Phase_Change_Plan_Proposal.md`, `design/D-B6_Tier_Policy_Function_and_Autonomy.md`.

**Scope:** documentation-only / no runtime code. No accepted decision is reopened; no ID is renumbered; no lifecycle state is changed; the gate/control set remains Fable-only. Nothing in the accepted v1.3 text is removed — every change is an amendment or an addition.

## Amended — Item 0, standing-role refresh (D-AM §1)

- **GOV-01 (register MD line 72 + CSV line 61):** requirement text replaced with D-AM §1.1's verbatim replacement, naming the Builder role as **currently assigned to Claude Opus 5 under APP-01 provider portability**. Status note `Amended v1.4 (CP-P2-A Item 0; trail entries 69/82)` **appended**; the trail-53 acceptance of the base requirement is preserved.
- **Manual current-facing tables — seven substitutions**, "Claude Code Opus 4.8" → "Claude Code Opus 5" and "**Claude Opus 4.8**" → "**Claude Opus 5**": §3.2 stage-mapping table (3 rows), §12.1 role-based lifecycle table (3 rows), §20A.1 Builder row (1 row). Each of the three locations is tagged *(v1.4 — CP-P2-A Item 0; trail entries 69/82)*.
- **ADR-019 (Manual Appendix D):** the original 2026-07-25 decision row is **byte-intact**; a dated amendment note is appended recording the Opus 4.8 → Opus 5 assignment change at trail entry 69, ratified at trail entry 82, role boundaries unchanged.
- **Historical and time-of-event records are untouched**, per D-AM §1.4's excluded-path classification and P2A-10.

## Amended — WF-09 PROVISIONAL marker resolved (D-AM §2.4)

- **WF-09 (register MD + CSV):** the PROVISIONAL marker resolves. The interjection-routing taxonomy is fixed by `D-B6_` §2.4 — placement and relationship are model-proposed recommendations, blocking is deterministic derived, disposition and attention are function outputs (attention via D-B7's band function), authority is a function output and never model-writable, and confidence is model-proposed metadata that is displayable but never an authority input. All seven dimensions carry an authority class. Status note `Amended v1.4 (CP-P2-A; owner acceptance trail 116)` appended; the v1.1 amendment record is preserved.

## Added — Decision Engine manual chapter (D-AM §2.2)

- **Manual §22 — Decision Engine Design**, carrying the committed design set **by reference**, not by inlining: D-B2 field-authority contract, D-B3 identity/dedup, D-B4 concurrency boundaries, D-B5 degraded-operation matrix, `D-B6_` tier/policy function and autonomy caps, D-B7 attention/quiet hours, D-B8 policy objects and precedence composite, D-B9 event model/replay, D-B10 partitioned queues, D-B11 rituals, D-B13 owner surfaces, D-B14 schema, plus `D-EC_` evidence contracts and `D-ODP_` owner decision package. The chapter records status and authority, states that the design documents are normative where they differ from it, closes the §19.2 forward reference, and confirms that the gate proved the provider-neutral core without certifying production readiness.

## Not applied — DE-R1..DE-R8 register additions (D-AM §2.1)

**This item is NOT built.** `D-AM_v14_Amendment_Package.md` §2.1 and packet `53_` §1.2 both require the eight new register rows to carry texts **byte-identical to "plan §5"**, which packet §1.2 states is included in the snapshot. It is not: `05_Design_Phase_Change_Plan_Proposal.md` has no §5, and no DE-R1..DE-R8 requirement text appears anywhere in the TASK-0006 snapshot. Authoring the texts would be normative discretion, which the Builder does not hold; packet §2 directs stopping and reporting instead. Returned to Fable as a change request.

**Consequence for this log:** the register carries **no DE-R rows**, and the arithmetic below is unchanged from v1.3 for that reason.

## Register arithmetic

| Measure | Before (v1.3) | After (this build) |
| --- | --- | --- |
| Register data rows (MD) | 125 | 125 |
| Register data rows (CSV) | 125 | 125 |
| New IDs added | — | 0 (8 expected; DE-R1..R8 not applied) |
| Existing rows amended | — | 2 (GOV-01, WF-09) |
| Rows renumbered or otherwise changed | — | 0 |
| MD / CSV ID sets identical | yes | yes |

125 accepted rows carried forward unchanged in count. When DE-R1..DE-R8 are supplied and applied, the total becomes 133.

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

1. **DE-R1..DE-R8 texts required** before v1.4 is complete (above).
2. **D-AM §2.2's document list omits D-B12**, while packet `53_` §1.3 says "D-B2 through D-B14". §22 follows D-AM's enumeration. Fable to confirm whether D-B12 exists and belongs.
3. **Exact file names and section numbers** for the twelve design documents other than `D-B6_` could not be cited: those files are not in the TASK-0006 snapshot. §22 cites them by document ID and subject.
4. **D-AM §1.3's section labels** for the two Manual tables are shifted — it calls them §12.1 and §12.1.1; the line numbers it gives (189/190/192 and 1017/1018/1020) are correct and fall under **§3.2** and **§12.1** respectively. This log and §22 cite the corrected sections.
