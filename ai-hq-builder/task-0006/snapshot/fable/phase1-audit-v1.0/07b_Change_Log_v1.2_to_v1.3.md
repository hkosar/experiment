# Change Log — Version 1.2 (accepted) to Version 1.3 (accepted)

**Successor identity (verifier N-03, adopted):** change-plan ID **CP-v1.2-B** is historical and unchanged; the baseline layer it produces is **v1.3** (proposed until the owner event); the post-release owner event — **acceptance of v1.3** — was recorded at trail entry 73. The accepted v1.1→v1.2 change log (`07a`) is historical and receives no successor content.

**Status:** built by TASK-0002, post-build verified (`18_`), released under the final scoped acknowledgment (`21_`, PASS; content commit `32cb74f0679acb5731baa03d360e553bb7cf4010`, trail entry 72), and **ACCEPTED by the owner 2026-07-28 (trail entry 73, echoing receipt commit `d7d8f376…`). Phase 2 is open.** Body sections below are the time-of-event build record; statuses named in them describe the pre-acceptance state and are superseded by this header.

---

# CP-v1.2-B — Nate Herk idea-register adoption (built by TASK-0002; not released)

**Status:** **Built (TASK-0002); post-build verified — current gate state in the file header above.** This section records the TASK-0002 build only. The CP-v1.2-B layer is **not released**, **not owner-accepted**, and claims no gate beyond this build. Its successor identity is v1.3-proposed per the file header; no Phase 2 transition is asserted or implied here.

**Process:** v1.2 layer (CP-v1.2-A) released by two-step compare-and-swap (trail entry 59) and owner-accepted 2026-07-27 (trail entry 65) → Nate Herk comprehensive review classified external/reference-only → owner dispositions the sixteen items (trail entry 62) → Fable drafts CP-v1.2-B Revision 1 → ChatGPT independent verification **Pass with changes**, findings M-01..M-11, 3 Concur / 13 Concur-with-modification / 0 Dissent (trail entry 63) → Fable concurs with all eleven findings and all thirteen modifications, none contested, and reissues **Revision 2** → owner approves Revision 2, confirms FLAG-1 and ratifies FLAG-2 (trail entry 64) → Fable allocates TASK-0002 as a control-plane act and issues the release packet → Builder instantiates Parts C and C2 into the implementation allowlist (this build).

**Authoritative instructions:** CP-v1.2-B Revision 2 (Parts C and C2) and `17_TASK-0002_Release_Packet.md`. **Reference-only (no instruction authority):** `14_NateHerk_Comprehensive_Review.md` (source register) and `16_Verifier_Response_CP-v1.2-B_Rev1.md` (verifier record), byte-preserved.

**Scope:** documentation-only / no runtime code. No accepted decision is reopened; no ID is renumbered; no lifecycle state is changed; the gate/control set remains Fable-only.

## Added

- **Requirements (register MD + CSV):** MEM-08 memory-contract hardening, MEM-09 checkpointed interviews, BUS-10 connections registry, AUD-03 scored self-audit, LRN-09 improvement ritual, LRN-10 observation-promotion threshold, SEC-02 owner-voice profile, CAP-03 cost telemetry, CAP-04 economic retirement review, ONB-01 grant-once onboarding, DEC-02 decision falsifier, AUT-12 risk-tiered automation-first rollout, ORG-07 structure-addition test, SCH-02 scheduled-run control envelope. (14 new IDs, all status `v1.3-proposed (CP-v1.2-B)`; ONB is a new requirement family.)
- **Manual §11A.8 — Outbound identity and owner voice** (SEC-02; CPB-06): the four separated voice controls — profile use, draft generation, draft approval, external-send authority.
- **Manual Appendix C — DP-027** (Automation-first for eligible execution).
- **Manual Appendix D — ADR-021** (external managed-memory provider direction) and **ADR-022** (grant-once, activate-staged onboarding), both status `Proposed (v1.3, CP-v1.2-B)`.
- **Manual Appendix A.4** — consolidated index of the CP-v1.2-B additions and amendments, marked *(v1.3-proposed — CP-v1.2-B)*.

## Amended

- **APP-06 amended** (register MD + CSV; Manual §12.6, Appendix A.4): Builder Delivery Records must, for each material acceptance or evidence claim, identify plausible disconfirming evidence or record a reasoned `N/A`; the Builder-authored falsifier is review input only and never replaces independent reproduction (CPB-14). Status note `Amended by CP-v1.2-B (CPB-14); v1.3-proposed` appended; the trail-65 acceptance of the base requirement is preserved.
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

104 accepted v1.1 requirements + 7 v1.2 additions (CP-v1.2-A, accepted trail entry 65) = 111; plus 14 CP-v1.2-B additions = **125 current rows**, of which 14 are `v1.3-proposed (CP-v1.2-B)` and 1 (APP-06) carries a proposed amendment over an accepted requirement.

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
