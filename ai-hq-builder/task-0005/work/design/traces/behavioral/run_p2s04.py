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

P2V-04 — WHAT THE VERSION-BINDING STILL MISSED. Retiring a version made its horizon
ineligible while that version was out of force, and left the materialized ticks in
place under their version key. Changing BACK to a retired version therefore reinstated
its entire pre-retirement horizon: v1's 41 ticks became eligible again, none of them
extended since before the first change, and the exhaustion warning went quiet. A
schedule changed away from and back was covered by a horizon nobody had touched.

Retirement is permanent now. `change_schedule()` refuses a spec whose version has been
retired and adopts nothing; `register()` refuses one too. The legitimate need — an
owner reinstating a schedule — is `reactivate()`, which mints a version number that has
never been in force and an empty horizon the scheduler must extend. Behavior 5 is the
probe, with `retired_versions_can_return` as its targeted defect.

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


# --------------------------------------------------------------------------
# The control journal — the durable authority (P2W-04)
#
# R1 kept `retired_versions` as a dict on the Watchdog and disclosed that it was
# in-memory only. The verifier took the disclosure and built the falsifier: restore a
# process with its spec and horizons but without the retirement list, and the retired
# version walks back into force with 41 stale ticks. "In-memory permanence cannot
# satisfy a system designed to survive process failure and replay."
#
# Fable's RW-35 ruling makes the journal the authority. Every governed transition is
# an entry; `retired_versions`, `versions_ever_used`, the live spec and the
# materialized horizons are all DERIVED by folding it. A restarting watchdog is
# `Watchdog.from_journal(entries)` and rebuilds the retired set before it will accept
# a registration — there is no path that restores some of the state and not the rest,
# because there is only one thing to restore.
# --------------------------------------------------------------------------

JOURNAL_SCHEMA = "watchdog-control-journal/1"

J_REGISTERED = "ScheduleRegistered"
J_CHANGED = "ScheduleChanged"
J_RETIRED = "HorizonRetired"
J_REFUSED = "TransitionRefused"
J_HORIZON = "HorizonExtended"
J_RUN_STARTED = "RunStarted"


def _entry(kind: str, schedule_id: str, at: int, **fields) -> Dict[str, object]:
    row: Dict[str, object] = {"kind": kind, "schedule_id": schedule_id, "at": at}
    row.update(fields)
    return row


