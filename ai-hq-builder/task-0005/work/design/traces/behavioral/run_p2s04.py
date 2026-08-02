"""P2S-04 schedule-liveness suite — the watchdog owns the recurrence definition.

Verifier finding P2T-03: D-KR's P2S-04 correction promises deterministic tests for
scheduler death before next-occurrence registration, rolling-horizon exhaustion, and
a schedule change racing a computed deadline. No such executable test existed. The
cover cited A14 (an expired control envelope) and the watchdog heartbeat evidence,
which exercise neither behavior.

D-KR P2S-04, the contract these tests encode (full document supplied with TASK-0004):

  1  "The watchdog holds the authoritative schedule definitions. Schedule
     creation/change is a governed event (SCH-01 versioned) that registers the
     recurrence spec with the D-KR watchdog itself; the watchdog computes expected
     deadlines from the spec — it does not depend on the scheduler announcing each
     occurrence. A dead scheduler changes nothing about the watchdog's expectations;
     the next computed deadline simply passes unanswered and alarms."
  2  "Rolling ExpectedRun horizon (corroboration, not the primary): the scheduler
     still materializes future-dated ExpectedRun records (>= 7 days ahead); the
     watchdog alarms on horizon exhaustion (the scheduler stopped extending) as an
     early-warning signal that fires before any run is even due."
  3  Tests: scheduler death after a run and before registering the next occurrence;
     horizon exhaustion; a schedule change racing a computed deadline.

P2U-03 — WHAT THE THIRD BEHAVIOR MISSED. `change_schedule()` replaced the spec and
left `expected_runs` alone: an unversioned list of materialized ExpectedRun ticks that
`horizon_exhausted()` then read as if it were coverage for whatever spec was current.
The verifier materialized a v1 horizon far into the future, changed atomically to v2,
killed the scheduler before it extended anything, and got

    current spec version:        2
    materialized horizon:        still v1
    horizon warning at v2 start: None

so a schedule nobody was going to run looked healthy on the strength of the horizon
its previous version left behind. The supplied test never saw it because it recomputed
expectations from the new spec instead of inspecting the watchdog's actual state — it
checked the arithmetic, not the machine.

The horizon is version-bound now: `expected_runs` is keyed by schedule AND version, a
governed change retires every prior-version entry in the same transaction that adopts
the new spec, and `horizon_exhausted()` counts only entries materialized under the
version currently in force. Behavior 4 is the verifier's probe, and behavior 3 now
inspects `expected_runs` rather than re-deriving it.

THIS IS A HARNESS SELF-TEST, NOT A FIXTURE, and is labelled as one everywhere it is
reported — the same standing as the D-B5 degradation self-test (`run_defects.py`
layer E). No corpus fixture carries a recurring schedule at all: A14 is a single
expired envelope, so there is no fixture-driven route to these behaviors and none is
claimed. All time here is a logical tick count; there is no wall-clock read anywhere.

Each behavior ships with its TARGETED DEFECT — the specific wrong implementation the
finding names — and the suite requires the clean run to detect and the defect run to
miss. A test that cannot fail is not evidence.

Usage:  python3 run_p2s04.py [--out DIR]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# Logical clock only. Deadlines are computed by arithmetic over recorded ticks.
DAY = 24
HORIZON_MIN_DAYS = 7          # D-KR P2S-04 rule 2: ">= 7 days ahead"


@dataclass(frozen=True)
class RecurrenceSpec:
    """A versioned recurrence definition the WATCHDOG holds (D-KR P2S-04 rule 1)."""

    schedule_id: str
    version: int
    first_due: int            # logical tick of the first occurrence
    period: int               # ticks between occurrences

    def deadlines_through(self, horizon_end: int) -> List[int]:
        """Every deadline the spec implies up to `horizon_end` — computed, not told."""
        out, t = [], self.first_due
        while t <= horizon_end:
            out.append(t)
            t += self.period
        return out

    def next_deadline_after(self, now: int) -> int:
        t = self.first_due
        while t <= now:
            t += self.period
        return t


@dataclass
class Watchdog:
    """The control-service watchdog. Holds specs; computes its own expectations.

    Three TARGETED DEFECT switches, one per behavior that needs one:
      `depends_on_scheduler_reports`  behavior 1 — the superseded model in which the
                                      watchdog only knew about occurrences the
                                      scheduler announced.
      `horizon_monitoring`            behavior 2 — horizon monitoring off.
      `atomic_schedule_change`        behavior 3 — withdraw-then-fail-to-adopt.
      `version_bound_horizon`         behavior 4 (P2U-03) — the horizon read as one
                                      unversioned list, so a retired version's
                                      coverage answers for the current one.

    `expected_runs` is keyed schedule -> VERSION -> materialized ticks. It was
    `schedule -> ticks` and that single missing key is the whole of P2U-03: the ticks
    were real, they were simply attributed to no version, so nothing could tell
    coverage for the spec in force from coverage for a spec that had been replaced.
    """

    specs: Dict[str, RecurrenceSpec] = field(default_factory=dict)
    run_started: List[Tuple[str, int]] = field(default_factory=list)
    expected_runs: Dict[str, Dict[int, List[int]]] = field(default_factory=dict)
    retired_versions: Dict[str, List[int]] = field(default_factory=dict)
    depends_on_scheduler_reports: bool = False
    horizon_monitoring: bool = True
    atomic_schedule_change: bool = True
    version_bound_horizon: bool = True
    journal: List[str] = field(default_factory=list)

    # --- governed registration (SCH-01 versioned) --------------------------
    def register(self, spec: RecurrenceSpec) -> None:
        self.specs[spec.schedule_id] = spec
        self.expected_runs.setdefault(spec.schedule_id, {}).setdefault(spec.version, [])
        self.journal.append("ScheduleRegistered:%s@v%d" % (spec.schedule_id, spec.version))

    def change_schedule(self, spec: RecurrenceSpec, now: int) -> None:
        """A governed change re-registers the spec ATOMICALLY with the watchdog.

        The non-atomic defect drops the old expectation before adopting the new one,
        which is exactly the orphaned-old / missing-new hazard rule 3 names.

        P2U-03: the same transaction that adopts the new spec RETIRES every
        prior-version horizon entry and establishes the new version's horizon state —
        empty, because the scheduler has not extended it yet. Both legs land together
        or neither does; a change that adopted the spec and left the old horizon
        eligible is the state the verifier found, and it is no longer reachable
        through this method.
        """
        if not self.atomic_schedule_change:
            self.specs.pop(spec.schedule_id, None)
            self.journal.append("ScheduleWithdrawn:%s" % spec.schedule_id)
            # ... and the adoption never lands (the race the rule forbids).
            return

        horizons = self.expected_runs.setdefault(spec.schedule_id, {})
        superseded = sorted(v for v in horizons if v != spec.version)
        self.specs[spec.schedule_id] = spec
        for version in superseded:
            self.retired_versions.setdefault(spec.schedule_id, []).append(version)
            self.journal.append(
                "HorizonRetired:%s@v%d(%d materialized tick(s) now ineligible)"
                % (spec.schedule_id, version, len(horizons[version])))
        horizons.setdefault(spec.version, [])
        self.journal.append("ScheduleChanged:%s@v%d(atomic; horizon reset at tick %d)"
                            % (spec.schedule_id, spec.version, now))

    # --- the scheduler's side ----------------------------------------------
    def scheduler_completes_run(self, schedule_id: str, at: int) -> None:
        self.run_started.append((schedule_id, at))

    def scheduler_extends_horizon(self, schedule_id: str, through: int) -> None:
        """Materialize ExpectedRun records UNDER THE VERSION CURRENTLY IN FORCE."""
        spec = self.specs.get(schedule_id)
        if spec is None:
            return
        self.expected_runs.setdefault(schedule_id, {})[spec.version] = \
            spec.deadlines_through(through)

    # --- the watchdog's own audit ------------------------------------------
    def _all_materialized(self, schedule_id: str) -> List[int]:
        out: List[int] = []
        for ticks in self.expected_runs.get(schedule_id, {}).values():
            out.extend(ticks)
        return sorted(out)

    def eligible_horizon(self, schedule_id: str) -> List[int]:
        """The materialized ticks that count as coverage for the spec in force.

        With `version_bound_horizon` off this returns every tick ever materialized
        regardless of which spec produced it — the pre-P2U-03 reading, kept as the
        targeted defect for behavior 4 rather than deleted, so the fix is observed
        rather than asserted.
        """
        if not self.version_bound_horizon:
            return self._all_materialized(schedule_id)
        spec = self.specs.get(schedule_id)
        if spec is None:
            return []
        return sorted(self.expected_runs.get(schedule_id, {}).get(spec.version, []))

    def horizon_state(self, schedule_id: str) -> Dict[str, object]:
        """The watchdog's ACTUAL horizon, for a test to inspect rather than re-derive."""
        spec = self.specs.get(schedule_id)
        return {
            "version_in_force": spec.version if spec else None,
            "materialized_by_version": {
                str(v): list(t) for v, t
                in sorted(self.expected_runs.get(schedule_id, {}).items())},
            "retired_versions": sorted(self.retired_versions.get(schedule_id, [])),
            "eligible_ticks": self.eligible_horizon(schedule_id),
        }

    def missed_deadlines(self, schedule_id: str, now: int) -> List[int]:
        """Deadlines that passed with no matching RunStarted receipt (rule 1)."""
        if self.depends_on_scheduler_reports:
            # SUPERSEDED MODEL: the watchdog can only check occurrences the scheduler
            # registered. A scheduler that died before registering the next one
            # leaves nothing to check, so nothing alarms — the exact defect D-KR
            # P2S-04 supersedes.
            known = self._all_materialized(schedule_id)
        else:
            spec = self.specs.get(schedule_id)
            known = spec.deadlines_through(now) if spec else []
        answered = {t for sid, t in self.run_started if sid == schedule_id}
        return sorted(t for t in known if t <= now and t not in answered)

    def horizon_exhausted(self, schedule_id: str, now: int) -> Optional[str]:
        """Early warning BEFORE anything is due: the horizon stopped being extended."""
        if not self.horizon_monitoring:
            return None
        materialized = self.eligible_horizon(schedule_id)
        furthest = max(materialized) if materialized else now
        if furthest - now < HORIZON_MIN_DAYS * DAY:
            spec = self.specs.get(schedule_id)
            return ("horizon exhausted: %d ticks of cover remain for v%s, below the "
                    "%d-tick minimum"
                    % (max(0, furthest - now), spec.version if spec else "?",
                       HORIZON_MIN_DAYS * DAY))
        return None


