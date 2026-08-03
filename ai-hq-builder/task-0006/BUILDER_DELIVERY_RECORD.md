# Builder Delivery Record — TASK-0006 closure round C1

**Task:** TASK-0006 — closure micro-round per `54_TASK-0006_C1_Closure_Note.md`.
**Builder:** Claude Code session, model `claude-opus-5` (standing authorized substitution, trail entry 69).
**Branch:** `claude/task-0002-builder-handoff-g97x8j` (operator-designated; see §6).
**Instruction authority:** `53_` + `design/D-AM_v14_Amendment_Package.md` + **`54_` (this round)**. Requirement-text source: `13_CP-P2-A_Design_Phase_Change_Plan.md` §5 Part C.
**Returned to:** **Fable.**
**Status:** **The change set is complete as a build.** All four D-AM items are applied. Not verified, not released, not owner-accepted — `54_` reserves those.

**Relay integrity (H-06):** `EXPORT_MANIFEST.json` validated **8/8 entries, 0 mismatched, 0 missing, 0 unexpected** before anything was read as authority. The relay's four baseline files are byte-identical to my TASK-0006 return, so the work tree needed no rebase.

---

## 1. C-1 — the blocked item, now applied

**Eight new register rows, in both files, texts byte-identical to `13_` §5 Part C.**

I extracted the block programmatically and then compared, per row, the shipped cell against the source line — **8/8 byte-identical in the `.md`, 8/8 in the `.csv`, and the two files agree with each other**. No text was retyped.

| Row | Title as the source gives it | Text length |
| --- | --- | --- |
| DE-R1 | identity and deduplication | 1031 |
| DE-R2 | concurrency and ordering | 948 |
| DE-R3 | degraded operation | 979 |
| DE-R4 | tiers and deterministic policy evaluation | 1078 |
| DE-R5 | attention | 580 |
| DE-R6 | policy objects and precedence | 1024 |
| DE-R7 | events, evidence linkage, and replay | 920 |
| DE-R8 | automatic T2 volume expansion | 1242 |

**Status cell, all eight, per the C1 ruling:** `Proposed v1.4 (CP-P2-A; design accepted trail 116) — Accepted on v1.4 owner acceptance`. **CSV audit-disposition column:** `Added by CP-P2-A Part C (verifier replacement texts adopted verbatim, P2A-03..P2A-09)`.

**Placement:** in register order, immediately after `DEC-02` and before `EX-01`. Pre-existing row order is unchanged end to end.

**One rendering decision, stated so it is checkable.** The source line is `> **DE-R1 (identity and deduplication)** — <text>`. The ID becomes the register's ID column, so the cell carries the remainder verbatim: `**(identity and deduplication)** — <text>`. I kept the parenthetical title rather than drop it, because it is information the source block carries and the ID column cannot hold. **If Fable wants the bare text with no lead-in, it is a mechanical strip of the first 8–50 characters of each cell** — say so and I will do it.

**WF-09 harmonization applied** in both files: `Amended v1.1; Amended v1.4 (CP-P2-A; design accepted trail 116 — final on v1.4 owner acceptance)`.

## 2. C-2 through C-5

| Item | Disposition | What I did |
| --- | --- | --- |
| **C-2** section labels | Ratified, no action | Nothing. The Manual continues to carry the true section identities (§3.2, §12.1, §20A.1); `D-AM_` stays byte-intact as a historical instrument |
| **C-3** D-B12 | One sentence into §22.1 | Inserted **verbatim**, once, at the end of §22.1's third paragraph — the paragraph that already scopes what the gate did and did not do, which is where a gate-evidence pointer belongs |
| **C-4** filenames | Applied | All thirteen document-ID citations in §22.2 replaced with the C1 filenames (`D-B6_` already carried its full name). **No new section numbers** — §22.2's lead-in now says so explicitly. **I re-checked all 14 names against `design_directory_listing.txt` in the relay: 14/14 present.** Given that an earlier draft of that list had four wrong names, I did not take it on trust |
| **C-5** ADR-019 placement | Ratified, no action | Nothing moved |

## 3. Change log

`07c_` now reads as a completed build: the status paragraph drops the incompleteness caveat and records that the texts arrived via the C1 relay; the "Not applied" section becomes **"Added — DE-R1..DE-R8 requirement rows"**; the arithmetic table reads **125 → 133** with 8 new IDs; the process line records the verify-and-unblock round; and "Open against this log" lists the four items as **closed by `54_`**, with the remaining path stated as Fable verification → owner v1.4 acceptance → receipt-commit restamp of the eight proposed status cells.

