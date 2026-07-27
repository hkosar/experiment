# TASK-0002 — Builder return (message to Fable)

Attached: `TASK-0002_Builder_Return.zip` — SHA-256 `8eaeba482dc14f3bc6256a0181598ea5b8aa5845381b6e3b9abf209316249b8a`, 91,548 bytes, 6 members.

Contents: `RETURN_MANIFEST.json`, `BUILDER_DELIVERY_RECORD.md`, and `returned/` holding complete copies of all four changed files at packet-relative paths.

---

## H-06 gate — re-validated independently before any edit

I did not trust the prior session's "12/12". I recomputed it in a clean session:

- Snapshot zip SHA-256 `032bdb4cd3e060b30878695c7fd4747da2c984922c9a44bc7635d02e180e1e66` — matches the packet fingerprint.
- `EXPORT_MANIFEST.json`: **12/12 = 100 %** across WRITABLE (4), NORMATIVE (2), REFERENCE-ONLY (2), CONTEXT (4).
- No unlisted files present; none absent. 13 archive members = 12 listed + the manifest.
- **Re-validated after the build: still 12/12**, proving the pinned inputs were read but never mutated.

## Status

**Built; post-build verification pending.** Not released, not owner-accepted. No later version layer and no Phase 2 transition is claimed or implied. All downstream gates — your re-verification, ChatGPT post-build verification, corrections, final acknowledgment, GOV-03 compare-and-swap release, owner acceptance — remain yours and are not claimed here.

## What was built

Changed set is **exactly the four WRITABLE files**. No gate/control artifact touched: `bootstrap_id_registry.md`, `manifest.json`, `checksums.sha256`, packet/gate documents, decision trail and README are untouched. No ID allocated, renumbered, or lifecycle-changed.

| File | SHA-256 |
| --- | --- |
| `fable/phase1-audit-v1.0/04_Proposed_Operating_Manual_v1.1.md` | `292f2b8d150fbbc6a3838d47aaa18c2f872ba4438caab894c74f0c53dcc8fab1` |
| `fable/phase1-audit-v1.0/05_Requirements_Register_v1.1.md` | `95e0f34c91dcc321bd45da1e6845bd21f80f9ce42b608fa4b4182c6fb6be5e25` |
| `fable/phase1-audit-v1.0/05_Requirements_Register_v1.1.csv` | `0347263ab6ff3e1b8a182ee5e2d6ac5ddbc7217ae9decfd84c41e051eb0383bb` |
| `fable/phase1-audit-v1.0/07a_Change_Log_v1.1_to_v1.2.md` | `e311d8567d31ac6d40f6faccda54e54c03b5e3fa92ce2d4f571f174ba2434025` |

- **Register:** 14 Part C rows verbatim (MEM-08, MEM-09, BUS-10, AUD-03, LRN-09, LRN-10, SEC-02, CAP-03, CAP-04, ONB-01, DEC-02, AUT-12, ORG-07, SCH-02), status `v1.2-proposed (CP-v1.2-B)`, CSV disposition `CP-v1.2-B (CPB-nn; trail 62)`; APP-06 amendment appended. **111 → 125 rows**, MD/CSV ID sets identical, no renumbering, and the 110 untouched baseline rows are byte-identical to the snapshot.
- **Manual:** all 18 Part C2 amendment texts at their stated anchors, new **§11A.8**, plus **ADR-021**, **ADR-022** (`Proposed (v1.2, CP-v1.2-B)`) and **DP-027**, all verbatim.
- **Change log:** CP-v1.2-B section with Added / Amended / register arithmetic / Preserved, the M-01..M-11 landing table, and a semantic regression matrix — snapshot-truthful: built, not released.

**Packet wording quirk, disclosed not acted on:** the packet prose says "three implementation-allowlist files" while the manifest's WRITABLE category lists four. They reconcile — three *work items*, four *files*, because the register is an MD + CSV pair. I built all four per the manifest.

## Verification highlights

- **Verbatim discipline enforced mechanically.** All 36 payload strings were machine-verified as literal substrings of CP-v1.2-B Rev 2 *before* any edit, and every anchor replacement asserted it matched exactly once — an ambiguous or missing anchor aborts the build rather than guessing.
- **Register (L-01):** `csv.reader` parse → 125 rows × 4 fields = 500 cells; byte-identical round-trip through a quoting-safe `csv.writer` (`QUOTE_MINIMAL`). 80 rows contain embedded quotes or commas and all re-parse correctly. No string concatenation anywhere in the CSV path.
- **Whitespace/line endings (K-03):** proved at byte level, with the exact `git check-attr` output, the exact `core.whitespace` configuration, a demonstrably non-empty diff, and **working positive controls**. All four files: 0 CR, 0 trailing whitespace, single final LF. Zero new consecutive-blank-line sequences introduced.

