# P2S-01 Behavioral Candidate-Transition/Fold Simulator

Deterministic behavioral simulator for the CP-P2-A design gate, built under TASK-0003.
It computes candidate behavior from the design rules and the fixtures' **input side
only**, then judges the computed result against the fixtures' expectations in a
separate component.

This replaces the withdrawn `gen_shape_traces.py` / `run_fold_comparison.py` evidence,
which was circular: it copied each fixture's prewritten transitions, expected results
and verdicts into shape-labeled records and then verified that copies of one object
agreed with themselves. Nothing here reuses that approach.

## Running everything

```
cd fable/phase2-decision-engine/design/traces/behavioral
python3 run_gate.py                 # every suite + the acceptance-criteria table
```

Individual suites (each exits non-zero on failure):

```
python3 check_anticircularity.py    # criterion 1 — engine has no path to oracle data
python3 run_all.py                  # 27 fixtures x 3 shapes = 81 combinations
python3 run_defects.py              # seeded-defect falsifier proof
python3 run_shuffle.py              # P2S-06 shuffle invariance
python3 run_p2s05.py                # P2S-05 five linearization traces
python3 run_p2s07.py                # P2S-07 negative + positive eligibility tests
python3 run_composition.py          # D-B8 composition cases through the real compose_policies
python3 run_oracle_mutations.py     # P2T-01 — every expected dimension shown load-bearing
python3 run_basis.py                # P2T-02 — incomplete causal basis fails closed
python3 run_p2s04.py                # P2T-03 — schedule-liveness suite (harness self-test)
```

Two more validators live one level up, outside this directory:

```
python3 ../check_supersessions.py              # P2T-04 — patterns derived from D-SM at runtime
python3 ../check_supersessions.py --self-test  #          seeded violations must fail
python3 ../../../13V_validate_design_matrix.py --self-test   # P2T-05 — summary/finding checks
```

Fixture-driven runners default to `--fixtures ../../../03F_Replay_Fixtures.json`
(the frozen corpus at its packet-relative path); every runner defaults to
`--out out`. `run_p2s05.py`, `run_p2s07.py` and `run_composition.py` drive synthetic
inputs and take `--out` only — passing `--fixtures` to them is an argument error,
not a silent no-op. Outputs land in `out/`; `run_gate.py` writes all ten.

### Deterministic reproduction

No wall-clock, no unseeded randomness, no network, no model API calls. Shuffle seeds
are a fixed list; the permutation uses a seeded linear congruential shuffle rather
than the `random` module. Two consecutive runs produce byte-identical output files:

```
python3 run_gate.py --out /tmp/runA
python3 run_gate.py --out /tmp/runB
diff -r /tmp/runA /tmp/runB && echo "byte-identical"
```

## The anti-circularity boundary

This is the acceptance condition the prior attempt failed, so it is enforced
**structurally**, not by convention.

| Field group | Fields | Who may read |
| --- | --- | --- |
| INPUT-SIDE | `id`, `title`, `normalized_input`, `envelope`, `start_state`, `policy` | engine, scenario, simulate |
| ORACLE-ONLY | `expected`, `actual`, `verdict`, `pass_rule`, `forbidden`, `required_evidence`, `allowed_alternatives`, `trace_S2`, `delta_S1`, `delta_S3`, `gap_or_falsifier` | `oracle.py`, `judge.py` only |

`fixture_io.load_stimuli()` returns `Stimulus` objects that **physically do not carry**
the oracle fields, so an engine module cannot read one even by mistake. `trace_S2`,
`delta_S1`, `delta_S3` and `actual` are classified oracle-only because they are
prewritten *results* — the S2 transition trace and the S1/S3 divergences are exactly
what the engine must compute for itself.

`check_anticircularity.py` proves this three ways: textual (no oracle field name
appears in engine code), import (no engine module can reach the oracle side), and
structural (`Stimulus` exposes only the six input-side attributes). Engine identifiers
were deliberately renamed away from oracle field names — e.g. `EnvelopeCheck`, not
`EnvelopeVerdict` — so a reviewer's plain `grep` over the engine modules returns zero
hits rather than false positives.

## Module map

