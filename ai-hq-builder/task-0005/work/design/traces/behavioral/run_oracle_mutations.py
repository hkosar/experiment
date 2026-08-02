"""Oracle-mutation suite — proof that every expected dimension is load-bearing.

Verifier finding P2T-01 was demonstrated with four probes: change one fixture's
`expected.route`, `expected.authority` or `expected.receipt` to an impossible
sentinel, or replace all 27 authority values at once, and the gate still returned
PASS. This runner reproduces those probes and every generalisation of them, and
requires each to FAIL.

Five sections:

  A  VERIFIER PROBES — the exact four probes from `28A_Verifier_Probe_Evidence`,
     re-run against the corrected harness. Each must now produce a gate failure.
     A probe that still passes fails this runner.

  A2 P2U-01 PRESENTATION PROBES — the two probes from `32A_`, which rewrote S1's
     receipt to "completely wrong card" and "completely wrong summary surface". Both
     stayed inside the old PRESENTATION kind, both were still reported MAPPED, and
     the gate passed. These are reported here honestly, and the honest report is not
     "the gate now fails on them": the harness no longer claims to check those values.
     The requirement this section enforces is the one the reclassification makes
     true — NO mutated presentation value may be counted as mapped or compared on any
     shape. A mutation that comes back classified `mapped` fails this runner.

  B  SENTINEL CORRUPTION — for every fixture and every one of the four dimensions
     (108 pairs), replace the expected value with an unrecognised sentinel. The
     fail-closed coverage floor must reject it: a declared-mapped pair becoming
     unmappable, a declared not-simulated pair becoming unmappable, or a declared
     not-applicable pair becoming anything else, is a gate failure. This is what makes
     "unmapped" safe rather than a free pass.

  C  CONTRADICTORY-BUT-VALID CORRUPTION — the verifier's closure falsifier: "replacing
     the expected value with a contradictory but schema-valid value must cause that
     fixture/shape to fail." Rather than inventing values, this section SWAPS IN
     ANOTHER FIXTURE'S REAL VALUE for the same dimension — schema-valid by
     construction, since it is a value the frozen corpus already contains. For each
     declared-mapped pair it reports the swapped value that flips the case. A pair no
     corpus value can flip is reported as NOT LOAD-BEARING and fails this runner,
     because a dimension that cannot disagree is not evidence.

  D  SAME-KIND CONTRADICTORY CORRUPTION (P2U-01) — section C's weakness, named by the
     verifier: "The supplied contradictory-witness routine proves that SOME borrowed
     wrong value can fail, often because it changes the expectation kind or adds a
     structural feature. It does not prove that the original presentation value is
     evaluated." This section repeats C with the borrowed values restricted to those
     that parse to the SAME kind AND differ in what the judge would actually look at
     (`Expectation.comparable_content`). A governed pair with at least one same-kind
     alternative in the corpus must have at least one that flips it; if every
     genuinely different same-kind value still passes, the comparator is not reading
     the value and this runner fails. A pair the corpus offers no same-kind
     alternative for is reported as such — an honest limit of a corpus-borrowing
     probe, not a hole, and never counted as evidence it is not.

  E  DEFECT WITNESS — the P2U-01 defect restored, so the new guards are observed
     failing rather than asserted. E1 puts a mapped-with-empty-comparator receipt
     back and requires the judge invariant to fail all five cases. E2 removes one
     declared coarsened comparison and requires section D to report it as a hole.

Exit code 0 only if every probe is defeated, no mutated presentation value is counted
as mapped or compared, every sentinel is rejected, every governed fixture-dimension
pair has a named contradictory witness, every governed pair is either same-kind
falsifiable or a declared coarsened comparison, every pair excluded from the compared
set carries a recorded reason, and both defect witnesses are caught.

Usage:  python3 run_oracle_mutations.py [--fixtures PATH] [--out DIR]
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
from dataclasses import replace
from typing import Dict, List, Optional

import oracle
import oracle_schema
import scenarios as scen
from events import SHAPES
from fixture_io import load_oracle, load_stimuli
from judge import judge
from simulate import Defects, simulate

SENTINELS = {
    "route": "__IMPOSSIBLE_ROUTE__",
    "attention": "__IMPOSSIBLE_ATTENTION__",
    "authority": "__IMPOSSIBLE_AUTHORITY__",
    "receipt": "__IMPOSSIBLE_RECEIPT__",
}


def _corrupt(oc, dimension: str, value: str):
    """Return a copy of one OracleCase with a single expected dimension replaced."""
    expected = copy.deepcopy(oc.expected) if isinstance(oc.expected, dict) else {}
    expected[dimension] = value
    return replace(oc, expected=expected)


# Every simulation in this runner uses the same clean `Defects()`, so the computed
# result for a (fixture, shape) pair is a pure function of the frozen stimulus. Only
# the ORACLE side varies across the mutations below, which is the point of the suite.
# Memoized because section D judges each candidate value against every computed result
# in the corpus, and re-simulating 81 combinations per candidate is the difference
# between a two-second run and a four-minute one.
_SIM_CACHE: Dict[str, object] = {}


def _simulate(stim, shape: str):
    key = "%s/%s" % (stim.id, shape)
    if key not in _SIM_CACHE:
        _SIM_CACHE[key] = simulate(stim, shape, Defects())
    return _SIM_CACHE[key]


def _case_passes(stim, oracle_case, shape: str) -> bool:
    return judge(_simulate(stim, shape), oracle_case, stim, scen.get(stim.id)).passed


def _judge_case(stim, oracle_case, shape: str):
    return judge(_simulate(stim, shape), oracle_case, stim, scen.get(stim.id))


def _dimension_verdict(j, dimension: str) -> bool:
    """Did ONE dimension pass, on this computed result, under this expected value?

    Deliberately excludes `passed` and the coverage floor: swapping fixture F's value
    onto fixture G trips G's floor, which says nothing about whether the comparator
    reads the value.

    Deliberately excludes the NAMES of the comparisons too, and that is a correction
    made during this task rather than a first draft. The first version returned the
    executed-comparison tuple alongside the verdict, and every one of the nine
    ceiling-kind attention pairs came back "discriminating" on the strength of an
    EXTRA CHECK THAT ALSO PASSED — 'display-only' runs the read-path surface check and
    'None' does not, so the tuples differed while both values passed everywhere. That
    is not the judge telling two expectations apart; it is the judge doing slightly
    more work for one of them. Discrimination means one value passes where the other
    fails, and nothing less counts here.
    """
    parts = [j.check_results.get("expected_" + dimension)]
    if dimension == "attention":
        parts.append(j.check_results.get("expected_attention_surface"))
    return all(p for p in parts if p is not None)


def _expectation_shape(dimension: str, fixture: str, raw: str):
    """(kind, comparable-content) for one raw expected value, for any dimension.

    Route, authority and receipt go through the typed schema. Attention has its own
    parser in `oracle.py` (it predates the schema and owns the D-B7 band vocabulary),
    so its kind and content are derived from the flags that decide which branch of
    `judge` runs — which is the same question `Expectation.comparable_content` answers
    for the other three: what would a comparison of this value actually look at?
    """
    if dimension in oracle_schema.PARSERS:
        exp = oracle_schema.PARSERS[dimension](fixture, raw)
        return exp.kind, exp.comparable_content()
    att = oracle.expected_attention({"attention": raw}, fixture)
    kind = ("UNMAPPED" if not att.mapped else
            "RELATIONAL" if att.relational else
            "HUB_UPDATE" if att.hub_update else
            "CONDITIONAL" if att.conditional else
            "MULTI_BAND" if len(att.bands) > 1 else
            "CEILING" if att.ceiling_only else "EXACT")
    return kind, (kind, tuple(att.bands), att.conditional,
                  bool(att.surface and "display" in att.surface.lower()))


def _corpus_passes(stimuli, cases) -> bool:
    """True only if EVERY combination passes — the gate's own pass condition."""
    for stim in stimuli:
        for shape in SHAPES:
            if not _case_passes(stim, cases[stim.id], shape):
                return False
    return True


