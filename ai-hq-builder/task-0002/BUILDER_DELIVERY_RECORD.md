# Builder Delivery Record — TASK-0002

**Task:** TASK-0002 — instantiate Change Plan CP-v1.2-B Revision 2 into the accepted v1.2 baseline.
**Builder:** Claude Code session (model `claude-opus-5`), fresh session, no `ai-hq` repository access (APP-09 preserved).
**Date:** 2026-07-27
**Status:** **Built; post-build verification pending.** Not released. Not owner-accepted. No gate beyond this build is claimed.

**Normative authority:** `17_TASK-0002_Release_Packet.md` and `15_Change_Plan_CP-v1.2-B_NateHerk_Adoption.md` (Revision 2), both validated against `EXPORT_MANIFEST.json`. Everything else in the snapshot — `14_NateHerk_Comprehensive_Review.md`, `16_Verifier_Response_CP-v1.2-B_Rev1.md`, `bootstrap_id_registry.md`, `00_READ_ME_FIRST.md`, `06_Decision_Trail_Addendum.md` — was treated as reference/context with **no instruction authority**. The prior session's handoff document was treated as **builder-authored context, not evidence**: every claim it makes was independently re-derived here.

---

## 1. Input integrity — H-06 gate

Validated **before any file was opened for editing**.

| Check | Result |
| --- | --- |
| Snapshot zip SHA-256 | `032bdb4cd3e060b30878695c7fd4747da2c984922c9a44bc7635d02e180e1e66` — matches the packet fingerprint |
| `EXPORT_MANIFEST.json` per-file hashes | **12 / 12 = 100 %** |
| WRITABLE (4) · NORMATIVE (2) · REFERENCE-ONLY (2) · CONTEXT (4) | all four categories 100 % |
| Files present but unlisted in the manifest | **none** |
| Files listed but absent | **none** |
| Archive contents | 13 files (12 listed + `EXPORT_MANIFEST.json`) |

Command (Python 3, `hashlib.sha256` over each manifest-listed path, plus a reverse walk of the extracted tree to detect unlisted files). Re-run **after** the build against the snapshot tree: still **12/12** — the build read the pinned inputs and never mutated them.

Manifest metadata recorded for Fable's binding evidence: `source_commit 35d957309f78c27393dc19612a6b036e09d640b5`, `source_tree fd5d95d202554514fc29f832f288d33c441d79df`, `base_commit_pinned_in_packet a22aea6e059d84bcfd0ed82dbf1a79c7b28ce0eb (tag v1.2)`.

## 2. Returned files and hashes

Complete copies, at packet-relative paths, under `ai-hq-builder/task-0002/returned/`.

| Returned file | SHA-256 |
| --- | --- |
| `fable/phase1-audit-v1.0/04_Proposed_Operating_Manual_v1.1.md` | `292f2b8d150fbbc6a3838d47aaa18c2f872ba4438caab894c74f0c53dcc8fab1` |
| `fable/phase1-audit-v1.0/05_Requirements_Register_v1.1.md` | `95e0f34c91dcc321bd45da1e6845bd21f80f9ce42b608fa4b4182c6fb6be5e25` |
| `fable/phase1-audit-v1.0/05_Requirements_Register_v1.1.csv` | `0347263ab6ff3e1b8a182ee5e2d6ac5ddbc7217ae9decfd84c41e051eb0383bb` |
| `fable/phase1-audit-v1.0/07a_Change_Log_v1.1_to_v1.2.md` | `e311d8567d31ac6d40f6faccda54e54c03b5e3fa92ce2d4f571f174ba2434025` |

**Changed set = exactly these four files.** Verified programmatically with a dotfile-inclusive `os.walk`: the returned file set equals the manifest's WRITABLE category exactly — no extra files, none missing, and no gate/control artifact (`bootstrap_id_registry.md`, `manifest.json`, `checksums.sha256`, packet/gate documents, decision trail, README) present in the return. All four differ from their snapshot originals; nothing else was written.

