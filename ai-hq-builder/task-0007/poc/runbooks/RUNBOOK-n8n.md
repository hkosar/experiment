# Runbook — n8n (self-hosted / developer-controlled slot)

**Slot:** `05_` §1 self-hosted candidate. **Host:** Mac Studio or an equivalent host you own.
**Partition:** Business only. **Status of every measure below: NOT TESTED until you run it.**

Time each step into `data/owner_friction_log.template.csv`. "Owner action" marks steps only you can do.

---

## Part A — stand up the host

| # | Step | Owner action? | Expected friction | Record |
| --- | --- | --- | --- | --- |
| 1 | Install Docker Desktop (or Podman) on the host | Yes | One-time; a restart is likely | Minutes; whether a restart was needed |
| 2 | `docker volume create n8n_data` | No | None | — |
| 3 | Start n8n: `docker run -d --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n -e N8N_SECURE_COOKIE=false docker.n8n.io/n8nio/n8n` | No | First pull is slow | Image pull time; image digest |
| 4 | Open `http://localhost:5678`, create the owner account | **Yes** | Email + password on your screen only | Minutes |
| 5 | Record the n8n version from Help → About | No | — | **Version string — the cost/capability findings are version-bound** |

> **The Builder never sees this host, this account, or any credential in it.** Nothing in Part A produces a value that should be sent anywhere.

## Part B — import the workflows

| # | Step | Owner action? | Record |
| --- | --- | --- | --- |
| 6 | Workflows → Import from File → `workflows/n8n/POC2_email_triage_readonly.json` | No | **Whether the import is accepted, and every node n8n flags.** This is the first real test of the definitions: the Builder validated them structurally but could NOT validate node types or parameters (the node-type registry install is blocked in the Builder environment). Node/parameter errors here are expected findings, not failures |
| 7 | Repeat for `POC1_call_review_delegation.json` and `POC3_durable_overnight.json` | No | Same |
| 8 | For each flagged node, correct it in the editor and **export the corrected workflow back over the file** | No | What had to change — this is capability evidence about how faithfully a definition survives round-tripping (portability axis) |

## Part B2 — start the wrapper stub (before any workflow runs)

The three workflows call an AI OS wrapper. For the POC round that is a **throwaway stub**
shipped in `poc/stub/` — evidence apparatus, not the AI OS wrapper, and it must not
survive into production use.

| # | Step | Owner action? | Record |
| --- | --- | --- | --- |
| B2.1 | From `poc/stub/`, run `python3 stub_server.py --candidate n8n --port 8787`. Python 3 standard library only — no install, no database, no Docker. **`--candidate` is required**: it namespaces this candidate's evidence so n8n's and Zapier's corpora stay separately attributable | No | That it started; the port if you changed it |
| B2.2 | Confirm it is live: `curl -s http://127.0.0.1:8787/health` — expect `"ok": true`, `"candidate": "n8n"`, and a `run_instance` | No | The `run_instance` — it appears in every capture filename from this run |
| B2.3 | Read the two keys into shell variables **without pasting them into a command**: `read -rs OWNER_KEY` then paste, Enter; `read -rs PROVIDER_KEY` then paste, Enter. The stub prints both at startup as bare values | **Yes** | That you did not put either key into a command line or into n8n's UI |
| B2.4 | In n8n set `AIOS_WRAPPER_BASE=http://127.0.0.1:8787` and `AIOS_PROVIDER_KEY=<the provider credential>` (Settings → Variables, or `-e` on the `docker run`). If n8n runs in Docker and the stub runs on the host, use `http://host.docker.internal:8787` **and start the stub with `--advertise http://host.docker.internal:8787`** so the endpoints it hands back resolve from inside the container | No | Which base URL worked — **itself a finding about self-hosted networking friction** |

> **The provider credential is not the owner key.** `AIOS_PROVIDER_KEY` goes into n8n; it
> lets the workflows call the provider-facing routes and confers **no** owner authority.
> `OWNER_KEY` never leaves your terminal.

**Do not redirect the stub's stderr to a shared or checked-in file** — the startup banner
contains both keys. Run it in a terminal you can see.

**The owner decision surface.** The stub stands in for the Discord/AI OS card. The provider
never learns the case id, so you list your own pending cases:

    curl -s -X POST http://127.0.0.1:8787/owner/cases \
         -H "X-Owner-Key: $OWNER_KEY" -H 'Content-Type: application/json' -d '{}'

    curl -s -X POST http://127.0.0.1:8787/owner/decide \
         -H "X-Owner-Key: $OWNER_KEY" -H 'Content-Type: application/json' \
         -d '{"case_id":"<from the list above>","decision":"accept"}'

Both calls send `Content-Type: application/json` — the stub refuses anything else, and the
R1 runbook's `/owner/cases` line omitted it, which would have broken step one.

**The first decision is terminal.** A second decision on the same case is refused 409 and
recorded. That is deliberate: a reject silently overwritten by an accept would mint a relay
for a case you rejected.

Run `python3 selftest_stub.py` once before the session if you want to watch the refusals
fire, and `python3 r1_witnesses.py` to see the same probes against the superseded build.

## Part C — connect accounts (owner only)

| # | Step | Owner action? | Expected friction | Record |
| --- | --- | --- | --- | --- |
| 9 | Credentials → Gmail OAuth2 → connect the **Business** mailbox | **Yes** | Google consent screen; n8n self-hosted needs your own Google Cloud OAuth client — this is the step most likely to be slow | Minutes, **and every sub-step** (creating a GCP project, enabling the API, configuring the consent screen, adding a redirect URI). This is the single richest owner-friction datapoint in the round |
| 10 | Confirm the mailbox is the Business one before saving | **Yes** | — | Confirmed yes/no |
| 11 | Set `AIOS_WRAPPER_BASE` in the n8n environment to your wrapper base URL | No | — | — |

**If step 9 requires a Google Cloud project you do not want to create, stop.** "Self-hosted n8n requires the owner to run their own OAuth client for Google" is a legitimate governance/operations finding and belongs in the results.

## Part D — run the POCs

| # | Step | Record |
| --- | --- | --- |
| 12 | POC-2: activate, let it poll, watch one message flow through | Latency; whether the envelope node ran before the wrapper call; cost/units |
| 13 | POC-1: fire a test webhook, take the approval on the AI OS surface, confirm the send | Approval transport behaviour; duplicate-send prevention; evidence quality |
| 14 | **POC-1 revocation test:** revoke the Gmail/app connection, retry the action | Whether access actually severed, and **how long it took** |
| 15 | POC-3: schedule it, then **kill the container mid-run** (`docker stop n8n`) between the bounded stage and the checkpoint, then restart | What n8n did on restart: resumed, replayed, or lost the run. Whether the AI OS detected the miss independently, and how fast |
| 16 | Save every raw provider result JSON into `data/captures/n8n/<poc>/` | These feed the receipt-conformance analysis |

## Part E — economics

| # | Step | Record |
| --- | --- | --- |
| 17 | Executions list → count executions consumed | Executions, not steps — this is n8n's billing unit |
| 18 | Note the host's real cost | Hardware amortisation, electricity, and **the hours you spent in Parts A–D**; the last one is the line no invoice shows |

## Teardown

`docker rm -f n8n && docker volume rm n8n_data`, and revoke the Google OAuth client if you created one for this round. Nothing here is load-bearing.