# --------------------------------------------------------------------------
# A — the verifier's own probes
# --------------------------------------------------------------------------

def verifier_probes(stimuli, cases) -> List[Dict[str, object]]:
    by_id = {s.id: s for s in stimuli}
    out: List[Dict[str, object]] = []

    for dim in ("route", "authority", "receipt"):
        mutated = dict(cases)
        mutated["S1"] = _corrupt(cases["S1"], dim, SENTINELS[dim])
        passed = _corpus_passes(stimuli, mutated)
        out.append({
            "probe": "28A_/oracle_mutation_probes/%s" % dim,
            "mutation": "S1 expected.%s=%s" % (dim, SENTINELS[dim]),
            "verifier_observed": "gate PASS",
            "now": "gate PASS" if passed else "gate FAIL",
            "defeated": not passed,
        })

    mutated = {fid: _corrupt(oc, "authority", SENTINELS["authority"])
               for fid, oc in cases.items()}
    passed = _corpus_passes(stimuli, mutated)
    out.append({
        "probe": "28A_/oracle_mutation_probes/all_authority_values",
        "mutation": "all 27 expected.authority values replaced by an unrecognised sentinel",
        "verifier_observed": "gate PASS, 0 mapped / 81 unmapped",
        "now": "gate PASS" if passed else "gate FAIL",
        "defeated": not passed,
    })
    del by_id
    return out