> **Self-caught verification defect (disclosed).** My first conformance check used `glob.glob('**/*', recursive=True)`, which **silently skips dotfiles**. A stray `.gitattributes` — copied into `returned/` only so `git check-attr` could resolve the real attribute policy in §4 — was therefore present while the check still reported "returned set == allowlist exactly: True". The file has been removed and the check rewritten to use `os.walk`, which sees dotfiles; the result above is from the corrected check. Recorded because a conformance check with a blind spot is the same defect class as K-03, and because the original PASS was, briefly, a false PASS of my own making.

### Packet wording quirk — disclosed, not acted on

The packet prose says "three implementation-allowlist files" and "all three changed files" while the manifest's WRITABLE category lists **four**. These reconcile: three *work items* map to four *files* because the register is a matched MD + CSV pair. **Built all four**, per the manifest. No clarification was invented beyond this reconciliation.

## 3. Register proofs

| Measure | Before | After | Required |
| --- | --- | --- | --- |
| MD data rows | 111 | **125** | 125 ✓ |
| CSV data rows | 111 | **125** | 125 ✓ |
| MD / CSV ID sets identical | yes | **yes** (symmetric difference empty) | yes ✓ |
| New IDs | — | **14** | 14 ✓ |
| Rows amended | — | **1** (APP-06) | 1 ✓ |
| Rows renumbered or otherwise changed | — | **0** | 0 ✓ |

The 14 new rows — MEM-08, MEM-09, BUS-10, AUD-03, LRN-09, LRN-10, SEC-02, CAP-03, CAP-04, ONB-01, DEC-02, AUT-12, ORG-07, SCH-02 — are inserted in alphabetical position (`ONB` is a new family sorting between MEM and ORG), each with status `v1.2-proposed (CP-v1.2-B)` and CSV audit disposition `CP-v1.2-B (CPB-nn; trail 62)`.

**No-other-row-changes proof:** all 110 baseline rows other than APP-06 were compared field-by-field against the snapshot CSV and are **byte-identical**. All 111 baseline IDs are retained.

### CSV schema validation — exact command and output (L-01)

A quoting-safe writer was mandatory and used: `csv.writer(..., lineterminator='\n', quoting=csv.QUOTE_MINIMAL)`. The Part C texts contain embedded double quotes, commas, backticks and `MUST NOT` phrasing; no string concatenation was used anywhere in the CSV path.

```
$ python3 -c "parse 05_Requirements_Register_v1.1.csv with csv.reader; report row and field counts"

  PASS  CSV header == 4 declared fields   ['ID', 'Requirement', 'Status', 'Audit disposition']
  PASS  every data row has exactly 4 fields   observed field-count set: [4]
  PASS  total parsed cells == 125x4 == 500   actual 500
  PASS  CSV round-trips byte-identically (quoting stable)
  PASS  rows containing quote/comma re-parse correctly   80 such rows, e.g. ['ACT-01', 'APP-02', 'APP-04', 'APP-05']
  PASS  MD data rows == 125   actual 125
  PASS  CSV data rows == 125   actual 125
  PASS  MD/CSV ID sets identical   symmetric difference: none
  PASS  MD/CSV ID ORDER identical
  PASS  no duplicate IDs
  PASS  IDs sorted alphabetically
  PASS  MD text == CSV text for all 125
  PASS  MD status == CSV status for all 125
```

This is a **parse-based** validation (`csv.reader` → row × field counts → round-trip re-serialisation), not an eyeball. The round-trip check is the discriminating one: it re-serialises the parsed structure and compares bytes, so a quoting error that changed field boundaries could not survive it.

## 4. Whitespace and line-ending proof (K-03)

The TASK-0001 false PASS may not recur, so the exact command, configuration, attributes context, **and a positive control** are all recorded.

### Attributes context