Two internal citations inside `07c_` were stale after the edits and were harmonized: the WF-09 bullet now quotes the ruled status form, and the §22 bullet now lists the fourteen filenames instead of document IDs.

## 4. Verification

- **Register: 133 rows in the `.md` and 133 in the `.csv`**, ID sets identical **and in the same order**; no duplicate IDs; no ID removed; the eight DE-R IDs appear exactly once each; pre-existing row order preserved exactly.
- **Against the original snapshot:** 125 → 133; the only pre-existing rows that differ are **GOV-01 and WF-09**, as intended across both rounds.
- **Manual:** the C-3 sentence appears **once, verbatim**. §22.2 cites **14 filenames, all 14 confirmed against the live `design/` listing**; no bare document-ID row remains.
- **Excluded-path scan re-run:** register `.md` and `.csv` contain **0** occurrences of "Opus 4.8"; the Manual contains **2**, both by design (the preserved ADR-019 row, and the amendment note's own quotation of the prior value). Current-facing occurrences: **0**.
- **ADR-019 original row byte-intact.**
- **Allowlist: 3 modified + 1 added, 0 outside.** Read-only inputs **9/9 byte-identical**.
- **`checksums.sha256` regenerated** over all seven files in the touched directory. Still shipped in the zip root rather than written into `fable/phase1-audit-v1.0/`, because adding a file there would breach the packet §4 allowlist — unchanged reasoning from the first round, and Fable must still regenerate the repo's own file at integration.
- **`RETURN_MANIFEST.json` self-verified** by re-hashing every entry from the unpacked zip.

## 5. Falsifier element (APP-06 / CPB-14, reflexive)

| # | Claim | Who would have to be wrong, and how | Status |
| --- | --- | --- | --- |
| 1 | The eight texts are byte-identical to `13_` §5 | **The extraction, and it is machine-checked both ways.** I parsed the source block with a regex, wrote the cells from the parse, then re-read the shipped files and compared cell against source line for all eight in both formats. If the regex mis-parsed a line — a stray `—` inside a text, say — the comparison would fail, because it compares against the same source line the parse came from. **The residual risk is a line the regex did not match at all**: I checked the count is exactly 8, which is the number `13_` §5 declares | Not disconfirmed; **count and content both checked** |
| 2 | The rendering decision is harmless | **Fable.** Keeping `**(title)** — ` as a lead-in is my call, disclosed in §1 with the exact reversal. If the register's convention is bare text, eight cells need a prefix stripped | **Interpretive, disclosed, trivially reversible** |
| 3 | The 14 filenames are correct | **The relay listing, or my transcription of it.** I compared my citations against `design_directory_listing.txt` set-wise: 14/14 present. If that listing is itself stale relative to the live directory, my citations inherit it — but `54_` states it was read directly from `design/` at C1 issuance, which is the strongest provenance available to me | Not disconfirmed; **provenance is Fable's** |
| 4 | Nothing else moved | **The allowlist and read-only checks.** 3 modified + 1 added, 0 outside; 9/9 read-only inputs byte-identical; pre-existing register row order preserved | Not disconfirmed |
| 5 | My record matches my files | **Me, and my checker was wrong this round.** My row-counting regex was `[A-Z]+-[0-9]+`, which does not match the ID form `DE-R1`. It reported **125 rows and zero DE-R rows** on a file that had 133 and all eight. The rows were correct; **the verification was not**. I found it because a second check in the same run — one that matched DE-R rows explicitly — disagreed, and two checks in one report cannot both be right. Corrected pattern, re-ran, 133/133. Had I shipped on the first pattern I would have reported the C-1 item as not landed | **Checker defect caught by cross-checking, not by reading** |
| 6 | v1.4 is complete as a build | **Nobody, if `54_` is complete** — it names five items and all five are done. But "complete as a build" is not "accepted": Fable verification and the owner v1.4 event both remain, and the eight status cells say `Proposed` until the restamp. The change log and the return manifest both carry that distinction | **Asserted at build scope only** |

## 6. Open items and deviations

- **Nothing blocking.** All five C1 items are applied or were no-action by ruling.
- **One interpretive call to ratify or reverse:** the DE-R cell lead-in — §1.
- **`checksums.sha256` placement** — §4, allowlist-driven, unchanged from the first round.
- **No scope deviations.** Nothing written outside the four allowlisted paths. Nothing from Track B was touched.
- **Branch deviation (unchanged, disclosed):** operator-designated branch.
- **Recommended reviewer focus:** falsifier row 5. The finding of this round is not in the deliverable — it is that a verification regex silently under-reported and was caught only because two checks in the same report contradicted each other.

---

*Builder-authored completion claim and evidence index — not independent evidence (APP-06). The build is claimed complete; no acceptance is claimed.*
