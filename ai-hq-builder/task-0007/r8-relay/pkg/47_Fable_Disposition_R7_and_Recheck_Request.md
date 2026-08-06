# 47 — Fable Disposition: R7, and the re-check request

**Input:** `TASK0007_R7_Builder_Return.zip`, SHA-256 `802fd92f95163d2011a157f8a963974b9db6c9a7e72b1299434a18ea31438872`.

## 1. Structural verification (static only, per the trail-127 practice)

**Manifest 102 entries — 102 match, 0 missing, 0 mismatch, 0 undeclared.** The first perfectly clean return manifest of this workstream: the `out/**` non-determinism slip recorded at trail 139 and repeated at 143, 147 and 152 is gone, because the manifest was regenerated after the final run rather than before it. **Immutable denylist 7/7 byte-identical** (harness code plus `r1_`–`r5_reference`); the new `r6_reference/stub_server_r6.py` is **byte-identical to the R6 stub this repository integrated**, so the pin is genuine; stdlib-only; secret scan clean; shipped evidence **215/215** self-test and **34/34** witnesses, zero failures — Builder-authored self-claims, no suite run by Fable.

## 2. The five items, confirmed by reading

**Item 1** — every conversion in the outer handler is now gated on `published`, with `_absorb_post_durable` handling the post-durability tail explicitly. **Item 3** — `_rollback_capture` has an explicit *"nothing created, nothing to prove"* path; a failure before any name exists no longer runs a proof it cannot complete. **Item 4** — a `rollback_durable` flag mirrors the publication path's boundary, and a post-fsync close error becomes a **soft anomaly** on a new `storage_anomalies` list, distinct from the hard `storage_quarantine`. **Item 5** — quarantine now persists to `<data_dir>/storage_quarantine/<candidate>/`, so a restart cannot silently clear it. **Item 2/6** — red-before-green with the anti-evasion check stated explicitly: *both R7 probes are red against pinned R6 and green against R7, **with the injected fault firing identically on both***. That last clause is the check this workstream learned to demand, and the Builder applied it unprompted.

The four defect flags flip R6 → R7 (`ordinary_failure_with_durable_committed_evidence`, `preartifact_spurious_quarantine`, `post_rollback_fsync_spurious_quarantine`, `restart_bypasses_explicit_recovery` — all true → **false**) while `current_process_fail_closed` stays **true on both**, so the R6 behaviour did not move. Item 6's prepared-record/quota behaviour is shown side by side and is identical on both builds, the only difference being the new marker file *outside* `captures/`.

## 3. The Builder's judgement call — RULED: confirmed

`_absorb_post_durable` absorbs `KeyboardInterrupt` and `SystemExit` as well as ordinary exceptions. The Builder flags this rather than burying it: re-raising them would satisfy the *letter* of item 1, but would leave the transition stranded mid-commit with durable evidence and no in-memory record — **a worse contradiction than the one being fixed** — and would abort the verifier's own probe rather than answer it.

**Fable confirms.** The scope is a single `os.close` on a directory fd *after* durability is established; there is no remaining work in that tail for an interrupt to protect. Absorbing there and recording the anomaly is the behaviour that keeps evidence and state agreeing, which is the entire point of the finding. Recorded as Fable's ruling so the verifier can challenge it directly rather than infer it.

## 4. Fable's own over-correction, closed

Items 3 and 4 exist because Fable's trail-152 strict-fsync ruling was applied beyond its scope and Fable's structural review did not catch it (`45_` §2). Both are now closed. The ruling itself was never in dispute — the verifier concurred with it explicitly — and the corrective was a scoping boundary, not a reversal. Recorded as closed so the lesson stays attached to the review method rather than to the rule.

## 5. Disposition

**R7 STRUCTURALLY ACCEPTED and INTEGRATED** (5 added, 5 modified; `r6_reference/` accepted on the established precedent and added to the immutable denylist). Security posture **NOT independently verified**.

**Next: the verifier's re-check.** Fable's requested focus, following the Builder's own recommendation: (1) the loosened controls in items 3 and 4 — a control relaxed after being told it was too strict is exactly where an over-relaxation would hide; (2) the persisted quarantine marker's own failure modes, including what happens if the marker cannot be written; (3) the item-1 judgement call in §3, which is Fable's ruling and open to challenge; (4) that every R6-confirmed behaviour genuinely did not move.

**On this re-check the owner's hands-on POC session unblocks.** Nothing else in the gate is open.
