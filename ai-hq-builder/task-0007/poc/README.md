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
harness/     validate_n8n_workflows.mjs   structural validation, self-test 10 cases
             check_boundaries.py          05_ §2 / packet §3 compliance, self-test 9 cases
             cost_model.py                V1..V5 arithmetic, self-test 14 cases
             receipt_conformance.py       D-EC_ gap analysis, self-test 6 cases
             run_all.sh                   runs all of the above into out/
data/        measurements.template.json   every measure, all NOT TESTED
             owner_friction_log.template.csv
             captures/                    provider result JSON goes here during the session
```

## Binding constraints these artifacts encode
Business partition only · external-untrusted envelope before any classification ·
providers never receive policy artifacts, evidence contracts, journal contents or
step-up secrets · approval **authority** stays on the owner surface, a provider may carry
the pause only · no secret in any file here · nothing built here is load-bearing without
a Track B packet.

## What passing the harness means
That the definitions are well-formed, the boundary rules hold on their face, and the
arithmetic is correct. **It does not mean any POC ran.**