# --------------------------------------------------------------------------
# A2 — the P2U-01 presentation probes from `32A_`
# --------------------------------------------------------------------------

# The verifier's two mutations, verbatim from `32A_/probes/P2U-01/mutations`.
PRESENTATION_PROBES = (
    ("S1", "receipt", "Desk view", "completely wrong card"),
    ("S1", "receipt", "Desk view", "completely wrong summary surface"),
)


def presentation_probes(stimuli, cases) -> List[Dict[str, object]]:
    """Reproduce `32A_`'s P2U-01 mutations and report what they now resolve to.

    What the verifier observed: both values stayed PRESENTATION, all three shapes
    reported the receipt dimension as MAPPED, and the gate returned exit code 0.

    What is true now: PRESENTATION is not a kind any more. Both values resolve
    NOT_SIMULATED, which is what S1's own untouched "Desk view" resolves to as well —
    so the classification is unchanged by the mutation, and the gate still returns 0.
    THAT IS THE POINT, and stating it any other way would be the dishonesty the
    finding is about: the harness does not compare these values, so mutating one
    cannot make it fail. What changed is that it no longer says it compares them.

    The enforceable claim, and what this function fails on: the mutated value is never
    reported MAPPED and never appears in a `dimension_comparisons` list. A run in
    which a presentation mutation comes back mapped, or comes back carrying an
    executed comparison, is the P2U-01 defect back again.
    """
    by_id = {s.id: s for s in stimuli}
    out: List[Dict[str, object]] = []
    for fixture, dim, before, after in PRESENTATION_PROBES:
        mutated = _corrupt(cases[fixture], dim, after)
        classes, comparisons = [], []
        for shape in SHAPES:
            j = _judge_case(by_id[fixture], mutated, shape)
            classes.append(j.dimension_results.get(dim))
            comparisons.extend(j.dimension_comparisons.get(dim) or [])
        gate_passes = _corpus_passes(stimuli, dict(cases, **{fixture: mutated}))
        counted_mapped = any(c == "mapped" for c in classes)
        out.append({
            "probe": "32A_/probes/P2U-01",
            "mutation": "%s expected.%s: %r -> %r" % (fixture, dim, before, after),
            "verifier_observed": "kind PRESENTATION, mapped on all 3 shapes, gate PASS",
            "classification_now": sorted(set(c for c in classes if c)),
            "comparisons_executed_now": sorted(set(comparisons)),
            "gate_now": "PASS" if gate_passes else "FAIL",
            "counted_as_mapped": counted_mapped,
            "counted_as_compared": bool(comparisons),
            # The claim under test is NOT "the gate fails on this mutation" — see the
            # docstring. It is that the mutated value is excluded from the compared
            # set, which is the branch of the required correction this return took.
            "excluded_from_compared_set": not counted_mapped and not comparisons,
        })
    return out


# --------------------------------------------------------------------------
# B — sentinel corruption over all 108 fixture-dimension pairs
# --------------------------------------------------------------------------

def sentinel_matrix(stimuli, cases) -> Dict[str, object]:
    """Corrupt every fixture-dimension pair with an unrecognised value.

    Three outcomes, kept apart because conflating them is how "unmapped" became a
    free pass in the first place:

      rejected        the corruption fails the case — what a governed pair must do,
                      and what a declared not-applicable pair must do too (the corpus
                      is frozen, so a dimension that stops being "—" is a corpus edit
                      or a parser regression).
      not-rejectable  the pair is DECLARED unmappable or not-simulated: it carries no
                      comparable claim, so replacing one uncomparable value with
                      another changes nothing. This is the honest limit of a sentinel
                      probe, not a hole — and each such pair must carry a recorded
                      rationale, or it is indistinguishable from an oversight and
                      fails here.
      survived        a governed pair whose corruption still passed. A real hole.

    P2U-01: the five reclassified receipt pairs are declared `not-simulated`, and the
    sentinel is still REJECTED for all five — `__IMPOSSIBLE_RECEIPT__` names no
    projection surface, so it resolves UNMAPPED, and the floor forbids
    not-simulated -> unmappable. That is a narrower claim than the one those pairs
    used to make and it is the only one that is true: the classification is checked,
    the value is not.
    """
    by_id = {s.id: s for s in stimuli}
    rows: List[Dict[str, object]] = []
    survived: List[str] = []
    not_rejectable: List[str] = []
    missing_rationale: List[str] = []
    for stim in stimuli:
        for dim in oracle_schema.DIMENSIONS:
            decl = oracle_schema.declared(dim, stim.id)
            mutated = _corrupt(cases[stim.id], dim, SENTINELS[dim])
            fails = [sh for sh in SHAPES if not _case_passes(by_id[stim.id], mutated, sh)]
            rejected = len(fails) == len(SHAPES)
            key = "%s/%s" % (stim.id, dim)
            if decl in ("unmappable", "not-simulated"):
                outcome = "rejected" if rejected else "not-rejectable"
                if not rejected:
                    not_rejectable.append(key)
                    if not oracle_schema.excluded_rationale(dim, stim.id):
                        missing_rationale.append(key)
            else:
                outcome = "rejected" if rejected else "survived"
                if not rejected:
                    survived.append(key)
            rows.append({
                "fixture": stim.id, "dimension": dim, "declared": decl,
                "shapes_failed": len(fails), "outcome": outcome,
            })
    return {"pairs": len(rows),
            "rejected": sum(1 for r in rows if r["outcome"] == "rejected"),
            "not_rejectable": not_rejectable,
            "missing_rationale": missing_rationale,
            "survived": survived, "rows": rows}