@dataclass
class Watchdog:
    """The control-service watchdog. Holds specs; computes its own expectations.

    TARGETED DEFECT switches, one per behavior that needs one:
      `depends_on_scheduler_reports`  behavior 1 — the superseded model in which the
                                      watchdog only knew about occurrences the
                                      scheduler announced.
      `horizon_monitoring`            behavior 2 — horizon monitoring off.
      `atomic_schedule_change`        behavior 3 — withdraw-then-fail-to-adopt.
      `version_bound_horizon`         behavior 4 (P2U-03) — the horizon read as one
                                      unversioned list.
      `retired_versions_can_return`   behavior 5 (P2V-04) — retirement lapses when
                                      the version leaves force.
      `monotonic_versions`            behaviors 6-8 (P2W-04) — off, a version may be
                                      reused: `register()` replaces a live schedule
                                      and `change_schedule()` accepts the version
                                      already in force or a lower one.
      `durable_retirement`            behavior 9 (P2W-04) — off, `from_journal()`
                                      ignores the journal's retirement entries, which
                                      is exactly the restart the verifier simulated.
      `optimistic_concurrency`        behavior 10 (P2W-04) — off, the caller's
                                      expected-current-version is ignored, so two
                                      changes computed against one observed state
                                      both land.
      `register_replaces_live`        behavior 7 (P2W-04) — on, `register()` is the
                                      R1 version: it overwrites whatever is in force
                                      and retires nothing.

    STATE IS DERIVED. `specs`, `expected_runs`, `retired_versions` and
    `versions_ever_used` are rebuilt from `journal` by `_replay()`; nothing writes
    them except that fold. The journal is the only thing a restart needs.
    """

    journal: List[Dict[str, object]] = field(default_factory=list)
    run_started: List[Tuple[str, int]] = field(default_factory=list)
    specs: Dict[str, RecurrenceSpec] = field(default_factory=dict)
    expected_runs: Dict[str, Dict[int, List[int]]] = field(default_factory=dict)
    retired_versions: Dict[str, List[int]] = field(default_factory=dict)
    versions_ever_used: Dict[str, List[int]] = field(default_factory=dict)
    depends_on_scheduler_reports: bool = False
    horizon_monitoring: bool = True
    atomic_schedule_change: bool = True
    version_bound_horizon: bool = True
    retired_versions_can_return: bool = False
    monotonic_versions: bool = True
    durable_retirement: bool = True
    optimistic_concurrency: bool = True
    register_replaces_live: bool = False

    # ---- journal fold ------------------------------------------------------
    def _replay(self) -> None:
        """Rebuild every piece of derived state from the journal. Idempotent."""
        self.specs = {}
        self.expected_runs = {}
        self.retired_versions = {}
        self.versions_ever_used = {}
        self.run_started = []
        specs_by_version: Dict[Tuple[str, int], RecurrenceSpec] = {}
        for entry in self.journal:
            kind = entry["kind"]
            sid = entry["schedule_id"]
            if kind in (J_REGISTERED, J_CHANGED):
                spec = RecurrenceSpec(sid, int(entry["version"]),
                                      first_due=int(entry["first_due"]),
                                      period=int(entry["period"]))
                specs_by_version[(sid, spec.version)] = spec
                self.specs[sid] = spec
                self.expected_runs.setdefault(sid, {}).setdefault(spec.version, [])
                seen = self.versions_ever_used.setdefault(sid, [])
                if spec.version not in seen:
                    seen.append(spec.version)
            elif kind == J_RETIRED:
                if not self.durable_retirement:
                    # TARGETED DEFECT for behavior 9: the restart restores the spec
                    # and the horizons and drops the retirement, which is the state
                    # the verifier restored by hand.
                    continue
                version = int(entry["version"])
                retired = self.retired_versions.setdefault(sid, [])
                if version not in retired:
                    retired.append(version)
            elif kind == J_HORIZON:
                version = int(entry["version"])
                spec = specs_by_version.get((sid, version))
                if spec is not None:
                    self.expected_runs.setdefault(sid, {})[version] = \
                        spec.deadlines_through(int(entry["through"]))
            elif kind == J_RUN_STARTED:
                self.run_started.append((sid, int(entry["at"])))

    @classmethod
    def from_journal(cls, entries, **switches) -> "Watchdog":
        """A restarting watchdog: the journal is all it is given."""
        wd = cls(journal=[dict(e) for e in entries], **switches)
        wd._replay()
        return wd

    def _append(self, entry: Dict[str, object]) -> None:
        self.journal.append(entry)
        self._replay()

    # --- governed registration (SCH-01 versioned) --------------------------
    def is_retired(self, schedule_id: str, version: int) -> bool:
        if self.retired_versions_can_return:
            return False
        return version in self.retired_versions.get(schedule_id, [])

    def highest_version_ever(self, schedule_id: str) -> int:
        """The highest version this schedule has EVER held, from the journal fold."""
        return max(self.versions_ever_used.get(schedule_id, [0]) or [0])

    def next_version(self, schedule_id: str) -> int:
        return self.highest_version_ever(schedule_id) + 1

    def _refuse(self, schedule_id: str, version: int, at: int, reason: str) -> bool:
        self._append(_entry(J_REFUSED, schedule_id, at, version=version,
                            reason=reason))
        return False

    def register(self, spec: RecurrenceSpec, now: int = 0) -> bool:
        """INITIAL registration only, or an exact re-registration of the live spec.

        P2W-04 falsifier B: `register()` used to overwrite whatever was in force. The
        verifier registered v1, materialized its horizon, registered v2, then
        registered v1 again — accepted, `retired_versions: []`, 41 stale ticks
        eligible, no warning. Registration is not a change; a change is
        `change_schedule()`, which is monotonic and retires what it supersedes.
        """
        live = self.specs.get(spec.schedule_id)
        if live is not None and self.register_replaces_live:
            # TARGETED DEFECT for behavior 7: R1's register(), which overwrote the
            # live schedule and retired nothing — the verifier's journal shows three
            # plain ScheduleRegistered lines and `retired_versions: []`.
            self._append(_entry(J_REGISTERED, spec.schedule_id, now,
                                version=spec.version, first_due=spec.first_due,
                                period=spec.period))
            return True
        if live is not None:
            if live == spec:
                return True                       # idempotent for the same immutable spec
            return self._refuse(
                spec.schedule_id, spec.version, now,
                "register() is initial-only: %s already has v%d in force; a change "
                "is change_schedule(), which is monotonic and retires what it "
                "supersedes" % (spec.schedule_id, live.version))
        if self.is_retired(spec.schedule_id, spec.version):
            return self._refuse(spec.schedule_id, spec.version, now,
                                "version is retired and can never re-enter force")
        if self.monotonic_versions \
                and spec.version <= self.highest_version_ever(spec.schedule_id):
            return self._refuse(
                spec.schedule_id, spec.version, now,
                "version %d is not above the highest ever used (%d)"
                % (spec.version, self.highest_version_ever(spec.schedule_id)))
        self._append(_entry(J_REGISTERED, spec.schedule_id, now,
                            version=spec.version, first_due=spec.first_due,
                            period=spec.period))
        return True

    def change_schedule(self, spec: RecurrenceSpec, now: int,
                        expected_current_version: Optional[int] = None) -> bool:
        """A governed change re-registers the spec ATOMICALLY with the watchdog.

        P2U-03: the same transaction that adopts the new spec retires every
        prior-version horizon entry and establishes the new version's horizon state.

        P2V-04: retirement is permanent — a retired version cannot re-enter force.

        P2W-04: version identity is MINTED ONCE and strictly monotonic per schedule.
        The R1 version excluded the current version from retirement and then
        `setdefault()`-ed that same version's horizon, so a change that kept
        `version=1` while altering the recurrence left 41 ticks materialized under the
        OLD definition eligible for the NEW one — falsifier A, and it needed no
        retirement to happen at all. A change must now name a version strictly above
        the highest ever used for the schedule.

        `expected_current_version` is optimistic concurrency: two changes computed
        against the same observed state cannot both land, because the second one's
        expectation no longer matches what the first one put in force.
        """
        if not self.atomic_schedule_change:
            self.journal.append(_entry(J_REFUSED, spec.schedule_id, now,
                                       version=spec.version,
                                       reason="non-atomic withdraw, adoption lost"))
            self.specs.pop(spec.schedule_id, None)
            return False

        live = self.specs.get(spec.schedule_id)
        if expected_current_version is not None and self.optimistic_concurrency:
            in_force = live.version if live is not None else None
            if in_force != expected_current_version:
                return self._refuse(
                    spec.schedule_id, spec.version, now,
                    "concurrent change: caller expected v%s in force, found v%s"
                    % (expected_current_version, in_force))

        if self.is_retired(spec.schedule_id, spec.version):
            return self._refuse(
                spec.schedule_id, spec.version, now,
                "version retired at an earlier change; its horizon has %d stale "
                "tick(s) and cannot answer for the schedule again — use reactivate()"
                % len(self.expected_runs.get(spec.schedule_id, {}).get(
                    spec.version, [])))

        highest = self.highest_version_ever(spec.schedule_id)
        if self.monotonic_versions and spec.version <= highest:
            return self._refuse(
                spec.schedule_id, spec.version, now,
                "version %d is not above the highest ever used for this schedule "
                "(%d) — schedule-version identity is minted once and never reused "
                "(P2W-04)" % (spec.version, highest))

        superseded = sorted(v for v in self.versions_ever_used.get(spec.schedule_id, [])
                            if v != spec.version
                            and v not in self.retired_versions.get(spec.schedule_id, []))
        entries = [_entry(J_RETIRED, spec.schedule_id, now, version=v,
                          stale_ticks=len(self.expected_runs.get(
                              spec.schedule_id, {}).get(v, [])))
                   for v in superseded]
        entries.append(_entry(J_CHANGED, spec.schedule_id, now, version=spec.version,
                              first_due=spec.first_due, period=spec.period))
        # One transaction: the retirements and the adoption are appended together, so
        # no fold of this journal can ever see one without the other.
        self.journal.extend(entries)
        self._replay()
        return True

    def reactivate(self, schedule_id: str, first_due: int, period: int,
                   now: int) -> RecurrenceSpec:
        """Bring a retired recurrence back under a FRESH version and empty horizon."""
        spec = RecurrenceSpec(schedule_id, self.next_version(schedule_id),
                              first_due=first_due, period=period)
        self.change_schedule(spec, now=now)
        return spec

    # --- the scheduler's side ----------------------------------------------
    def scheduler_completes_run(self, schedule_id: str, at: int) -> None:
        self._append(_entry(J_RUN_STARTED, schedule_id, at))

    def scheduler_extends_horizon(self, schedule_id: str, through: int,
                                  at: int = 0) -> None:
        """Materialize ExpectedRun records UNDER THE VERSION CURRENTLY IN FORCE."""
        spec = self.specs.get(schedule_id)
        if spec is None:
            return
        self._append(_entry(J_HORIZON, schedule_id, at, version=spec.version,
                            through=through))

    # --- the watchdog's own audit ------------------------------------------
    def _all_materialized(self, schedule_id: str) -> List[int]:
        out: List[int] = []
        for ticks in self.expected_runs.get(schedule_id, {}).values():
            out.extend(ticks)
        return sorted(out)

    def eligible_horizon(self, schedule_id: str) -> List[int]:
        """The materialized ticks that count as coverage for the spec in force."""
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
            "versions_ever_used": sorted(self.versions_ever_used.get(schedule_id, [])),
            "eligible_ticks": self.eligible_horizon(schedule_id),
        }

    def journal_lines(self) -> List[str]:
        """The journal as readable lines, for shipped evidence."""
        out = []
        for e in self.journal:
            extra = ", ".join("%s=%s" % (k, v) for k, v in sorted(e.items())
                              if k not in ("kind", "schedule_id", "at"))
            out.append("%s:%s@t%s%s" % (e["kind"], e["schedule_id"], e["at"],
                                        "(" + extra + ")" if extra else ""))
        return out

    def missed_deadlines(self, schedule_id: str, now: int) -> List[int]:
        """Deadlines that passed with no matching RunStarted receipt (rule 1)."""
        if self.depends_on_scheduler_reports:
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
    """3 — a versioned change races a computed deadline; no orphan, no gap."""
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
    """4 — the P2U-03 probe: a v1 horizon far ahead cannot satisfy v2 coverage."""
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
            "journal": wd.journal_lines()}


