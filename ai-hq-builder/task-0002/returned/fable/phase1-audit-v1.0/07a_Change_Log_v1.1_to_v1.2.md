# Change Log — Version 1.1 (accepted) to Version 1.2 (accepted)

**Process:** v1.1 accepted by owner (trail entry 53) → v1.2 ideas pass opened with the peer's dual-agent workflow documents (trail entry 51) → Fable change plan CP-v1.2-A drafted → ChatGPT independent verification, **Pass with changes**, findings H-01..H-09 (trail entry 52) → Fable dispositions all nine (none contested) and reissues CP-v1.2-A **Revision 2** → owner approves Revision 2 and releases TASK-0001 to the Builder (trail entry 54) → Builder integrates Parts B–D into the proposed document set (this change log). **Status:** v1.2 released (two-step compare-and-swap, trail entry 59) and **accepted by the owner 2026-07-27 (trail entry 65)**. The process narrative below is historical and unchanged.

**Authoritative instructions:** CP-v1.2-A Revision 2 (Parts B and C) and `02_TASK-0001_Release_Packet.md`. **Reference-only (no instruction authority):** the two peer source documents under `fable/v1.2-ideas-pass/sources/`, preserved verbatim (hashes unchanged).

**Scope:** documentation-only / no runtime code. The product concept, executive experience, and every non-targeted v1.1 mechanism are unchanged; per the verifier's Part A amendment, only CP-04 (build-scoped release dimension), CP-07 (source-of-truth mechanics), and CP-09 (release-execution governance) make limited cross-cutting changes, each flagged below.

## Added

- **Requirements (register MD + CSV):** APP-05 Task Packet, APP-06 Builder Delivery Record, APP-07 Rework Packet, APP-08 optional build-scoped `release_state` profile, APP-09 two-lane trust-boundary invariant + pinned combined-tree gate, APP-10 sandboxed review execution, GOV-03 Release Executor. (7 new IDs; register grows 104 → 111; MD and CSV ID sets identical.)
- **Manual §12.5 — Release-state profile** (APP-08): the optional build-specific `release_state` ladder — Developer-complete → Reviewed → Approved → Merged → Deployed → Live-verified — with exact definitions, authority mapping, applicability/publication profile, and deterministic candidate-change invalidation. `Rework-required` is a review disposition and return transition, never a forward state.
- **Manual §12.6 — Task Packet, Builder Delivery Record, and two-lane build safety** (ADR-020; APP-05/06/07/09/10): the dual-agent build mechanisms adopted as concrete Application Development practice.
- **Manual §17.3 — Stage-2 activation controls:** the two-lane invariant and its supporting mechanisms activate at Stage 2 (not Stages 0–1), behind the §11A.7 security gate.
- **Manual §20A.1 / §20A.3 — Release execution** (GOV-03): a constrained Release Executor role and the approval-vs-execution separation that closes verifier finding H-05.
- **Manual Appendix C — DP-026** (Structure over vigilance).
- **Manual Appendix D — ADR-020** (adopt the peer mechanisms; preserve AI OS governance; status Proposed).
- **Manual Appendix A.3** — consolidated index of the v1.2 additions/amendments, with Manual homes.
- **New file `07a_Change_Log_v1.1_to_v1.2.md`** (this document).

## Changed

- **APP-02 amended** (register MD + CSV; Manual Appendix A.3): durable records now explicitly include Task Packets, Builder Delivery Records, independent verification references, and Rework Packets, keyed to operational-database object IDs; repository folders and status labels are non-authoritative projections, never ID allocators or competing state stores (CP-07 source-of-truth mechanics).
- **Manual Document Control:** a v1.2-proposed-layer note added; no existing v1.1 line altered.
- **Decision trail:** entry 55 appended recording the actually-occurred Builder build event only (per the trail-allocation rule; no future entries preallocated).
- **`manifest.json` / `checksums.sha256`** regenerated to cover the changed files and add the new `07a_Change_Log_v1.1_to_v1.2.md`.
- **`fable/v1.2-ideas-pass/bootstrap_id_registry.md`** — TASK-0001 status column advanced to build-delivered (status column only; identity/allocation unchanged).

