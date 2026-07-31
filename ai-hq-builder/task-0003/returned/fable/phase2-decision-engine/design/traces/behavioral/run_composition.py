"""D-B8 composition cases, driven through the REAL `compose_policies`.

Rework finding RW-13: several D-B8 layers were implemented but never exercised —
PC-4 window filtering, PC-3/PC-6 exception rejection, the rule-5/PC-10 refusal
branch and layer-3's higher-priority-wins path all had no live route, and the
`floor-overwrite` mutation proved the *predicate* rather than the *mechanism*
because it bypassed `compose_policies` entirely.

Every case here calls `engine_core.compose_policies` directly — the same function
the simulator uses — and each carries a seeded defect variant that must flip it.
A case whose defect variant still passes is asserting a constant, not measuring.

EXACT ACCOUNTING OF THE PC TABLE (rework finding RW-23 — the header used to read
"PC-1..PC-12", which this suite has never held):

  Driven here (9)  PC-1, PC-2, PC-3, PC-4, PC-6, PC-7, PC-9, PC-10, PC-11
  Plus (2)         D-B8 §2 `scope`, D-B8 §2 `applicability_predicate`
  PC-5             NOT SIMULATED — nothing generates a rollback (see run_gate.py).
  PC-8             NOT SIMULATED — composition is per governed output, not per
                   action field (see run_gate.py).
  PC-12            NOT driven here, and NOT unaccounted: it is mechanically PC-2's
                   shape (an equal-priority contradiction failing closed), and it is
                   exercised fixture-side through A4's policy-version dispute. It
                   would add a duplicate of `pc2` and no new mechanism, so it is
                   listed rather than duplicated.

TWO DELIBERATE SUBSTITUTIONS, so the mapping to D-B8's table is exact about where
this suite differs from the document's own example rows:

  PC-3  The table's row uses the untrusted-content quarantine floor; this case uses
        the DAT render floor instead. The mechanism under test — an exception whose
        `supersession_target` names a protection floor is refused — is identical;
        only the floor's governed output differs (render class rather than ceiling).
  PC-7  The table's row names a third domain this simulator does not model; the case
        substitutes the `attention` domain as the third independent constraint. What
        is tested is the same: constraints from different domains all land, and
        losing one loses its output.

SCOPE OF THIS SUITE'S COVERAGE, stated plainly: `scope`, `applicability_predicate`
and `effective_window` execute ONLY here. No fixture-driven path in the corpus
supplies a policy that is out of scope, predicate-excluded, or outside its window,
so those three layers have no coverage outside this synthetic suite.

Usage:  python3 run_composition.py [--out DIR]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Callable, Dict, List, Tuple

import engine_core as core

NOW = 1000

OWNER_ENV: Dict[str, str] = {
    "origin": "owner-conversation", "trust_class": "trusted-internal",
    "instruction_authority": "owner", "sensitivity_class": "business-internal",
    "data_class": "operational", "verification_state": "session-verified",
    "identity_session_state": "bound (IDN-01 verified)", "domain": "business",
}

FLOOR_RENDER = core.PolicyObject(
    policy_id="floor.dat-render", version=1, authority_domain="protection",
    priority=100, protection_floor=True, floor_class="security",
    render_class="masked-metadata+deep-link")


def _case(name: str, description: str, build: Callable[[bool], Tuple[core.Composition, bool]]):
    """build(defect) -> (composition, passed)."""
    clean, ok_clean = build(False)
    broken, ok_defect = build(True)
    return {
        "case": name, "description": description,
        "passed": ok_clean, "defect_passed": ok_defect,
        "discriminates": bool(ok_clean and not ok_defect),
        "clean_refused": list(clean.refused), "clean_reasons": list(clean.reasons),
    }


def pc1(defect):
    """Higher priority wins within one domain and output (layer 3)."""
    strict = core.PolicyObject("routing.specific", 1, "routing", 80, tier_max=core.T1)
    general = core.PolicyObject("routing.general", 1, "routing",
                                80 if defect else 20, tier_max=core.T3)
    c = core.compose_policies([strict, general], at_time=NOW, envelope=OWNER_ENV)
    # clean: 80 beats 20 -> T1. defect: equal priority, differing values -> fail closed.
    return c, (c.tier_max == core.T1 and not c.failed_closed)


def pc2(defect):
    """Equal-priority contradiction fails closed (layer 4)."""
    a = core.PolicyObject("routing.a", 1, "routing", 50, tier_max=core.T1)
    b = core.PolicyObject("routing.b", 1, "routing",
                          10 if defect else 50, tier_max=core.T3)
    c = core.compose_policies([a, b], at_time=NOW, envelope=OWNER_ENV)
    return c, c.failed_closed


def pc3(defect):
    """An exception may not target a protection floor.

    SUBSTITUTION (RW-23): the DAT render floor stands in for the table's
    untrusted-quarantine floor. Same mechanism, different governed output.
    """
    exc = core.PolicyObject("exc.floor", 1, "routing", 90,
                            supersession_target=None if defect else ("floor.dat-render", 1))
    c = core.compose_policies([FLOOR_RENDER, exc], at_time=NOW, envelope=OWNER_ENV)
    refused = any("illegal-exception-against-floor" in r for r in c.refused)
    return c, (refused and c.render_class == "masked-metadata+deep-link")


def pc4(defect):
    """An expired policy is inert (window filtered before ordering)."""
    expired = core.PolicyObject("routing.expired", 1, "routing", 90, tier_max=core.T0,
                                effective_window=(0, 5) if not defect else (0, 99999))
    c = core.compose_policies([expired], at_time=NOW, envelope=OWNER_ENV)
    return c, (c.tier_max is None
               and any("outside-effective-window" in r for r in c.refused))


def pc6(defect):
    """An exception against a policy permitting none is rejected."""
    target = core.PolicyObject("routing.base", 1, "routing", 10, tier_max=core.T2,
                               exception_authority="owner-with-step-up" if defect else "none")
    exc = core.PolicyObject("exc.base", 1, "routing", 90, tier_max=core.T4,
                            supersession_target=("routing.base", 1))
    c = core.compose_policies([target, exc], at_time=NOW, envelope=OWNER_ENV)
    return c, any("target-permits-no-exception" in r for r in c.refused)


def pc7(defect):
    """Independent constraints from different domains all land.

    SUBSTITUTION (RW-23): `attention` stands in as the third domain, since the
    table's third domain is not modelled here. Same conjunction mechanism.
    """
    routing = core.PolicyObject("routing.r", 1, "routing", 10, tier_max=core.T2)
    autonomy = core.PolicyObject("autonomy.a", 1, "autonomy", 10,
                                 ceiling=core.CEILING_ACT_WITH_RECEIPT)
    attention = core.PolicyObject("attention.x", 1, "attention", 10, attention_min="hub")
    pols = [routing, autonomy] if defect else [routing, autonomy, attention]
    c = core.compose_policies(pols, at_time=NOW, envelope=OWNER_ENV)
    return c, (c.tier_max == core.T2 and c.ceiling == core.CEILING_ACT_WITH_RECEIPT
               and c.attention_min == "hub")


def pc9(defect):
    """Two floors on one output intersect to the most restrictive."""
    mask = FLOOR_RENDER
    suppress = core.PolicyObject("floor.suppress", 1, "protection", 100,
                                 protection_floor=True, floor_class="security",
                                 render_class="full-content" if defect else "suppressed")
    c = core.compose_policies([mask, suppress], at_time=NOW, envelope=OWNER_ENV)
    return c, c.render_class == "suppressed"


def pc10(defect):
    """A non-protection policy cannot write another domain's output.

    THIS is the mechanism-level PC-10 test the rework asked for: the defect is a
    composition-path change (the writer claims the owning domain), not a post-hoc
    perturbation of the result.
    """
    writer = core.PolicyObject("autonomy.widen", 1,
                               "data" if defect else "autonomy", 90,
                               render_class="full-content")
    c = core.compose_policies([FLOOR_RENDER, writer], at_time=NOW, envelope=OWNER_ENV)
    refused = any("not-owned-by" in r for r in c.refused)
    return c, (refused and c.render_class == "masked-metadata+deep-link")


def pc11(defect):
    """A valid exception replaces ONLY its named target; other constraints stand.

    The defect models over-broad displacement: the exception reaches past its named
    target and takes out an unrelated autonomy constraint, which is exactly the
    failure PC-11 exists to exclude.
    """
    target = core.PolicyObject("routing.t", 1, "routing", 10, tier_max=core.T1,
                               exception_authority="owner-with-step-up")
    autonomy = core.PolicyObject("autonomy.a", 1, "autonomy", 10,
                                 ceiling=core.CEILING_ACT_WITH_RECEIPT,
                                 exception_authority="owner-with-step-up")
    exc = core.PolicyObject("exc.t", 1, "routing", 90, tier_max=core.T3,
                            supersession_target=("autonomy.a", 1) if defect
                            else ("routing.t", 1))
    c = core.compose_policies([target, exc, autonomy], at_time=NOW, envelope=OWNER_ENV)
    # Clean: the named routing target is displaced (T3 stands) AND the unrelated
    # autonomy ceiling survives. Over-broad displacement loses the ceiling.
    return c, (c.tier_max == core.T3 and c.ceiling == core.CEILING_ACT_WITH_RECEIPT)


def pc_scope(defect):
    """D-B8 §2 `scope` excludes a policy outside its partition."""
    personal = core.PolicyObject("routing.personal", 1, "routing", 90, tier_max=core.T0,
                                 scope=("business",) if defect else ("personal",))
    c = core.compose_policies([personal], at_time=NOW, envelope=OWNER_ENV)
    return c, (c.tier_max is None and any("out-of-scope" in r for r in c.refused))


def pc_predicate(defect):
    """D-B8 §2 `applicability_predicate` over control fields only."""
    pol = core.PolicyObject(
        "routing.external-only", 1, "routing", 90, tier_max=core.T0,
        applicability_predicate=(lambda env: True) if defect
        else (lambda env: str(env.get("trust_class", "")).startswith("external")))
    c = core.compose_policies([pol], at_time=NOW, envelope=OWNER_ENV)
    return c, (c.tier_max is None
               and any("applicability-predicate-false" in r for r in c.refused))


CASES = [
    ("PC-1", "higher priority wins within one domain/output", pc1),
    ("PC-2", "equal-priority contradiction fails closed", pc2),
    ("PC-3", "exception against a protection floor is refused", pc3),
    ("PC-4", "expired policy is inert (window filter)", pc4),
    ("PC-6", "exception against exception_authority=none is refused", pc6),
    ("PC-7", "independent cross-domain constraints all land", pc7),
    ("PC-9", "two floors on one output intersect to most restrictive", pc9),
    ("PC-10", "non-protection policy cannot write another domain's output", pc10),
    ("PC-11", "exception replaces only its named target", pc11),
    ("SCOPE", "D-B8 §2 scope excludes out-of-partition policies", pc_scope),
    ("PRED", "D-B8 §2 applicability predicate over control fields", pc_predicate),
]


def run(out_dir: str) -> Dict[str, object]:
    results = [_case(n, d, f) for n, d, f in CASES]
    payload = {
        "summary": {
            "cases": len(results),
            "passed": sum(1 for r in results if r["passed"]),
            "failed": sum(1 for r in results if not r["passed"]),
            "discriminating": sum(1 for r in results if r["discriminates"]),
        },
        "cases": results,
    }
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "composition_cases.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    return payload


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out")
    args = ap.parse_args(argv)
    payload = run(args.out)
    print("D-B8 composition cases — driven through the real compose_policies()")
    print("  %-7s %-8s %-13s %s" % ("CASE", "CLEAN", "UNDER DEFECT", "DESCRIPTION"))
    for r in payload["cases"]:
        print("  %-7s %-8s %-13s %s"
              % (r["case"], "PASS" if r["passed"] else "FAIL",
                 "flips" if r["discriminates"] else "*** constant ***",
                 r["description"]))
    s = payload["summary"]
    print("\n  %d/%d pass, %d/%d discriminate"
          % (s["passed"], s["cases"], s["discriminating"], s["cases"]))
    ok = s["failed"] == 0 and s["discriminating"] == s["cases"]
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