`.gitattributes` declares `*.md text eol=lf` and `*.csv text eol=lf`, and marks immutable/verbatim trees `-text -whitespace` (`/baseline/**`, `/fable/v1.2-ideas-pass/sources/**`, and named verifier records). Those exemptions are **content, not defects** — and critically, **none of the four writable files falls under them**:

```
$ git check-attr text eol whitespace -- <each returned file>
fable/phase1-audit-v1.0/04_Proposed_Operating_Manual_v1.1.md: text: set
fable/phase1-audit-v1.0/04_Proposed_Operating_Manual_v1.1.md: eol: lf
fable/phase1-audit-v1.0/04_Proposed_Operating_Manual_v1.1.md: whitespace: unspecified
   (identical for 05_..._v1.1.md, 05_..._v1.1.csv, 07a_Change_Log_v1.1_to_v1.2.md)
```

`whitespace: unspecified` means these files inherit git's **default** policy. Configuration in effect: `core.autocrlf` unset (default `false`); `core.whitespace` unset (default `blank-at-eol,space-before-tab,blank-at-eof`).

### Proof 1 — git diff, on a genuinely non-empty diff

```
$ git -c core.whitespace=blank-at-eol,space-before-tab,blank-at-eof diff --cached --check <BASE>
(no output; exit 0)

$ git diff --cached --stat <BASE>
 .../04_Proposed_Operating_Manual_v1.1.md  | 69 ++++++++++++++++++-
 .../05_Requirements_Register_v1.1.csv     | 16 ++++-
 .../05_Requirements_Register_v1.1.md      | 20 +++++-
 .../07a_Change_Log_v1.1_to_v1.2.md        | 77 ++++++++++++++++++++++
 4 files changed, 178 insertions(+), 4 deletions(-)
```

`<BASE>` is a commit of the **pinned snapshot originals**, with the snapshot `.gitattributes` in place, so the attribute policy above is actually active. The `--stat` output is included deliberately: **an empty diff is the most likely mechanism of a false PASS**, and this diff is demonstrably non-empty.

### Proof 2 — byte-level, attribute-independent (authoritative)

```
file                                     bytes     CR   CRLF trail-ws  final-LF
04_Proposed_Operating_Manual_v1.1.md    142887      0      0        0       yes
05_Requirements_Register_v1.1.csv        36020      0      0        0       yes
05_Requirements_Register_v1.1.md         34587      0      0        0       yes
07a_Change_Log_v1.1_to_v1.2.md           15681      0      0        0       yes

VERDICT: CLEAN - 0 CR, 0 trailing whitespace, single final LF on all 4 files
```

Additionally verified: this build introduced **zero** new consecutive-blank-line sequences (Manual baseline 6, returned 6; register and change log 0 → 0). The build script itself asserts no-CR and no-trailing-whitespace on every file at write time and would have aborted otherwise.

### Positive controls — proof that these checks can fail

| Injected defect | `git diff --check` | Byte-level check |
| --- | --- | --- |
| trailing space at EOL | **caught** (`trailing whitespace.`) | **caught** |
| space-before-tab in initial indent | **caught** (`space before tab in indent.`) | n/a by design |
| **CRLF line ending** | **MISSED — silent false PASS** | **caught** |
| missing final LF | n/a by design | **caught** |
| blank line at EOF | n/a (no diff context) | **caught** |

### ⚠ K-03 finding for Fable and the verifier — a live false-PASS mechanism

While building the positive control I reproduced a concrete false-PASS mechanism that plausibly explains the TASK-0001 defect:

**`git diff --check` structurally cannot detect CRLF in files governed by `text eol=lf`.** The attribute normalises CRLF → LF when the file is staged, so the defect is destroyed *before* the diff is computed. Demonstrated directly: a file with a confirmed CR byte in the working tree (`grep -c $'\r'` → 1) produced **empty** `--check` output and exit 0.