# --------------------------------------------------------------------------
# The three behaviors, each with its targeted defect
# --------------------------------------------------------------------------

def behavior_scheduler_death(defect: bool) -> Dict[str, object]:
    """1 — scheduler dies after a run, before registering the next occurrence."""
    spec = RecurrenceSpec("ritual.audit", 1, first_due=10 * DAY, period=DAY)
    wd = Watchdog(depends_on_scheduler_reports=defect)
    wd.register(spec)
    # The scheduler materializes the horizon, runs the first occurrence, then dies —
    # so nothing registers the SECOND occurrence anywhere.
    wd.scheduler_extends_horizon("ritual.audit", through=10 * DAY)
    wd.scheduler_completes_run("ritual.audit", 10 * DAY)
    now = 11 * DAY + 1                       # the next deadline has passed unanswered
    missed = wd.missed_deadlines("ritual.audit", now)
    return {"now": now, "missed": missed, "detected": bool(missed),
            "watchdog_computed_deadlines":
                wd.specs["ritual.audit"].deadlines_through(now) if wd.specs else []}


def behavior_horizon_exhaustion(defect: bool) -> Dict[str, object]:
    """2 — the scheduler stops extending; the alarm must fire BEFORE anything is due."""
    spec = RecurrenceSpec("ritual.sweep", 1, first_due=30 * DAY, period=DAY)
    wd = Watchdog(horizon_monitoring=not defect)
    wd.register(spec)
    wd.scheduler_extends_horizon("ritual.sweep", through=32 * DAY)   # ~2 days of cover
    now = 30 * DAY - 5                        # nothing is due yet
    warning = wd.horizon_exhausted("ritual.sweep", now)
    next_due = spec.next_deadline_after(now)
    return {"now": now, "next_deadline": next_due, "warning": warning,
            "detected": warning is not None,
            "fires_before_anything_is_due": warning is not None and now < next_due}