# --------------------------------------------------------------------------
# C — contradictory-but-schema-valid corruption (the closure falsifier)
# --------------------------------------------------------------------------

def contradiction_matrix(stimuli, cases) -> Dict[str, object]:
    by_id = {s.id: s for s in stimuli}
    ids = [s.id for s in stimuli]
    rows: List[Dict[str, object]] = []
    not_load_bearing: List[str] = []

    for stim in stimuli:
        for dim in oracle_schema.DIMENSIONS:
            if oracle_schema.declared(dim, stim.id) != "mapped":
                continue                      # not a governed pair; section B covers it
            own = str((cases[stim.id].expected or {}).get(dim) or "")
            witness: Optional[str] = None
            witness_from: Optional[str] = None
            for other in ids:
                if other == stim.id:
                    continue
                alt = str((cases[other].expected or {}).get(dim) or "")
                if not alt or alt == own:
                    continue
                mutated = _corrupt(cases[stim.id], dim, alt)
                if all(not _case_passes(by_id[stim.id], mutated, sh) for sh in SHAPES):
                    witness, witness_from = alt, other
                    break
            rows.append({
                "fixture": stim.id, "dimension": dim, "own_value": own,
                "contradictory_value": witness, "borrowed_from": witness_from,
                "load_bearing": witness is not None,
            })
            if witness is None:
                not_load_bearing.append("%s/%s" % (stim.id, dim))

    return {"governed_pairs": len(rows),
            "load_bearing": sum(1 for r in rows if r["load_bearing"]),
            "not_load_bearing": not_load_bearing, "rows": rows}


# --------------------------------------------------------------------------
# D — same-kind contradictory corruption (P2U-01)
# --------------------------------------------------------------------------

