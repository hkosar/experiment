# Owner Session Runbook — TASK-0007 POC round

**Read this one first.** It is the session script. The two candidate runbooks are the detail.

**Who does what.** You create every account, grant every credential, and click every OAuth consent — personally, on your screen. The Builder never holds, requests, or receives a password, token, or API key. If any step in any runbook seems to ask you to send a secret somewhere, **stop** — that is a defect in the runbook, not an instruction to follow.

**What this round tests.** The Release-1 App-Building Management Platform workload, per the owner ruling in `09_`: POC-1 is the **Builder-return pipeline**, POC-2 is **idea capture and staging**, POC-3 is the **durable nightly integrity sweep**. The Release-2 call-review and email-triage scenarios are parked, not deleted.

**What this session is for.** Producing numbers. Packet `07_` §4: *"the deliverable is numbers plus observations, not impressions."* Everything in `data/measurements.template.json` currently reads `NOT_TESTED` (one measure reads `UNSUPPORTED`). The session's job is to replace those with measured values and evidence references. A measure you could not run stays `NOT_TESTED` **with a reason** — that is a result, and a truthful one.

**An evidence reference is a record, not a filename.** `25_` §D: an `evidence_ref` resolves only when a *measurement-evidence record* binds it to that exact measurement — same candidate, same POC, same `measure_id`, same value. A file that merely exists proves nothing, because one unrelated file can be cited for every result. So for each value you record, add a record to `evidence_records` in the same file:

```json
"evidence_records": {
  "ev-poc1-n8n-approval-latency": {
    "candidate": "n8n", "poc": "POC1", "measure_id": "approval_latency_seconds",
    "observed_value": 143, "unit": "seconds",
    "observed_at": "2026-08-04T18:22:10Z",
    "collector": "owner session, stopwatch on the Discord card",
    "artifact_or_capture_hash": "<sha256 of the capture or screenshot it came from>",
    "source_path": "captures/n8n/POC1/relay-delivered-....json"
  }
}
```

Run `python3 data/validate_measurements.py` **before you start and again before you hand the file back**. It checks completeness and provenance, never values — it will not tell you a number is wrong, only that a number claiming to be measured has nothing behind it, or that a measure went missing. Exit 0 means clean.

**One measure is `UNSUPPORTED` and stays that way unless you supply evidence.** `original_vs_reconstituted` — whether the artifact that arrived is byte-for-byte the artifact that was sent. The stub cannot establish it: `25_` §C, it never receives the destination bytes and cannot hash them, so `destination_verified` is always false with that reason recorded, and `destination_digest_claimed` is a provider claim that gates nothing. If you can compare the delivered artifact against the owner-registered `source_digest` out of band, that observation is what turns this measure into `MEASURED` — record how you compared them in the `collector` field.

---

## 0. Before you start

| Check | Why |
| --- | --- |
| You are using the **Business** mailbox/accounts only | Packet §3: no Personal-partition data enters any provider this round. This is binding, not a preference |
| You have a throwaway-eligible mindset about everything built here | Packet §6: nothing built here becomes load-bearing without a Track B packet |
| A timer you can start and stop per step | Setup wall-clock and owner-friction minutes are themselves measures |
| `data/owner_friction_log.template.csv` open | One row per step **you** had to perform, with its time |
| **The wrapper stub running, with the candidate named** — `cd poc/stub && python3 stub_server.py --candidate n8n --port 8787`, then `curl -s http://127.0.0.1:8787/health` | The three workflows call it. `--candidate` is **required**: it keeps n8n's and Zapier's evidence separately attributable, and a defaulted value would silently merge the two corpora the round exists to compare. Restart it with `--candidate zapier` when you switch |
| **Both keys read into shell variables** — `read -rs OWNER_KEY`, `read -rs PROVIDER_KEY` | The stub prints them at startup as bare values. **Never paste either into a command line**; the owner key never goes near a provider, and the provider credential carries no owner authority |

**Cost exposure.** Both candidates have free tiers adequate for this round. If any step asks for a paid plan before a POC can complete, stop and record it — "the free tier cannot express this flow" is a genuine economics finding, not an obstacle to work around by spending.

## 1. Order of work, and why this order

1. **n8n first, POC-2 first.** n8n self-hosted is the slower setup and POC-2 takes no external action — so the first thing you do is the lowest-risk flow on the higher-effort candidate. If self-hosting is going to be painful, you learn it early, on a flow that cannot touch anything.
2. **Then Zapier POC-2.** Same flow, other candidate — the first genuine like-for-like comparison. **Restart the stub with `--candidate zapier`** so the two corpora stay separate.
3. **Then POC-1 on both.** This one relays something. It carries the duplicate/replay/unauthorized-target tests and the revocation test.
4. **Then POC-3 on both.** This one needs an overnight window and a deliberate mid-flight kill.
5. **POC-4 only if needed.** Packet §1: run it only if tool-scoping/revocation is still undiscriminated after POC-1..3. **State the decision either way** — "we did not run POC-4 because X" is a required output, not an omission.

