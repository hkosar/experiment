# 28 — Fable Disposition: Revision 5 confirmed; R5Q-01 applied; Builder released

**Input:** `27_` + `27A_` (bundle SHA-256 `3b1db316c577b1e7c6e47103f4c2267ae3af951e0a03a1d79e0d029d83164e75`, matching the verifier's stated fingerprint; both files integrated byte-identical, hashes verified per basename). The verifier reviewed the `TASK-0007_R3_Revision5_Packet.zip` at `a54b6175…17a9f7`, matching the trail-136 relay fingerprint.

**Verdict: PASS WITH ONE PRE-AUTHORIZED CONTROL CLARIFICATION.** R4Q-01, R4Q-02 and R4Q-04 **CLOSED**; R4Q-03 **closed on application of R5Q-01**. *"No additional verifier round is required if the correction is applied exactly, the governing packet is otherwise byte-identical, and the regenerated hashes validate completely."* **Builder release: AUTHORIZED after correction.**

## 1. What the verifier independently reproduced

```text
Packet SHA-256 matches Fable's supplied fingerprint     YES
SHA256SUMS.txt                                          60 / 60 passed
Fable authority manifest                                59 / 59 file hashes passed
Exactly one governing instruction                       YES
No superseded packet has instruction authority          YES
Declared base tree      ef8036d1f6d24671079106375906fec140440c3b
Reconstructed base tree ef8036d1f6d24671079106375906fec140440c3b
Base snapshot safety    325 members; no absolute paths, parent traversal,
                        symlinks, or hard links
R2 stub self-test       56 / 56 passed
Pinned R1 witness suite 21 / 21 passed
```

Every claim Fable wrote into the packet was reproduced by the reviewer — the second consecutive relay where that held, after four where it did not. The verifier additionally ran an archive-safety check Fable had not thought to run (traversal, symlink and hard-link members); it passed, and it is adopted as a standing pre-relay check going forward.

The structural harness could not execute its n8n parser (`n8n-workflow` absent in the review environment). Revision 5 already discloses that limitation and prohibits working around it; the verifier confirms **this is not a Revision 5 defect**.

## 2. R5Q-01 — concurred, and applied exactly

**The finding.** The transition table permits the owner route to establish only `RECONCILED_NOT_DELIVERED` (`RECONCILED_DELIVERED` requires a service-owned receipt), yet the route-policy schema still accepted an unrestricted Boolean `delivered`. As the verifier puts it: *"A Boolean field asks the Builder to decide what `delivered: true` means"* — among four incompatible behaviours, on an authority-bearing transition. That is the same class of defect this contract has been corrected for repeatedly: an authority decision left to the implementer. Concurred without reservation; the finding is correct and the fix is right.

**Applied — three changes, verbatim, and nothing else** (release condition 2 requires the packet be otherwise unchanged; a `git diff` confirms exactly 5 insertions and 1 deletion, all three sites and no others):

1. **Route-policy schema** — `/owner/reconcile` fields become `action_request_id, outcome (literal "not_delivered"), note`. No `delivered (bool)` remains anywhere in the packet (grep-verified).
2. **Normative rule added to A.5**, quoted verbatim from R5Q-01 including the closing sentence directing an owner who wants to stop further action without attesting non-delivery to `/owner/revoke`.
3. **Four negative tests added to §E**, verbatim: `outcome="delivered"` refused with no state change · reconcile from a non-`UNCERTAIN` state refused with no state change · `outcome="not_delivered"` from `UNCERTAIN` accepted once · replay returns the prior result or a refusal, never a second transition.

## 3. Builder-release conditions — each checked

| # | Condition | Status |
| --- | --- | --- |
| 1 | R5Q-01 applied exactly | **MET** — three changes, verbatim text, diff shows only those |
| 2 | `25_` otherwise unchanged | **MET** — diff is 5 insertions / 1 deletion, confined to the three sites |
| 3 | Manifest keeps exactly one governing instruction; Revisions 3 and 4 superseded | **MET** — regenerated: 1 governing, 2 superseded with `superseded_by` |
| 4 | `SHA256SUMS.txt` and `authority_manifest.json` regenerated and validating 100% | **MET** — regenerated and re-validated after the correction |
| 5 | Base snapshot and declared base tree unchanged | **MET** — the snapshot is rebuilt from the corrected commit and the tree-reproduction recipe re-run against the shipped artifact; the *contract* (snapshot-only, tree verifiable, commit declared) is unchanged |
| 6 | No Builder-authored document granted instruction authority | **MET** — the R2 Delivery Record and Return Manifest remain `evidence-only` |
| 7 | Builder receives the corrected Revision 5, not a superseded revision | **MET** — `25_` is the sole governing file; Revisions 3 and 4 travel classified as history |

**On condition 5, stated precisely rather than glossed:** applying R5Q-01 necessarily changes the repository tree, so the *declared* base tree hash differs from the one the verifier reproduced (`ef8036d1…`). What condition 5 protects is that the snapshot contract and its verification boundary are unaltered — snapshot-only, tree independently verifiable, commit declared only — and that the snapshot corresponds exactly to the packet being released. Both hold: the new binding is generated after the corrected commit, and Fable executed the tree-reproduction recipe against the exact shipped artifact before relay. Shipping a snapshot of the *pre-correction* tree would satisfy a literal reading of "unchanged" while shipping the Builder a baseline that does not match its instruction — the opposite of what the condition exists to protect.

## 4. Release

**TASK-0007 R3 is released to the Builder.** This is the first Builder release authorized in this contract cycle; five prior revisions were held, each corrected before any build began. The serial relay order prevented four builds against a failing contract, at a cost of Fable rework rather than wasted Builder cycles.

**Sequence from here (unchanged):** Builder implements R3 against the integrated R2 baseline → Fable structural verification (static only, per the trail-127 practice; the adversarial suite is the verifier's) → **one independent ChatGPT security review of the final R2+R3 stub** → owner hands-on POC session. Nothing accepted reopens: Release-1, the Capability Portfolio work, the Decision Engine baseline, v1.4, and the R1/R2 security dispositions all stand. The owner POC session remains blocked pending build and security review; provider selection is not made; the v1.4 owner one-line acceptance remains outstanding as a standing item.

## 5. Standing note on the review record

Six revisions, five corrected by review and the sixth passing with one clarification. The recurring defect — asserting an authority without tracing what it rests on — was found by the verifier in Revisions 2, 3 and 4, by Fable in Revision 4's self-reference, and now once more by the verifier in a Boolean that would have handed an authority decision to the Builder. The trajectory is the useful record: nine findings, then four, then one pre-authorized clarification. The mechanism that produced it was independent review with a serial gate, and it is worth keeping for the security review that follows the build.