## Preserved

- The entire product concept and executive experience: Reception, Executive Desk, recursive hubs, topic lifecycle, the five-dimension canonical state model, learning governance, Business/Personal separation, Discord-first strategy, protection layer (§11A), memory architecture, and program governance (§20A).
- The five universal canonical dimensions remain five; `release_state` is an **optional build-scoped profile**, never a replacement (non-adoption N-3).
- The four-way role separation (Builder / Independent Auditor / Verifier / integration owner) — now completed by a distinct Release Executor; no reviewer/integrator fusion (N-1), no two-agent ceiling (N-2).
- Peer source documents verbatim; the performance appendix parked with provenance (CP-10).
- No ID renumbering; no v1.1 / v1.2 acceptance marking; Phase 2 remains closed.

## Verifier findings H-01..H-09 — build-side landing

| Finding | Where it lands in this build |
| --- | --- |
| H-01 task-ID allocation | APP-02 amendment + bootstrap registry: operational identity/state authoritative; folders/labels non-authoritative. |
| H-02 builder-authored evidence | APP-06 Builder Delivery Record as claim/index; independent reproduction required before approval (§12.6). |
| H-03 packet authority envelope | APP-05 Task Packet envelope (§12.6); the Part D authority/source envelope was honored by this build. |
| H-04 candidate identity binding | APP-08 deterministic invalidation + APP-09 pinned combined-tree gate (§12.5 / §12.6). |
| H-05 release execution unassigned | GOV-03 Release Executor (§20A.1 / §20A.3). |
| H-06 snapshot integrity | Input `EXPORT_MANIFEST.json` validated 100% before editing; `manifest.json` / `checksums.sha256` regenerated (see Builder Delivery Record). |
| H-07 worktrees ≠ sandboxes | APP-10 sandboxed execution (§12.6). |
| H-08 v1.1 state cleanup | Precedes this task (erratum already applied to v1.1-final-candidate); zero live legacy-term usage verified before editing. |
| H-09 trail preallocation | Only the actually-occurred build event (entry 55) appended; no future numbers reserved. |

## Regression matrix (semantic — state model, source-of-truth, protection, staged activation, governance)

| v1.1 mechanism | Effect of the v1.2 layer | Result |
| --- | --- | --- |
| Five-dimension canonical state model (4.4) | `release_state` added as an optional build-scoped profile only | Not weakened; five universal dimensions intact ✓ |
| Operational-DB owns identity/state (5.2.1) | APP-02 amendment reinforces DB ownership; folders/labels non-authoritative | Reinforced ✓ |
| Independent / tamper-evident evidence (11.2) | APP-06 keeps the Builder record as claim/index; evidence reproduced independently | Reinforced ✓ |
| Protection layer / trust boundaries (11A) | APP-09/APP-10 add credential separation and sandboxed execution | Reinforced ✓ |
| Staged activation (17) | Two-lane invariant maps to Stage 2; Stages 0/1 preserved | Not weakened ✓ |
| Program governance (20A) | GOV-03 adds a distinct execution actor without fusing roles | Reinforced ✓ |
| Provider portability (PLAT-04) | Repository topology risk-selected; no mandatory two-repository topology | Preserved ✓ |

All targeted Part B / Part C items are implemented in the proposed document set; none required return as a change request.

---

# CP-v1.2-B — Nate Herk idea-register adoption (built by TASK-0002; not released)

**Status:** **Built; post-build verification pending.** This section records the TASK-0002 build only. The CP-v1.2-B layer is **not released**, **not owner-accepted**, and claims no gate beyond this build. No later version layer and no Phase 2 transition is asserted or implied here.

