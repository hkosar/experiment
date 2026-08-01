"""Seeded-defect falsifier suite + per-predicate and per-judge-check proofs.

Five layers:

  A  ENGINE-LEVEL DEFECTS (`Defects`) — the P2S-01 named falsifier classes, seeded
     inside the engine/fold so the whole pipeline misbehaves. Each must flip at
     least one previously-passing fixture x shape combination.

  B  PREDICATE REACHABILITY (`mutations`) — rework finding RW-02. Every forbidden
     predicate must be provably able to fire. For each predicate we search the
     mutation catalogue for a candidate defect that makes it return True. A
     predicate no mutation can reach is reported NOT-EVALUABLE with rationale and
     is EXCLUDED from the evaluated count — an honest smaller number over a padded
     larger one.

  C  WITNESS-CHANNEL TRIPWIRE — a regression check over `mutations.py` for known
     answer-key write patterns. Read its docstring for what it does and does not
     establish; it is a tripwire, not a proof.

  D  JUDGE-CHECK FALSIFIABILITY (rework finding RW-21) — layer B proves the
     *forbidden predicates* can fire, but the judge's own pass-rule and requirement
     checks were never run over mutated results. Their ability to fail was asserted.
     This layer runs the REAL judge over every seeded defect and every mutation and
     reports, per judge check, every named witness that flips it True -> False. A
     check with no witness is reported NOT-FALSIFIABLE and named, not quietly
     counted; a check no fixture ever selects is named too.

  E  DEGRADATION-RULE SELF-TEST (rework finding RW-19) — a harness self-test, NOT a
     fixture. See `degradation_rule_self_test`.

Exit code 0 only if every named defect class flips a case AND no predicate is
silently counted as evidence when it cannot discriminate AND no `Defects` switch is
orphaned AND no catalogue mutation witnesses nothing AND the degradation self-test
discriminates.

Both witness searches (B and D) record COMPLETE witness sets rather than stopping at
the first hit. Stopping early let a targeted defect be masked by a blunter one that
sorted earlier, which meant a rule could be claimed falsifiable with no shipped run
showing its own defect flipping it.

Usage:  python3 run_defects.py [--fixtures PATH] [--out DIR]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, List

import engine_core as core
import mutations
import oracle
import scenarios as scen
from events import SHAPES
from fixture_io import Stimulus, load_oracle, load_stimuli
from judge import judge
from simulate import CONSEQUENTIAL_CLASSES, Defects, simulate

# The P2S-01 falsifier's five named classes, plus the extra invariants this
# harness enforces. Each is seeded INSIDE the engine, not post-hoc.
CATALOGUE = [
    ("authority-raise", lambda: Defects(authority_raise=True),
     "changes authority — a model proposal raises the ceiling above the model-free base"),
    ("dropped-receipt", lambda: Defects(drop_receipt=True),
     "drops a receipt — the action still advances to executed with no evidence"),
    ("causal-reorder", lambda: Defects(causal_reorder=True),
     "reorders a causal event — delivery permuted and the topological sort disabled"),
    ("forbidden-outcome-admission", lambda: Defects(admit_forbidden=True),
     "admits a forbidden outcome — state written on a read-only path"),
    ("stale-projection", lambda: Defects(stale_projection=True),
     "produces a stale projection — S3 projections are not rebuilt"),
    ("engine-authored-receipt", lambda: Defects(engine_authored_receipt=True),
     "breaks external-receipt ownership — the engine authors its own evidence"),
    ("skip-eligibility-check", lambda: Defects(skip_eligibility_check=True),
     "P2S-07 — proposals from untrusted content with no eligibility policy"),
    ("normalizer-authority-leak", lambda: Defects(normalizer_authority_leak=True),
     "E2E-1 — a substituted normalizer raises the maximum authorized action"),
    # RW-21: `render_leak` was declared and wired into no runner. It is a named
    # defect class like the rest, so it is seeded like the rest.
    ("render-policy-ignored", lambda: Defects(render_leak=True),
     "D-B8 render floor ignored — no render-policy application record is produced"),
]

# The artifact channels the three review cycles actually found: a summary key whose
# only reader is a paired predicate. Named here so the tripwire below and its
# reporting stay in sync.
ARTIFACT_CHANNELS = ("extras", "receipt_violations")

# Assignments whose VALUE is a direct call to one of these are the legitimate
# re-derivations (RW-17): the mutation perturbed the event stream and is refreshing
# the summary through the production writer. Anything else assigning a channel is
# authoring the answer. Keep this list minimal — each entry is a hole in the
# tripwire, so each must be a function that computes the channel from the basis.
PRODUCTION_DERIVATION_WRITERS = ("receipt_ownership_violations",)


def witness_channel_integrity() -> Dict[str, object]:
    """REGRESSION TRIPWIRE for known answer-key write patterns — not a proof.

    What it does: parses `mutations.py` and reports any mutation that writes an
    artifact channel (`result.extras`, `result.receipt_violations`) by any of the
    forms below. Those two channels are where RW-11 and RW-17 found mutations
    authoring the very keys their paired predicates read.

        extras["k"] = v          subscript assignment       (RW-11)
        extras["k"] += v         augmented subscript assignment
        result.extras = {...}    wholesale reassignment
        extras.update(...)       bulk write
        setattr(r, "extras", …)  reflective write
        alias = result.extras    alias binding (the write itself is then invisible)
        receipt_violations.append/.extend/+=/= …            (RW-17)

    One exemption, and only one: assigning a channel the RESULT of a production
    derivation writer (`PRODUCTION_DERIVATION_WRITERS`) is the legitimate refresh a
    mutation performs after perturbing the event stream. Every exemption is a hole,
    so the list is kept to functions that recompute the channel from the basis.

    What it does NOT do, stated plainly because R2's docstring and README claimed
    otherwise: it does not prove that no mutation writes an artifact channel. It
    enumerates KNOWN channels and KNOWN write forms. A mutation that authored a new
    summary field — one added tomorrow, read only by its own predicate — passes this
    check untouched, and so would any write reached through an indirection the AST
    forms above do not name (a dict handed to a helper, a channel reached through
    `vars()`, a write inside an imported module). The general property is not
    decidable here and is not claimed. The reviewer's five evasion forms are matched
    now because they were demonstrated; the sixth is the one nobody has tried yet.

    Delivery Record falsifier row 1 states the same limit. Treat a clean result as
    "no known-shape regression", never as "no artifact witnesses exist".
    """
    import ast
    here = os.path.dirname(os.path.abspath(__file__))
    src = open(os.path.join(here, "mutations.py"), "r", encoding="utf-8").read()
    tree = ast.parse(src)
    violations: List[Dict[str, object]] = []

    def channel_of(node) -> str:
        """The artifact channel this expression bottoms out in, or ''."""
        while isinstance(node, ast.Subscript):
            node = node.value
        if isinstance(node, ast.Attribute) and node.attr in ARTIFACT_CHANNELS:
            return node.attr
        return ""

    def is_production_rederivation(value) -> bool:
        return (isinstance(value, ast.Call) and isinstance(value.func, ast.Name)
                and value.func.id in PRODUCTION_DERIVATION_WRITERS)

    def flag(lineno: int, channel: str, form: str) -> None:
        violations.append({"line": lineno, "channel": channel, "form": form})

    for node in ast.walk(tree):
        # `result.extras[...] = v`, `result.receipt_violations = [...]`, and the
        # alias binding `alias = result.extras` that would hide either.
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                ch = channel_of(tgt)
                if ch and not is_production_rederivation(node.value):
                    flag(node.lineno, ch, "assignment")
            ch = channel_of(node.value)
            if ch and not isinstance(node.value, ast.Subscript):
                flag(node.lineno, ch, "alias binding")
        # `result.extras[...] += v`
        if isinstance(node, ast.AugAssign):
            ch = channel_of(node.target)
            if ch:
                flag(node.lineno, ch, "augmented assignment")
        if isinstance(node, ast.Call):
            # `setattr(result, "extras", ...)`
            if isinstance(node.func, ast.Name) and node.func.id == "setattr":
                if (len(node.args) >= 2 and isinstance(node.args[1], ast.Constant)
                        and node.args[1].value in ARTIFACT_CHANNELS):
                    flag(node.lineno, str(node.args[1].value), "setattr")
            # `result.extras.update(...)`, `result.receipt_violations.append(...)`
            if isinstance(node.func, ast.Attribute):
                ch = channel_of(node.func.value)
                if ch and node.func.attr in ("update", "append", "extend",
                                             "setdefault", "insert"):
                    flag(node.lineno, ch, "%s(...)" % node.func.attr)

    return {"check": "witness-channel-tripwire",
            "scope": "known channels %s; known write forms only — see docstring"
                     % ", ".join(ARTIFACT_CHANNELS),
            "proves_absence_of_artifact_witnesses": False,
            "passed": not violations, "violations": violations}


def _ctx(res, stim, spec, oc):
    return {"result": res, "stim": stim, "spec": spec, "oracle": oc}


def baseline(fixtures_path: str):
    stimuli = load_stimuli(fixtures_path)
    oracle_cases = load_oracle(fixtures_path)
    passes = {}
    for stim in stimuli:
        for shape in SHAPES:
            res = simulate(stim, shape, Defects())
            j = judge(res, oracle_cases[stim.id], stim, scen.get(stim.id))
            passes[(stim.id, shape)] = j.passed
    return stimuli, oracle_cases, passes


def prove_reachability(stimuli, oracle_cases) -> Dict[str, object]:
    """For every predicate, find the candidate defects that make it fire.

    EVERY witness is recorded, not the first one alphabetically. R2 stopped at the
    first hit, which meant a targeted defect could be masked by a blunter one that
    happened to sort earlier — "unlogged override" would report `drop-decision`
    (which removes the whole DecisionEvent) and never show `drop-override`, so the
    OverrideEvent leg added for RW-24 would be a claim with no shipped evidence
    behind it. The full set makes the difference visible to a reviewer.
    """
    # which fixtures carry which phrase
    carriers: Dict[str, List[str]] = {}
    for fid, oc in oracle_cases.items():
        for phrase in oc.forbidden:
            carriers.setdefault(phrase, []).append(fid)

    predicates = {phrase: oracle.forbidden_predicate(phrase) for phrase in carriers}
    witnesses: Dict[str, List[str]] = {}
    fires_in_production: Dict[str, bool] = {p: False for p in carriers}

    for stim in stimuli:
        spec = scen.get(stim.id)
        oc = oracle_cases[stim.id]
        carried = [p for p in oc.forbidden if p in predicates]
        if not carried:
            continue
        for shape in SHAPES:
            base_res = simulate(stim, shape, Defects())
            for phrase in carried:
                try:
                    if predicates[phrase](_ctx(base_res, stim, spec, oc)):
                        fires_in_production[phrase] = True
                except Exception:
                    pass
            for mut in mutations.mutation_names():
                res = simulate(stim, shape, Defects())
                try:
                    mutations.apply_mutation(mut, res, spec, stim)
                except Exception:
                    continue
                ctx = _ctx(res, stim, spec, oc)
                for phrase in carried:
                    try:
                        fired = bool(predicates[phrase](ctx))
                    except Exception:
                        fired = False
                    if fired:
                        witnesses.setdefault(phrase, []).append(
                            "%s@%s/%s" % (mut, stim.id, shape))

    reach: Dict[str, Dict[str, object]] = {}
    for phrase, fixture_ids in sorted(carriers.items()):
        found = sorted(set(witnesses.get(phrase, [])))
        reach[phrase] = {
            "fixtures": sorted(fixture_ids),
            "defect_reachable": bool(found),
            "witness": found[0] if found else None,
            "witness_count": len(found),
            "witnesses": found,
            "fires_in_production": fires_in_production[phrase],
        }
    return reach


# --------------------------------------------------------------------------
# layer D — judge-check falsifiability (rework finding RW-21)
# --------------------------------------------------------------------------

def _single(field: str) -> Defects:
    return Defects(**{field: True})


def prove_judge_check_falsifiability(stimuli, oracle_cases) -> Dict[str, object]:
    """Every judge check must be SHOWN flipping True -> False in a shipped run.

    Layer B proves the forbidden predicates can fire. It says nothing about the
    judge's own checks — `masked_render`, `hearsay_provenance`,
    `interrupt_policy_cited`, the requirement-4/6 comparisons and the pass-rule
    decomposition — because `prove_reachability` never runs the judge. Their ability
    to fail was asserted (RW-21). This runs the real judge over every seeded defect
    and every mutation and names the witnesses that flip each check.

    EVERY witness is recorded, not just the first found: a check with one incidental
    witness (`drop-decision` removes the DecisionEvent, so anything reading a
    decision "flips") is materially weaker evidence than one a targeted defect flips.
    Reporting the full set lets a reviewer see which is which — and it is why
    `pending-policy-cited-as-ratified` appears under `interrupt_policy_cited` instead
    of being masked by an earlier, blunter witness.
    """
    defect_fields = list(Defects.__dataclass_fields__)
    baseline_true: Dict[str, List[str]] = {}
    witnesses: Dict[str, List[str]] = {}

    for stim in stimuli:
        spec = scen.get(stim.id)
        oc = oracle_cases[stim.id]
        for shape in SHAPES:
            base = judge(simulate(stim, shape, Defects()), oc, stim, spec)
            live = {n for n, ok in base.check_results.items() if ok}
            if not live:
                continue
            for name in live:
                baseline_true.setdefault(name, []).append("%s/%s" % (stim.id, shape))

            def record(label: str, checks: Dict[str, bool]) -> None:
                for name in live:
                    if checks.get(name) is False:
                        witnesses.setdefault(name, []).append(
                            "%s@%s/%s" % (label, stim.id, shape))

            for fld in defect_fields:
                try:
                    res = simulate(stim, shape, _single(fld))
                    record(fld, judge(res, oc, stim, spec).check_results)
                except Exception:
                    continue
            for mut in mutations.mutation_names():
                try:
                    res = simulate(stim, shape, Defects())
                    mutations.apply_mutation(mut, res, spec, stim)
                    record(mut, judge(res, oc, stim, spec).check_results)
                except Exception:
                    continue

    out: Dict[str, Dict[str, object]] = {}
    for check in sorted(baseline_true):
        found = sorted(set(witnesses.get(check, [])))
        # Prefer an engine-level witness in the headline: a switch inside `simulate`
        # perturbs the mechanism, while a mutation perturbs its output.
        engine_first = [x for x in found if x.split("@")[0] in defect_fields]
        out[check] = {
            "true_in_baseline": len(baseline_true[check]),
            "falsifiable": bool(found),
            "witness": (engine_first or found)[0] if found else None,
            "witness_kind": ("engine-defect" if engine_first
                             else ("mutation" if found else None)),
            "witness_count": len(found),
            "witnesses": found,
        }
    return out


# --------------------------------------------------------------------------
# layer E — D-B5 degradation-rule self-test (rework finding RW-19)
# --------------------------------------------------------------------------
#
# THIS IS A HARNESS SELF-TEST, NOT A FIXTURE, and it is labeled as one everywhere it
# is reported. It follows the `run_composition.py` precedent: drive a synthetic input
# through the REAL mechanism when no corpus case can discriminate.
#
# CORPUS LIMITATION, plainly: no fixture pairs degraded stores with an envelope that
# would otherwise authorize a consequential action. A10's envelope stops at
# internal-write, so A10's refusal is over-determined — deleting the D-B5 degradation
# rule entirely leaves A10's judged verdict unchanged. The rule was load-bearing
# nowhere on this corpus, which is the "guarded by accident" shape RW-15 diagnosed
# one level down. This self-test is the ONLY place the rule is shown discriminating;
# no fixture-driven coverage of it is claimed.

SELF_TEST_ENVELOPE: Dict[str, str] = {
    "origin": "owner-conversation", "source_id": "selftest-degradation",
    "source_type": "coordinator-chat", "trust_class": "trusted-internal",
    "instruction_authority": "owner", "sensitivity_class": "financial-restricted",
    "data_class": "payment-affecting",
    "verification_state": "session-verified + step-up required",
    "identity_session_state": "bound (IDN-01 verified)",
    "policy_version": "P1", "schema_version": "SV-1",
}


def degradation_rule_self_test() -> Dict[str, object]:
    """Clean run refuses citing degradation; `ignore_degradation` seeded, it emits."""
    stim = Stimulus(
        id="SELFTEST-DEGRADATION",
        title="harness self-test: degraded stores, otherwise-sufficient envelope",
        normalized_input="owner-approved payment action while the evidence store is down",
        start_state="evidence store degraded",
        policy="policy_version P1, schema_version SV-1, calibration pre-cal defaults",
        envelopes=(dict(SELF_TEST_ENVELOPE),),
    )
    spec = scen.ScenarioSpec(
        fixture_id=stim.id,
        degraded_stores=("evidence",),
        owner_step_up_provided=True,
        policies=(),
        actions=(scen.RequestedAction("act-selftest-pay", CONSEQUENTIAL_CLASSES[0]),),
        notes="HARNESS SELF-TEST — not a corpus fixture",
    )

    def probe(defects: Defects) -> Dict[str, object]:
        res = simulate(stim, "S1", defects, spec=spec)
        return {
            "ceiling": res.ceiling,
            "envelope_would_authorize": (
                core.CEILING_ORDER[res.ceiling]
                >= core.CEILING_ORDER[core.CEILING_ACT_WITH_RECEIPT]),
            "action_emitted": any(e.event_type == "ActionRequest" for e in res.events),
            "refused_citing_degradation": any(
                e.event_type == "RefusalEvent"
                and bool(e.payload.get("refused_due_to_degradation"))
                for e in res.events),
        }

    clean = probe(Defects())
    seeded = probe(Defects(ignore_degradation=True))
    # The test is only meaningful if the envelope itself would have permitted the
    # action — otherwise it repeats A10's over-determined refusal.
    discriminates = bool(
        clean["envelope_would_authorize"]
        and clean["refused_citing_degradation"] and not clean["action_emitted"]
        and seeded["action_emitted"] and not seeded["refused_citing_degradation"])
    return {
        "test": "d-b5-degradation-rule",
        "kind": "HARNESS SELF-TEST (synthetic stimulus, not a corpus fixture)",
        "action_class": CONSEQUENTIAL_CLASSES[0],
        "clean": clean, "ignore_degradation_seeded": seeded,
        "discriminates": discriminates,
        "corpus_limitation":
            "No fixture pairs degraded stores with an envelope that would otherwise "
            "authorize a consequential action; A10's refusal is over-determined by "
            "its internal-write envelope. The D-B5 degradation rule is exercised "
            "discriminatingly only here.",
    }


def run(fixtures_path: str, out_dir: str) -> Dict[str, object]:
    stimuli, oracle_cases, base = baseline(fixtures_path)
    base_passes = sum(1 for v in base.values() if v)

    # ---- layer A: engine-level named defect classes ----
    report: List[Dict[str, object]] = []
    all_effective = True
    for name, factory, description in CATALOGUE:
        d = factory()
        flipped: List[str] = []
        for stim in stimuli:
            for shape in SHAPES:
                try:
                    res = simulate(stim, shape, d)
                    passed = judge(res, oracle_cases[stim.id], stim,
                                   scen.get(stim.id)).passed
                except Exception:
                    passed = False
                if base[(stim.id, shape)] and not passed:
                    flipped.append("%s/%s" % (stim.id, shape))
        effective = bool(flipped)
        all_effective = all_effective and effective
        report.append({"defect": name, "witnesses": description,
                       "flipped_count": len(flipped), "flipped": flipped,
                       "effective": effective})

    # ---- layer B: per-predicate reachability ----
    reach = prove_reachability(stimuli, oracle_cases)
    channel = witness_channel_integrity()
    reachable = [p for p, r in reach.items() if r["defect_reachable"]]
    not_evaluable = [p for p, r in reach.items() if not r["defect_reachable"]]

    # A mutation that witnesses nothing is a catalogue entry with no evidence behind
    # it — the same class as an orphaned defect switch. Now that both witness
    # searches record COMPLETE sets, "witnesses nothing" means exactly that.
    witnessing = set()
    for r in reach.values():
        witnessing.update(w.split("@")[0] for w in r["witnesses"])

    # ---- layer D: judge-check falsifiability (RW-21) ----
    judge_checks = prove_judge_check_falsifiability(stimuli, oracle_cases)
    checks_falsifiable = [c for c, r in judge_checks.items() if r["falsifiable"]]
    checks_not_falsifiable = [c for c, r in judge_checks.items() if not r["falsifiable"]]
    # A check no fixture's pass rule ever selects is not evidence either, and neither
    # is one that is selected but has nothing to look at. R2's counts could not tell
    # "passed" from "never asked"; these two lists say which is which.
    selected = set()
    for oc in oracle_cases.values():
        selected.update(oracle.pass_rule_predicates(oc.pass_rule))
    never_selected = sorted(c for c in oracle.PASS_RULE_CHECKS if c not in selected)
    selected_but_vacuous = sorted(
        c for c in selected if ("pass_rule:" + c) not in judge_checks)

    # ---- layer E: degradation-rule self-test (RW-19) ----
    degradation = degradation_rule_self_test()

    # RW-21 return requirement 2 — a declared switch wired into no runner is a claim
    # with no evidence behind it. Reported, not merely intended.
    wired = set()
    for _, factory, _ in CATALOGUE:
        d = factory()
        wired.update(f for f in d.__dataclass_fields__ if getattr(d, f))
    wired.update(r["witness"].split("@")[0] for r in judge_checks.values()
                 if r["witness_kind"] == "engine-defect")
    wired.add("ignore_degradation")          # layer E, above
    orphaned = sorted(set(Defects.__dataclass_fields__) - wired)

    for r in judge_checks.values():
        witnessing.update(w.split("@")[0] for w in r["witnesses"])
    dead_mutations = sorted(set(mutations.mutation_names()) - witnessing)

    payload = {
        "summary": {
            "baseline_passes": base_passes,
            "defects_seeded": len(CATALOGUE),
            "defects_effective": sum(1 for r in report if r["effective"]),
            "all_effective": all_effective,
            "predicates_total": len(reach),
            "predicates_defect_reachable": len(reachable),
            "predicates_not_evaluable": len(not_evaluable),
            "mutations_in_catalogue": len(mutations.mutation_names()),
            "witness_channel_tripwire": channel["passed"],
            "judge_checks_total": len(judge_checks),
            "judge_checks_falsifiable": len(checks_falsifiable),
            "judge_checks_not_falsifiable": len(checks_not_falsifiable),
            "pass_rule_checks_never_selected": never_selected,
            "pass_rule_checks_selected_but_vacuous": selected_but_vacuous,
            "orphaned_defect_switches": orphaned,
            "mutations_witnessing_nothing": dead_mutations,
            "degradation_self_test_discriminates": degradation["discriminates"],
        },
        "witness_channel_tripwire": channel,
        "defects": report,
        "predicate_reachability": reach,
        "not_evaluable": sorted(not_evaluable),
        "judge_check_falsifiability": judge_checks,
        "judge_checks_not_falsifiable": sorted(checks_not_falsifiable),
        "pass_rule_checks_never_selected": never_selected,
        "pass_rule_checks_selected_but_vacuous": selected_but_vacuous,
        "mutations_witnessing_nothing": dead_mutations,
        "degradation_rule_self_test": degradation,
    }
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "seeded_defects.json"), "w",
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

    print("TASK-0003 seeded-defect falsifier suite")
    print("  baseline passing combinations: %d" % s["baseline_passes"])
    print()
    print("A. ENGINE-LEVEL DEFECT CLASSES (P2S-01 falsifier)")
    print("   %-30s %-9s %s" % ("DEFECT", "FLIPPED", "VERDICT"))
    for r in payload["defects"]:
        print("   %-30s %-9d %s" % (
            r["defect"], r["flipped_count"],
            "DETECTED" if r["effective"] else "*** NOT DETECTED — harness defect ***"))
    print("   effective: %d / %d" % (s["defects_effective"], s["defects_seeded"]))
    print()
    print("B. PER-PREDICATE REACHABILITY (rework finding RW-02)")
    print("   mutation catalogue        : %d candidate defects" % s["mutations_in_catalogue"])
    print("   predicates total          : %d" % s["predicates_total"])
    print("   defect-reachable          : %d" % s["predicates_defect_reachable"])
    print("   NOT-EVALUABLE (excluded)  : %d" % s["predicates_not_evaluable"])
    for p in payload["not_evaluable"]:
        print("      NOT-EVALUABLE: %s" % p)
    print("   mutations witnessing nothing : %s"
          % (", ".join(s["mutations_witnessing_nothing"]) or "none — every "
             "catalogue entry makes at least one predicate or judge check fire"))

    print()
    print("C. WITNESS-CHANNEL TRIPWIRE (regression check, NOT a proof — see docstring)")
    ci = payload["witness_channel_tripwire"]
    print("   known artifact-channel write forms in mutations.py : %s"
          % ("none found" if ci["passed"] else "FOUND"))
    print("   scope: %s" % ci["scope"])
    for v in ci["violations"][:10]:
        print("      HIT mutations.py:%s %s via %s" % (v["line"], v["channel"], v["form"]))

    print()
    print("D. JUDGE-CHECK FALSIFIABILITY (rework finding RW-21)")
    print("   judge checks true in baseline : %d" % s["judge_checks_total"])
    print("   shown flippable by a witness  : %d" % s["judge_checks_falsifiable"])
    print("   NOT-FALSIFIABLE (named below) : %d" % s["judge_checks_not_falsifiable"])
    print("   %-44s %-13s %3s  %s" % ("CHECK", "WITNESS KIND", "N", "HEADLINE WITNESS"))
    for name, r in sorted(payload["judge_check_falsifiability"].items()):
        print("   %-44s %-13s %3d  %s" % (
            name, r["witness_kind"] or "-", r["witness_count"],
            r["witness"] or "*** NOT FALSIFIABLE ***"))
    for c in payload["pass_rule_checks_never_selected"]:
        print("      NEVER SELECTED by any fixture pass rule: %s" % c)
    for c in payload["pass_rule_checks_selected_but_vacuous"]:
        print("      SELECTED BUT VACUOUS on every case that selects it: %s" % c)
    if s["orphaned_defect_switches"]:
        print("   *** orphaned Defects switches (in no runner): %s ***"
              % ", ".join(s["orphaned_defect_switches"]))
    else:
        print("   orphaned Defects switches     : none — every switch is wired")

    print()
    print("E. D-B5 DEGRADATION-RULE SELF-TEST (rework finding RW-19)")
    dg = payload["degradation_rule_self_test"]
    print("   %s" % dg["kind"])
    print("   clean  : envelope authorizes=%s, action emitted=%s, refused citing "
          "degradation=%s" % (dg["clean"]["envelope_would_authorize"],
                              dg["clean"]["action_emitted"],
                              dg["clean"]["refused_citing_degradation"]))
    print("   seeded : action emitted=%s, refused citing degradation=%s"
          % (dg["ignore_degradation_seeded"]["action_emitted"],
             dg["ignore_degradation_seeded"]["refused_citing_degradation"]))
    print("   discriminates : %s" % ("YES" if dg["discriminates"] else "*** NO ***"))
    print("   limitation: %s" % dg["corpus_limitation"])

    # RW-26(c): the standalone runner used to omit the judge-check condition that
    # run_gate.py criterion 13 enforces, so the two could disagree about whether the
    # same run passed. They agree now.
    ok = (bool(s["all_effective"]) and bool(ci["passed"])
          and bool(dg["discriminates"]) and not s["orphaned_defect_switches"]
          and not s["mutations_witnessing_nothing"]
          and s["judge_checks_not_falsifiable"] == 0)
    print()
    print("FALSIFIER PROOF %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
