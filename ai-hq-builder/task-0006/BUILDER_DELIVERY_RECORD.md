# Builder Delivery Record — TASK-0006 (v1.4 Baseline Integration, Track A)

**Task:** TASK-0006 — apply `design/D-AM_v14_Amendment_Package.md` to the accepted baseline.
**Builder:** Claude Code session, model `claude-opus-5` (standing authorized substitution, trail entry 69).
**Branch:** `claude/task-0002-builder-handoff-g97x8j` (operator-designated; see §7).
**Instruction authority:** `53_TASK-0006_Task_Packet_v1.4_Integration.md`; change set `design/D-AM_v14_Amendment_Package.md`.
**Returned to:** **Fable** — this is Fable's integration to verify; the design-gate verifier's role ended with `51_`.
**Status:** **PARTIAL. Three of the four change-set items applied; one is BLOCKED and returned as a change request. v1.4 is NOT complete and must not be presented for owner acceptance until item 2 lands.**

**Snapshot integrity (H-06):** `EXPORT_MANIFEST.json` validated **11/11 entries — every hash and byte-count matched, 0 mismatched, 0 missing, 0 unexpected files** — before anything was read as authority.

---

## 1. The blocked item, first, because it gates the task

**DE-R1..DE-R8 register additions (D-AM §2.1 / packet §1.2) — NOT APPLIED.**

Both instruments require the eight new register rows to carry texts **byte-identical to "plan §5"**, and packet §1.2 states that block is *"included in the snapshot."* It is not:

- `05_Design_Phase_Change_Plan_Proposal.md` has **no §5**. Its sections are the title, "Item 0", "Design scope (complete carried surface)" (a 14-item list), "Out of scope", and "Pipeline".
- A grep for `DE-R[1-8]` across **every file in the snapshot** returns only *references* to those IDs in prose — no requirement row texts anywhere. `design/D-B6_` line 3 cites the same missing source: *"Authority: proposed DE-R4/DE-R8 (verbatim, plan §5)."*

Authoring the eight texts would be normative discretion, which I do not hold, and packet §2 is explicit: *"If applying D-AM's text literally produces a contradiction with the current repository state … stop and report — do not paper over it with a judgment call."* So I stopped on this item and completed the other three.

**What Fable needs to supply:** the verifier-confirmed DE-R1..DE-R8 block, or the document that actually contains it. **One conflict to resolve while you are there:** packet §1.2 specifies row status `Amended v1.4 (CP-P2-A; owner acceptance trail 116)`, D-AM §2.1 specifies `Proposed v1.4 → Accepted on v1.4 acceptance`. These differ; I did not pick one.

## 2. Disposition of the three applied items

| Item | D-AM | What changed | Evidence |
| --- | --- | --- | --- |
| **Item 0 — standing-role refresh** | §1 | GOV-01 replaced with §1.1's verbatim text in register `.md` line 72 and `.csv` line 61; seven current-facing "Opus 4.8" → "Opus 5" substitutions at the exact lines §1.3 names; each of the three locations tagged; ADR-019 amendment note appended with the original row byte-intact | Full diffs in the zip. Every one of the eight Manual anchors D-AM §1.4 declares was found exactly where declared — 189, 190, 192, 1017, 1018, 1020, 1534, 1796 |
| **Decision Engine chapter** | §2.2 | New **Manual §22**, placed after §21.3 and before Appendix A, carrying the committed design set **by reference** — no design text inlined. Records status and authority, states the design documents win where they differ, closes the §19.2 forward reference, and repeats that the gate proved the provider-neutral core without certifying production readiness | §22.2 table |
| **Change log + WF-09** | §2.3, §2.4 | `07c_Change_Log_v1.3_to_v1.4.md` authored to the N-03 pattern located in `07b_` (header successor-identity paragraph, status paragraph, process/authority/scope block, Added/Amended/arithmetic/Preserved/regression-matrix sections). WF-09's PROVISIONAL marker resolved per `D-B6_` §2.4 in both register files | `07c_`; WF-09 row diff |

## 3. Three defects found in the instructions, reported rather than absorbed

**(a) D-AM §1.3's section labels are wrong; its line numbers are right.** It calls the first table "§12.1 mapping table (lines 189, 190, 192)" and the second "§12.1.1 role table (lines 1017, 1018, 1020)". Lines 189/190/192 are under **§3.2 Current AI and development workflow**; lines 1017/1018/1020 are under **§12.1 Role-based lifecycle**. §12.1.1 exists but begins at line 1026, *after* the rows in question. The line numbers and the target string are unambiguous, so the substitutions are safe — but I tagged and cited the **corrected** sections rather than write wrong section numbers into the accepted Manual.

**(b) D-AM §2.2's document list omits D-B12**, while packet §1.3 says "D-B2 through D-B14". D-AM's enumeration runs B2, B3, B4, B5, B6, B7, B8, B9, B10, B11, B13, B14 — twelve documents. Packet §1 says apply D-AM exactly, so §22 follows D-AM's list. **Fable to confirm whether D-B12 exists and belongs.**

**(c) Exact file names and section numbers could not be cited for twelve of the fourteen design documents.** Packet §1.3 asks for "file names and section numbers." Only `D-AM_v14_Amendment_Package.md` and `D-B6_Tier_Policy_Function_and_Autonomy.md` are in the snapshot. §22 therefore cites `D-B6_` by full file name with **real** section numbers (§2.4, §3, §4, all verified against the file) and everything else by document ID with D-AM's own subject phrase. I did not guess a filename or a section number for a document I cannot read.

## 4. The one interpretive call I made, disclosed

