# 42 — Fable Dispositions: TASK-0005 R2 Re-Verification Findings (P2X-01..P2X-05)

**Input:** `41_ChatGPT_Scoped_Reverification_TASK-0005_R2.md` — **FAIL** (SHA-256 `b5b5fa2f9f4b5352b71f40c779da2169ec5991a29605857c003409a527c22dfd`; probe evidence `41A_` `34946638fa856999cbf3a21efe43cae6b7fd34882f972fc6fbdc7191cc78d3b3`; bundle `00c84050…8b3e42` verified). Mechanics "excellent" (51/51, 52/52, bundle clone/fsck, patch byte-identical, gate + validators + checker all reproduced). **P2W-01 and P2W-05 CLOSED.** Five new findings — bounded authority-binding corrections, all Builder-executable, no owner decision touched. **All five CONCUR, none contested.**

| Key | Finding | Disposition |
| --- | --- | --- |
| P2X-01 | Manifest binds the registry's snapshot label, not its content digest — two registries under one label diverge | **Concur** — bind the registry content digest |
| P2X-02 | Receipt purpose and authority version unenforced — a display receipt grounded a delete; version skew accepted | **Concur** — purpose matched to the consuming contract; identity fields must agree with the owning registry |
| P2X-03 | Schedule compare-and-swap optional — omission bypasses it | **Concur** — expected version mandatory on every change |
| P2X-04 | Run receipts not schedule-version-bound — a stale v1 receipt satisfied v2's deadline | **Concur** — receipts name their exact version/activation epoch |
| P2X-05 | Contradictory journal histories replay into authoritative state | **Concur** — replay validates transition invariants and refuses contradictory/orphaned/duplicated/incomplete histories; completes the durable-identity ruling: an authority that accepts a corrupt history is not an authority |

Ownership: all five Builder (TASK-0005 R3, packet `43_`). Gate state: FAIL standing; owner action: relay only.