def behavior_retired_version_reentry(defect: bool) -> Dict[str, object]:
    """5 — the P2V-04 probe: a retired version cannot re-enter force."""
    v1 = RecurrenceSpec("ritual.brief", 1, first_due=40 * DAY, period=DAY)
    v2 = RecurrenceSpec("ritual.brief", 2, first_due=40 * DAY + 3, period=DAY)
    wd = Watchdog(retired_versions_can_return=defect, monotonic_versions=not defect)
    wd.register(v1)
    wd.scheduler_extends_horizon("ritual.brief", through=80 * DAY)
    now = 39 * DAY
    wd.change_schedule(v2, now=now)
    warning_at_v2 = wd.horizon_exhausted("ritual.brief", now)

    accepted = wd.change_schedule(v1, now=now)      # back to the RETIRED version
    state = wd.horizon_state("ritual.brief")
    warning_after = wd.horizon_exhausted("ritual.brief", now)

    reactivated = wd.reactivate("ritual.brief", first_due=41 * DAY, period=DAY, now=now)
    after_reactivation = wd.horizon_state("ritual.brief")

    return {
        "now": now,
        "warning_at_v2": warning_at_v2,
        "reentry_accepted": accepted,
        "version_in_force_after_reentry_attempt": state["version_in_force"],
        "eligible_ticks_after_reentry_attempt": len(state["eligible_ticks"]),
        "warning_after_reentry_attempt": warning_after,
        "reactivated_version": reactivated.version,
        "reactivated_eligible_ticks": len(after_reactivation["eligible_ticks"]),
        "reactivated_warning_fires":
            wd.horizon_exhausted("ritual.brief", now) is not None,
        "detected": (not accepted and state["version_in_force"] == 2
                     and not state["eligible_ticks"] and warning_after is not None),
        "journal": wd.journal_lines(),
    }


