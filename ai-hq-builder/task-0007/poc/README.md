# TASK-0007 POC apparatus — Business partition only

**STATUS: THE POC ROUND HAS NOT BEEN RUN.** No provider account exists, no host exists,
no OAuth grant has been made, no provider was contacted, and every measure in
`data/measurements.template.json` reads `NOT_TESTED` — one reads `UNSUPPORTED`, because
this apparatus cannot establish it at all. This directory is the apparatus
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
workflows/   n8n/  three importable workflow JSON definitions, re-aimed to the
                   Release-1 scenarios in 09_ §2 (structurally validated)
             zapier/  build specs — Zapier has no import format (finding F-1)
stub/        THROWAWAY wrapper stub the workflows call — single file, stdlib only,
             selftest_stub.py (the R3 contract, 167 cases), r1_witnesses.py (the
             unfixed behaviour, against the pinned R1 build in r1_reference/ and
             the pinned R2 build in r2_reference/)
harness/     validate_n8n_workflows.mjs   structural validation, self-test 10 cases
             check_boundaries.py          05_ §2 / packet §3 compliance, self-test 9 cases
             cost_model.py                V1..V5 arithmetic, self-test 14 cases
             receipt_conformance.py       D-EC_ gap analysis, self-test 6 cases
             run_all.sh                   runs all of the above into out/
data/        measurements.template.json   every measure, NOT_TESTED or UNSUPPORTED
             validate_measurements.py     completeness and provenance, 25_ §D
             owner_friction_log.template.csv
             captures/                    provider result JSON goes here during the session
```

## The wrapper stub — throwaway, and it says so

`stub/stub_server.py` is the service the three workflows call. **It is POC evidence
apparatus: it is not the AI OS wrapper, it earns no Track B credit, and it must not survive
into production use** — its header says exactly that, and so does its `/health` response.
It has no real authentication, no cryptography, no persistence, and no clock authority,
which are four of the things `13B_` says the real wrapper needs.

    cd stub && python3 stub_server.py --candidate n8n --port 8787   # stdlib only
    curl -s http://127.0.0.1:8787/health
    python3 selftest_stub.py      # the R3 contract holds — 167 cases
    python3 r1_witnesses.py       # the same probes against the superseded R1 and R2 builds
    python3 ../data/validate_measurements.py    # measurement completeness and provenance

It implements the F-3 pattern the boundary requires: the provider's pause carries an
**opaque token only**; the owner decision is recorded on the owner surface
(`POST /owner/decide`, standing in for the Discord card); `/poc1/verify-decision` joins the
two and returns an authorized ActionRequest or refuses. It refuses a missing, forged or
replayed token, and it refuses any approval outcome arriving from the provider side.

The owner surface is protected by a **per-process owner key** printed at startup and never
given to a provider; provider-facing routes carry a **separate provider credential** with no
owner authority. `--candidate` is required, so n8n's and Zapier's evidence stay separately
attributable.

**R2 rebuilt this against the corrected contract in `14_` §2 (C-1..C-19)**, after an
independent security review returned FAIL with eight findings and Fable's disposition added
seventeen more — most of them evidence-integrity defects rather than security defects. The
POC-1 side effect requires a single-use capability bound to the action, case, target and
payload digest; owner decisions are terminal and atomic; every capture is written
before the state it records is committed, carries a stub-minted timestamp and provenance,
and cannot overwrite a prior run's records.

**R3 rebuilt it again against `25_` Revision 5**, whose §A is a complete self-contained
contract. What is new, and what each closes:

- **owner-authoritative artifact registration** (A.2) — the artifact identity is registered
  by the owner and is immutable; a provider-supplied digest is only ever *checked against*
  it. Before this there was nothing for it to be checked against.
- **owner-idea authority bound to canonical content** (A.3) — authority derives from a ref
  the owner minted against content the service stored, not from a field the caller sets. R2
  let a provider send `origin: "owner"` and have its own text recorded as owner-authorized.
- **an eight-state capability machine with explicit invalid transitions** (A.4), and
  **reconciliation where local absence can only produce UNCERTAIN** (A.5). Only an owner
  attestation reaches not-delivered, because a wrong not-delivered would authorize a
  duplicate real-world action — the exact failure POC-1 exists to disprove.
- **prepared → committed evidence at six write boundaries** (A.7). A transition is
  effective only once its committed record has landed; if it has not, the state rolls back,
  or where an external effect cannot be rolled back, the subject fails closed as UNCERTAIN.
- **three disjoint capture pools** (A.8), so a provider flooding refusals cannot crowd out
  the evidence an owner decision needs.
- **the route policy as data** (§B). Delete a row and the route fails closed.

`25_` §E's required tests ship in `selftest_stub.py` (167 cases, including a live-HTTP
block over a real socket), and `r1_witnesses.py` runs the same probes against the pinned,
byte-identical R1 **and R2** builds to show what the unfixed behaviour was.
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
