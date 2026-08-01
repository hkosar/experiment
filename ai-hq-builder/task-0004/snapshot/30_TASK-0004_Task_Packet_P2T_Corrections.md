# 30 — TASK-0004 Task Packet: P2T Oracle/Fold/Schedule/Validator Corrections

**Purpose:** authorize and specify the Builder-side corrections for verifier findings **P2T-01, P2T-02, P2T-03**, and the executable halves of **P2T-04/P2T-05**, per the third scoped re-verification (`28_`, FAIL) and Fable's dispositions (`29_`). Issued per the standing APP-05 template (`19_TASK-0002_APP05_Conformance_Addendum.md`). **This packet is the sole authorization for build mechanics on this task.** The verifier's §6 scope rule governs: corrections stay narrow; unrelated improvements are backlog.

---

## Identity and authority

- **Task:** TASK-0004 — canonical bootstrap-registry ID (allocated 2026-07-30, trail entry 99). **Parent topic:** TOPIC-0002.
- **Prior task:** TASK-0003 is CLOSED (trail entry 98) — this is a NEW task on the same artifact area, not a TASK-0003 rework cycle. All TASK-0003-era binding rules carry forward: anti-circularity contract, determinism, byte hygiene, no-manual-claims (anything that can fail is shown failing in shipped evidence), no orphaned switches, no dead mutations, no mutation writing a channel only its predicate reads, per-claim record-vs-file re-check.
- **Requirement authority:** the verifier's exact P2T-01..03 required-correction texts (`28_` §4, quoted below in compressed form — the preserved full text governs); P2S-04's original test obligation (`21_`); `13V_`'s P2T-05 validator requirements (`28_`); D-SM-driven checking (`28_` P2T-04 items 5–6).
- **Decision authority:** trail entries 98 (TASK-0003 closure), 99 (this allocation); Fable dispositions `29_` (all six findings concurred; ownership split per the verifier's §6).
- **Builder:** Claude Opus 5 (`claude-opus-5`), standing authorized substitution (trail entry 69).
- **Risk class:** internal design-test tooling and governance validators only. No runtime deployment, no credentials, no network, synthetic data only.

## Trust, data, and the anti-circularity contract (unchanged from `22_`)

Engine/scenario modules never read fixture `expected`/`actual`/`verdict`/`pass_rule`/`forbidden`/`required_evidence`/`allowed_alternatives`/`trace_S2`/`delta_S1`/`delta_S3` fields; oracle/judge modules own them. The `Stimulus` structural split stays intact. Mutations perturb computed events/state only. `03F_Replay_Fixtures.json` remains frozen — **fixture corpus defects, ambiguities, or missing design rules return as change requests; nothing is reinterpreted.**

## Source/context manifest (hash-bound; snapshot supplied WITH this packet)

Read and encode from these; modify only what the allowlist permits.

| # | File | Role |
| --- | --- | --- |
| 1 | `03F_Replay_Fixtures.json` | frozen corpus (input-side for engine; oracle side for oracle/judge) |
| 2 | `28_Verifier_Scoped_Reverification_P2S_Packet3.md` | exact P2T findings + required corrections (governing text) |
| 3 | `28A_Verifier_Probe_Evidence_P2S_Packet3.json` | the verifier's machine-readable probes — your corrections must defeat every probe in it |
| 4 | `29_P2T_Dispositions.md` | Fable dispositions + ownership split |
| 5 | `design/D-B9_Event_Model_and_Replay.md` | fold-order + causal-basis contract (P2T-02) |
| 6 | `design/D-KR_Kill_Revoke_and_Resilience.md` | watchdog-owned recurrence contract (P2T-03 tests encode THIS, incl. its P2S-04 section) |
| 7 | `design/D-B7_Attention_and_Quiet_Hours.md` | band definitions incl. ATT-03 hub mapping (route/attention oracle mapping ground truth — full document this time) |
| 8 | `design/D-B2_Field_Authority_Contract.md` | authority/ceiling semantics for the authority-dimension oracle completion |
| 9 | `design/D-SM_Supersession_Map.md` | the authoritative supersession rows your generated checker derives from (READ AT RUNTIME — Fable will extend rows in parallel; the checker must pick up new rows without code changes) |
| 10 | `13G_Design_Gate_Status_and_Evidence_Matrix.md` + `13M_Design_Requirements_Applicability_Matrix.md` | structures the extended `13V_` must parse (read-only reference) |
| 11 | `13V_validate_design_matrix.py` | current validator (you modify this one, per allowlist) |
| 12 | `design/traces/check_supersessions.py` | current literal checker (you replace its mechanism, per allowlist) |
| 13 | `design/traces/behavioral/` (complete current tree, 28 files) | the integrated simulator you extend |

Exact SHA-256 per file: `EXPORT_MANIFEST.json` in the accompanying `TASK-0004_Builder_Snapshot.zip` — validate 100% before any work (H-06).

## Required behavior

### W1 — Complete expected-result enforcement (P2T-01, Critical)
Parse and compare **every** expected dimension for all 81 combinations: route (against computed disposition/route), attention (existing, kept), authority (mapping completed — the current 36/45-mapped coverage becomes explicit per-dimension accounting), receipts (expected receipt behavior vs computed evidence chain). Where a dimension's expectation is genuinely unmappable, it is per-fixture reported AND bounded: **a fail-closed floor makes mapping collapse impossible** — a corpus whose parsed-and-compared count falls below the declared floor (or whose previously-mapped fixture becomes unmapped) FAILS the gate. **Oracle-mutation self-tests:** for each dimension, a shipped test corrupts fixture expectations (impossible route / nonsense authority / dropped receipt expectation / absurd attention) and shows the gate FAIL — every probe in `28A_` must be demonstrated defeated, plus your own per-dimension corruptions.

### W2 — Fail-closed causal basis (P2T-02, High)
The fold rejects (FoldError or recorded violation that fails the case — never silence) any event whose `caused_by` references an id absent from the fold input. Missing-basis test suite: dangling reference, forward reference to a never-delivered event, cross-store dangling reference; each with a seeded-defect witness proving the check can fail. The verifier's exact probe (DecisionEvent with `caused_by=[missing-policy-event]`) must be a shipped failing case.

### W3 — P2S-04 schedule-liveness suite (P2T-03, High)
A bounded suite (harness self-test style, like layer E) where the watchdog computes deadlines from a versioned recurrence specification it owns: (1) scheduler death after a run, before next-occurrence registration ⇒ the missed deadline is detected; (2) rolling-horizon exhaustion ⇒ early warning BEFORE the next deadline; (3) a versioned schedule change atomically updates expectations — no orphaned old deadline, no missing new one; (4) each case flips under a targeted defect (scheduler-self-report dependence restored; horizon monitoring disabled; non-atomic change). Encode from D-KR's P2S-04 contract — full document supplied.

### W4 — D-SM-driven supersession checker (P2T-04 executable half)
Replace the nine-literal checker with one that derives its patterns from parsing `design/D-SM_Supersession_Map.md` rows at runtime (so Fable's parallel row additions are picked up without code changes), plus structural checks for retired artifact paths (e.g. `gen_shape_traces.py`, `run_fold_comparison.py` as instructions), retired parameter values, retired evidence labels, and retired mechanism identifiers. Ships with a self-test: seeding a retired phrase outside a SUPERSEDED block into a scratch copy must fail the check.

### W5 — `13V_` semantic-consistency extension (P2T-05 executable half)
`13V_` additionally: (a) parses any declared summary/count block in `13G_` and FAILS on disagreement with the actual rows; (b) supports a finding-dependency notation in the Remaining-dependency column (e.g. `P2T-02: …`) and FAILS `--final-gate` while any referenced finding appears in a machine-readable open-findings list (a small file Fable maintains; format: your design, documented); (c) keeps all current checks. Self-test: a doctored matrix copy with a contradictory summary must fail.

## Implementation allowlist (Builder-writable)

- `design/traces/behavioral/**` — modify existing + new files (the oracle/judge/fold/runner corrections, W1–W3 suites, outputs).
- `design/traces/check_supersessions.py` — replace mechanism (W4).
- `13V_validate_design_matrix.py` — extend (W5).
- **Nothing else.** No document (`13G_`/`13M_`/`D-B*`/`D-SM`/trail/registry/checksums), no fixture corpus, no gate/status artifact. Fable applies all document changes. Scope-deviation rule of `22_` applies verbatim: ambiguity or out-of-allowlist need ⇒ stop, change request.

## Acceptance criteria (each independently verifiable; shipped evidence only)

| # | Criterion |
| --- | --- |
| 1 | All TASK-0003-era criteria re-pass (anti-circularity incl. any new modules; 81/81; determinism two-run byte-identical; hygiene; allowlist walk) |
| 2 | Every `28A_` probe reproduced and DEFEATED: each probe scenario now yields gate FAIL, shown in shipped output |
| 3 | Per-dimension expected-result accounting (route/attention/authority/receipts): compared / unmapped-with-rationale counts per dimension; fail-closed floor demonstrated (a below-floor corpus FAILS, shipped) |
| 4 | Oracle-mutation suite: every expected dimension shown load-bearing (corruption ⇒ FAIL) per fixture-dimension coverage table |
| 5 | Causal-basis: the three missing-basis cases fail closed; seeded-defect witnesses shipped; the verifier's exact probe is a shipped failing case |
| 6 | P2S-04 suite: all four behaviors demonstrated with targeted-defect flips, shipped |
| 7 | Generated supersession checker: derives from D-SM at runtime; structural retired-artifact checks; self-test shipped |
| 8 | Extended `13V_`: summary/row consistency enforced; finding-dependency gate enforced; self-tests shipped; current matrices still validate (structural PASS; `--final-gate` honestly FAILS while open findings exist) |
| 9 | No regressions: previously passing behavior unchanged except where a W1–W5 correction legitimately changes it — each such change individually dispositioned in the Delivery Record |
| 10 | Delivery Record per APP-06 with reflexive falsifiers, per-finding disposition table (P2T-01/02/03 + W4/W5), and the record-vs-file re-check applied to every claim |

## Failure / return

Defects found in Fable's independent verification return as an APP-07 Rework Packet, as in TASK-0003. Return format unchanged: zip + `RETURN_MANIFEST.json` + Delivery Record, fingerprint quoted in-channel.