# --------------------------------------------------------------------------
# P2W-04 — the three paths the verifier found, plus replay
# --------------------------------------------------------------------------

def _seeded(sid, defect):
    """v1 registered, 41 ticks materialized, at the observation tick."""
    v1 = RecurrenceSpec(sid, 1, first_due=40 * DAY, period=DAY)
    wd = Watchdog(monotonic_versions=not defect)
    wd.register(v1)
    wd.scheduler_extends_horizon(sid, through=80 * DAY)
    return wd, v1, 39 * DAY


def behavior_same_version_change(defect: bool) -> Dict[str, object]:
    """6 — falsifier A: `change_schedule()` with a DIFFERENT recurrence, version=1.

    R1 excluded the current version from retirement and `setdefault()`-ed its horizon,
    so the 41 ticks materialized under the OLD definition stayed eligible under the
    NEW one. No retirement was involved; the version simply never changed.
    """
    sid = "same-version"
    wd, v1, now = _seeded(sid, defect)
    mutated = RecurrenceSpec(sid, 1, first_due=40 * DAY + 5, period=2 * DAY)
    accepted = wd.change_schedule(mutated, now=now)
    state = wd.horizon_state(sid)
    in_force = wd.specs[sid]
    # The claim is NOT that a warning fires. After a refusal v1 is still in force with
    # its own horizon, and that horizon legitimately covers it — there is nothing to
    # warn about. My first version of this predicate demanded a warning anyway and
    # reported the correct behavior as a failure. What must be true is that the
    # mutated recurrence never took effect while keeping the old coverage.
    return {"now": now, "accepted": accepted,
            "version_in_force": state["version_in_force"],
            "eligible_stale_ticks": len(state["eligible_ticks"]),
            "recurrence_in_force": [in_force.first_due, in_force.period],
            "mutated_recurrence": [mutated.first_due, mutated.period],
            "stale_ticks_cover_the_mutated_definition":
                accepted and len(state["eligible_ticks"]) > 0,
            "detected": (not accepted
                         and [in_force.first_due, in_force.period]
                         == [v1.first_due, v1.period]),
            "journal": wd.journal_lines()}


