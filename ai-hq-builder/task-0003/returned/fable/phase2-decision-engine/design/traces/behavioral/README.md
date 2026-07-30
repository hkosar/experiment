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
```

All runners default to `--fixtures ../../../03F_Replay_Fixtures.json` (the frozen
corpus at its packet-relative path) and `--out out`. Outputs land in `out/`.

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

## Outputs

| File | Contents |
| --- | --- |
| `out/results.json` | computed result per fixture x shape: tier, ceiling, attention, events, executed/verified, fold digest, reasons |
| `out/judgements.json` | pass/fail per combination with every forbidden predicate evaluated |
| `out/divergences.json` | candidate-specific divergences |
| `out/seeded_defects.json` | falsifier proof — which combinations each defect flipped |
| `out/p2s06_shuffle_invariance.json` | digests across seeded permutations |
| `out/p2s05_linearization.json` | the five policy/lease traces |
| `out/p2s07_eligibility.json` | negative and positive eligibility tests |
| `out/anticircularity.json` | the three-way boundary proof |
| `out/gate_report.json` | acceptance-criteria table |

## Scope and limits

- Documentation/design-test tooling only. No runtime deployment, no production
  credentials, no network, no real owner data. `M1`/`M2` in E2E-1 are deterministic
  local functions, not live model invocations.
- The scenario encodings translate each fixture's prose narrative into structured
  parameters. That translation is Builder-authored mechanical encoding, and it is the
  layer most worth reviewer scrutiny: a mis-encoded stimulus would produce a confidently
  wrong computed result. Each entry quotes the fixture text it derives from.
- The engine models the design rules as specified in the hash-bound sources; it is not
  an implementation of the Decision Engine and makes no claim to be.