**The ADR-019 amendment note is placed after the ADR table, not "immediately after the ADR-019 row."** D-AM §1.2 says to append it immediately after the row at line 1796. That row is *inside* a markdown table; a blockquote there splits the table in two and breaks rendering. I placed the note as a tagged blockquote immediately after the last ADR row and before the "End of Version 1.1" marker — following the repo's own precedent that later-version ADR content (ADR-021/022, both v1.3) sits in the ADR area before that marker.

The ADR-019 row is byte-intact, which is what §1.2 protects. **If Fable prefers a different placement it is a one-line move** — I am flagging it rather than letting it pass as if D-AM's literal instruction had been satisfiable.

## 5. Verification

- **Allowlist: 3 modified + 1 added, 0 outside.** Nothing written outside the four paths packet §4 names.
- **Read-only inputs: 9/9 byte-identical**, including `D-AM_`, `D-B6_`, `05_`, `52_`, `53_`, and the three prior change logs.
- **Excluded-path scan (D-AM §1.4), re-run and counted:** `grep -rn "Opus 4.8"` over the whole work tree returns **9 hits in 4 files**. Register `.md` and `.csv`: **0**. Manual: **2**, both by design — the preserved ADR-019 row (line 1835) and the amendment note's own quotation of the prior value (line 1840). The other 5 are in the read-only instruction inputs (`53_`, `D-AM_`), which quote the substitution itself and were not touched. **Current-facing occurrences within the included set: 0**, which is D-AM §1.4's stated acceptance check.
- **Register integrity:** 125 data rows before and after in both files; MD and CSV ID sets identical; exactly two rows changed (GOV-01, WF-09); the CSV diff is **4 lines — the two changed rows, before and after** — with no requoting or reformatting of the other 123 rows.
- **`checksums.sha256`** generated over all seven files in the touched directory. **Note:** it is in the zip root, not written into `fable/phase1-audit-v1.0/`, because adding a file there would breach the packet §4 allowlist. The repo's existing `checksums.sha256` was not in the snapshot, so this is a fresh computation over the touched directory, not a regeneration of the repo's own file — Fable must regenerate that at integration.
- **`RETURN_MANIFEST.json`** self-verified: every entry re-hashed from the unpacked zip before relay.

## 6. Falsifier element (APP-06 / CPB-14, reflexive)

| # | Claim | Who would have to be wrong, and how | Status |
| --- | --- | --- | --- |
| 1 | The DE-R texts are genuinely absent | **Me, about where to look.** I searched every file in the snapshot for `DE-R[1-8]` and read `05_` end to end. If the block lives in a document Fable holds but did not ship, the finding is a packaging error, not a missing artifact — and the fix is the same: ship it. If it is in the snapshot in a form my grep would miss (an image, a differently-spelled ID), I am wrong and the item is unblocked. | **Blocking; falsifiable by producing the block** |
| 2 | Item 0 is complete | **The excluded-path classification.** I applied exactly the eight anchors D-AM §1.4 declares and no others. If a current-facing "Opus 4.8" exists in a file **outside this snapshot**, Item 0 is incomplete and my scan could not have seen it — my grep covers 12 files; D-AM §1.4 says **26 files** contain the string repo-wide. The other 14 are outside the snapshot and I cannot confirm their classification, only trust it. | **Verified within the snapshot; unverifiable beyond it** |
| 3 | §22 cites the design set correctly | **Me, about twelve documents I cannot read.** Only `D-B6_`'s citations are checked against the file. The other twelve entries are D-AM's own subject phrases attached to D-AM's own document IDs — accurate by construction, but if D-AM's list is itself stale (e.g. D-B12, §3b), §22 inherits that. It cites no section number it did not verify. | **Not disconfirmed; inherits D-AM's list** |
| 4 | The ADR-019 placement is acceptable | **Fable.** It is a deviation from a literal instruction, made for a rendering reason, and it is theirs to accept or move (§4). | **Deviation, disclosed** |
| 5 | My record matches my files | **Me, and I was — once, caught here.** I first wrote "the CSV diff is 2 lines," a figure measured after the GOV-01 edit and before the WF-09 edit. The end-of-run re-check against the files returned 4 and the record was corrected. Every other number in §5 was produced by a command run against the work tree after the last edit. | **Failed before; one stale figure caught and fixed here** |
| 6 | v1.4 is not complete | **Nobody — this is the point.** The change log itself says so in its status paragraph, the return manifest carries `v1_4_complete: false`, and this record's header says it. If any downstream document treats v1.4 as complete, it is contradicting three artifacts in this delivery. | **Asserted, deliberately hard to miss** |

## 7. Open items and deviations

- **Item 2 (DE-R1..R8) blocked** — §1. This is the whole of what stands between this delivery and a complete v1.4.
- **Three instruction defects** to disposition — §3(a) section labels, §3(b) D-B12, §3(c) missing design files.
- **One interpretive call** to ratify or reverse — §4.
- **`checksums.sha256` placement** — §5, allowlist-driven.
- **No scope deviations.** Nothing written outside the four allowlisted paths. Nothing from Track B was touched; no `13B_` obligation was implemented.
- **Branch deviation (unchanged, disclosed):** operator-designated branch.
- **Recommended reviewer focus:** §1 first, then §3(a) — the section-label shift is the kind of thing that silently propagates a wrong citation into an accepted baseline if the next Builder trusts D-AM's labels instead of its line numbers.

---

*Builder-authored completion claim and evidence index — not independent evidence (APP-06). No item is claimed accepted; three items are claimed applied and one is claimed blocked.*