| Module | Role | Side |
| --- | --- | --- |
| `fixture_io.py` | loads fixtures; enforces the input/oracle split | boundary |
| `mutations.py` | candidate-defect catalogue that proves each predicate can fire | engine-side |
| `oracle_schema.py` | typed schema for all four expected dimensions + the fail-closed coverage floor | oracle |
| `engine_core.py` | envelope authority (D-B2 §3), policy composition (D-B8 P2G-10), tier function (D-B6 §2.2) | engine |
| `events.py` | event taxonomy, store-ownership matrix, ordering keys/phases (D-B9), the three shapes | engine |
| `fold.py` | deterministic causal-topological replay fold (D-B9 P2S-06) | engine |
| `scenarios.py` | 27 input-side stimulus encodings | engine |
| `simulate.py` | orchestration; E2E-1 normalizers; seeded-defect switches | engine |
| `oracle.py` | parses expectations into computable predicates | oracle |
| `judge.py` | compares computed vs expected; evaluates every forbidden predicate | oracle |
| `run_*.py`, `check_anticircularity.py` | runners | — |

## Candidate shapes

Per plan §B1: **S1** aggregate root · **S2** Decision Case linking separately-owned
typed records · **S3** independent records/events + separately materialized projections.

Fixture ID `S1` and shape `S1` collide in name only; every output labels them
separately as `fixture` and `shape`.

Authority and policy outputs are **shape-invariant** by construction (D-B6 §2.1 purity;
plan §309 neutrality preconditions) — the simulator asserts this and reports any breach
as an `authority-divergence`. Genuine candidate-specific divergences therefore appear
in storage layout and projection mechanics, which is where the shapes actually differ:
S3's read path depends on separately materialized projections and so carries a
freshness obligation that S1 and S2 do not.

## Evidence counts — read these honestly

The R1 rework replaced a padded headline with a measured one. `run_defects.py`
searches a **62-mutation candidate-defect catalogue** for the defects that make each
forbidden predicate return True, and reports the result per predicate:

| Figure | Meaning |
| --- | --- |
| 171 predicate evaluations | evaluations performed across the 81 combinations |
| 56 distinct predicates | the corpus's distinct `forbidden` phrases |
| **56 defect-reachable** | each has a named witness defect that makes it fire |
| **0 NOT-EVALUABLE** | none is counted as evidence without being able to discriminate |

R0 reported "171 predicates evaluated" while only **5 of 56** could ever fire. R1
raised that to 56/56 — but **four of those witnesses were artifacts**: the mutation
wrote a `result.extras` key whose only reader was its paired predicate, and four more
detected mutation-authored tokens rather than computed state. R2 rebuilt every one of
those channels: the engine now genuinely computes watchdog liveness, the focus
pointer, recall results, provenance labelling and interrupt-policy citation, and the
mutations perturb those computed records.

**Witness channels have a regression tripwire — not a proof.** `run_defects.py`
parses `mutations.py` and reports any mutation that writes an artifact channel
(`result.extras`, `result.receipt_violations`) by any of seven known forms
(subscript assignment, augmented assignment, wholesale reassignment, `update()`,
`append`/`extend`, `setattr`, alias binding). Section C reports it. R2's README said
"checked structurally, not asserted", which claimed more than the check delivers: it
enumerates KNOWN channels and KNOWN forms, and a novel channel — a summary field
added tomorrow and read only by its own predicate — passes it untouched. The general
property is not decidable by this check and is not claimed. Read a clean result as
"no known-shape regression". The one exemption, an assignment whose value is a call
to a declared production derivation writer, is named in the code.

**Every judge check is now shown flippable (section D).** R2 proved the 56 forbidden
predicates could fire but never ran the judge over a mutated result, so the judge's
own checks — `masked_render`, `hearsay_provenance`, `interrupt_policy_cited` and the
rest — were asserted falsifiable rather than demonstrated. Section D runs the real
judge over every seeded defect and every mutation and lists, per check, EVERY witness
that flips it. It also names the checks no fixture pass rule ever selects, and the
one that is selected but vacuous. Both witness searches record complete sets rather
than stopping at the first hit, because stopping early let a blunt witness mask a
targeted one.

**Section E is a harness self-test, not a fixture.** No corpus case pairs degraded
stores with an envelope that would otherwise authorize a consequential action, so
the D-B5 degradation rule was load-bearing nowhere: deleting it left A10's verdict
unchanged. Section E drives a synthetic stimulus through the real action-emission
path — clean refuses citing degradation, `ignore_degradation` seeded and the action
emits. That is the only place the rule is shown discriminating, and no fixture-driven
coverage of it is claimed.

The same rule applies to the P2S-05 traces: three of five previously asserted literal
constants and could not fail. Every trace verdict is now computed from the
`PolicyPlane`/lease/receipt objects the trace manipulates, and each is proven to flip
under a seeded defect in its own mechanism (`falsifier` block in
`out/p2s05_linearization.json`).