def behavior_schedule_change(defect: bool) -> Dict[str, object]:
    """3 — a versioned change races a computed deadline; no orphan, no gap.

    P2U-03: this used to compute `expectations` from the new spec and compare that
    arithmetic against itself, which is why it stayed green while the watchdog's own
    horizon state was still v1's. It now materializes a v1 horizon first and reads
    `wd.horizon_state()` — the machine's state, not a re-derivation of it.
    """
    v1 = RecurrenceSpec("ritual.review", 1, first_due=20 * DAY, period=DAY)
    v2 = RecurrenceSpec("ritual.review", 2, first_due=20 * DAY + 6, period=DAY)
    wd = Watchdog(atomic_schedule_change=not defect)
    wd.register(v1)
    wd.scheduler_extends_horizon("ritual.review", through=25 * DAY)
    horizon_before = wd.horizon_state("ritual.review")
    now = 20 * DAY - 1                        # one tick before the v1 deadline
    wd.change_schedule(v2, now=now)
    after = 21 * DAY
    spec_now = wd.specs.get("ritual.review")
    expectations = spec_now.deadlines_through(after) if spec_now else []
    orphaned_old = [t for t in v1.deadlines_through(after) if t in expectations
                    and t not in v2.deadlines_through(after)]
    missing_new = [t for t in v2.deadlines_through(after) if t not in expectations]
    horizon_after = wd.horizon_state("ritual.review")
    # The state assertions the old version of this test did not make: the v1 ticks
    # must still be RECORDED (nothing is destroyed) and no longer ELIGIBLE.
    v1_ticks = horizon_before["eligible_ticks"]
    v1_still_recorded = bool(horizon_after["materialized_by_version"].get("1"))
    v1_still_eligible = any(t in horizon_after["eligible_ticks"] for t in v1_ticks)
    return {"now": now, "version_in_force": spec_now.version if spec_now else None,
            "expectations": expectations,
            "orphaned_old_deadlines": orphaned_old,
            "missing_new_deadlines": missing_new,
            "horizon_before_change": horizon_before,
            "horizon_after_change": horizon_after,
            "v1_ticks_still_recorded": v1_still_recorded,
            "v1_ticks_still_eligible": v1_still_eligible,
            "detected": (bool(spec_now) and not orphaned_old and not missing_new
                         and v1_still_recorded and not v1_still_eligible)}