def same_kind_matrix(stimuli, cases) -> Dict[str, object]:
    """Section C, restricted to borrowed values that DO NOT change the kind.

    A witness that flips a case by changing the expectation's kind proves the kind is
    load-bearing. It does not prove the VALUE is read — which is exactly how five
    receipt expectations kept a clean bill of health for two cycles while comparing
    nothing. A candidate qualifies here only if, parsed against this fixture, it

      * resolves to the same kind as the fixture's own value, and
      * differs in `comparable_content()` — the tuple the judge would actually look
        at. A corpus value that merely re-words the same claim is not a
        counter-example and is not counted as one.

    Outcomes, strongest first:

      witness        at least one qualifying value flips this fixture on every shape.

      discriminating-elsewhere
                     nothing the corpus offers flips THIS fixture, but the judge does
                     reach a different conclusion for the own value and some
                     alternative on some other computed result. The comparator reads
                     the value; the corpus simply contains no same-kind value this
                     fixture contradicts. Named with the (fixture, shape) where the
                     two verdicts diverge, so the claim is checkable.

      value-blind    the judge returns an IDENTICAL dimension verdict for the own
                     value and every same-kind alternative on ALL 81 computed
                     results. The comparator does not read the differing part of the
                     value. This is the P2U-01 shape, one degree less severe (a
                     comparison does run), and it fails this runner unless the pair is
                     declared in `oracle_schema.COARSENED_COMPARISONS` with a stated
                     reason. A declaration that no longer holds also fails.

      no-alternative the frozen corpus contains no same-kind value with different
                     content for this pair. Reported, never counted as evidence. A
                     limit of borrowing from a 27-row corpus, not a finding.

    The observational test runs on the CLEAN corpus. A difference visible only under
    an injected defect is not counted here — `run_defects.py` is where defect-side
    discrimination is proven, and conflating the two would let this section claim
    coverage it did not exercise.
    """
    by_id = {s.id: s for s in stimuli}
    ids = [s.id for s in stimuli]
    rows: List[Dict[str, object]] = []
    survived: List[str] = []
    no_alternative: List[str] = []
    coarsened: List[str] = []
    stale_declarations: List[str] = []

    for stim in stimuli:
        for dim in oracle_schema.DIMENSIONS:
            if oracle_schema.declared(dim, stim.id) != "mapped":
                continue
            own = str((cases[stim.id].expected or {}).get(dim) or "")
            own_kind, own_content = _expectation_shape(dim, stim.id, own)

            candidates: List[str] = []
            for other in ids:
                if other == stim.id:
                    continue
                alt = str((cases[other].expected or {}).get(dim) or "")
                if not alt or alt == own or alt in candidates:
                    continue
                alt_kind, alt_content = _expectation_shape(dim, stim.id, alt)
                if alt_kind == own_kind and alt_content != own_content:
                    candidates.append(alt)

            key = "%s/%s" % (stim.id, dim)
            declared_coarse = (dim, stim.id) in oracle_schema.COARSENED_COMPARISONS
            witness: Optional[str] = None
            flipped = 0
            for alt in candidates:
                mutated = _corrupt(cases[stim.id], dim, alt)
                if all(not _case_passes(by_id[stim.id], mutated, sh) for sh in SHAPES):
                    flipped += 1
                    if witness is None:
                        witness = alt

            divergence: Optional[Dict[str, str]] = None
            if candidates and witness is None:
                divergence = _first_divergence(stimuli, cases, dim, own, candidates)

            if not candidates:
                outcome = "no-alternative"
                no_alternative.append(key)
            elif witness is not None:
                outcome = "witness"
            elif divergence is not None:
                outcome = "discriminating-elsewhere"
            else:
                outcome = "value-blind"
                coarsened.append(key)
                if not declared_coarse:
                    survived.append(key)
            if declared_coarse and outcome != "value-blind":
                stale_declarations.append("%s (declared coarsened, resolved %s)"
                                          % (key, outcome))
            rows.append({
                "fixture": stim.id, "dimension": dim, "kind": own_kind,
                "own_value": own, "same_kind_alternatives": len(candidates),
                "alternatives_that_flip": flipped,
                "same_kind_witness": witness, "outcome": outcome,
                "divergence_elsewhere": divergence,
                "declared_coarsened": declared_coarse,
            })

    return {"governed_pairs": len(rows),
            "with_witness": sum(1 for r in rows if r["outcome"] == "witness"),
            "discriminating_elsewhere": sum(
                1 for r in rows if r["outcome"] == "discriminating-elsewhere"),
            "value_blind": coarsened,
            "stale_declarations": stale_declarations,
            "no_alternative": no_alternative, "survived": survived, "rows": rows}


def _first_divergence(stimuli, cases, dimension: str, own: str,
                      candidates: List[str]) -> Optional[Dict[str, str]]:
    """The first computed result on which `own` and some candidate are judged apart.

    Judges every other fixture/shape twice — once with the own value substituted for
    that fixture's own, once with the candidate — and compares only the dimension
    verdict. Returns the naming evidence, or None if the judge never tells them apart.
    """
    for alt in candidates:
        for other in stimuli:
            base = cases[other.id]
            with_own = _corrupt(base, dimension, own)
            with_alt = _corrupt(base, dimension, alt)
            for shape in SHAPES:
                vo = _dimension_verdict(_judge_case(other, with_own, shape), dimension)
                va = _dimension_verdict(_judge_case(other, with_alt, shape), dimension)
                if vo != va:
                    return {"alternative": alt, "distinguished_on": other.id,
                            "shape": shape,
                            "dimension_passes_with_own_value": vo,
                            "dimension_passes_with_alternative": va}
    return None


# --------------------------------------------------------------------------
# E — the P2U-01 defect witness
# --------------------------------------------------------------------------

def _defective_parse_receipt(fixture: str, raw: str):
    """`parse_receipt` with the P2U-01 defect restored, and nothing else changed.

    The original defect was `KIND_PRESENTATION in MAPPED_KINDS`: a receipt naming a
    projection surface resolved to a MAPPED kind carrying only a `surface` string,
    with empty `requires`, empty `forbids`, and no branch in `_compare_dimension`. Any
    mapped kind with an empty comparator reproduces it exactly, and STRUCTURAL with no
    features is that in one line — no switch inside the schema, no second definition
    of "mapped" to keep in sync.
    """
    exp = oracle_schema.parse_receipt(fixture, raw)
    if exp.kind != oracle_schema.KIND_NOT_SIMULATED:
        return exp
    return replace(exp, kind=oracle_schema.KIND_STRUCTURAL,
                   rationale="P2U-01 DEFECT WITNESS: mapped with an empty comparator")