Consequence: **a CRLF/line-ending claim backed only by `git diff --check` is not evidence.** Any such proof must inspect working-tree bytes, as Proof 2 does. I recommend this be recorded as a durable control alongside K-03. My own line-ending claim above rests on Proof 2, not Proof 1.

## 5. What was built — mapping to CPB items

**Register** (`05_..._v1.1.md` + `.csv`): 14 Part C texts verbatim; APP-06 amendment appended (CPB-14).

**Manual** (`04_...`): all 18 Part C2 amendment texts at their stated anchors —
§15.4 (CPB-01) · §13.5 (CPB-02) · §13.7 (CPB-02) · §7.5 (CPB-03) · §10.5 (CPB-04) · §15.3.1 **and** §7.3 (CPB-05) · new **§11A.8** (CPB-06) · §18.1 (CPB-07/12) · §17.1 note + §17.2 cross-reference (CPB-08) · §10.1 (CPB-09) · §6.3 **and** §8.6 (CPB-10) · §8.2.1 + §11.3 (CPB-11) · §10.4 (CPB-12) · §8.5 (CPB-13) · §12.6 (CPB-14) · §17.0 (CPB-15) · glossary **WAT** (CPB-16) · Appendix A.3 extension.
Plus **ADR-021**, **ADR-022** (status `Proposed (v1.2, CP-v1.2-B)`) and **DP-027**, all verbatim.

**Change log** (`07a_...`): CP-v1.2-B section with Added / Amended / register arithmetic / Preserved, the M-01..M-11 build-side landing table, and a semantic regression matrix. Snapshot-truthful: built, **not** released.

### Verbatim conformance evidence

Every payload string was transcribed into a separate literals file and then **machine-verified as a literal substring of the plan document** before any edit was made — 36/36 exact. Where the plan separates an italic version marker from a quoted body (`*(v1.2 — CP-v1.2-B, CPB-nn)* "…"`), the marker and body were verified independently and rejoined; the quotation marks are delimiters, not content. Each anchor replacement asserted it matched **exactly once** in the target document, so no edit could land ambiguously.

### Builder-authored text — the complete list

No normative text was authored. Beyond inserting supplied text at supplied anchors, the following **mechanical anchoring** was required. Each is disclosed for Fable to accept or revert:

1. **Table-shape adaptation (4 places).** Four anchors are tables, not prose, so a supplied sentence was split at its natural label boundary into the table's columns — all words preserved verbatim:
   - §18.1 "append bullet" → table row: Measure `Cost posture *(v1.2 — CP-v1.2-B, CPB-07/CPB-12)*` | remainder of the supplied sentence.
   - Glossary → `| WAT (Workflows/Agents/Tools) *(v1.2 — CP-v1.2-B)* | <definition> |`, split at the supplied em dash.
   - Appendix C → `| DP-027 *(v1.2 — CP-v1.2-B)* | <principle> |`; the ID moved to the ID column, so the plan's bold span `**DP-027 — Automation-first…**` becomes `**Automation-first…**`.
   - Appendix D → `| ADR-0nn *(v1.2 — CP-v1.2-B)* | **<short title>.** <verbatim text> | Proposed (v1.2, CP-v1.2-B) |`. The short titles ("External managed-memory provider direction", "Grant-once, activate-staged onboarding") are the plan's own Part C2 sub-headings. The Status column carries the packet-specified `Proposed (v1.2, CP-v1.2-B)`; the verbatim "accepted upon owner plan approval" wording remains inside the Decision cell, which the packet expressly anticipates as describing the trail-64 owner event, not a release claim.