def behavior_stale_horizon(defect: bool) -> Dict[str, object]:
    """4 — the verifier's P2U-03 probe, step for step.

        1. Register v1.
        2. Materialize v1 ExpectedRun records far into the future.
        3. Atomically change to v2.
        4. Simulate the scheduler dying before extending the v2 horizon.

    The v1 horizon runs 40 days past the observation tick, so under the unversioned
    reading there is ample cover and nothing warns. Version-bound, v2 has no cover at
    all and the early warning fires — which is the whole claim: stale coverage from a
    retired version cannot answer for the version in force.
    """
    v1 = RecurrenceSpec("ritual.digest", 1, first_due=40 * DAY, period=DAY)
    v2 = RecurrenceSpec("ritual.digest", 2, first_due=40 * DAY + 3, period=DAY)
    wd = Watchdog(version_bound_horizon=not defect)
    wd.register(v1)
    wd.scheduler_extends_horizon("ritual.digest", through=80 * DAY)   # far ahead
    now = 39 * DAY                            # nothing is due under either version
    wd.change_schedule(v2, now=now)
    # ... and the scheduler dies here: no `scheduler_extends_horizon` for v2.
    warning = wd.horizon_exhausted("ritual.digest", now)
    state = wd.horizon_state("ritual.digest")
    return {"now": now,
            "current_spec_version": state["version_in_force"],
            "materialized_by_version": state["materialized_by_version"],
            "retired_versions": state["retired_versions"],
            "eligible_ticks": state["eligible_ticks"],
            "v1_cover_ticks_past_now": max(
                [t - now for t in state["materialized_by_version"].get("1", [])]
                or [0]),
            "next_deadline": v2.next_deadline_after(now),
            "warning": warning,
            "detected": warning is not None,
            "fires_before_anything_is_due":
                warning is not None and now < v2.next_deadline_after(now),
            "journal": list(wd.journal)}


BEHAVIORS = [
    ("scheduler-death-before-registration",
     "D-KR P2S-04 rule 1 — the spec-computed deadline fires even though the "
     "scheduler died before registering the next occurrence",
     "watchdog depends on scheduler self-reports (the superseded ExpectedRun model)",
     behavior_scheduler_death),
    ("horizon-exhaustion-early-warning",
     "D-KR P2S-04 rule 2 — the horizon stops being extended and the alarm fires "
     "before any run is due",
     "horizon monitoring disabled",
     behavior_horizon_exhaustion),
    ("versioned-schedule-change-atomic",
     "D-KR P2S-04 rule 3 — a governed change re-registers atomically: no orphaned "
     "old deadline, no missing new one, and the prior version's materialized ticks "
     "are retained as a record but retired as coverage",
     "non-atomic change (withdraw then fail to adopt)",
     behavior_schedule_change),
    ("stale-prior-version-horizon",
     "P2U-03 — a v1 horizon extending far ahead cannot satisfy v2 coverage: after an "
     "atomic change the v2 horizon-exhaustion warning fires even though v1 had 40 "
     "days of cover left",
     "unversioned horizon (the pre-P2U-03 reading: any materialized tick counts)",
     behavior_stale_horizon),
]


