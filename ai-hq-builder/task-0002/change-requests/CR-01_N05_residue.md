# CR-01 — N-05 residue in two current-facing control records

**From:** Builder (`claude-opus-5`) · **To:** Fable (control plane) · **Task:** TASK-0002
**Type:** Change request — the affected files are Fable-only control artifacts, outside the Builder implementation allowlist. The Builder does not edit them; this is the correction, not an edit.
**Against:** final candidate `3ec2a09385bf5fd5be81efa5548a58b80a498674` / tree `e15cc9dbded1d8088cdfcfba111800902f4d85de`
**Patch:** `CR-01_N05_residue.patch` — SHA-256 `262aa2d8252ed20c5e15acc88166e864252562d742c94260996da2478ba5ca02`, 2,914 bytes. Verified `git apply --check` clean against `3ec2a09`.

## Why this is a change request and not a fix

Two reasons, the second decisive:

1. `bootstrap_id_registry.md` is the first-named item on the Fable-only gate/control list, and `00_READ_ME_FIRST.md` is README-class. Neither is in the Builder's four-file implementation allowlist.
2. Every file in the gate packet is bound to tree `e15cc9db`. Editing the extracted bytes would break the packet manifest hashes, both `checksums.sha256` files, and `manifest.json`, and would desynchronise the export from `task-0002-full-history.bundle` — destroying exactly the N-01 evidence chain the corrected packet was built to establish. A hand-edited packet would be a packet whose hashes lie.

The correction has to happen in the repository and produce a new commit/tree and a re-export. Only Fable can do that.

## Finding

N-05 was closed as an owner-authorized standing substitution (trail entry 69), which is correct and correctly authorized. `20_` §Finding closures scopes the remaining cleanup as a "Manual 20A.1 nominal text refresh." The residue is slightly wider: two **current-facing** records outside Manual 20A.1 still name Opus 4.8 as the builder.

**Accuracy note on the registry row:** it is internally inconsistent rather than silently wrong — the status field already ends *"N-05 resolved — owner-confirmed standing Builder substitution to Claude Opus 5 (trail entry 69)"*, while the description field still reads `(Builder: Opus 4.8)`. A reader scanning the description gets the wrong answer; a reader reaching the status gets the right one.

| File | Line | Current | Corrected |
| --- | --- | --- | --- |
| `fable/v1.2-ideas-pass/bootstrap_id_registry.md` | 11 (TASK-0002 row) | `…accepted v1.2 baseline (Builder: Opus 4.8)` | `…accepted v1.2 baseline (Builder: Claude Opus 5)` |
| `fable/phase1-audit-v1.0/00_READ_ME_FIRST.md` | 32 (Program governance) | `Opus 4.8 — builder.` | `Claude Opus 5 — builder (owner-confirmed standing substitution, trail entry 69).` |

Both substitutions were asserted to match exactly once in their file before being applied.

**Deliberately NOT changed by this CR:** the TASK-0001 registry row (that task genuinely was built by Opus 4.8 — correct as history), the decision trail (immutable append-only; entry 69 is the correction), `manifest.json`'s TASK-0001 builder field, verifier and auditor records, and all time-of-event plan/packet texts.

## Consequential regenerations (Fable)

1. `fable/v1.2-ideas-pass/checksums.sha256` — covers `bootstrap_id_registry.md`.
2. `fable/phase1-audit-v1.0/checksums.sha256` — covers `00_READ_ME_FIRST.md`.
3. `fable/phase1-audit-v1.0/manifest.json` — only if it records either file's hash.
4. New commit → new candidate commit/tree; re-run `make_packet.py`; update `20_` identities table and the export manifest.

Byte hygiene confirmed on both corrected files: 0 CR, 0 trailing-whitespace lines, single final LF (trail-67 rule).

## Post-correction state

After this CR, every remaining `Opus 4.8` occurrence in the tree falls into one of three defensible classes — historical/immutable records, time-of-event plan texts, or the standing-role definitions deferred below. No current-facing record misstates the TASK-0002 builder.

Worth noting in support of the closure: `19_TASK-0002_APP05_Conformance_Addendum.md` already states the mapping explicitly — *"nominally assigned Opus 4.8 per Manual 20A.1; actual runtime **Claude Opus 5**"* — which is precisely what N-05 asked for.

## Two wording additions recommended for `20_` before the acknowledgment goes out

**A. Strengthen the deferral justification (replaces "nominal text refresh").** The standing-role text should stay deferred, but for a stronger reason than currently stated:

> Manual §20A.1, ADR-019, and the §12.1.1 role tables name Opus 4.8 as the standing Builder; register requirement **GOV-01 carries the same list and is an owner-accepted v1.1 requirement (trail entry 53)**. Amending GOV-01 is a governed change requiring its own change plan and owner acceptance event — it is deliberately *not* folded into a deterministic restamp, since a restamp must not alter accepted requirement text. Trail entry 69 governs the substitution under the authority order until that change is planned; the standing-role refresh is scheduled for the next mechanical cycle.

This converts the deferral from an unexplained omission into a correct application of the accepted-baseline boundary.

**B. Disclose the ADR-021/ADR-022 status rewording explicitly.** The N-03 restamp changed two ADR **Status:** sentences in wording, not only in version marker. Their Context/Decision/Consequence bodies are byte-identical, and the change is visible in `reviewed_to_final.patch` — but inside 157 KB, and `18_` §N-03 said a semantic expansion requires targeted re-review. Naming it costs one paragraph and removes the discovery risk:

> **ADR-021:** `Proposed (v1.2, CP-v1.2-B); accepted upon owner plan approval.` → `Proposed (v1.3, CP-v1.2-B); accepted at owner v1.3 acceptance.`
> **ADR-022:** `Proposed (v1.2, CP-v1.2-B); accepted upon owner plan approval with FLAG-1 confirmation.` → `Proposed (v1.3, CP-v1.2-B); FLAG-1 confirmed at plan approval (trail entry 64); accepted at owner v1.3 acceptance.`
>
> Rationale: the original Part C2 wording tied ADR acceptance to plan approval, which already occurred at trail entry 64 — under that wording the ADRs would read as already accepted, contradicting their `Proposed` status and the no-acceptance-claim constraint. N-03 required every acceptance event to carry the single successor identity. Scope is the two `**Status:**` sentences only; both ADR bodies are byte-identical to the Builder return.

## Verification performed for this CR

- Patch `git apply --check` clean against `3ec2a09`; applied to a scratch clone from the shipped bundle with the expected 2-file / 2-line delta and nothing else.
- Both substitutions unique in their file (asserted, not assumed).
- Post-apply `git grep` sweep over the whole tree to confirm no current-facing record still misstates the TASK-0002 builder.
- Byte-level line-ending check on both corrected files.

**Falsifier for this CR:** what would disconfirm it is a demonstration that either changed field is in fact historical rather than current-facing — in which case the correct action is to revert that half and leave the record as time-of-event text. I judge both current-facing because `00_READ_ME_FIRST.md` is an orientation document for future agents and the registry row is live lifecycle state, and because Fable's own N-04 zero-count scan lists both files in its declared **current-facing** set. If Fable disagrees on either, revert that hunk — the patch is two independent hunks precisely so it can be split.