2. **§6.3 placement.** The plan says "§6.3 (Decision object: append sentence)". The supplied sentence was appended to the **Decision** row's Definition cell — the only placement honouring the "Decision object" scoping.
3. **§17.2 cross-reference.** The plan supplies a note for §17.1 and asks for a *cross-reference* at §17.2 without supplying its words. Authored minimally as a pointer: *"Grant collection for this stage's integrations follows the ONB-01 / ADR-022 onboarding note at §17.1."* **This is the only sentence in the build whose wording is mine.**
4. **Appendix A.3 "extend" → new A.4 subsection.** A.3 is a closed, accepted CP-v1.2-A record ("post-build verified… accepted by the owner"). Extending it in place would have folded proposed CP-v1.2-B content into an accepted section and implied acceptance. Instead a parallel **A.4** carries the CP-v1.2-B index, explicitly marked *(v1.2-proposed — CP-v1.2-B)* / "not released and not owner-accepted". A.3 is byte-unchanged. The list contents are IDs and short descriptors drawn from the Part C texts; **this is the largest authored surface in the build** and the item most worth Fable's review.
5. **Register header arithmetic.** The self-count line would otherwise have read "111 current rows" over a 125-row table. Updated to state the CP-v1.2-B additions and `**Current total: 125 rows.**` — following the precedent set by the CP-v1.2-A build, which updated this same line. A short scoped note was also added stating the CP-v1.2-B rows are built, verification pending, **not** released and **not** owner-accepted, so the trail-65 acceptance recorded above it cannot be read as extending to them.
6. **APP-06 status composition.** Rendered as `Accepted v1.2 (owner acceptance, trail entry 65); Amended by CP-v1.2-B (CPB-14); v1.2-proposed` — appending rather than replacing, so the base requirement's genuine acceptance is not silently dropped while the amendment is correctly marked proposed.
7. **Contents list — deliberate no-op.** The packet says "update the Contents list **only** as needed for §11A.8". The Contents list enumerates top-level sections **only** (verified: no `N.M` subsection entry exists anywhere in it); §11A.8 is a subsection of the already-listed `11A.` entry. **Nothing was needed, so nothing was changed** — the list is byte-identical to baseline.

**Confirmation:** no text outside the Part C / Part C2 payloads was Builder-authored beyond items 1–7 above.

## 6. Falsifier element (APP-06 as amended by CPB-14, applied reflexively)

For each material claim: what would disconfirm it. This is Builder-authored review input only and never replaces independent reproduction.

