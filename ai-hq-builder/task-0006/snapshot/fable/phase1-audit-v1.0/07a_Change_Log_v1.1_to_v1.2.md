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