def defect_witness(stimuli, cases) -> Dict[str, object]:
    """Put the defect back and show both new guards catching it.

    A guard that has never been observed failing is a claim, not a check — the same
    reason every case in `run_basis.py` ships the fold that accepts it.

    E1 restores the defect and shows the JUDGE INVARIANT catching it: all five
    receipts come back `mapped` with zero comparisons, and every case fails.

    E1 does NOT reach section D, and saying otherwise would be the overstatement this
    return exists to stop making. The invariant fails the case first, so under the
    restored defect every borrowed value "flips" and section D records a witness — it
    never gets to ask whether the value is read. The layers are ordered, and E1
    exercises the first one only.

    E2 therefore exercises section D's own failure path directly: drop one entry from
    `COARSENED_COMPARISONS` and the pair it described must be reported `survived`. The
    detector is already exercised on the live corpus (nine pairs resolve value-blind);
    what E2 adds is the demonstration that an UNDECLARED one fails the run.

    `oracle_schema.PARSERS` and `COARSENED_COMPARISONS` are mutated for the duration
    and restored in `finally`; the runner's other sections have already completed.
    """
    by_id = {s.id: s for s in stimuli}
    affected = sorted(f for (d, f) in oracle_schema.NOT_SIMULATED_RATIONALE
                      if d == "receipt")

    original = oracle_schema.PARSERS["receipt"]
    oracle_schema.PARSERS["receipt"] = _defective_parse_receipt
    try:
        rows: List[Dict[str, object]] = []
        for fid in affected:
            j = _judge_case(by_id[fid], cases[fid], "S1")
            empty = [f for f in j.failures if "empty comparator" in f]
            rows.append({
                "fixture": fid,
                "receipt_value": str((cases[fid].expected or {}).get("receipt") or ""),
                "classification_under_defect": j.dimension_results.get("receipt"),
                "comparisons_under_defect": j.dimension_comparisons.get("receipt") or [],
                "case_passed_under_defect": j.passed,
                "invariant_fired": bool(empty),
                "invariant_message": empty[0] if empty else None,
            })
    finally:
        oracle_schema.PARSERS["receipt"] = original

    # E2 — section D's failure path, with the live corpus and no defective parser.
    dropped_key = sorted(oracle_schema.COARSENED_COMPARISONS)[0]
    saved = dict(oracle_schema.COARSENED_COMPARISONS)
    del oracle_schema.COARSENED_COMPARISONS[dropped_key]
    try:
        sk = same_kind_matrix(stimuli, cases)
    finally:
        oracle_schema.COARSENED_COMPARISONS.clear()
        oracle_schema.COARSENED_COMPARISONS.update(saved)

    dropped_pair = "%s/%s" % (dropped_key[1], dropped_key[0])
    return {
        "defect": "KIND_PRESENTATION restored as a mapped kind with an empty comparator",
        "fixtures": affected,
        "judge_invariant": rows,
        "invariant_fired_for": sum(1 for r in rows if r["invariant_fired"]),
        "all_cases_failed_under_defect": all(not r["case_passed_under_defect"]
                                             for r in rows),
        "e1_reaches_section_d": False,
        "e2_dropped_declaration": dropped_pair,
        "e2_reported_survived": sorted(sk["survived"]),
        "e2_detected": sk["survived"] == [dropped_pair],
    }


