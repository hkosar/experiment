# 08 — TASK-0007 Supplemental Round R1: the POC wrapper stub

**Context:** Fable verification of the TASK-0007 R0 return (zip SHA-256 `836946be254864b06ca92bbad5c162e47fc482e625454fb7b334179bdb4dc6be`) is complete. **The apparatus is ACCEPTED and integrated verbatim** (36/36 hash-verified at `provider-adoption-review/poc/`): pristine manifest 36/36; the full harness re-run by Fable **on a copy** — HARNESS PASS, 39/39 self-test cases across four checkers, 3/3 workflows structurally valid, and Fable's outputs **byte-identical to the shipped `out/`**. The all-NOT-TESTED posture is exactly right and no measurement is claimed by anyone. F-1..F-6 recorded (F-2 — the 4/9/3 receipt-field split — feeds D4/D5 directly). Your §6 change request is GRANTED; this round is its instruction.

## R1 scope — one thing: the throwaway wrapper stub

Build the stub service the three workflows already call, so the owner session can run end to end.

- **Endpoints:** `/poc1/review-case`, `/poc1/verify-decision`, `/poc2/triage`, and the `/poc3/*` set — exactly the paths the shipped workflow definitions reference, plus a health endpoint the runbooks can curl.
- **The F-3 pattern is the point:** the provider's pause carries an opaque resume token only; `/poc1/verify-decision` validates the token and returns the authorized ActionRequest or refuses. The stub must refuse a missing/forged/replayed token and must never accept an approval decision arriving *from* the provider side — those two refusals ship **shown failing** in the self-test.
- **Boundary rules apply in code:** external-untrusted envelope applied before any classification path; no Personal-partition route exists at all (not guarded — absent); nothing secret-shaped logged or persisted; every stub decision writes a capture record in the `data/` shapes the harness consumes, marked `synthetic: true` until the live session overwrites them.
- **Deployment reality:** single-file service (Python stdlib or Node, your call), runnable on the owner's host with one command, no database, Docker optional but not required. The n8n runbook gains the two steps that point the imported workflows at the stub's local URL.
- **THROWAWAY marker, in the code and the README:** this stub is POC evidence apparatus. It is not the AI OS wrapper, earns no Track B credit, and must not survive into production use — its header says so.
- **Workflow corrections permitted:** if pointing the flows at a real stub surfaces import-time or parameter corrections in `workflows/n8n/*.json`, make them, diff them, and re-run the structural harness — that is falsifier row 2's named gap being closed, not new scope.

## Allowlist

`poc/stub/**` (new) · `poc/workflows/n8n/*.json` (corrections only, diffed) · `poc/runbooks/RUNBOOK-n8n.md` + `poc/runbooks/RUNBOOK-owner-session.md` (the stub-startup steps only) · `poc/README.md` (stub section). Nothing else; no ai-hq file outside `poc/`.

## Return requirements

Standard Delivery Record with reflexive falsifier element; stub self-tests with the two mandatory refusals shown failing; any workflow diffs with the harness re-run; one zip; manifest self-verified; H-06 on this snapshot first.

## After R1 (stated so the sequence is fixed)

R1 return → Fable verification → **the owner working session** (RUNBOOK-owner-session.md, with the stub running): accounts, OAuth grants, the three POCs on both candidates, the deliberate POC-3 mid-flight kill, the POC-1 revocation test. Populated `data/` comes back to Fable; `run_all.sh` consumes it; the write-up and per-axis scoring follow. POC-4's trigger condition is evaluated then.