## 2. The three rules that override convenience

1. **Approval authority never moves to the provider.** Both fabrics have a human-in-the-loop feature. It may carry the *pause*. The decision is made on your AI OS/Discord surface and verified by the wrapper before anything is sent. If you find yourself approving something inside Zapier's or n8n's own UI and that approval directly causes the send, the flow is wired wrong — record it and fix the wiring.
   **In this round the owner surface is the stub:** record each POC-1 decision with
   `curl -s -X POST http://127.0.0.1:8787/owner/decide -H "X-Owner-Key: $OWNER_KEY" -H 'Content-Type: application/json' -d '{"case_id":"<from POST /owner/cases>","decision":"accept"}'` — the provider never learns the case id, so you list your own pending cases first (`POST /owner/cases`, same header, `Content-Type` required on both). **Your first decision on a case is terminal**; a second is refused and recorded.
   **The owner-surface key never goes into a provider.** It is what makes "the owner decided"
   a checked fact rather than "something reached the port" — keep it in your terminal.
   The provider carries only an opaque token; the stub refuses an approval outcome that arrives from the provider side, and refuses a token that is missing, forged, or replayed. Provoking one of those refusals on purpose is a legitimate thing to record.
   **Register the artifact before it is submitted.** POC-1 will not open a case without a `registration_ref` you minted:
   `curl -s -X POST http://127.0.0.1:8787/owner/artifact/register -H "X-Owner-Key: $OWNER_KEY" -H 'Content-Type: application/json' -d '{"source_digest":"<sha256 of the artifact>","size_bytes":<n>,"file_count":<n>,"task_id":"TASK-0007","transition":"builder->verifier","target_role":"verifier"}'`
   The `source_digest` you register is the **authoritative** artifact identity and is immutable once registered. Whatever digest the provider later supplies is only ever *checked against* it. Re-registering the same identity returns the same refs; changing only `target_role` is a **distinct** registration, not a role change on the old one.
   **When a relay comes back ambiguous, do not let anyone retry it.** The provider's `/poc1/reconcile` can answer only *delivered* or *uncertain* — never *not delivered*, because the absence of a local record cannot rule out a side effect that completed before the stub recorded it. Reaching not-delivered is **your** call and yours alone:
   `curl -s -X POST http://127.0.0.1:8787/owner/reconcile -H "X-Owner-Key: $OWNER_KEY" -H 'Content-Type: application/json' -d '{"action_request_id":"<ar-…>","outcome":"not_delivered","note":"<how you checked>"}'`
   Only attest that after you have actually looked at the destination. Exactly one re-attempt is permitted afterwards, and a second is refused. If you want to stop further action **without** attesting non-delivery, use `/owner/revoke` instead — that is the whole reason both routes exist. What you did here, and how long it took, is the `uncertain_reconciliation_outcome` measure.
2. **The provider never receives the rulebook.** No policy artifacts, no evidence contracts, no journal contents, no step-up secrets. Workflow payloads and OAuth-scoped access only.
3. **Content minimisation is measured, not assumed.** Where a metadata path suffices, use it. Where raw content must flow to make the flow work at all, **say so and log it** — packet §3 says that observation is itself B-2-relevant evidence. Do not quietly widen the data path to make a step succeed.

## 3. What to capture at every step

- **Time.** Start/stop per step, into the friction log.
- **Every click you had to make.** The measure is owner friction, and it is invisible unless recorded as it happens.
- **The raw provider result JSON**, whenever a step produces one. Save it under `data/captures/<candidate>/<poc>/`. These feed `harness/receipt_conformance.py`, which computes what each provider can and cannot supply against the D-EC_ shape.
- **Actual costs and billing units consumed.** Not the plan price — the metered units the run actually burned. These correct the cost model.
- **Surprises.** Packet §5 requires incidents and surprises named. A surprise you explain away is the one worth recording.

## 4. The induced failure (POC-3) is mandatory

Packet §4: *"kill a run mid-flight in POC-3 — do not simulate the failure in prose."* Start the overnight run, then kill it between the bounded stage and the checkpoint. Record what each fabric actually did: retried, replayed from the top, resumed, or lost the run. Then check whether the AI OS side detected a missed run independently, and how long that took.

**This is the measure most likely to separate the candidates**, and it is the one that cannot be inferred from any documentation.

## 5. The revocation test (POC-1) is mandatory

Packet §3: kill/revoke must demonstrate **connection-level revocation actually severing the provider's access, measured**. Revoke the connection from the app side, then attempt the action again, and record whether it failed and how quickly. A provider that keeps working for some interval after revocation is a finding with direct bearing on `04_` §7's exit-strategy column.

## 6. When you are done

Run `harness/run_all.sh`. It re-validates the workflow definitions, re-checks the boundary constraints, recomputes the cost model against your measured values, and runs the receipt-conformance analysis over your captures. Then hand the whole `poc/` directory back — the Builder writes it up, and nothing gets a disposition here. Packet §6: **no provider selection or recommendation in this round.**
