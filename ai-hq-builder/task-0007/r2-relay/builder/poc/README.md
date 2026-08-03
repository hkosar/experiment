# TASK-0007 POC apparatus — Business partition only

**STATUS: THE POC ROUND HAS NOT BEEN RUN.** No provider account exists, no host exists,
no OAuth grant has been made, no provider was contacted, and every measure in
`data/measurements.template.json` reads `NOT TESTED`. This directory is the apparatus
the owner session runs — packet `07_` §2's Builder deliverables — plus the findings that
building it produced.

## Where to start
1. `runbooks/RUNBOOK-owner-session.md` — the session script. Read this first.
2. `FINDINGS.md` — the six findings that exist without running anything.
3. `harness/run_all.sh` — every check, before or after the session.

**One-time setup for the harness:** `cd harness && npm install n8n-workflow`.
The library is not vendored here (~90 packages, no evidence value). Without it the
two structural checks are skipped; everything else runs.

## Layout
```
runbooks/    owner-session script + one runbook per candidate
workflows/   n8n/  three importable workflow JSON definitions (structurally validated)
             zapier/  build specs — Zapier has no import format (finding F-1)
stub/        THROWAWAY wrapper stub the workflows call — single file, stdlib only,
             plus its self-test (the two mandatory refusals shown failing)
harness/     validate_n8n_workflows.mjs   structural validation, self-test 10 cases
             check_boundaries.py          05_ §2 / packet §3 compliance, self-test 9 cases
             cost_model.py                V1..V5 arithmetic, self-test 14 cases
             receipt_conformance.py       D-EC_ gap analysis, self-test 6 cases
             run_all.sh                   runs all of the above into out/
data/        measurements.template.json   every measure, all NOT TESTED
             owner_friction_log.template.csv
             captures/                    provider result JSON goes here during the session
```

## The wrapper stub — throwaway, and it says so

`stub/stub_server.py` is the service the three workflows call. **It is POC evidence
apparatus: it is not the AI OS wrapper, it earns no Track B credit, and it must not survive
into production use** — its header says exactly that, and so does its `/health` response.
It has no real authentication, no cryptography, no persistence, and no clock authority,
which are four of the things `13B_` says the real wrapper needs.

    cd stub && python3 stub_server.py --port 8787     # stdlib only, no install
    curl -s http://127.0.0.1:8787/health
    python3 selftest_stub.py                          # 39 cases

It implements the F-3 pattern the boundary requires: the provider's pause carries an
**opaque token only**; the owner decision is recorded on the owner surface
(`POST /owner/decide`, standing in for the Discord card); `/poc1/verify-decision` joins the
two and returns an authorized ActionRequest or refuses. It refuses a missing, forged or
replayed token, and it refuses any approval outcome arriving from the provider side.

The owner surface is protected by a **per-process owner key** printed at startup and never
given to a provider. Without it, anything that could reach the port — the provider's own
HTTP node included — could record a decision and approve its own case, which is the second
mandatory refusal defeated through the owner door rather than the provider door. Both the
attack and its refusal are self-test cases.
Every stub decision writes a capture record marked `synthetic: true` until the live session
overwrites it.

## Binding constraints these artifacts encode
Business partition only · external-untrusted envelope before any classification ·
providers never receive policy artifacts, evidence contracts, journal contents or
step-up secrets · approval **authority** stays on the owner surface, a provider may carry
the pause only · no secret in any file here · nothing built here is load-bearing without
a Track B packet.

## What passing the harness means
That the definitions are well-formed, the boundary rules hold on their face, and the
arithmetic is correct. **It does not mean any POC ran.**