## ⚠ K-03 — I reproduced a live false-PASS mechanism, please record it

**`git diff --check` structurally cannot detect CRLF in files governed by `text eol=lf`.** The attribute normalises CRLF → LF at staging time, so the defect is destroyed *before* the diff is computed. I demonstrated this directly: a file with a confirmed CR byte in the working tree (`grep -c $'\r'` → 1) produced empty `--check` output and exit 0.

This is a plausible mechanism for the TASK-0001 false PASS. **A line-ending claim backed only by `git diff --check` is not evidence.** My own claim rests on the byte-level check instead. I'd recommend recording this as a durable control alongside K-03 — it is not a one-off, it will silently recur for any future builder who reaches for the obvious command.

## Decisions needing your accept-or-revert

No normative text was authored. Seven mechanical-anchoring decisions are enumerated in §5 of the Delivery Record. In priority order:

1. **Appendix A.4 instead of extending A.3.** The plan says "Appendix A.3 (extend)". A.3 is a *closed, accepted* CP-v1.2-A record; extending it in place would have folded proposed CP-v1.2-B content into an accepted section and implied acceptance. I created a parallel **A.4**, explicitly marked proposed/not-accepted, and left A.3 byte-unchanged. **This is the largest authored surface in the build** — if you want it folded into A.3 instead, that is a clean revert.
2. **§17.2 cross-reference.** The plan supplies a note for §17.1 and asks for a cross-reference at §17.2 without supplying its words. **This is the only sentence in the build whose wording is mine.**
3. **MEM-09 and ORG-07 trailing annotations.** I retained the trailing italic notes (*"(CPB-05: verifier Concur; …)"*) because they sit inside the Part C blockquote. If you intend them as editorial commentary rather than requirement text, that is a one-line fix in both MD and CSV. Flagging rather than guessing.
4. **Register header arithmetic.** The self-count line would otherwise have read "111 current rows" over a 125-row table. Updated to `**Current total: 125 rows.**`, following the precedent your CP-v1.2-A build set on that same line, plus a short scoped note that the CP-v1.2-B rows are proposed and carry no acceptance — so the trail-65 acceptance above it cannot be misread as covering them.
5. **Table-shape adaptations (4).** §18.1, glossary WAT, DP-027 and ADR-021/022 anchors are tables, not prose, so supplied sentences were split at their natural label boundary into the table's columns. All words preserved verbatim.
6. **§6.3 placement** — appended to the Decision row's Definition cell, the only placement honouring the plan's "Decision object:" scoping.
7. **Contents list — deliberate no-op.** The packet says update it "only as needed for §11A.8". The Contents list enumerates top-level sections only (verified: no `N.M` entry exists anywhere in it), and §11A.8 is a subsection of the already-listed `11A.` entry. Nothing was needed, so nothing changed — it is byte-identical to baseline.

## Falsifier element (CPB-14, applied reflexively to this build)

Nine material claims each carry what would disconfirm them (Delivery Record §6). Two are worth your attention:

- **One claim was genuinely disconfirmed.** My first allowlist-conformance check used `glob('**/*')`, which silently skips dotfiles, and reported PASS while a stray `.gitattributes` sat in `returned/`. Removed, re-verified with `os.walk`, disclosed in §2. Same defect class as K-03 — a check with a blind spot — and briefly a false PASS of my own making.
- **One claim I cannot self-verify:** whether my mechanical anchoring stayed mechanical and never became normative authorship. That is a judgment about my own work; items 1 and 2 above are where authored wording actually exists. No reasoned N/A is available — it needs your eyes and the verifier's.

## Housekeeping

- `RETURN_MANIFEST.json` in the zip is a **Builder-authored packaging aid with no gate authority**. It is not, and does not claim to be, the Fable-only `manifest.json`.
- Still outstanding from the previous session and not Builder work: the stale remote branch `claude/task-0001-release-packet-t962px` on `Twisted-Nail/tnbs-ap-tool` needs manual deletion. Unmerged and inert — hygiene, not risk.
