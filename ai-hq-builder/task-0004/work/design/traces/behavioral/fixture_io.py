"""Fixture loading with a STRUCTURAL input/oracle split (P2S-01 anti-circularity).

The prior harness failed because engine code could reach the fixtures' prewritten
results. This module makes that impossible by construction rather than by
convention: `load_stimuli()` returns `Stimulus` objects that physically do not
carry the oracle fields, so no engine module can read one even by mistake.

Field taxonomy (Task Packet §Trust and data classes; §Implementation allowlist):

  INPUT-SIDE  (engine + scenario modules may read)
      id, title, normalized_input, envelope, start_state, policy

  ORACLE-ONLY (oracle/judge modules only)
      expected, actual, verdict, pass_rule, forbidden, required_evidence,
      allowed_alternatives, trace_S2, delta_S1, delta_S3, gap_or_falsifier

`trace_S2`, `delta_S1`, `delta_S3` and `actual` are classified ORACLE because they
are prewritten *results* — the S2 transition trace and the S1/S3 divergences are
exactly what the engine must compute for itself (P2S-01 requirements 2, 3 and 9).
Copying them is the specific defect the verifier found.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

INPUT_SIDE_FIELDS: Tuple[str, ...] = (
    "id",
    "title",
    "normalized_input",
    "envelope",
    "start_state",
    "policy",
)

ORACLE_FIELDS: Tuple[str, ...] = (
    "expected",
    "actual",
    "verdict",
    "pass_rule",
    "forbidden",
    "required_evidence",
    "allowed_alternatives",
    "trace_S2",
    "delta_S1",
    "delta_S3",
    "gap_or_falsifier",
)


@dataclass(frozen=True)
class Stimulus:
    """Input-side view of one fixture. Carries no oracle data, by construction."""

    id: str
    title: str
    normalized_input: str
    start_state: str
    policy: str
    envelopes: Tuple[Dict[str, str], ...]

    @property
    def envelope_count(self) -> int:
        return len(self.envelopes)


@dataclass(frozen=True)
class OracleCase:
    """Oracle-side view of one fixture. Consumed only by oracle.py / judge.py."""

    id: str
    expected: Any
    actual: Any
    verdict: Any
    pass_rule: Any
    forbidden: List[str] = field(default_factory=list)
    required_evidence: List[str] = field(default_factory=list)
    allowed_alternatives: List[str] = field(default_factory=list)
    trace_S2: Any = None
    delta_S1: Any = None
    delta_S3: Any = None
    gap_or_falsifier: Any = None


def _read(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_stimuli(path: str) -> List[Stimulus]:
    """Load INPUT-SIDE stimuli only. This is the engine's sole fixture entry point."""
    doc = _read(path)
    out: List[Stimulus] = []
    for case in doc["cases"]:
        env = case["envelope"]
        envelopes = tuple(dict(e) for e in (env if isinstance(env, list) else [env]))
        out.append(
            Stimulus(
                id=case["id"],
                title=case["title"],
                normalized_input=case["normalized_input"],
                start_state=case["start_state"],
                policy=case["policy"],
                envelopes=envelopes,
            )
        )
    return out


def load_oracle(path: str) -> Dict[str, OracleCase]:
    """Load ORACLE-side data. Imported only by oracle.py / judge.py."""
    doc = _read(path)
    out: Dict[str, OracleCase] = {}
    for case in doc["cases"]:
        out[case["id"]] = OracleCase(
            id=case["id"],
            expected=case.get("expected"),
            actual=case.get("actual"),
            verdict=case.get("verdict"),
            pass_rule=case.get("pass_rule"),
            forbidden=list(case.get("forbidden") or []),
            required_evidence=list(case.get("required_evidence") or []),
            allowed_alternatives=list(case.get("allowed_alternatives") or []),
            trace_S2=case.get("trace_S2"),
            delta_S1=case.get("delta_S1"),
            delta_S3=case.get("delta_S3"),
            gap_or_falsifier=case.get("gap_or_falsifier"),
        )
    return out


def envelope_contract(path: str) -> Dict[str, Any]:
    """The SV-1 envelope contract (required fields, multi-input and unknown rules)."""
    return _read(path)["envelope_contract"]
