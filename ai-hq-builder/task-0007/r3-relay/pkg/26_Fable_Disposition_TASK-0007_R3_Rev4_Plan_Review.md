# 26 — Fable Disposition: ChatGPT scoped confirmation of R3 / Revision 4

**Input:** `24_` + `24A_` (bundle SHA-256 `cfea844f36cd5e2ba36af3abb203926a6a3c12619dfea9c1e58291ebe8925ef8`; both files integrated byte-identical, hashes verified per basename since the verifier's checksum file again carries sandbox-absolute paths). The verifier reviewed the `TASK-0007_R3_Revision4_Packet.zip` at `887fbccc…11bbe3`, matching the trail-134 relay fingerprint.

**Verdict: FAIL on the R3 Task Packet gate — CONCURRED IN FULL on all four findings.**

## 1. What closed, and the one result worth recording

Five of the nine Rev-3 findings are now **closed**, and the verifier independently reproduced the thing Revision 4 was built to fix:

```text
Tree independently reconstructed from base_snapshot.tar
404d1914945494272c2f2304dc2ca5fb14887452
MATCH
```

That is the first time in this contract's history that a verification claim Fable wrote into a packet was independently reproduced by the reviewer. **R3Q-01 closed** (snapshot honest and reproducible, with the commit/ancestry boundary disclosed accurately), **R3Q-06 closed** at plan level (provisional state non-authoritative, committed-write failure fails closed), **R3Q-07 closed** at plan level (provider traffic cannot consume the owner pool; live-secret ceiling matches redaction capacity), **R3Q-09 closed** (Fable owns authority classification, Builder returns evidence), and **R3Q-02 substantially closed**. The verifier also listed ten accepted mechanisms to preserve (`24_` §5) — the selected direction is right; the remaining work is boundary correction, not redesign.

## 2. The four findings — all concurred, all genuine defects of Fable's making

**R4Q-01 — the governing packet depended on a packet it declared fully superseded.** Revision 4 said it superseded Revision 3 "in full," classified Revision 3 `superseded, required_for_task: false` in the authority manifest, and then relied on it for material requirements: *"the transition matrix is otherwise as Revision 3 specified," "other bounds unchanged from Revision 3," "everything Revision 3 required."* A Builder obeying the manifest cannot read it; a Builder obeying the packet must. That is a flat contradiction, and it is exactly the class of defect this program keeps finding in Fable's packets — an authority declared without checking what it actually rests on.

**Corrected in `25_`:** the packet is now genuinely self-contained. §A writes out, directly: the five-component submission identity and duplicate/reject semantics (A.1); the immutable artifact-registration record with lookup and refusal semantics (A.2); the complete capability transition table including **every invalid transition** (A.4); the exact state effects of every POC-1 route — including explicitly that provider receipt/refusal records are **corroborating evidence only and cannot mark an action delivered** (A.6); the prepared/committed evidence contract (A.7); and every limit, redaction rule, HMAC contract and quota (A.8). Fable verified by grep that **no normative dependency on any superseded packet remains**; the only surviving mentions of Revisions 3 and 4 are historical explanations of what changed and why.

**R4Q-02 — a valid `idea_ref` authorized content the owner never approved.** The sharpest finding of the four. Revision 4 granted the whole `owner_content` object `owner-authorized` status whenever a valid `idea_ref` was present, without requiring that content to match what the owner actually submitted. As the verifier puts it: *the reference authenticates the existence of an owner intake event, not the content presented later.* A provider holding a valid ref could rewrite the body, title, project or tags and have the altered material recorded as owner-authorized — the precise failure POC-2 exists to disprove, reintroduced by the mechanism meant to prevent it.

**Corrected in `25_` A.3:** `/owner/idea` now accepts the complete owner content, **canonicalizes and stores it server-side**, records `owner_content_digest`, and mints an `idea_ref` **bound to that stored record**. `/poc2/triage` **loads the owner content server-side** and triages that; a provider-carried copy is a convenience only and must canonicalize to the stored digest or be refused. Negative tests are required proving a valid ref paired with altered body/tags/title/project is refused and never appears as owner-authorized.

**R4Q-03 — "positive negative evidence" was still two forms of local absence.** Revision 4 stated the correct principle — absence of a local record is not proof no external action occurred — and then defined the check as the service's own ledger *plus* absence from its own capture log. Both local. It did not exclude the exact failure it was written to address.

**Corrected in `25_` A.5, binding:** **local absence may produce only `UNCERTAIN`.** `/poc1/reconcile` (provider-facing) may return `RECONCILED_DELIVERED` when a service-owned receipt exists, or `UNCERTAIN` otherwise, and **can never return `RECONCILED_NOT_DELIVERED`**. That state is reachable only through owner attestation on the protected surface, since this POC includes no independently authoritative downstream query. The required negative test is the verifier's own: remove every local receipt after a simulated uncertain external completion and prove **no retry becomes authorized**.

**R4Q-04 — `evidence_ref` proved file existence, not the measurement.** Revision 4 called an evidence reference resolvable if the named file merely existed, so `poc/data/captures/README.md` could be cited for every result. **Corrected in `25_` §D:** evidence is now a **record** carrying candidate, poc, measure_id, observed value, unit, observed_at, collector, and the artifact/capture hash, and the validator must confirm those **match the measurement tuple and value**. `UNSUPPORTED` requires capability-gap evidence naming the same candidate, poc and measure. Path existence survives only as a preliminary integrity check.

## 3. Pattern, stated honestly

Five consecutive revisions have each been corrected by review: Rev 1 incomplete contracts · Rev 2 delegated architecture · Rev 3 unsound selected mechanisms · Rev 4 unsound boundaries on sound mechanisms · now Rev 5. The trajectory is real and measurable — nine findings became four, five findings closed outright, and the verifier's own summary is that the selected direction is accepted and only boundaries need correcting. But the recurring shape is unchanged and worth naming without softening: **Fable keeps asserting an authority without tracing what it actually rests on.** R4Q-01 (a governing packet resting on a superseded one), R4Q-02 (a reference standing in for content it never bound), R4Q-03 (absence standing in for proof), and R4Q-04 (a filename standing in for provenance) are four instances of one error in a single revision.

`25_` was written against that specific failure mode: every authority claim in it was traced to what establishes it, and the self-containment claim was **verified by grep before shipping** rather than asserted. That is the same discipline that made Rev 4's snapshot claim survive review — the first Fable verification claim the verifier successfully reproduced.

## 4. Returned to the verifier (minor, repeat)

`SHA256SUMS_TASK0007_R3_REV4_PLAN_REVIEW.txt` again lists absolute sandbox paths (`/mnt/data/...`), so `sha256sum -c` fails on any other machine. Integrity was confirmed per basename, both files matching. Second occurrence; non-blocking, noted only because relay integrity is checked in both directions.

## 5. Sequencing

`25_` (Revision 5) goes to **ChatGPT first** for the narrow Revision-5 confirmation; **Builder release stays held** until it returns. Serial order has now prevented four Builder releases against a failing contract — the cost has been Fable's rework rather than wasted build cycles, which is the trade it was adopted to make. On confirmation: Builder implements R3 against the integrated R2 baseline → Fable structural verification → the single independent security review of the final R2+R3 stub → owner POC session. Nothing accepted reopens: Release-1, the Capability Portfolio work, the Decision Engine baseline, v1.4, and the R1/R2 security dispositions all stand.
