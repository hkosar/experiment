# 14 — TASK-0007 Round R2: stub rework (security + evidence integrity) and the Release-1 scenario re-aim

**Context.** R1 (`08_`) is structurally accepted and integrated (40/40 hash-verified, trail 126). Its two mandatory refusals work, and your own adversarial pass found and fixed eight defects before shipping — including the token-lifecycle bug and the self-approval bypass — which is the reason this round is narrow rework rather than a rebuild. Under the owner's trail-127 practice the stub's security properties then went to the independent verifier, which returned **FAIL** on the end-to-end approval boundary with eight findings (`12_`, `12A_`). Fable's disposition (`13_`) concurs with all eight, corrects four of them, and adds seventeen findings the review did not reach — most of them evidence-integrity defects rather than security defects.

**Read `13_` before starting.** It carries the reasoning, the line citations, and four corrections (`VC-01`..`VC-04`) where the verifier's stated repro or proposed fix is wrong. In particular **do not implement `SEC-R1-01`'s correction as literally written** — it would break POC-3 (see `13_` §3 VC-03 and C-4 below).

**Two work items merge into this one round.** The security/evidence rework and the Release-1 scenario re-aim (`09_` §2) were sequenced separately on the assumption that R1's endpoints were scenario-neutral. `13_` FAB-15 falsifies that: the stub carries no task identity, no artifact digest and no target role, so `09_` §2's POC-1 cannot run against it regardless of the security findings. Both work items change the same handlers and the same contract, so they ship together. The contract below is settled — implement against it rather than deriving it.

**Nothing accepted reopens.** Provider selection, `09_`'s Release-1 definition, the Decision Engine design, the v1.4 baseline, and `13B_`'s production-wrapper scope are untouched. This remains throwaway POC apparatus and still earns no Track B credit — keep every THROWAWAY marker.

## 1. Work items

- **A — Security corrections.** `SEC-R1-01`..`SEC-R1-08` and `DOC-01`, as dispositioned in `13_` §2 (not as literally stated in `12_` where `13_` corrects them).
- **B — Evidence integrity.** `FAB-01`..`FAB-17` from `13_` §4.
- **C — Release-1 re-aim of the stub contract.** The identity tuple, target roles and capability binding `09_` §2 requires (C-1..C-4 below).
- **D — Workflow definitions and runbooks.** Re-aim `poc/workflows/n8n/*.json` and the Zapier build specs to `09_` §2's POC-1/POC-2 scenarios against the corrected contract; update the three runbooks, including the two corrections in `13_` §2.2 that would otherwise break the owner's session on step one.

## 2. The corrected endpoint contract (authoritative for this round)

Where this section and any earlier document disagree, this section governs. Shapes are specified; implementation is yours.

**C-1 — Identity tuple.** `/poc1/review-case` accepts and binds the five components `09_` §2 R1P-04 requires: task/workflow ID, stage/expected transition, artifact content digest, target **role**, and submission epoch. All five required; a missing or malformed component is a captured 400 refusal. The idempotency key derives from all five. A raw archive hash alone is explicitly **not** sufficient identity.