def behavior_register_replacement(defect: bool) -> Dict[str, object]:
    """7 — falsifier B: register(v1), register(v2), register(v1) again.

    R1's `register()` overwrote whatever was in force and retired nothing. The
    verifier's journal shows three plain `ScheduleRegistered` lines,
    `retired_versions: []`, v1 back in force with 41 eligible ticks and no warning.
    """
    sid = "register-bypass"
    v1 = RecurrenceSpec(sid, 1, first_due=40 * DAY, period=DAY)
    wd = Watchdog(register_replaces_live=defect, monotonic_versions=not defect)
    wd.register(v1)
    wd.scheduler_extends_horizon(sid, through=80 * DAY)
    now = 39 * DAY
    v2 = RecurrenceSpec(sid, 2, first_due=40 * DAY + 3, period=DAY)
    register_v2 = wd.register(v2, now=now)
    # Re-registering the EXACT immutable spec is idempotent and changes nothing —
    # the required correction says "initial-only OR idempotent for the exact same
    # immutable spec", so this returning True is the contract, not a bypass. My first
    # predicate demanded False here and reported the contract as a failure.
    register_v1_identical = wd.register(
        RecurrenceSpec(sid, 1, first_due=40 * DAY, period=DAY), now=now)
    # A DIFFERENT recurrence under a used version is the bypass, and must be refused.
    register_v1_mutated = wd.register(
        RecurrenceSpec(sid, 1, first_due=40 * DAY + 9, period=3 * DAY), now=now)
    state = wd.horizon_state(sid)
    in_force = wd.specs[sid]
    return {"now": now, "register_v2": register_v2,
            "register_v1_identical_is_idempotent": register_v1_identical,
            "register_v1_mutated": register_v1_mutated,
            "version_in_force": state["version_in_force"],
            "recurrence_in_force": [in_force.first_due, in_force.period],
            "eligible_stale_ticks": len(state["eligible_ticks"]),
            "retired_versions": state["retired_versions"],
            "detected": (not register_v2 and not register_v1_mutated
                         and register_v1_identical
                         and [in_force.first_due, in_force.period]
                         == [v1.first_due, v1.period]),
            "journal": wd.journal_lines()}


