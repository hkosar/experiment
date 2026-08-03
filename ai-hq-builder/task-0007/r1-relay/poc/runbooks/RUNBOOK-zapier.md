# Runbook — Zapier (managed / SaaS-first slot)

**Slot:** `05_` §1 managed candidate. **Partition:** Business only.
**Status of every measure below: NOT TESTED until you run it.**

Time each step into `data/owner_friction_log.template.csv`.

> **Portability note before you begin.** Zapier has no public import format for arbitrary Zaps. Unlike n8n, these flows cannot be delivered as files — `workflows/zapier/POC_zap_build_specs.json` is a build *specification* you follow in the editor. That asymmetry is recorded as finding **F-1** and is itself evidence on the portability axis; you do not need to do anything about it beyond noticing how long the manual build takes.

---

## Part A — account

| # | Step | Owner action? | Record |
| --- | --- | --- | --- |
| 1 | Create a Zapier account (free tier) | **Yes** | Minutes |
| 2 | Note the plan and its task allowance | **Yes** | Plan name, tasks/month included — the cost model needs the real rate, not the marketing page |

## Part B — build the Zaps

Follow `workflows/zapier/POC_zap_build_specs.json`, one Zap per `zaps[]` entry, steps in order.

| # | Step | Owner action? | Record |
| --- | --- | --- | --- |
| 3 | Build POC-2 (3 steps: Gmail trigger → Code envelope → wrapper POST) | **Yes** (OAuth) | **Build wall-clock**, compared against n8n's import time. This is the setup-effort measure |
| 4 | Connect the **Business** Gmail account only | **Yes** | Confirm before saving; note whether Zapier's managed OAuth avoided the GCP project work n8n needed |
| 5 | Build POC-1 (8 steps incl. Human in the Loop) | **Yes** | Whether the HIL step can be configured to carry a pause **without** deciding — if it cannot, that is a capability finding against packet §3 and the flow stops there |
| 6 | Build POC-3 (6 steps incl. Schedule trigger) | **Yes** | Whether Zapier's retry/autoreplay is configurable per step |

**If a required step cannot be expressed at all**, packet §6 applies: stop that flow, record it as a capability finding, and continue the rest. A blocked flow is a result.

## Part C — run

| # | Step | Record |
| --- | --- | --- |
| 7 | POC-2: let one message flow | Latency; task consumption **per message** — Zapier meters every step, so watch the multiplier |
| 8 | POC-1: fire the webhook, approve on the AI OS surface, confirm the send | Approval transport; duplicate-send prevention; evidence quality |
| 9 | **POC-1 revocation test:** revoke the connected app, retry | Whether access severed, and how long it took |
| 10 | POC-3: schedule, then **kill the run mid-flight** (turn the Zap off between the stage and the checkpoint), then re-enable | What Zapier did: held, replayed, dropped. Whether the AI OS detected the miss independently, and how fast |
| 11 | Save every raw provider result JSON into `data/captures/zapier/<poc>/` | Feeds the receipt-conformance analysis |

## Part D — economics

| # | Step | Record |
| --- | --- | --- |
| 12 | Zap History → count **tasks** consumed per run | Tasks, not runs — this is Zapier's billing unit and the crossover hypothesis turns on it |
| 13 | If any MCP tool call was used, confirm the task multiplier | `00_` §17 records 2 tasks per MCP call; **revalidate it rather than quoting it** |

## Teardown

Turn every Zap off, disconnect every app connection, and delete the Zaps. Nothing here is load-bearing.