## Declared NOT-SIMULATED

The R1 version of this section carried a **false completeness sentence** ("everything
not listed is implemented and exercised") while several D-B8 layers were implemented
but dead. That sentence is gone. The authoritative lists are `not_simulated` and
`exercised_by_composition_suite` in `out/gate_report.json`; together they cover the
D-B8 layers.

**Exercised through the real mechanism** (`run_composition.py`, each with a
composition-path defect that flips it): PC-1, PC-2, PC-3, PC-4, PC-6, PC-7, PC-9,
PC-10, PC-11, D-B8 §2 `scope`, D-B8 §2 `applicability_predicate`. PC-3 substitutes
the DAT render floor for the table's untrusted-quarantine floor and PC-7 substitutes
the `attention` domain as its third domain; both are mechanism-equivalent and each
case says so.

**Accounted elsewhere:** PC-12 is mechanically PC-2's shape (an equal-priority
contradiction failing closed) and is exercised fixture-side through A4's
policy-version dispute. It appeared in neither list before; duplicating `pc2` would
add no mechanism, so it is listed rather than re-driven.

**Not exercised** — no coverage implied:

- D-B8 `conflict_behavior` — schema field carried, not used as a resolution input.
- D-B8 `rollback_pointer` / PC-5 rollback-vs-history — nothing generates a rollback.
- D-B8 `schema_compat` gating — the corpus has one schema version (SV-1).
- D-B8 PC-6 is enforced at **composition** time; D-B8 grades **authoring**-time
  rejection as the required protection. The simulator models no authoring surface,
  so the protection is demonstrated one stage later than the design specifies.
- D-B8 PC-8 (two policies constraining different fields of one action) — composition
  is per governed output, not per action field.
- Calibration-plane versioning (D-B9 §6) — carried in the basis, never varied.
- Live DP-001 ack-latency measurement — a build-gate obligation, not a design one.
- 13 of 39 registered D-B9 event types are never emitted by any scenario — the
  taxonomy is declared, not exercised, for those.
- D-B5 degraded-operation authority and the D-B7 §3 interrupt-policy citation rule
  are encoded from the rule text **quoted in Rework Packet R2**; neither document is
  in the Builder snapshot.
- D-B5's degradation rule has **no discriminating fixture-driven coverage**: A10's
  refusal is over-determined by its `internal-write` envelope, so the rule is shown
  load-bearing only by the harness self-test (`run_defects.py` section E).
- D-B8 §2 `scope`, `applicability_predicate` and `effective_window` execute **only**
  in the synthetic composition suite. No fixture supplies a policy that is out of
  scope, predicate-excluded, or outside its window.
- Pass-rule checks `external_receipt_ownership`, `fail_closed` and `step_up_enforced`
  are implemented but **no fixture pass rule ever selects them**; `receipt_required`
  is selected only by S3, where it is vacuous (S3 emits no action, so the check has
  nothing to look at and is not recorded as evidence). Reported per run.
- **All four expected dimensions are compared** (route, attention, authority,
  receipt) as of TASK-0004. Before it, only attention and a partial authority
  mapping were compared at all: the verifier replaced one fixture's route,
  authority or receipt with an impossible value, and replaced all 27 authority
  values at once, and the gate returned PASS every time. `oracle_schema.py` types
  each expectation (EXACT / ALTERNATIVES / CEILING / CONDITIONAL / STRUCTURAL /
  RELATIONAL / PRESENTATION / NOT_APPLICABLE / UNMAPPED) and the judge compares it.
  Coverage per dimension, of 27 fixtures: **route 26, attention 22, authority 24
  (+3 the corpus marks "—"), receipt 25 (+2 marked "—")**.
- **A fail-closed coverage floor makes mapping collapse impossible.**
  `DECLARED_COVERAGE` records the classification each fixture-dimension pair is
  known to produce; a run that resolves WEAKER than the declaration fails the gate,
  while resolving stronger is allowed and reported. That is what turns "unmapped"
  from a coverage note into a verdict — an unrecognised expected value makes a
  declared-mapped pair unmappable, which fails.
- Every one of the six declared-unmappable pairs carries a **recorded reason**, and
  `run_oracle_mutations.py` fails if one does not. A sentinel cannot contradict a
  claim that does not exist, so those pairs are reported as *not rejectable* rather
  than counted as either passes or holes.