| # | Claim | What would disconfirm it | Status |
| --- | --- | --- | --- |
| 1 | Manifest validated 12/12 | Recomputing SHA-256 over any listed path and getting a different digest; finding a file in the archive absent from the manifest, or a listed file missing. Both directions were tested, including a reverse walk of the extracted tree. **Strongest disconfirmer:** an attacker-supplied manifest that matches a tampered payload — the manifest is self-consistent, so it cannot detect that. Mitigated only by the independently-supplied zip fingerprint matching the packet, which I checked; I cannot rule it out further from inside the snapshot. | Not disconfirmed |
| 2 | Register is 125 rows, MD/CSV ID sets identical | A `csv.reader` parse returning ≠ 125 rows; a non-empty symmetric difference between MD and CSV ID sets. Both computed, both clean. Would also be disconfirmed by a markdown row whose pipe count differs from 3 (my MD parser would mis-split) — checked separately: MD text and status match CSV cell-for-cell on all 125 rows, which could not hold under a mis-parse. | Not disconfirmed |
| 3 | CSV quoting is correct | Round-trip re-serialisation producing different bytes; any row parsing to ≠ 4 fields. Both tested; 80 rows contain embedded quotes or commas and all re-parse correctly. A residual gap: a field could be *semantically* wrong yet still well-quoted — covered instead by claim 5. | Not disconfirmed |
| 4 | Zero CRLF / trailing whitespace | **`git diff --check` alone would NOT disconfirm this — it structurally cannot see CRLF under `text eol=lf`, as demonstrated in §4.** The byte-level check would: injected CRLF, trailing space, missing final LF and blank-at-EOF were each caught by it. This is precisely the TASK-0001 false-PASS class, so the positive control is the evidence, not the clean result. | Not disconfirmed |
| 5 | All texts inserted verbatim | Any payload string failing a literal-substring test against the plan (checked pre-edit, 36/36) or against the returned files (checked post-edit). **Known residual:** for MEM-09 and ORG-07 I retained the trailing italic annotations (*"(CPB-05: verifier Concur; …)"*) because they sit inside the Part C blockquote. If Fable intends those as editorial commentary rather than requirement text, this is wrong and is a one-line fix in both MD and CSV. Flagging it explicitly rather than guessing. | Not disconfirmed; one judgment call flagged |
| 6 | Only the 4 allowlist files changed | Any file outside the WRITABLE set appearing in the return, or any snapshot input whose hash changed. Both tested — the post-build manifest re-validation (still 12/12) is the discriminating check, since it would catch in-place mutation of an input. **This claim was actually disconfirmed once:** the first check used `glob('**/*')`, which skips dotfiles, and passed while a stray `.gitattributes` sat in `returned/` (see §2). Removed; re-verified with `os.walk`. The lesson generalises — a file-set check that cannot see every file class is not evidence. | Disconfirmed once, corrected, now not disconfirmed |
| 7 | Nothing claims release or acceptance | A `v1.3` / "Phase 2 open" / unqualified "released"/"accepted" token appearing in **added** lines. Diffed line-by-line; every remaining occurrence in added text is either verbatim plan wording (LRN-09's "at most one accepted improvement artifact"; ADR-021/022's plan-approval language), a true CP-v1.2-A historical fact, or an explicit disclaimer. Enumerated and reviewed individually rather than grep-passed. | Not disconfirmed |
| 8 | Mechanical anchoring did not become normative authorship | An independent reader judging any item in §5 to change meaning rather than shape. **This is the claim I can least self-verify** — it is a judgment about my own work, and items 4 (Appendix A.4) and 3 (§17.2 cross-reference) are where authored wording actually exists. No reasoned N/A is available; this needs Fable's and the verifier's eyes. | **Explicitly unverified by me** |
| 9 | The build is complete | A CPB item with no corresponding change. All 16 CPB items were mapped to landed changes (§5). CPB-16 (WAT) is glossary-only by design and CPB-14 lands in two places; M-10 is Fable-owned and correctly produced no build-side change — recorded as such in the change log rather than silently omitted. | Not disconfirmed |

## 7. Deviations, scope, and open items

- **No scope deviations.** Nothing outside the writable allowlist was touched; no ID was allocated, renumbered, or lifecycle-changed; no gate/control artifact was modified. Nothing was returned as a change request — every CPB item was buildable as specified.
- **Branch deviation (disclosed).** The handoff suggests `builder/task-0002`; this session was placed on the operator-designated branch **`claude/task-0002-builder-handoff-g97x8j`**, which takes precedence. All work is confined to `ai-hq-builder/`.
- **Not claimed:** post-build verification, release, owner acceptance, any v1.3 layer, Phase 2 opening. Downstream gates (Fable re-verification → ChatGPT post-build verification → corrections → final acknowledgment → GOV-03 compare-and-swap release → owner acceptance) are not mine to claim and are not claimed.
- **For Fable's attention, in priority order:** (1) the K-03 CRLF/`git diff --check` false-PASS mechanism in §4 — recommend recording as a durable control; (2) Appendix **A.4** vs extending A.3, §5 item 4; (3) the MEM-09 / ORG-07 trailing-annotation judgment, falsifier row 5; (4) the register header arithmetic edit, §5 item 5.
- **Not Builder work, carried forward from the handoff:** the stale remote branch `claude/task-0001-release-packet-t962px` on `Twisted-Nail/tnbs-ap-tool` still needs manual deletion by the owner. It is unmerged and inert — hygiene, not risk.

---

*Builder-authored completion claim and evidence index — not independent evidence. Every proof above is reproducible from the pinned snapshot with the commands and configuration stated. Required proofs must be independently reproduced or verified into the tamper-evident harness store before approval.*