**C-2 — Target role, never target URL.** The request declares a symbolic `target_role`. The service resolves role → endpoint from its own table; it never takes a destination from the request (keep R1's control, and its comment). An unknown or unauthorized role is a **captured REJECT**, distinguishable in both the response and the capture from a duplicate-suppression success — this is R1P-04 test (3) and the distinction is the whole test.

**C-3 — Execution capability, POC-1 relay path only.** On authorization, mint a single-use capability bound to the ActionRequest ID, case ID, resolved target endpoint, canonical payload digest, and a short lifetime. The relay sink fails closed without it, refuses a payload whose digest does not match the binding, and refuses an expired one. **Replay returns the prior receipt** marked replayed with an explicit no-second-side-effect field, rather than a bare refusal — that satisfies R1P-04 test (4) and `12_` §5 test 3 while remaining honest about provider retries. Every attempt is captured; attempt and delivery must stay separately countable, because "how often did the provider retry" is a provider-discriminating measurement and a fix that stops recording attempts converts it into a stub self-test.

**C-4 — POC-3 staging is a separate, retry-tolerant path.** POC-3 has no case, no owner decision and no ActionRequest; it must not require a POC-1 capability, and its stage target must not share POC-1's single-use semantics (`13_` VC-03). Give it its own stage identity, tolerant of the retry-after-kill the round deliberately induces, and file its captures under POC3 (FAB-11).

**C-5 — Decision terminality and atomicity.** The first valid owner decision is terminal: a second for the same case is a captured 409 refusal. Decision lookup and token consumption occur in one critical section against an immutable decision record; no unlocked read may gate an authorization.

**C-6 — Capture-before-commit, at every transition.** Write the capture to a temporary file in the destination directory, flush, fsync, atomically rename, and only then commit in-memory state. On any capture failure, refuse with a structured error and commit nothing. This applies to the owner-decision path **and** to the token-spend path (FAB-04) — the second is the more damaging of the two, because a consumed token cannot be un-consumed. Note the ordering hazard in `13_`: adding a generic exception boundary (C-16) *before* this fix makes the failure quieter without making it safer.

**C-7 — Capture identity and provenance.** Filenames must not collide across process lifetimes — carry a per-process run instance in the name, or create exclusively and retry; never silently truncate an existing record. Each record body carries a stub-minted `recorded_at` explicitly labelled as a local wall clock with no authority (keep the header's honesty), the run instance, the originating route, and an `authored_by` classification of `owner-surface` / `provider` / `stub`.

**C-8 — Candidate namespace.** The candidate is a required, name-validated startup argument; refuse to start without it rather than defaulting, since a defaulted candidate is worse than none. Thread it through every capture path and into every record body, matching the layout `data/captures/README.md` already specifies.

**C-9 — Capture content allowlist and provenance split.** Per-endpoint allowlisted fields. Unknown fields are reduced to name, type, byte length and a non-reversible digest rather than persisted verbatim. Provider-supplied content lives under one reserved key; the top level is reserved for stub-minted fields, so no provider-authored object can read as a stub-authored record.

**C-10 — Redaction, corrected in both directions.** Add exact-value scrubbing: compare candidate strings *and their substrings* against active token digests and the owner key by constant-time comparison before anything reaches a log or a capture — whole-value comparison alone is defeated by concatenation. **Simultaneously stop over-redacting** (FAB-05): anchor key-name matching to whole underscore-separated segments so `authority_id`, `authority_version`, `tokens_used` and `session_id` survive, and keep an explicit non-secret allowlist for the D-EC_ field names in `harness/receipt_conformance.py`'s REQUIRED table. Where a value genuinely must be withheld, emit a structured marker carrying name, type, length and digest — never a bare constant, which the harness currently scores as PRESENT and thereby hides the loss. These two directions pull against each other; a change to either must be tested against both.

**C-11 — Boundary checks as a dispatch default.** Apply the provider-decision refusal and the partition/envelope checks at dispatch for every POST route, with an explicit commented exemption list, rather than per-handler opt-in. Three of thirteen routes carry them today (FAB-06, `13_` VC-02).

**C-12 — Capture on refusal, by default.** Every refusal path writes a capture, including the owner-key refusal, the verify-pending branch, and the boundary 400s (FAB-01). Never capture key material itself — record that a decision was attempted without owner authority, not what was presented.

**C-13 — Run identity.** Mint the run identity server-side, or refuse a duplicate declaration with a captured 409 that preserves the prior record's start and checkpoint count. A duplicate run-started is itself a POC-3 measurement — record it, never overwrite with it. Any provider-supplied correlation value is kept in a separate, explicitly provider-marked field and never used as the anchor.

**C-14 — Attestation honesty.** No response or capture may assert a check the service did not perform (FAB-08). The reconcile path either performs a real post-state check against recorded state or returns an explicit not-checked marker with the ACT-01 citation removed. The triage path must not assert provider conduct it cannot observe. `h_poc3_receipt`'s existing note is the correct posture — apply it uniformly.

**C-15 — Transport hardening.** Enforce `0 <= Content-Length <= MAX_BODY`; reject negative values, duplicate or conflicting length headers, and unsupported transfer encodings. Add a handler socket timeout — and note it also closes the connect-and-send-nothing case, which no length bound can reach. Require a JSON content type. Give provider-facing routes a per-process provider credential, distinct from the owner key and conferring **no** owner authority. Bound case, receipt and capture counts.

**C-16 — Exception boundary and type validation.** Wrap route dispatch so any handler exception becomes a structured refusal with no traceback in the response. Validate nested types before use — and note `13_` VC-01: the crash needs a **truthy** non-dict, so a test using an empty list passes against unfixed code. Guard comparison-primitive operands for type and charset (FAB-13). Cap recursion depth in redaction.

**C-17 — Logging.** Log a route-matched constant plus the status, and nothing caller-supplied, under any path — including unmatched routes, malformed request lines, and secrets placed in the path rather than the query (`13_` VC-04; neither remedy in `12_` §3 closes this). Add no-store cache headers to owner-surface responses.

**C-18 — Advertised endpoints derive from the bound port**, with an explicit override argument for the container case the n8n runbook sets up. No second hardcoded literal anywhere (FAB-12).

**C-19 — Owner key handling.** The startup banner must not print a copyable command containing the key. Apply the same read-into-a-shell-variable pattern at all three runbook sites named in `13_` §2.2, watching the single-vs-double quoting.

## 3. Required tests

All must ship in the self-test, each **demonstrated failing against the unfixed behaviour** — that is the standard R1 met and this round keeps.

**From `09_` §2 R1P-04 (already verifier-approved as the acceptance spec):** (1) same artifact, same task, same transition → suppress reprocessing and return the prior receipt; (2) same artifact, different task → process independently; (3) same task and artifact, different unauthorized target → **REJECT**, distinguishable from duplicate-success; (4) replayed owner decision token → no second relay; (5) uncertain provider result → reconcile before any second side effect.

**From `12_` §5:** direct relay-sink call without a capability → refused; capability with altered action ID, target, payload or case → refused; capability replay → prior receipt, no second side effect; resume token under arbitrary and Unicode-confusable keys → absent from every capture and log; second owner decision → refused; capture-write failure during a decision → neither decision nor authorization survives; malformed nested metadata and deeply malformed JSON → structured refusal, service healthy; negative length, unsupported transfer encoding and slow-body → prompt refusal or timeout; query strings and paths containing secrets → absent from logs; browser-simple cross-origin-shaped POST without the provider credential → refused.

**From `13_` §4, additionally:** both mandatory refusals produce capture records; a restart does not overwrite a prior run's captures; two candidates produce separately attributable corpora; a token-spend capture failure leaves the token unspent; `authority_id`, `authority_version` and `tokens_used` survive redaction intact while a live token under a benign key does not; a provider-authored decision field is refused on every persisting route; a duplicate run declaration preserves the prior record; the reconcile path does not assert an unperformed check; every capture carries a stub-minted timestamp; a truthy non-dict nested value yields a structured refusal.

## 4. Allowlist

`poc/stub/**` · `poc/workflows/n8n/*.json` · `poc/workflows/zapier/POC_zap_build_specs.json` (added this round — the re-aim and the contract change both reach it) · `poc/runbooks/RUNBOOK-n8n.md`, `RUNBOOK-owner-session.md`, `RUNBOOK-zapier.md` · `poc/README.md` · `poc/FINDINGS.md` · `poc/data/captures/README.md` and `poc/data/measurements.template.json` (only where the contract or measure set changes). Nothing else; no `ai-hq` file outside `poc/`.

`harness/**` is **not** in the allowlist. If a corrected capture shape requires a harness change, stop and report it as a change request rather than editing — the harness is the instrument the evidence is scored with, and it changes under its own round.

## 5. Return requirements

Standard Delivery Record with the reflexive falsifier element. Self-test covering §3 with the mandatory cases shown failing first. Diffs for every workflow and runbook change, with the structural harness re-run. One zip, manifest self-verified, H-06 on this snapshot before work begins.

**Report, do not silently absorb:** any place where this contract is internally inconsistent, conflicts with `09_` §2, or cannot be satisfied without touching something outside the allowlist. R0's fail-closed stop on Fable's packaging error was the correct behaviour and is the behaviour wanted again — `13_` §6 records that R1's brief being too narrow was a Fable defect, and this packet is longer precisely so that class of gap is visible before you build rather than after.

## 6. After R2

R2 return → Fable structural verification → the corrected stub's adversarial re-verification goes to **ChatGPT** as an independent review under the trail-127 practice, carrying `13_`'s four corrections (`VC-01`..`VC-04`) and any further probes it directs, which you or Fable execute and return to it. Fable assembles and dispositions; Fable does not run the probes. On that closing, the owner's hands-on POC session runs the re-aimed content against a stub whose evidence output can be trusted.
