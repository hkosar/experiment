# Runbook — Zapier (managed / SaaS-first slot)

**Slot:** `05_` §1 managed candidate. **Partition:** Business only.
**Status of every measure below: NOT TESTED until you run it.**

Time each step into `data/owner_friction_log.template.csv`.

> **Portability note before you begin.** Zapier has no public import format for arbitrary Zaps. Unlike n8n, these flows cannot be delivered as files — `workflows/zapier/POC_zap_build_specs.json` is a build *specification* you follow in the editor. That asymmetry is recorded as finding **F-1** and is itself evidence on the portability axis; you do not need to do anything about it beyond noticing how long the manual build takes.

---

## Part A0 — the stub, named for this candidate

Restart the stub with **`--candidate zapier`** before any Zapier step:

    cd poc/stub && python3 stub_server.py --candidate zapier --port 8787

`--candidate` is required. Zapier's evidence lands under `data/captures/zapier/`, keeping it
separately attributable from n8n's — the round exists to compare the two, and one shared
directory would make that impossible.

Read both keys into shell variables (`read -rs OWNER_KEY`, `read -rs PROVIDER_KEY`) rather
than pasting them into commands. **`AIOS_PROVIDER_KEY` goes into the Zap's HTTP steps;
`OWNER_KEY` never does.**

## Part A — account

| # | Step | Owner action? | Record |
| --- | --- | --- | --- |
| 1 | Create a Zapier account (free tier) | **Yes** | Minutes |
| 2 | Note the plan and its task allowance | **Yes** | Plan name, tasks/month included — the cost model needs the real rate, not the marketing page |

## Part B — build the Zaps

Follow `workflows/zapier/POC_zap_build_specs.json`, one Zap per `zaps[]` entry, steps in order. The specs are re-aimed to `09_` §2's Release-1 scenarios.

| # | Step | Owner action? | Record |
| --- | --- | --- | --- |
| 3 | Build POC-2 — idea capture and staging (4 steps: catch hook → Code envelope splitting Case A from Case B → wrapper POST → filter asserting no authority escalation) | **Yes** | **Build wall-clock**, compared against n8n's import time. This is the setup-effort measure |
| 4 | Build POC-1 — the Builder-return pipeline (9 steps incl. Human in the Loop) | **Yes** | Whether the HIL step can carry a pause **without** deciding — if it cannot, that is a capability finding against packet §3 and the flow stops there. Also: can Code by Zapier compute a SHA-256 over the artifact for the identity tuple? |
| 5 | Build POC-3 — the durable nightly integrity sweep (6 steps incl. Schedule trigger) | **Yes** | Whether Zapier's retry/autoreplay is configurable per step |
| 6 | Every HTTP step sends `X-Provider-Key: <the provider credential>` and `Content-Type: application/json` | **Yes** | The stub refuses calls without both |

**If a required step cannot be expressed at all**, packet §6 applies: stop that flow, record it as a capability finding, and continue the rest. A blocked flow is a result.

## Part C — run

| # | Step | Record |
| --- | --- | --- |
| 7 | POC-2: send one owner-authored idea (Case A) and one imported note (Case B) | Latency; task consumption **per idea** — Zapier meters every step, so watch the multiplier. Confirm Case B comes back `instruction_authority: none` |
| 8 | POC-1: post a Builder return, approve on the AI OS surface, confirm the relay | Approval transport; evidence quality; **relay attempts vs deliveries** |
| 9 | **POC-1 duplicate/target tests:** resubmit the identical artifact for the same task and transition (expect duplicate-suppressed with the prior receipt); resubmit under a different `task_id` (expect independent processing); resubmit with `target_role: owner` (expect a REJECT, distinguishable from duplicate-success) | All three outcomes, verbatim — these are R1P-04 (1), (2) and (3) |
| 10 | **POC-1 revocation test:** revoke the connected app, retry | Whether access severed, and how long it took |
| 11 | POC-3: schedule, then **kill the run mid-flight** (turn the Zap off between the stage and the checkpoint), then re-enable | What Zapier did: held, replayed, dropped. The stub refuses a duplicate run declaration and preserves the prior record, so "resumed" and "replayed from the top" are now distinguishable. Whether the AI OS detected the miss independently, and how fast |
| 12 | Save every raw provider result JSON into `data/captures/zapier/<poc>/` | Feeds the receipt-conformance analysis. The stub already writes its own records there under this candidate |

## Part D — economics

| # | Step | Record |
| --- | --- | --- |
| 13 | Zap History → count **tasks** consumed per run | Tasks, not runs — this is Zapier's billing unit and the crossover hypothesis turns on it |
| 14 | If any MCP tool call was used, confirm the task multiplier | `00_` §17 records 2 tasks per MCP call; **revalidate it rather than quoting it** |

## Teardown

Turn every Zap off, disconnect every app connection, and delete the Zaps. Nothing here is load-bearing.