def run(out_dir: str) -> Dict[str, object]:
    rows: List[Dict[str, object]] = []
    for name, contract, defect_name, fn in BEHAVIORS:
        clean = fn(False)
        seeded = fn(True)
        rows.append({
            "behavior": name,
            "contract": contract,
            "kind": "HARNESS SELF-TEST (synthetic recurrence spec, not a corpus fixture)",
            "targeted_defect": defect_name,
            "clean": clean,
            "defect": seeded,
            "clean_detects": bool(clean["detected"]),
            "defect_misses": not bool(seeded["detected"]),
            "discriminates": bool(clean["detected"]) and not bool(seeded["detected"]),
        })

    payload = {
        "summary": {
            "behaviors": len(rows),
            "discriminating": sum(1 for r in rows if r["discriminates"]),
            "not_discriminating": [r["behavior"] for r in rows if not r["discriminates"]],
            "corpus_limitation":
                "No corpus fixture carries a recurring schedule: A14 is a single "
                "expired control envelope. All four behaviors have NO fixture-driven "
                "coverage and none is claimed — this suite is the only place they "
                "are exercised.",
            "clock": "logical ticks only; no wall-clock read anywhere in this suite",
        },
        "behaviors": rows,
    }
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "p2s04_schedule_liveness.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    return payload


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out")
    args = ap.parse_args(argv)
    payload = run(args.out)
    s = payload["summary"]

    print("TASK-0004 P2S-04 schedule-liveness suite (P2T-03)")
    print("  HARNESS SELF-TEST — synthetic recurrence specs, not corpus fixtures")
    print()
    for r in payload["behaviors"]:
        print("  %s" % r["behavior"])
        print("     contract       : %s" % r["contract"])
        print("     targeted defect: %s" % r["targeted_defect"])
        print("     clean detects  : %s   |   defect misses: %s   |   discriminates: %s"
              % (r["clean_detects"], r["defect_misses"],
                 "YES" if r["discriminates"] else "*** NO ***"))
        if r["behavior"].startswith("scheduler-death"):
            print("     clean missed deadlines %s ; under the superseded model %s"
                  % (r["clean"]["missed"], r["defect"]["missed"]))
        elif r["behavior"].startswith("horizon"):
            print("     clean warning at tick %d, next deadline %d (fires early: %s)"
                  % (r["clean"]["now"], r["clean"]["next_deadline"],
                     r["clean"]["fires_before_anything_is_due"]))
        elif r["behavior"].startswith("versioned-schedule-change"):
            print("     clean version in force %s, orphaned %s, missing %s ; "
                  "under the defect version in force %s"
                  % (r["clean"]["version_in_force"], r["clean"]["orphaned_old_deadlines"],
                     r["clean"]["missing_new_deadlines"],
                     r["defect"]["version_in_force"]))
            print("     watchdog horizon BEFORE change: %s"
                  % json.dumps(r["clean"]["horizon_before_change"]
                               ["materialized_by_version"]))
            print("     watchdog horizon AFTER  change: %s ; retired %s ; eligible %s"
                  % (json.dumps(r["clean"]["horizon_after_change"]
                                ["materialized_by_version"]),
                     r["clean"]["horizon_after_change"]["retired_versions"],
                     r["clean"]["horizon_after_change"]["eligible_ticks"]))
            print("     v1 ticks still recorded %s, still eligible %s"
                  % (r["clean"]["v1_ticks_still_recorded"],
                     r["clean"]["v1_ticks_still_eligible"]))
        else:
            c, d = r["clean"], r["defect"]
            print("     the verifier's probe: v1 horizon materialized, atomic change "
                  "to v2, scheduler dies")
            print("     %-26s %-28s %s" % ("", "VERSION-BOUND (clean)",
                                           "UNVERSIONED (defect)"))
            print("     %-26s %-28s %s" % ("current spec version",
                                           c["current_spec_version"],
                                           d["current_spec_version"]))
            print("     %-26s %-28s %s" % ("v1 cover past now (ticks)",
                                           c["v1_cover_ticks_past_now"],
                                           d["v1_cover_ticks_past_now"]))
            print("     %-26s %-28s %s" % ("eligible horizon ticks",
                                           len(c["eligible_ticks"]),
                                           len(d["eligible_ticks"])))
            print("     %-26s %-28s %s" % ("horizon warning at v2",
                                           (c["warning"] or "None")[:26],
                                           d["warning"] or "None"))
            print("     fires before anything is due: %s"
                  % c["fires_before_anything_is_due"])
            for entry in c["journal"]:
                print("       journal: %s" % entry)
        print()

    print("  discriminating: %d / %d" % (s["discriminating"], s["behaviors"]))
    print("  limitation: %s" % s["corpus_limitation"])
    ok = not s["not_discriminating"]
    print()
    print("P2S-04 SUITE %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