- Two comparison semantics, and the split is grounded rather than convenient.
  Expectations naming a demanding band (Critical, Needs-Owner) or a specific channel
  (Briefing) are compared for **equality**; a "Hub" expectation is an equality on band
  **and** flag. Expectations of "None", "Record-only" or a pure display surface are
  compared as a **ceiling** — the computed band must not reach Needs-Owner — because
  the corpus itself uses "None" that way: A11 pairs `attention: "None"` with a
  `"monthly digest"` receipt and a forbidden entry reading literally "owner attention
  consumed"; S5 pairs `"None (brief line only)"` with a `"Desk brief line"` receipt.
  Reading those as equality against Record-only would contradict the fixtures' own
  receipts. The ceiling reading is weaker than equality and is labelled as such in
  every shipped record.
- The interrupt-policy citation is parsed twice — once engine-side, once oracle-side —
  by functions that are currently byte-identical in body. The independence is
  **structural** (a change to one cannot drag the other along, which is what lets the
  judge disagree with the engine), **not diverse**: a start_state phrasing neither
  regex matches would be invisible to both.

The quarantine rule is a Builder **operationalization**: D-B6 §2.2 scopes quarantine
to "where the governing policy requires it", and this engine hard-codes the
unclassifiable-source test instead of expressing it as a governing PolicyObject. The
direction matches the document; the mechanism is not the policy-driven form.

## Seeded-defect falsifier suite

`run_defects.py` seeds each defect, re-runs all 81 combinations, and requires each to
flip at least one previously-passing combination to FAIL. If any seeded defect still
passes everywhere, **the harness itself fails acceptance** and the runner exits
non-zero.

| Defect | P2S-01 class it witnesses |
| --- | --- |
| `authority-raise` | changes authority — a model proposal raises the ceiling above the model-free base |
| `dropped-receipt` | drops a receipt — the action still advances to executed with no evidence |
| `causal-reorder` | reorders a causal event — delivery is permuted and the topological sort disabled |
| `forbidden-outcome-admission` | admits a forbidden outcome — state written on a read-only path |
| `stale-projection` | produces a stale projection — S3 projections are not rebuilt |
| `engine-authored-receipt` | breaks external-receipt ownership |
| `skip-eligibility-check` | P2S-07 — proposals from untrusted content with no eligibility policy |
| `normalizer-authority-leak` | E2E-1 — a substituted normalizer raises the maximum authorized action |

A second layer (`mutations.py`, 62 candidate defects) exists purely to prove
predicate reachability — see "Evidence counts" above. No catalogue entry is dead:
the runner fails if any mutation witnesses no predicate and no judge check.

## Outputs

| File | Contents |
| --- | --- |
| `out/results.json` | computed result per fixture x shape: tier, ceiling, attention, events, executed/verified, fold digest, reasons |
| `out/judgements.json` | pass/fail per combination with every forbidden predicate evaluated |
| `out/divergences.json` | candidate-specific divergences |
| `out/seeded_defects.json` | falsifier proof + per-predicate reachability with named witnesses |
| `out/p2s06_shuffle_invariance.json` | digests across seeded permutations |
| `out/p2s05_linearization.json` | the five policy/lease traces |
| `out/p2s07_eligibility.json` | negative and positive eligibility tests |
| `out/anticircularity.json` | the three-way boundary proof |
| `out/oracle_mutations.json` | P2T-01 — verifier probes defeated, sentinel + contradictory corruption per fixture-dimension pair |
| `out/basis_validation.json` | P2T-02 — missing-basis cases, each with its defect witness |
| `out/p2s04_schedule_liveness.json` | P2T-03 — the three schedule-liveness behaviors and their targeted defects |
| `out/gate_report.json` | acceptance-criteria table |

## Scope and limits

- Documentation/design-test tooling only. No runtime deployment, no production
  credentials, no network, no real owner data. `M1`/`M2` in E2E-1 are deterministic
  local functions, not live model invocations.
- The scenario encodings translate each fixture's prose narrative into structured
  parameters. That translation is Builder-authored mechanical encoding, and it is the
  layer most worth reviewer scrutiny: a mis-encoded stimulus would produce a confidently
  wrong computed result. Each entry quotes the fixture text it derives from. The R1
  rework corrected six of them (A7, S2, A4, A8, A13, A15) where dropped or reshaped
  input-side facts had made the fixture's central hazard untestable.
- `scenarios.py`'s `derived` dict mixes D-B2 §2.3 computed fields (`domain`, `aging`,
  `blocking`) with Builder-authored encodings of narrative facts. Its module docstring
  says which is which; do not read the whole dict as "derived" in the design's sense.
- The engine models the design rules as specified in the hash-bound sources; it is not
  an implementation of the Decision Engine and makes no claim to be.