def behavior_lower_and_duplicate_version(defect: bool) -> Dict[str, object]:
    """8 — lower-version and duplicate-version submission through change_schedule."""
    sid = "monotonic"
    wd, _v1, now = _seeded(sid, defect)
    wd.change_schedule(RecurrenceSpec(sid, 5, first_due=41 * DAY, period=DAY), now=now)
    duplicate = wd.change_schedule(
        RecurrenceSpec(sid, 5, first_due=42 * DAY, period=DAY), now=now)
    lower = wd.change_schedule(
        RecurrenceSpec(sid, 3, first_due=43 * DAY, period=DAY), now=now)
    state = wd.horizon_state(sid)
    return {"now": now, "duplicate_accepted": duplicate, "lower_accepted": lower,
            "version_in_force": state["version_in_force"],
            "versions_ever_used": state["versions_ever_used"],
            "detected": not duplicate and not lower
                        and state["version_in_force"] == 5,
            "journal": wd.journal_lines()}


def behavior_restart_state_restore(defect: bool) -> Dict[str, object]:
    """9 — falsifier C: a process restart must not lose permanent retirement.

    The verifier restored the spec and the horizons without the retirement list. That
    state is now unreachable: retirement is a journal entry, and a restart is
    `from_journal()` over the same entries. The targeted defect makes the fold IGNORE
    retirement entries, which reproduces exactly what the verifier restored by hand.
    """
    sid = "restart"
    wd, _v1, now = _seeded(sid, False)
    v2 = RecurrenceSpec(sid, 2, first_due=40 * DAY + 3, period=DAY)
    wd.change_schedule(v2, now=now)
    retired_before = dict(wd.retired_versions)
    durable = list(wd.journal)

    restarted = Watchdog.from_journal(durable, durable_retirement=not defect,
                                      monotonic_versions=not defect)
    retired_after = dict(restarted.retired_versions)
    reentry = restarted.change_schedule(
        RecurrenceSpec(sid, 1, first_due=40 * DAY, period=DAY), now=now)
    state = restarted.horizon_state(sid)
    warning = restarted.horizon_exhausted(sid, now)
    return {"now": now,
            "journal_entries_persisted": len(durable),
            "retired_before": {k: sorted(v) for k, v in retired_before.items()},
            "retired_after": {k: sorted(v) for k, v in retired_after.items()},
            "reentry_accepted": reentry,
            "version_in_force": state["version_in_force"],
            "eligible_stale_ticks": len(state["eligible_ticks"]),
            "warning": warning,
            "detected": (retired_after == retired_before and not reentry
                         and warning is not None),
            "journal": restarted.journal_lines()}