**Process:** v1.2 layer (CP-v1.2-A) released by two-step compare-and-swap (trail entry 59) and owner-accepted 2026-07-27 (trail entry 65) → Nate Herk comprehensive review classified external/reference-only → owner dispositions the sixteen items (trail entry 62) → Fable drafts CP-v1.2-B Revision 1 → ChatGPT independent verification **Pass with changes**, findings M-01..M-11, 3 Concur / 13 Concur-with-modification / 0 Dissent (trail entry 63) → Fable concurs with all eleven findings and all thirteen modifications, none contested, and reissues **Revision 2** → owner approves Revision 2, confirms FLAG-1 and ratifies FLAG-2 (trail entry 64) → Fable allocates TASK-0002 as a control-plane act and issues the release packet → Builder instantiates Parts C and C2 into the implementation allowlist (this build).

**Authoritative instructions:** CP-v1.2-B Revision 2 (Parts C and C2) and `17_TASK-0002_Release_Packet.md`. **Reference-only (no instruction authority):** `14_NateHerk_Comprehensive_Review.md` (source register) and `16_Verifier_Response_CP-v1.2-B_Rev1.md` (verifier record), byte-preserved.

**Scope:** documentation-only / no runtime code. No accepted decision is reopened; no ID is renumbered; no lifecycle state is changed; the gate/control set remains Fable-only.

## Added

- **Requirements (register MD + CSV):** MEM-08 memory-contract hardening, MEM-09 checkpointed interviews, BUS-10 connections registry, AUD-03 scored self-audit, LRN-09 improvement ritual, LRN-10 observation-promotion threshold, SEC-02 owner-voice profile, CAP-03 cost telemetry, CAP-04 economic retirement review, ONB-01 grant-once onboarding, DEC-02 decision falsifier, AUT-12 risk-tiered automation-first rollout, ORG-07 structure-addition test, SCH-02 scheduled-run control envelope. (14 new IDs, all status `v1.2-proposed (CP-v1.2-B)`; ONB is a new requirement family.)
- **Manual §11A.8 — Outbound identity and owner voice** (SEC-02; CPB-06): the four separated voice controls — profile use, draft generation, draft approval, external-send authority.
- **Manual Appendix C — DP-027** (Automation-first for eligible execution).
- **Manual Appendix D — ADR-021** (external managed-memory provider direction) and **ADR-022** (grant-once, activate-staged onboarding), both status `Proposed (v1.2, CP-v1.2-B)`.
- **Manual Appendix A.4** — consolidated index of the CP-v1.2-B additions and amendments, marked *(v1.2-proposed — CP-v1.2-B)*.

## Amended

- **APP-06 amended** (register MD + CSV; Manual §12.6, Appendix A.4): Builder Delivery Records must, for each material acceptance or evidence claim, identify plausible disconfirming evidence or record a reasoned `N/A`; the Builder-authored falsifier is review input only and never replaces independent reproduction (CPB-14). Status note `Amended by CP-v1.2-B (CPB-14); v1.2-proposed` appended; the trail-65 acceptance of the base requirement is preserved.
- **Manual amendments at their stated anchors** (Part C2, verbatim): §15.4 (MEM-08 binding), §13.5 and §13.7 (BUS-10 registry and its wiring cross-reference), §7.5 (AUD-03 housekeeping trigger), §10.5 (LRN-09 ritual cadence), §15.3.1 and §7.3 (MEM-09 interview checkpointing), §18.1 (cost-posture measure), §17.1 with a §17.2 cross-reference (ONB-01/ADR-022 onboarding), §10.1 (LRN-10 threshold), §6.3 and §8.6 (DEC-02 falsifier), §8.2.1 and §11.3 (AUT-12 rollout schedule and action-class autonomy ceilings), §10.4 (CAP-04 retirement-review flags), §8.5 (ORG-07 three-question test), §12.6 (APP-06 falsifier element), §17.0 (SCH-02 control envelope), Appendix B glossary (WAT vocabulary).
- **Register header arithmetic** updated to remain self-truthful, with an explicit note that the CP-v1.2-B rows are proposed and carry no acceptance.

## Register arithmetic

| Measure | Before | After |
| --- | --- | --- |
| Register data rows (MD) | 111 | 125 |
| Register data rows (CSV) | 111 | 125 |
| New IDs added | — | 14 |
| Existing rows amended | — | 1 (APP-06) |
| Rows renumbered or otherwise changed | — | 0 |
| MD / CSV ID sets identical | yes | yes |

