# 25 — TASK-0007 R3 Task Packet, Revision 5 — the complete, self-contained contract

**Status of prior revisions:** `17_` (Rev 2), `20_` (Rev 3) and `22_` (Rev 4) are **superseded and are NOT instruction**. They remain in the repository as history only. **This document is the entire contract.** It has no normative dependency on any superseded packet — that was R4Q-01, and §A below exists to close it: every requirement previously reachable only through Revision 3 is written out here.

**Reference (read for reasoning, never as instruction):** `26_` (Fable's disposition of the Rev-4 review), `24_`/`24A_`, `21_`, `18_`, `15_`, `12_` (verifier findings); `23_`, `19_`, `16_`, `13_` (Fable dispositions); `09_` §2 (the authoritative D3 scenario definition); `08_` (the R1 instruction). Where any of them disagrees with this document, **this document governs.**

**Nature of the round:** an increment on the integrated R2 stub baseline. Throwaway POC apparatus, no Track B credit, every THROWAWAY marker preserved. **Baseline status, verbatim wherever described:** *"R2 is structurally integrated as the implementation baseline; its security claims remain Builder-authored and unaccepted until the final independent review of the R2+R3 stub."*

**Governing rule:**

> Every authority the service asserts must trace to something the service itself established. A value a caller supplied is corroborating material, never an authority.

Revisions 3 and 4 each broke this rule inside the document that stated it. **If any clause here asserts an authority not rooted in something this service established, that is a defect — stop and report it before building.**

---

## 0. Snapshot, authority manifest, allowlists

**Snapshot (accepted at Rev 4, unchanged).** The relay carries `base_snapshot.tar` and `BASE_BINDING.txt`; there is **no git bundle and no clone instruction**, because this working repository is a shallow clone (graft at `18c571b`, whose parent `ffd5cc6c` does not exist locally) and a complete `fsck`-clean bundle cannot be produced from it at all. `BASE_BINDING.txt` declares the base commit and tree and states the boundary exactly: the **tree** is independently verifiable by `tar -x` → `git init -q .` → `git add -Af .` → `git write-tree`; the **commit** is declared only, with no ancestry included. Fable executes that recipe against the shipped artifact before every relay.

**Authority manifest (accepted at Rev 4, unchanged).** `authority_manifest.json` is **published by Fable**, never by the Builder. The Builder returns `RETURN_MANIFEST.json` (evidence-only) and MAY include `proposed_classifications.json` as a suggestion. `instruction_authority` values: **governing** (this packet, the only instruction) · **reference** (read, not instruction) · **superseded** (history, never executable) · **evidence-only** (never instruction) · **none** (implementation baseline the Builder edits).

**Implementation allowlist** (Builder MAY modify): `poc/stub/stub_server.py` · `poc/stub/selftest_stub.py` · `poc/stub/r1_witnesses.py` · `poc/workflows/n8n/*.json` · `poc/workflows/zapier/POC_zap_build_specs.json` · `poc/runbooks/*.md` · `poc/README.md` · `poc/FINDINGS.md` · `poc/data/captures/README.md` · `poc/data/measurements.template.json` · `poc/data/validate_measurements.py` (new).

**Control/evidence** (regenerate by running, never hand-edit): `poc/harness/out/**` · `poc/stub/out/**`.

**Immutable denylist** (a diff fails the round): `poc/stub/r1_reference/stub_server_r1.py` · all `poc/harness/*.py`, `*.mjs`, `run_all.sh` · `authority_manifest.json`.

---

## §A — Normative contract (self-contained; closes R4Q-01)

Everything in §A is governing. Nothing here requires reading a superseded packet.

### A.1 Submission identity (five components)

The stable submission identity for POC-1 is derived from **all five** of:

```text
task_id            string, non-empty
transition         string, non-empty   (the stage/expected transition)
artifact_digest    64-hex               (content digest; a raw archive hash alone is NOT identity)
target_role        string, non-empty    (a known, authorized role)
submission_epoch   non-negative integer
```

`idempotency_key = sha256(canonical_json({task_id, transition, artifact_digest, target_role, submission_epoch}))` with sorted keys and no whitespace. Any missing or malformed component is a **captured 400 refusal**. The idempotency key **travels in the ActionRequest payload to the target**, not only on the envelope.

**Duplicate semantics.** Same five components ⇒ same identity ⇒ **suppress reprocessing and return the prior receipt** (`reprocessed: false`), captured as `duplicate-suppressed`. Same artifact under a **different `task_id`** ⇒ distinct identity ⇒ processes independently. An **unauthorized `target_role`** ⇒ captured **403 REJECT** (`rejected-unauthorized-target`), which must be distinguishable in both response and capture from duplicate-suppression success. An **unknown role** ⇒ captured 400 (`rejected-unknown-target`).

**Target roles.** The service resolves role → endpoint from its **own** table and never takes a destination from the request. Authorized roles for this round: `integration-owner`, `verifier`, `reader` (all resolving to the relay route). Declared-but-unauthorized: `owner`, `release-executor`.

### A.2 Artifact registration (owner-authoritative; the artifact root of trust)

**`POST /owner/artifact/register`** — owner key required. Accepts:

```text
source_digest   REQUIRED 64-hex   the AUTHORITATIVE artifact identity; IMMUTABLE once registered
size_bytes      REQUIRED non-negative int
file_count      REQUIRED positive int      (archive member count, else 1)
task_id         REQUIRED string
transition      REQUIRED string
target_role     REQUIRED string, must be an authorized role (A.1)
```

Mints and returns `artifact_id` (`"art-" + 12 hex`) and `registration_ref` (`"reg-" + token_urlsafe(24)`) — the opaque value the provider may carry. **Registration identity** = `sha256(source_digest | task_id | transition | target_role)`. Re-registering the same identity is **idempotent**: return the existing `artifact_id`/`registration_ref`, never a second record. A re-registration differing **only** in `target_role` is a **distinct** registration, not a silent role change.

**Lookup and refusal semantics at `/poc1/review-case`.** The request carries `registration_ref` (REQUIRED) plus the five identity components. The service loads the registration and enforces: `task_id`, `transition`, `target_role` **equal** the registered values, and `artifact_digest` **equals** the registered `source_digest`. Any mismatch ⇒ captured **403** `rejected-artifact-binding`. An unknown or expired `registration_ref` ⇒ captured **403**. A provider-supplied digest is therefore only ever *checked against* the owner-registered one and never trusted alone.

### A.3 Owner-idea authority, bound to canonical content (closes R4Q-02)

Rev 4's `idea_ref` authenticated only that an owner intake event happened — a provider holding a valid ref could alter `title`/`body`/`project`/`tags` and have the altered material recorded as owner-authorized. Corrected:

**`POST /owner/idea`** — owner key required. Accepts the **complete** owner content schema:

```text
owner_content { title: str, body: str, project: str|null, tags: [str] }
```

The service **canonicalizes** it (sorted keys, no insignificant whitespace, UTF-8), **stores it server-side**, records `owner_content_digest = sha256(canonical)`, and mints `idea_ref` (`"idea-" + token_urlsafe(24)`) **bound to that stored record and digest**.

**`POST /poc2/triage`** accepts:

```text
idea_ref        optional (Case A). Authority derives ONLY from this.
owner_content   OPTIONAL and, if present, purely a convenience copy:
                it MUST canonicalize to the stored owner_content_digest or the
                request is REFUSED (captured 403). It NEVER replaces stored content.
external_items  optional array (0..MAX_LIST_ITEMS); EACH item:
                  { envelope: {partition: "business", trust: "external-untrusted"},  REQUIRED PER ITEM
                    source: str, content: str|object }
```

Rules, structural rather than narrative:

- With a valid `idea_ref`, the service **loads the owner content server-side** and triages *that*. Provider-authored replacement content is never used.
- `owner_content` present **without** a valid `idea_ref` ⇒ captured 403; never owner-authored.
- Every `external_items[i]` **requires its own envelope**; missing or non-conforming ⇒ captured 400. An item **never** inherits authority from the enclosing idea — `instruction_authority: none`, always, per item.
- Case B (no `idea_ref`) ⇒ the top-level external-untrusted envelope is required; authority `none`; classification and summary only.
- The capture records authority **per component** (`owner_content` → `owner-authorized`; each external item → `none`, with its own source). A single flattened authority value for the whole request is a defect.
- Any `origin` field in the payload is **ignored for authority** and recorded as provider-supplied.

### A.4 Capability state machine (complete; valid and invalid transitions)

States: `MINTED`, `ATTEMPT_STARTED`, `DELIVERED_WITH_RECEIPT`, `UNCERTAIN`, `RECONCILED_DELIVERED`, `RECONCILED_NOT_DELIVERED`, `REVOKED`, `EXPIRED`.

| From | To | Trigger | Who may effect it |
| --- | --- | --- | --- |
| — | `MINTED` | `/poc1/verify-decision` succeeds on a **terminal owner accept** | service only |
| `MINTED` | `ATTEMPT_STARTED` | first `/relay/deliver` with matching capability, binding and payload digest | provider bearing the capability |
| `ATTEMPT_STARTED` | `DELIVERED_WITH_RECEIPT` | delivery completes; service mints the receipt | service only |
| `ATTEMPT_STARTED` | `UNCERTAIN` | delivery result ambiguous (provider reports uncertain, or timeout) | service only |
| `UNCERTAIN` | `RECONCILED_DELIVERED` | a **service-owned** receipt exists for the `action_request_id` | service only |
| `UNCERTAIN` | `RECONCILED_NOT_DELIVERED` | **owner attestation** (A.5) or an independently authoritative downstream negative | owner surface only |
| `RECONCILED_NOT_DELIVERED` | `ATTEMPT_STARTED` | **exactly one** re-attempt, same idempotency identity, new attempt id | provider, once |
| `MINTED` / `ATTEMPT_STARTED` / `UNCERTAIN` | `EXPIRED` | `CAPABILITY_TTL_S` elapses | service |
| any non-terminal | `REVOKED` | `/owner/revoke` | owner surface |

**Terminal:** `DELIVERED_WITH_RECEIPT`, `RECONCILED_DELIVERED`, `REVOKED`, `EXPIRED`. `RECONCILED_NOT_DELIVERED` is terminal unless the single permitted re-attempt is taken.

**Invalid transitions — each a captured refusal with no state change:** `/relay/deliver` on `EXPIRED` or `REVOKED`; a second *distinct* delivery from `DELIVERED_WITH_RECEIPT`; a second re-attempt after `RECONCILED_NOT_DELIVERED`; any transition to `RECONCILED_NOT_DELIVERED` without owner attestation; any provider attempt to set a state directly; a **late provider receipt on `REVOKED` or `EXPIRED`** (captured, refused, changes nothing).

**Replay:** a repeat `/relay/deliver` returns the **prior receipt** with `replayed: true` and `no_second_side_effect: true` **only** from `DELIVERED_WITH_RECEIPT` or `RECONCILED_DELIVERED`. From any other state it is refused or routed to reconciliation — never a silent second delivery.

**Identities:** `attempt` is a per-`action_request_id` counter, **separate** from submission identity; provider retries increment `attempt` and never create a new submission. Delivery `receipt_id` is minted once, by the service, on first delivery.

**Capability binding** covers: submission identity (`idempotency_key`), `action_request_id`, `case_id`, resolved target endpoint, canonical payload digest, candidate, and expiry. A mismatch on any ⇒ captured 403.

**Restart posture (honest):** capability state is in-memory and does **not** survive a restart; a relay bearing a pre-restart capability **fails closed**. The capture log reconstructs transition *history* for audit; it never restores *authority*. Do not add durable capability persistence — that would pretend to be the AI OS journal.

### A.5 Reconciliation — local absence is never proof (closes R4Q-03)

Rev 4 defined "positive negative evidence" as the service's own ledger **plus** absence from its own capture log — two forms of **local absence**, which cannot rule out the very failure being addressed (an external side effect completed, then the service died before recording it). Corrected, and binding:

> **Local absence may produce only `UNCERTAIN`.** `RECONCILED_NOT_DELIVERED` is reachable **only** through (1) an owner attestation on the protected owner surface, or (2) a separately defined, independently authoritative downstream idempotency/status query that positively reports no delivery for the exact idempotency identity. **This POC includes no such downstream authority**, so in practice route (1) is the only path.

- **`POST /poc1/reconcile`** (provider credential) returns **only** `RECONCILED_DELIVERED` (when a service-owned receipt exists) or **`UNCERTAIN`**. It **must not** return `RECONCILED_NOT_DELIVERED`, and it never accepts a provider-asserted outcome.
- **`POST /owner/reconcile`** (owner key) records the owner attestation and is the only route that may reach `RECONCILED_NOT_DELIVERED`.

> `/owner/reconcile` is valid only while the subject is `UNCERTAIN` and only when `outcome` is the literal `not_delivered`. A valid request records the owner attestation and transitions to `RECONCILED_NOT_DELIVERED`. Any other outcome value, any other source state, or any attempt to use the route to create `RECONCILED_DELIVERED` is a captured refusal with no state change. An owner who wants to prevent further action without attesting non-delivery uses `/owner/revoke`.
- **`POST /owner/revoke`** (owner key) moves a non-terminal capability to `REVOKED`, terminal.

`UNCERTAIN` is an acceptable terminal outcome for this POC. A wrong `RECONCILED_NOT_DELIVERED` is not: it would authorize a duplicate real-world action, the exact failure POC-1 exists to disprove.

### A.6 State effects of every POC-1 route (explicit)

- `/owner/artifact/register` — creates the immutable registration (A.2). **Owner-authoritative.**
- `/poc1/review-case` — validates registration binding + identity, opens a case, mints the opaque resume token. The provider receives **the token only** — no case id, no case content, no decision.
- `/owner/cases` — owner-only listing.
- `/owner/decide` — the **only** origin of a decision. First valid decision is **terminal**; a second is a captured **409**. Decision lookup and token consumption occur in **one critical section** against an immutable decision record.
- `/poc1/verify-decision` — accepts **`token` only**; any additional key is a captured 403 recording the **count**, never the key names (a live token can be smuggled in as a key). No owner decision ⇒ captured `pending` refusal, token **not** consumed. Owner reject ⇒ token consumed, `authorized: false`. Owner accept ⇒ ActionRequest + capability minted, **capture written before the token is spent**.
- `/relay/deliver` — the POC-1 side effect; **fails closed without a valid capability**; enforces every binding in A.4.
- `/poc1/receipt` and `/poc1/refusal` — **corroborating evidence only.** They record what the provider reports and **cannot** mark an action delivered, alter capability state, or satisfy any acceptance check. A `provider_status` of `ok` is a provider claim, never a service conclusion.
- `/poc1/reconcile` — per A.5.
- `/health` — liveness only; exposes **no** case, decision, or capture-activity counts.

### A.7 Evidence: prepared → committed (fault-safe)

For every **authority-bearing** transition — owner decision, token spend, capability mint, capability spend/delivery, reconciliation, and each POC-3 run-started/checkpoint/reconcile — write append-only:

1. a **`prepared`** record `{transition_id, transition, prior_status, intended_status, phase: "prepared", recorded_at, links}` **before** mutating state;
2. mutate in-memory state **marked provisional** (invisible to every authority check);
3. a **`committed`** record `{transition_id, phase: "committed", final_status, recorded_at}`, then clear the provisional flag — only now is the state authoritative.

> **An authority-bearing transition becomes effective only when its `committed` record has durably landed.** If the committed write fails, the in-memory change is **rolled back**; if rollback is impossible, the subject enters an explicit non-authoritative `UNCERTAIN` that fails closed to every authority check.

`transition_id = "txn-" + token_hex(8)`. **Only a transition with a matching `committed` record satisfies an acceptance check**; an orphan `prepared` is reported **uncertain**, never complete, and is resolved through `/owner/reconcile` or `/owner/revoke` (so "permanently stuck" is not an outcome). Lower-stakes single-phase records (provider receipts/refusals, boundary and auth refusals) carry no authority and gate nothing.

Every capture is written durably — temp file in the destination directory, flush, `fsync`, atomic rename — and carries stub-minted `candidate`, `run_instance`, `route`, `authored_by` (`owner-surface` | `provider` | `stub`), `poc`, `step`, and `recorded_at` labelled as a local wall clock with **no** clock authority. Filenames must not collide across process lifetimes (per-process run instance, exclusive create). Provider-supplied content lives under a single reserved provenance key; the top level is reserved for stub-minted fields. Every refusal path captures, including the owner-key refusal, the `pending` branch, and boundary 400s — recording that an attempt occurred, **never** the material presented.

### A.8 Limits, redaction, quotas (complete)

```text
MAX_BODY 1 MiB          MAX_REDACT_DEPTH 12       MAX_OBJECT_FIELDS 256
MAX_LIST_ITEMS 1024     MAX_STRING_BYTES 65536    MAX_ACTIVE_SECRETS 512
MAX_CASES 5000          MAX_IDEAS 5000            MAX_TOKENS 5000
MAX_DECISIONS 5000      MAX_ATTEMPTS_PER_AR 100   MAX_RECEIPTS 5000
MAX_RUNS 5000           MAX_CHECKPOINTS_PER_RUN 1000
MAX_CAPTURES 20000      CAPABILITY_TTL_S 300      SOCKET_TIMEOUT_S 10
```

A payload exceeding a structural bound ⇒ captured 400 **before** handler dispatch.

**Redaction, corrected in both directions.** Key-name matching is **whole-segment** (never unanchored substring), with an explicit non-secret allowlist that must preserve the D-EC_ REQUIRED names (`receipt_id`, `subject_ref`, `executed_at`, `occurrence`, `schedule_version`, `purpose`, `authority_id`, `authority_version`, `content_hash`, `action_request_id`, `action_class`, `scope`, `policy_version`, `risk_class`, `idempotency_key`, `side_effect_status`) plus `tokens_used`, `task_count`, `execution_count`, `session_id`. Exact-value scrubbing compares candidate strings **and their substrings** against live secrets by constant-time comparison (whole-value comparison alone is defeated by concatenation). A withheld value becomes a **structured marker** `{"__withheld__", "name", "type", "bytes", "hmac"}` — **never** a bare constant, which the harness would score PRESENT and thereby hide the loss.

**Descriptor HMAC:** `HMAC-SHA256(key = per-process random 32 bytes, generated at startup, never persisted; msg = canonical JSON of the value)`, hex, first 32 chars. Per-process keying prevents precomputation and cross-run correlation.

**Live-secret ceiling.** `MAX_ACTIVE_SECRETS` is a **hard ceiling on live secrets, not on the scan**: every live secret is always scanned. Minting a token or capability when the index is full is **refused** (captured 429). Secrets leave the index the moment they become unusable (token consumed, capability terminal). **Tested invariant:** no live token or capability exists outside the index, and all of them redact.

**Three disjoint capture pools.**

```text
general           70% of MAX_CAPTURES   provider receipts, ideas, checkpoints, stage, triage
security-refusal  15%                   refusals arising from provider-reachable routes
reserved-owner    15%                   owner-surface routes ONLY
```

**No provider-reachable event may draw from `reserved-owner` under any condition.** Exhaustion: general full ⇒ provider writes get a captured 429 recorded in the security-refusal pool; security-refusal full ⇒ further provider refusals increment a bounded in-memory counter and are not captured (exposed only as an aggregate, never per-case); reserved-owner full ⇒ owner writes get 507 and the service refuses further owner state changes rather than silently dropping evidence. All pools full ⇒ fail closed, `GET /health` still served.

**Transport and dispatch.** Every POST requires `application/json` and `0 ≤ Content-Length ≤ MAX_BODY`; negative lengths, conflicting duplicate length headers and non-identity transfer encodings are refused; a socket timeout closes connect-and-send-nothing. Owner routes require the owner key; provider routes require a per-process **provider credential** that confers **no** owner authority. Boundary checks (provider-decision refusal, partition/envelope) run **at dispatch** with an explicit, commented exemption list. A route dispatch exception becomes a structured refusal with **no traceback** in the response. Comparison primitives handle non-ASCII input rather than raising before a verdict. Logging emits a **route-matched constant plus status and nothing caller-supplied**, under every path including unmatched routes, malformed request lines, and secrets placed in the path. `Cache-Control: no-store` on all responses. Advertised endpoints derive from the **bound port**, with an explicit override for the container case.

---

## §B — Route-policy table (complete; implement as data)

**Unknown route or missing policy row ⇒ fail closed.** A new route requires a Fable-approved change request. All POSTs: `application/json`, body ≤ `MAX_BODY`, `Cache-Control: no-store`, capture on success **and** refusal.

| Route | Caller | Credential | Fields (exact) | Envelope | Decision field | Log label | Quota pool |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GET /health` | open | none | — | n/a | n/a | `GET /health` | none |
| `POST /owner/artifact/register` | owner | X-Owner-Key | source_digest, size_bytes, file_count, task_id, transition, target_role | exempt | refused | `POST /owner/artifact/register` | reserved-owner |
| `POST /owner/idea` | owner | X-Owner-Key | owner_content{title,body,project,tags} | exempt | refused | `POST /owner/idea` | reserved-owner |
| `POST /owner/cases` | owner | X-Owner-Key | — | exempt | refused | `POST /owner/cases` | reserved-owner |
| `POST /owner/decide` | owner | X-Owner-Key | case_id, decision | exempt | **allowed (only here)** | `POST /owner/decide` | reserved-owner |
| `POST /owner/reconcile` | owner | X-Owner-Key | action_request_id, outcome (literal `"not_delivered"`), note | exempt | refused | `POST /owner/reconcile` | reserved-owner |
| `POST /owner/revoke` | owner | X-Owner-Key | capability \| action_request_id, reason | exempt | refused | `POST /owner/revoke` | reserved-owner |
| `POST /poc1/review-case` | provider | X-Provider-Key | registration_ref, task_id, transition, artifact_digest, target_role, submission_epoch, envelope | **required** | refused | `POST /poc1/review-case` | cases |
| `POST /poc1/verify-decision` | provider | X-Provider-Key | token (only) | exempt | refused | `POST /poc1/verify-decision` | none |
| `POST /poc1/reconcile` | provider | X-Provider-Key | capability, action_request_id | exempt | refused | `POST /poc1/reconcile` | none |
| `POST /poc1/receipt` | provider | X-Provider-Key | action_request_id, case_id, provider_status ∈ {ok,error,uncertain}, provider_message (≤1024), destination_digest_claimed (64-hex\|null), provider_metrics{task_count,step_count,execution_count,tokens_used:int} | exempt | refused | `POST /poc1/receipt` | receipts |
| `POST /poc1/refusal` | provider | X-Provider-Key | action_request_id \| case_id, refusal_code (≤64), refusal_message (≤1024) | exempt | refused | `POST /poc1/refusal` | receipts |
| `POST /relay/deliver` | provider + **capability** | X-Provider-Key | capability, action_request_id, case_id, payload, destination_digest_claimed | exempt | refused | `POST /relay/deliver` | attempts |
| `POST /poc2/triage` | provider | X-Provider-Key | idea_ref, owner_content (convenience copy; must match stored digest), external_items[{envelope,source,content}] | **conditional** (Case B) | refused | `POST /poc2/triage` | ideas |
| `POST /poc3/run-started` | provider | X-Provider-Key | schedule_id, occurrence, provider_correlation_id | exempt | refused | `POST /poc3/run-started` | runs |
| `POST /poc3/checkpoint` | provider | X-Provider-Key | run_id, stage | exempt | refused | `POST /poc3/checkpoint` | checkpoints |
| `POST /poc3/reconcile` | provider | X-Provider-Key | run_id | exempt | refused | `POST /poc3/reconcile` | none |
| `POST /poc3/receipt` | provider | X-Provider-Key | run_id, occurrence, provider_status ∈ {ok,error,uncertain} | exempt | refused | `POST /poc3/receipt` | receipts |
| `POST /stage/deliver` | provider | X-Provider-Key | run_id | exempt | refused | `POST /stage/deliver` | stage-attempts |

Any field not listed for a route is reduced to a descriptor (A.8) under the provider-supplied provenance key and never reaches the top level.

**POC-3 specifics:** run identity is **stub-minted**; a duplicate declaration is a captured **409** preserving the prior `started_at` and checkpoint count (a duplicate run-started is itself a POC-3 measurement, never an overwrite). Any provider correlation value is carried separately, explicitly provider-marked, and anchors nothing. `/stage/deliver` is **retry-tolerant** by design — the round induces a mid-flight kill, and a single-use rule there would mis-score the provider retry POC-3 exists to measure. `/poc3/reconcile` compares only what the service actually recorded and states `external_post_state_checked: false`; it must never assert a check it did not perform. `/poc2/triage` must not assert provider conduct (`links_followed`, `actions_taken`) it cannot observe.

---

## §C — Artifact fidelity: what is and is not established

`destination_digest_claimed` is **provider-reported and explicitly non-authoritative**. It is recorded under the provider-supplied provenance key, **cannot satisfy any security gate**, and **must not gate delivery**. The capture records the owner-registered `source_digest` (authoritative), `destination_digest_claimed` (provider), and `destination_verified: false` with the reason *"this service does not receive destination bytes and cannot hash them."*

**End-to-end binary fidelity is NOT ESTABLISHED by this apparatus.** It is an owner-session observation (compare the delivered artifact against the registered `source_digest` out-of-band) and is recorded `UNSUPPORTED` by the validator unless the session supplies evidence. Two earlier tests ("correct digest, wrong bytes ⇒ relay fails"; "altered digest, same bytes ⇒ relay fails") are **withdrawn as unsatisfiable** and replaced by: *a provider-supplied destination digest never gates delivery, is always recorded as provider-authored, and never appears as a verified fidelity claim.*

---

## §D — Measurement evidence and validator (closes R4Q-04)

Rev 4 treated an `evidence_ref` as resolvable merely because the named file existed — so an unrelated file could be cited for every result. Corrected: **evidence is a record, bound to the exact measurement tuple.**

Each measurement carries `{status, value, evidence_ref}`. Each `evidence_ref` resolves to a **measurement-evidence record** containing:

```text
candidate          must equal the measurement's candidate
poc                must equal the measurement's poc
measure_id         must equal the measurement's measure_id
observed_value     must equal the measurement's value
unit
observed_at
collector          who/what produced it (owner session, harness, capture)
artifact_or_capture_hash   sha256 of the capture/output the observation came from
```

`poc/data/validate_measurements.py` (stdlib only; Builder authors it) enforces:

```text
MEASURED     -> value REQUIRED (non-null); evidence_ref REQUIRED, resolvable, AND the evidence
                record's candidate/poc/measure_id/observed_value MUST MATCH the measurement
NOT_TESTED   -> reason REQUIRED (non-empty)
UNSUPPORTED  -> reason REQUIRED AND capability_gap_evidence REQUIRED, naming the SAME
                candidate, poc, and capability/measure
```

It also **enumerates the full expected (candidate × POC × measure) matrix and fails on any missing combination**, so nothing disappears by omission. Path existence remains a preliminary integrity check, never the provenance rule. Exit non-zero on any violation. It judges completeness and provenance, never values.

**Required measure family:** artifact bytes · file count · source digest · destination digest **claimed** (non-authoritative, §C) · original-vs-reconstituted (**`UNSUPPORTED` by default**, with the destination-verification gap as its evidence) · provider task/step/execution count · owner-attention steps and minutes · approval latency · retry count · uncertain-result reconciliation outcome · capture/receipt completeness · provider retention/deletion observation · failure/unsupported-capability reason. No provider capability is claimed from authored workflow files alone.

---

## §E — Required tests

Demonstrated failing against the pre-R3 behaviour using the **witness method**: probes run against the SHA-pinned artifact (`r1_reference/stub_server_r1.py`, byte-identical, run-time pin verified, refusing to continue on mismatch), **never** defect switches. Where a test needs the R2 baseline, pin the R2 artifact the same way.

**Identity and registration:** duplicate suppression returns the prior receipt · same artifact + different `task_id` processes independently · unauthorized `target_role` REJECTS distinguishably from duplicate-success · re-registration differing only in `target_role` is a distinct registration · registration-binding mismatch (task/transition/role/digest) refuses · unknown `registration_ref` refuses.

**Owner-idea authority:** a valid `idea_ref` with **altered** `body`, `tags`, `title` or `project` is **refused** and never appears as owner-authorized · `owner_content` without a valid `idea_ref` is refused · an `external_items` entry lacking its own envelope is refused · a valid `idea_ref` never elevates an external item · per-component authority appears in the capture · changing provider-supplied `origin`/`trust`/`instruction_authority` never increases authority.

**Owner reconciliation (R5Q-01):** `owner reconcile with outcome="delivered"` → refused, no state change · `owner reconcile from a non-UNCERTAIN state` → refused, no state change · `owner reconcile with outcome="not_delivered" from UNCERTAIN` → accepted once · `replay of the same owner reconciliation` → prior result or refusal, never a second transition.

**Capability and reconciliation:** every valid transition in A.4 · every invalid transition refuses with no state change · replay returns the prior receipt only from a verified-delivered state · a late receipt on `EXPIRED`/`REVOKED` changes nothing · `/poc1/reconcile` **can never return `RECONCILED_NOT_DELIVERED`** · **remove every local receipt after a simulated uncertain external completion and prove no retry becomes authorized** · `RECONCILED_NOT_DELIVERED` reachable only via owner attestation · exactly one re-attempt permitted, a second refused · a retry increments `attempt` and never creates a new submission · a provider-asserted outcome is refused.

**Evidence:** fault injection at **each of the six write boundaries** (owner decision, token spend, capability mint, capability spend, delivery, reconciliation) — committed write fails ⇒ authority not effective, state rolled back or uncertain · an orphan `prepared` never counts as complete · provider receipt/refusal cannot mark an action delivered or alter capability state.

**Capacity and redaction:** a provider flooding refusals **cannot** prevent an owner decision being recorded · every pool full ⇒ fail closed, `/health` still serves · minting beyond `MAX_ACTIVE_SECRETS` refused · no live secret outside the index; all redact · `authority_id`/`authority_version`/`tokens_used` survive redaction while a live token under a benign key does not · each structural bound refuses · the HMAC descriptor differs across two process runs for the same value.

**Transport and policy:** deleting any route-policy row makes the self-test fail closed · truthy non-dict nested value ⇒ structured refusal (an **empty** list does not reproduce it) · negative/conflicting `Content-Length`, unsupported transfer encoding, slow body ⇒ prompt refusal · browser-simple `text/plain` POST refused · secrets in path or query absent from logs · `/health` reveals no case or decision activity.

**Validator:** fails on a `MEASURED` with no value · a `MEASURED` whose evidence record's candidate/poc/measure_id/value does **not** match · an `UNSUPPORTED` without matching capability-gap evidence · a missing (candidate × POC × measure) combination.

---

## §F — Return requirements

Delivery Record with the reflexive falsifier element · self-test covering §E, mandatory cases shown failing first · `validate_measurements.py` run clean against the template populated with explicit `NOT_TESTED`/`UNSUPPORTED` · structural harness re-run (regenerated `out/` shipped; harness code untouched) · diffs for every workflow and runbook change · `RETURN_MANIFEST.json` self-verified, plus optional `proposed_classifications.json` (**suggestion only** — Fable publishes the authority manifest) · one zip · H-06 on the snapshot first.

`24A_` records the review environment lacks the n8n workflow-validation dependency (validator control 9/10). That is an environment limitation, not a defect to fix: keep the structural harness as-is and note any locally unrunnable check in the Delivery Record rather than working around it.

**Stop and report** if any clause here delegates a trust/authority/evidence/route/limit decision, asserts an authority not rooted in something the service established, requires reading a superseded packet to implement, is internally inconsistent, conflicts with `09_` §2, or cannot be met within the allowlist. Five consecutive revisions have each been corrected by review; the cheapest place to catch a sixth is before the build.

## §G — After R3

R3 return → Fable structural verification (static, per the trail-127 practice; the adversarial suite is the verifier's) → **one independent ChatGPT security review of the final R2+R3 stub** → owner POC session. Before any of that: **this packet goes to ChatGPT for the narrow Revision-5 confirmation**; Builder release stays held until it returns.
