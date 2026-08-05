# 41 — Fable Disposition: R5 re-check (SEC-R4-01 still open) and the R6 correction

**Input:** `40_`/`40A_`/`40B_` + probe scripts, regression logs and source evidence (bundle SHA-256 `b60ae6663baf3c9fe3b1458c2231a6fda5216116e57177c33cd6565c1f1f7755`; internal `SHA256SUMS` **41/41 valid**). **Verdict: FAIL — SEC-R4-01 remains OPEN.** Concurred.

## 1. What R5 did fix, confirmed independently

The verifier confirms the ordinary post-link failure paths are now correct: no final file and no consumed quota at link failure, one-shot temp-unlink failure, and directory-open failure — and **the legitimate `prepared` record plus exactly one reserved-owner quota unit correctly survive** a failed committed registration, which is the nuance `39_` §3 flagged and which the verifier independently confirms was the right call. The same probes remain red against pinned R4. That part of the work stands.

## 2. What is still open, and why it is fair

The defect is now one level deeper: **a failure of the rollback itself is swallowed.** `stub_server.py:735` is `except OSError: pass` — so if removing the final link fails after a publication failure, the success-named `committed` record survives while the service returns the ordinary "capture-failed / not effective" response. That is the same authority contradiction SEC-R4-01 was opened to eliminate, displaced from the first-order path into the recovery path. Reading the code confirms it: the `finally` block releases the pool unit and then attempts unlinks inside a bare `except OSError: pass`.

Fable's honest assessment: this requires **two** cascading filesystem failures, and on a supervised localhost session with a healthy disk it is close to unreachable in practice. But the principle the verifier is defending is the one this whole program has been built on — *evidence must never assert something the service did not establish* — and "the cleanup failed silently" is exactly how that guarantee dies quietly. The correction is bounded, precisely specified, and touches no architecture. **Concurred without reservation.**

## 3. Two honesty notes recorded

- **The verifier did not independently confirm 178/178.** Its runner hit a 240-second command limit partway through the measurement-validator block. It confirms only the **R5-specific capture-publication block, 8/8**. The Builder's full self-test count therefore remains a Builder-authored self-claim, and is recorded as such rather than repeated as verified.
- **A labeling discrepancy, benign.** The Builder record's `105/105` and `4b0874…` describe its own earlier relay snapshot, while the outer Fable re-check packet carries 103 checksum entries and binds to `36fcd20d…`. The verifier verified the outer packet cleanly and calls this a context-labeling note, not tampering. Fable concurs and records it so a later reader does not mistake the two counts for a contradiction.

## 4. The R6 correction (issued as `42_`)

All seven of the verifier's required items, unchanged in substance: quota is not released until rollback is **proven**; cleanup failure becomes a distinct **storage-uncertain** result rather than being swallowed; when rollback cannot be established the service **quarantines and fails closed** rather than returning an ordinary ineffective claim; durable publication is set at the true boundary so a later directory-close error cannot downgrade a durable record; temp housekeeping is separated from publication so a temp problem after durable publication cannot roll back live state; and red-against-R5 / green-against-corrected tests for all four boundaries, with the verifier's own `chatgpt_r5_cleanup_rollback_probe.py` required green.

**No concurrency change. No contract change.** The architecture stays closed, as the verifier directs.

## 5. Note on proportionality, recorded for the owner

This is the sixth build round on throwaway apparatus. Fable's judgement is that this round is worth taking — the stub produces the evidence that decides n8n versus Zapier, and evidence that can silently contradict itself undermines the decision it exists to serve. **But the owner holds final authority**, and an alternative was put to him: accept the residual risk with a formal record and a runbook check, and start the hands-on session now. That option remains open on his word; this packet issues under the default of fixing it.