def run(fixtures_path: str, out_dir: str) -> Dict[str, object]:
    stimuli = load_stimuli(fixtures_path)
    cases = load_oracle(fixtures_path)

    clean = _corpus_passes(stimuli, cases)
    probes = verifier_probes(stimuli, cases)
    presentation = presentation_probes(stimuli, cases)
    sentinel = sentinel_matrix(stimuli, cases)
    contradiction = contradiction_matrix(stimuli, cases)
    same_kind = same_kind_matrix(stimuli, cases)
    witness = defect_witness(stimuli, cases)

    payload = {
        "summary": {
            "clean_corpus_passes": clean,
            "verifier_probes": len(probes),
            "verifier_probes_defeated": sum(1 for p in probes if p["defeated"]),
            "presentation_probes": len(presentation),
            "presentation_probes_excluded": sum(
                1 for p in presentation if p["excluded_from_compared_set"]),
            "sentinel_pairs": sentinel["pairs"],
            "sentinel_rejected": sentinel["rejected"],
            "sentinel_not_rejectable": sentinel["not_rejectable"],
            "sentinel_missing_rationale": sentinel["missing_rationale"],
            "sentinel_survived": sentinel["survived"],
            "governed_pairs": contradiction["governed_pairs"],
            "contradiction_load_bearing": contradiction["load_bearing"],
            "not_load_bearing": contradiction["not_load_bearing"],
            "same_kind_with_witness": same_kind["with_witness"],
            "same_kind_discriminating_elsewhere": same_kind["discriminating_elsewhere"],
            "same_kind_value_blind": same_kind["value_blind"],
            "same_kind_stale_declarations": same_kind["stale_declarations"],
            "same_kind_no_alternative": same_kind["no_alternative"],
            "same_kind_survived": same_kind["survived"],
            "coverage_floor": oracle_schema.floor_counts(),
            "declared_accounting": oracle_schema.coverage_accounting(),
            "missing_exclusion_rationale": oracle_schema.missing_exclusion_rationale(),
            "defect_witness_invariant_fired": witness["invariant_fired_for"],
            "defect_witness_cases_failed": witness["all_cases_failed_under_defect"],
            "defect_witness_section_d_detected": witness["e2_detected"],
        },
        "verifier_probes": probes,
        "presentation_probes": presentation,
        "sentinel_corruption": sentinel,
        "contradictory_corruption": contradiction,
        "same_kind_corruption": same_kind,
        "defect_witness": witness,
        "coarsened_comparisons": {
            "%s/%s" % (f, d): v
            for (d, f), v in oracle_schema.COARSENED_COMPARISONS.items()},
        "declared_coverage": oracle_schema.DECLARED_COVERAGE,
        "unmappable_rationale": {"%s/%s" % k: v
                                 for k, v in oracle_schema.UNMAPPABLE_RATIONALE.items()},
        "not_simulated_rationale": {
            "%s/%s" % k: v
            for k, v in oracle_schema.NOT_SIMULATED_RATIONALE.items()},
    }
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "oracle_mutations.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    return payload


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures",
                    default=os.path.join("..", "..", "..", "03F_Replay_Fixtures.json"))
    ap.add_argument("--out", default="out")
    args = ap.parse_args(argv)

    payload = run(args.fixtures, args.out)
    s = payload["summary"]

    print("TASK-0004 oracle-mutation suite (P2T-01)")
    print("  clean corpus passes: %s" % s["clean_corpus_passes"])
    print()
    print("A. VERIFIER PROBES from 28A_ — each must now FAIL the gate")
    print("   %-56s %-12s %s" % ("MUTATION", "VERIFIER", "NOW"))
    for p in payload["verifier_probes"]:
        print("   %-56s %-12s %s%s" % (p["mutation"][:56], "PASS", p["now"],
                                       "" if p["defeated"] else "   *** NOT DEFEATED ***"))
    print("   defeated: %d / %d" % (s["verifier_probes_defeated"], s["verifier_probes"]))

    print()
    print("A2. P2U-01 PRESENTATION PROBES from 32A_ — the mutated value must be")
    print("    EXCLUDED from the compared set. The gate still passes on them, because")
    print("    the harness no longer claims to compare a projection surface it does")
    print("    not compute; what changed is the claim, not the verdict.")
    for p in payload["presentation_probes"]:
        print("   %s" % p["mutation"])
        print("     verifier saw : %s" % p["verifier_observed"])
        print("     now          : classification %s, comparisons %s, gate %s%s"
              % ("/".join(p["classification_now"]) or "-",
                 ", ".join(p["comparisons_executed_now"]) or "none",
                 p["gate_now"],
                 "" if p["excluded_from_compared_set"]
                 else "   *** STILL COUNTED AS COMPARED ***"))
    print("   excluded from the compared set: %d / %d"
          % (s["presentation_probes_excluded"], s["presentation_probes"]))

    print()
    print("B. SENTINEL CORRUPTION — every fixture x dimension, unrecognised value")
    print("   pairs corrupted : %d" % s["sentinel_pairs"])
    print("   rejected        : %d" % s["sentinel_rejected"])
    print("   not rejectable  : %d — declared UNMAPPABLE or NOT-SIMULATED, so there is"
          % len(s["sentinel_not_rejectable"]))
    print("                     no claim for a sentinel to contradict; each carries a"
          " recorded reason:")
    for key in s["sentinel_not_rejectable"]:
        fid, dim = key.split("/")
        print("       %-18s %s" % (key, oracle_schema.excluded_rationale(dim, fid)
                                   or "*** NO RATIONALE ***"))
    if s["sentinel_missing_rationale"]:
        print("   *** UNMAPPABLE WITHOUT A RECORDED REASON: %s ***"
              % ", ".join(s["sentinel_missing_rationale"]))
    if s["sentinel_survived"]:
        print("   *** SURVIVED (a governed pair passed while corrupted): %s ***"
              % ", ".join(s["sentinel_survived"]))
    else:
        print("   survived        : none — no governed pair passes while corrupted")

    print()
    print("C. CONTRADICTORY-BUT-VALID CORRUPTION — another fixture's real value")
    print("   governed pairs  : %d" % s["governed_pairs"])
    print("   load-bearing    : %d" % s["contradiction_load_bearing"])
    if s["not_load_bearing"]:
        print("   *** NOT LOAD-BEARING (no corpus value contradicts them): %s ***"
              % ", ".join(s["not_load_bearing"]))
    else:
        print("   not load-bearing: none — every governed pair has a named "
              "contradictory witness")

    print()
    print("D. SAME-KIND CONTRADICTORY CORRUPTION (P2U-01) — the borrowed value must")
    print("   parse to the SAME kind and differ in what the judge compares")
    print("   governed pairs  : %d" % payload["same_kind_corruption"]["governed_pairs"])
    print("   with a witness  : %d — a same-kind value flips the fixture itself"
          % s["same_kind_with_witness"])
    print("   discriminating  : %d — nothing in the corpus flips this fixture, but the"
          % s["same_kind_discriminating_elsewhere"])
    print("     elsewhere       judge tells the values apart on another computed "
          "result (named per row)")
    print("   value-blind     : %d — identical verdict for every same-kind value on"
          % len(s["same_kind_value_blind"]))
    print("                     all %d computed results; each must be declared:"
          % (len(payload["same_kind_corruption"]["rows"]) and
             3 * len(oracle_schema.DECLARED_COVERAGE["route"])))
    for key in s["same_kind_value_blind"]:
        fid, dim = key.split("/")
        print("       %-16s %s" % (key, oracle_schema.COARSENED_COMPARISONS.get(
            (dim, fid), "*** UNDECLARED ***")[:96]))
    print("   no alternative  : %d — the corpus offers no same-kind value with"
          % len(s["same_kind_no_alternative"]))
    print("                     different content; reported, not counted as evidence")
    for key in s["same_kind_no_alternative"]:
        print("       %s" % key)
    if s["same_kind_stale_declarations"]:
        print("   *** STALE COARSENED DECLARATIONS: %s ***"
              % ", ".join(s["same_kind_stale_declarations"]))
    if s["same_kind_survived"]:
        print("   *** SURVIVED (value-blind and NOT declared): %s ***"
              % ", ".join(s["same_kind_survived"]))
    else:
        print("   survived        : none — every governed pair either has a same-kind "
              "witness, is")
        print("                     shown discriminating elsewhere, or is a declared "
              "coarsened comparison")

    print()
    print("E. DEFECT WITNESS — the P2U-01 defect put back, and both guards catching it")
    w = payload["defect_witness"]
    print("   defect restored : %s" % w["defect"])
    print("   %-8s %-24s %-14s %-6s %s"
          % ("FIXTURE", "RECEIPT VALUE", "CLASSIFIED", "CMPS", "CASE / INVARIANT"))
    for r in w["judge_invariant"]:
        print("   %-8s %-24s %-14s %-6d %s"
              % (r["fixture"], r["receipt_value"][:24],
                 r["classification_under_defect"], len(r["comparisons_under_defect"]),
                 ("PASS *** NOT CAUGHT ***" if r["case_passed_under_defect"]
                  else "FAIL / invariant %s" % ("fired" if r["invariant_fired"]
                                                else "*** SILENT ***"))))
    print("   E1 does not reach section D: the invariant fails the case first, so every")
    print("   borrowed value flips and section D records a witness rather than a hole.")
    print("   E2 — drop the declaration for %s; section D must report it survived:"
          % w["e2_dropped_declaration"])
    print("        reported survived -> %s%s"
          % (", ".join(w["e2_reported_survived"]) or "none",
             "" if w["e2_detected"] else "   *** NOT DETECTED ***"))

    print()
    print("   declared coverage floor (fixtures that MUST map, per dimension): %s"
          % s["coverage_floor"])
    print("   declared accounting, per dimension (27 fixtures each):")
    for dim in oracle_schema.DIMENSIONS:
        a = s["declared_accounting"][dim]
        print("     %-10s mapped %2d | unmappable %2d | not-simulated %2d | "
              "not-applicable %2d | total %2d"
              % (dim, a["mapped"], a["unmappable"], a["not-simulated"],
                 a["not-applicable"], a["fixtures"]))
    if s["missing_exclusion_rationale"]:
        print("   *** EXCLUDED WITHOUT A RECORDED REASON: %s ***"
              % ", ".join(s["missing_exclusion_rationale"]))

    ok = (bool(s["clean_corpus_passes"])
          and s["verifier_probes_defeated"] == s["verifier_probes"]
          and s["presentation_probes_excluded"] == s["presentation_probes"]
          and not s["sentinel_survived"]
          and not s["sentinel_missing_rationale"]
          and not s["not_load_bearing"]
          and not s["same_kind_survived"]
          and not s["same_kind_stale_declarations"]
          and not s["missing_exclusion_rationale"]
          # Section E is a REQUIREMENT, not a report: if the restored defect stops
          # being caught, the guards have gone quiet and this suite says so.
          and bool(s["defect_witness_cases_failed"])
          and bool(s["defect_witness_section_d_detected"])
          and s["defect_witness_invariant_fired"] == len(
              payload["defect_witness"]["fixtures"]))
    print()
    print("ORACLE-MUTATION SUITE %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