104 accepted v1.1 requirements + 7 v1.2 additions (CP-v1.2-A, accepted trail entry 65) = 111; plus 14 CP-v1.2-B additions = **125 current rows**, of which 14 are `v1.2-proposed (CP-v1.2-B)` and 1 (APP-06) carries a proposed amendment over an accepted requirement.

## Preserved

- The entire product concept, executive experience, and every non-targeted v1.1 and v1.2-A mechanism.
- The five universal canonical dimensions; the four-way role separation plus the constrained Release Executor.
- Peer source documents and verifier records byte-preserved; the CP-v1.2-A record set (documents 00–13) untouched.
- No ID renumbering; no acceptance marking for CP-v1.2-B; **Phase 2 remains closed**.

## Verifier findings M-01..M-11 — build-side landing

| Finding | Where it lands in this build |
| --- | --- |
| M-01 protected onboarding/secrets boundary | ONB-01 text and ADR-022 carry the protected-secret-surface boundary verbatim; §17.1 note. |
| M-02 automation-first must be risk-tiered | AUT-12 and DP-027 verbatim; §8.2.1 states that raw model confidence never unlocks authority. |
| M-03 scheduled runs need a control envelope | SCH-02 verbatim; §17.0 note records the hashed, versioned, fail-closed envelope. |
| M-04 voice: four separate controls | SEC-02 verbatim; new §11A.8 separates profile use, drafting, approval, and send authority. |
| M-05 Builder authority package incomplete | Part C2 supplied exact ADR-021/022, DP-027 and all eighteen amendment texts; this build inserted them verbatim with no normative discretion. |
| M-06 self-audit score not reproducible | AUD-03 verbatim (versioned rubric, declared denominators, evidence links, no self-attestation). |
| M-07 cost telemetry coverage/value model | CAP-03 and CAP-04 verbatim; §18.1 cost-posture measure; §10.4 review-not-auto-retire. |
| M-08 observation counting can be gamed | LRN-10 verbatim (distinct verified occurrences; untrusted content cannot count); §10.1. |
| M-09 registry ownership/watchdog semantics | BUS-10 verbatim, homed at §13.5 with the §13.7 cross-reference; RES-02 watchdog untouched. |
| M-10 verifier packet not self-contained | Fable-owned (post-build packet assembly); not a Builder allowlist item — no build-side change. |
| M-11 wording/traceability corrections | Carried inside the verbatim Part C/C2 texts as adopted. |

## Regression matrix (semantic)

| Baseline mechanism | Effect of the CP-v1.2-B layer | Result |
| --- | --- | --- |
| Canonical ownership / source-of-truth (5.2.1, MEM-01) | MEM-08 binds any provider as a derived layer only | Reinforced ✓ |
| Protection layer and staged activation (11A, 17) | §11A.8 adds separated voice controls; ONB-01 keeps §11A.7 gating | Reinforced ✓ |
| Independent evidence authority (11.2, APP-06) | APP-06 falsifier is explicitly review input only, never independent evidence | Reinforced ✓ |
| Approval and action-class controls (11.3, IDN/DAT/ACT/AUT) | AUT-12 advances autonomy only where policy permits; step-up preserved | Not weakened ✓ |
| Observations are weak evidence (LRN-01, 10.1) | LRN-10 threshold explicitly remains weak evidence | Not weakened ✓ |
| Capture is never gated (DP-001) | ORG-07 is advisory coaching and states capture is never gated | Preserved ✓ |
| Independent watchdog (RES-02) | BUS-10 freshness feeds Data HQ/AUD-03, explicitly not the watchdog | Preserved ✓ |
| Phase 2 closure | No Phase 2 material added | Preserved ✓ |

All sixteen CPB items landed in the implementation allowlist as specified; none required return to Fable as a change request. The packet's "three implementation-allowlist files" wording reconciles with the manifest's four WRITABLE files because the register is a matched MD + CSV pair — three work items, four files.
