# 54 — TASK-0006 Closure Note C1: the blocked item unblocked, three instruction defects dispositioned, one interpretive call ratified

**Context:** Fable verification of the TASK-0006 return (zip SHA-256 `2b5dd7b457f93c7196076073ef77c771c49309672fdf9b0f4cffe1e3bcfe8f4a`) is complete. **The three applied items are verified and integrated** (manifest 7/7 present-and-matching with the six read-only inputs correctly declared unchanged; GOV-01/WF-09 the only register rows changed, 125 data rows before and after in both files; all eight Manual anchors landed; §22 present with D-EC_ and D-ODP_ included per packet §1.3; excluded paths clean — current-facing "Opus 4.8" count 0; hygiene clean 4/4). **The stop on item 2 was CORRECT and the defect is Fable's:** the packet cited "plan §5" but the snapshot shipped `05_Design_Phase_Change_Plan_Proposal.md` — the nonbinding draft — instead of the approved plan. The Builder's falsifier row 1 named the true failure mode exactly: a packaging error, and the fix is to ship it.

**This note is the closure micro-round.** Do the following; nothing else.

## C-1 (the blocked item): DE-R1..R8 register additions

The source is **`13_CP-P2-A_Design_Phase_Change_Plan.md` §5** ("Part C — proposed requirement texts DE-R1..DE-R8 (Revision 2; verifier replacement texts adopted verbatim, P2A-03..P2A-09)") — **included in this snapshot, hash in the manifest.** Add the eight rows to both register files, texts byte-identical to that block.

**Status-form ruling (the conflict you correctly refused to resolve):** D-AM §2.1's form governs — the DE-R rows are NEW normative requirements whose acceptance completes at the v1.4 release, so their status cell reads: `Proposed v1.4 (CP-P2-A; design accepted trail 116) — Accepted on v1.4 owner acceptance`. My packet §1.2's "Amended v1.4 … owner acceptance trail 116" conflated design acceptance with release acceptance — my error, superseded here. D-AM itself distinguishes correctly: Item 0's "Amended v1.4 (… trail entries 69/82)" marker stands as applied, because Item 0's authority (the role substitution) was owner-ratified at trails 69/82 already. **One harmonization edit:** WF-09's new status fragment becomes `Amended v1.1; Amended v1.4 (CP-P2-A; design accepted trail 116 — final on v1.4 owner acceptance)` for the same reason. At v1.4 owner acceptance, a receipt-commit restamp finalizes these cells (the v1.2/v1.3 pattern).

## C-2..C-4 (instruction defects, dispositioned)

- **C-2 (§3a, section labels):** your corrected citations are RATIFIED — the Manual carries the true section identities; D-AM's labels are recorded as an erratum of the instrument here (D-AM itself, a historical instruction document, stays byte-intact). No action.
- **C-3 (§3b, D-B12):** D-B12 exists — `design/D-B12_Design_Gate_Test_Report.md` — and D-AM's omission from the §22.2 list was CORRECT: it is gate *evidence*, not an operating mechanism. Add this single sentence to §22.1 (verbatim, Fable-authored): `The design-gate test record is D-B12_Design_Gate_Test_Report.md; the gate-closure verdict is preserved as 51_ChatGPT_Gate_Closure_Verdict_Packet10.md (decision trail entries 114–116).`
- **C-4 (§3c, filenames):** replace the document-ID-only citations in §22.2 with full filenames from this authoritative list, **read directly from the live `design/` directory by Fable at C1 issuance** (an earlier from-memory draft of this very list got four names wrong — the discipline you applied in §3c is the right one): `D-B2_Field_Authority_Contract.md` · `D-B3_Identity_and_Deduplication.md` · `D-B4_Concurrency_and_Ordering.md` · `D-B5_Degraded_Operation_Matrix.md` · `D-B6_Tier_Policy_Function_and_Autonomy.md` · `D-B7_Attention_and_Quiet_Hours.md` · `D-B8_Policy_Objects_and_Precedence.md` · `D-B9_Event_Model_and_Replay.md` · `D-B10_Partitioned_Queues.md` · `D-B11_Ritual_Integration.md` · `D-B13_INT01_Card_and_Owner_Templates.md` · `D-B14_Operational_DB_Schema.md` · `D-EC_Evidence_and_Schedule_Contracts.md` · `D-ODP_Owner_Decision_Package.md`. No new section numbers: cite sections only where you can read the file (D-B6_ as already done).

## C-5 (interpretive call): RATIFIED

The ADR-019 note placement (after the ADR table, tagged, original row byte-intact) is accepted — table integrity is the substance §1.2 protects, and the repo's own v1.3 precedent seats later-version ADR content exactly there. No move.

## Return requirements

Standard Delivery Record; per-item disposition with before/after for every changed row; the excluded-path scan re-run and counted; register row-count and ID-set integrity re-stated; same allowlist plus nothing; one zip; manifest self-verified. The change log `07c_` gains the DE-R addition entry and drops its incompleteness caveat only if this round completes it — state which.