def behavior_concurrent_change(defect: bool) -> Dict[str, object]:
    """10 — two changes computed against the same observed state; one must lose."""
    sid = "concurrent"
    v1 = RecurrenceSpec(sid, 1, first_due=40 * DAY, period=DAY)
    wd = Watchdog(optimistic_concurrency=not defect)
    wd.register(v1)
    wd.scheduler_extends_horizon(sid, through=80 * DAY)
    now = 39 * DAY
    observed = wd.specs[sid].version
    first = wd.change_schedule(RecurrenceSpec(sid, 2, first_due=41 * DAY, period=DAY),
                               now=now, expected_current_version=observed)
    second = wd.change_schedule(RecurrenceSpec(sid, 3, first_due=42 * DAY, period=DAY),
                                now=now, expected_current_version=observed)
    state = wd.horizon_state(sid)
    return {"now": now, "observed_version": observed,
            "first_accepted": first, "second_accepted": second,
            "version_in_force": state["version_in_force"],
            "detected": first and not second and state["version_in_force"] == 2,
            "journal": wd.journal_lines()}


def behavior_replay_determinism(defect: bool) -> Dict[str, object]:
    """11 — replaying the durable journal must reach the same version decision.

    The point of making the journal the authority is that it is sufficient. Folding
    the same entries in a fresh process must produce the same spec in force, the same
    retired set, and the same horizon — and must then make the same decision about a
    re-entry attempt.
    """
    sid = "replay"
    wd, _v1, now = _seeded(sid, False)
    wd.change_schedule(RecurrenceSpec(sid, 2, first_due=41 * DAY, period=DAY), now=now)
    wd.scheduler_extends_horizon(sid, through=90 * DAY, at=now)
    original = wd.horizon_state(sid)

    replayed = Watchdog.from_journal(wd.journal, durable_retirement=not defect,
                                     monotonic_versions=not defect)
    replayed_state = replayed.horizon_state(sid)
    twice = Watchdog.from_journal(replayed.journal,
                                  durable_retirement=not defect,
                                  monotonic_versions=not defect).horizon_state(sid)

    decision_original = wd.change_schedule(
        RecurrenceSpec(sid, 1, first_due=40 * DAY, period=DAY), now=now)
    decision_replayed = replayed.change_schedule(
        RecurrenceSpec(sid, 1, first_due=40 * DAY, period=DAY), now=now)
    return {"now": now,
            "original_state": original,
            "replayed_state": replayed_state,
            "replayed_twice_state": twice,
            "states_identical": original == replayed_state == twice,
            "decision_original": decision_original,
            "decision_replayed": decision_replayed,
            "decisions_identical": decision_original == decision_replayed,
            "detected": (original == replayed_state == twice
                         and decision_original == decision_replayed
                         and not decision_original)}


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
    ("retired-version-cannot-re-enter-force",
     "P2V-04 — retirement is permanent: changing back to a retired version is "
     "refused, its stale horizon never becomes eligible again, and reactivation "
     "mints a fresh version with an empty horizon",
     "retirement lapses when the version leaves force (the pre-P2V-04 reading)",
     behavior_retired_version_reentry),
    ("same-version-changed-recurrence",
     "P2W-04 falsifier A — a change that keeps the version in force must be refused: "
     "41 ticks materialized under the old definition cannot cover a new one",
     "versions reusable (the pre-P2W-04 reading: the current version is excluded "
     "from retirement and its horizon is kept)",
     behavior_same_version_change),
    ("register-is-initial-only",
     "P2W-04 falsifier B — register() is initial registration, not a change: it "
     "cannot replace a live schedule and cannot bring a superseded version back",
     "register() replaces whatever is in force and retires nothing",
     behavior_register_replacement),
    ("monotonic-version-identity",
     "P2W-04 — schedule-version identity is minted once: a duplicate or lower "
     "version is refused, and the highest version ever used is the floor",
     "versions reusable: any version number is accepted",
     behavior_lower_and_duplicate_version),
    ("restart-preserves-retirement",
     "P2W-04 falsifier C — retirement survives a process restart because it is a "
     "control-journal entry, and a restart is a fold of that journal",
     "the restart fold ignores retirement entries (R1's in-memory-only authority)",
     behavior_restart_state_restore),
    ("concurrent-change-attempts",
     "P2W-04 — two changes computed against the same observed state cannot both "
     "land; the second one's expectation no longer matches what is in force",
     "no optimistic concurrency: the caller's expected-current-version is ignored, "
     "so both changes land and the second silently overwrites the first",
     behavior_concurrent_change),
    ("replay-from-durable-events",
     "P2W-04 — folding the durable journal in a fresh process reaches the same "
     "spec, the same retired set, the same horizon and the same decision",
     "the restart fold ignores retirement entries, so the replay disagrees",
     behavior_replay_determinism),
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
                "expired control envelope. All eleven behaviors have NO fixture-driven "
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
        elif r["behavior"].startswith("retired-version"):
            c, d = r["clean"], r["defect"]
            print("     the P2V-04 probe: v1 horizon materialized, change to v2, "
                  "then change BACK to v1")
            print("     %-30s %-24s %s" % ("", "PERMANENT (clean)", "LAPSING (defect)"))
            for label, key in (("re-entry accepted", "reentry_accepted"),
                               ("version in force after",
                                "version_in_force_after_reentry_attempt"),
                               ("eligible ticks after",
                                "eligible_ticks_after_reentry_attempt")):
                print("     %-30s %-24s %s" % (label, c[key], d[key]))
            print("     %-30s %-24s %s"
                  % ("horizon warning after",
                     (c["warning_after_reentry_attempt"] or "None")[:22],
                     (d["warning_after_reentry_attempt"] or "None")[:22]))
            print("     reactivate() minted v%s with %d eligible tick(s); warning "
                  "still up: %s" % (c["reactivated_version"],
                                    c["reactivated_eligible_ticks"],
                                    c["reactivated_warning_fires"]))
            for entry in c["journal"]:
                print("       journal: %s" % entry)
        elif r["behavior"] in ("same-version-changed-recurrence",
                               "register-is-initial-only",
                               "monotonic-version-identity",
                               "restart-preserves-retirement",
                               "concurrent-change-attempts",
                               "replay-from-durable-events"):
            c, d = r["clean"], r["defect"]
            keys = [k for k in c
                    if k not in ("journal", "now", "detected", "original_state",
                                 "replayed_state", "replayed_twice_state",
                                 "retired_before", "retired_after")]
            print("     %-30s %-24s %s" % ("", "ENFORCED (clean)", "REUSABLE (defect)"))
            for k in keys:
                print("     %-30s %-24s %s" % (k, str(c.get(k))[:24],
                                               str(d.get(k))[:34]))
            if "retired_before" in c:
                print("     %-30s %-24s %s"
                      % ("retired before / after restart",
                         "%s / %s" % (c["retired_before"], c["retired_after"]),
                         "%s / %s" % (d["retired_before"], d["retired_after"])))
            for entry in (c.get("journal") or [])[:9]:
                print("       journal: %s" % entry)
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
