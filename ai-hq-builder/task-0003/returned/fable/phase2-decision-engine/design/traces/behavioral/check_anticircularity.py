"""Anti-circularity check (Task Packet acceptance criterion 1).

  "the engine/scenario code contains no read of any fixture `expected`, `actual`,
   `verdict`, or `pass_rule` field (grep-verifiable)"

Three independent checks:

  A  TEXTUAL   — no engine/scenario module mentions an oracle field name at all.
  B  IMPORT    — no engine/scenario module imports the oracle side or calls
                 `load_oracle`, so it has no path to that data even indirectly.
  C  STRUCTURAL— `Stimulus` (the engine's only fixture input) exposes exactly the
                 input-side attributes and physically carries no oracle value.
                 This is the check that survives refactoring: even a module that
                 *wanted* an expected result has nothing to read it from.

Exit code 0 only if all three pass.

Usage:  python3 check_anticircularity.py
"""

from __future__ import annotations

import ast
import json
import os
import re
import sys
from typing import Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))

# Modules that compute candidate behavior. These may never touch oracle data.
# `mutations.py` is included: it perturbs computed results and must be as
# oracle-blind as the engine itself, or a mutation could be tuned to a
# fixture's expected answer.
ENGINE_MODULES = ("engine_core.py", "events.py", "fold.py", "scenarios.py",
                  "simulate.py", "mutations.py")
# Modules permitted to read oracle data.
ORACLE_MODULES = ("oracle.py", "judge.py")
# The boundary module: declares both views, hands out only Stimulus to the engine.
BOUNDARY_MODULE = "fixture_io.py"

ORACLE_FIELDS = ("expected", "actual", "verdict", "pass_rule", "forbidden",
                 "required_evidence", "allowed_alternatives", "trace_S2",
                 "delta_S1", "delta_S3", "gap_or_falsifier")

INPUT_SIDE_FIELDS = ("id", "title", "normalized_input", "envelope", "start_state", "policy")


def check_textual() -> Dict[str, object]:
    """A — no oracle field name appears anywhere in engine/scenario source."""
    hits: List[Dict[str, object]] = []
    for mod in ENGINE_MODULES:
        path = os.path.join(HERE, mod)
        with open(path, "r", encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                stripped = line.strip()
                for fld in ORACLE_FIELDS:
                    # Word-boundary match, so `expected` matches but `expected_x` in a
                    # comment about the contract does not create false confidence:
                    # any occurrence at all is reported.
                    if re.search(r"\b%s\b" % re.escape(fld), line):
                        # Allow the documented prohibition itself to name the fields.
                        if stripped.startswith("#") or _in_docstring_region(path, lineno):
                            hits.append({"module": mod, "line": lineno, "field": fld,
                                         "text": stripped[:100], "context": "comment/docstring"})
                        else:
                            hits.append({"module": mod, "line": lineno, "field": fld,
                                         "text": stripped[:100], "context": "CODE"})
    code_hits = [h for h in hits if h["context"] == "CODE"]
    return {"check": "A-textual", "passed": not code_hits,
            "code_hits": code_hits, "doc_mentions": len(hits) - len(code_hits)}


def _in_docstring_region(path: str, lineno: int) -> bool:
    with open(path, "r", encoding="utf-8") as fh:
        src = fh.read()
    tree = ast.parse(src)
    spans: List[range] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc and node.body:
                first = node.body[0]
                if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                    spans.append(range(first.lineno, (first.end_lineno or first.lineno) + 1))
    return any(lineno in s for s in spans)


def check_imports() -> Dict[str, object]:
    """B — no engine/scenario module imports the oracle side or load_oracle."""
    violations: List[Dict[str, object]] = []
    banned_modules = {m[:-3] for m in ORACLE_MODULES}
    for mod in ENGINE_MODULES:
        path = os.path.join(HERE, mod)
        with open(path, "r", encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.split(".")[0] in banned_modules:
                        violations.append({"module": mod, "line": node.lineno,
                                           "imports": a.name})
            elif isinstance(node, ast.ImportFrom):
                root = (node.module or "").split(".")[0]
                if root in banned_modules:
                    violations.append({"module": mod, "line": node.lineno,
                                       "imports": node.module})
                for a in node.names:
                    if a.name == "load_oracle" or a.name == "OracleCase":
                        violations.append({"module": mod, "line": node.lineno,
                                           "imports": a.name})
            elif isinstance(node, ast.Call):
                fn = node.func
                name = getattr(fn, "id", None) or getattr(fn, "attr", None)
                if name == "load_oracle":
                    violations.append({"module": mod, "line": node.lineno,
                                       "imports": "load_oracle() call"})
    return {"check": "B-imports", "passed": not violations, "violations": violations}


def check_structural() -> Dict[str, object]:
    """C — the engine's fixture input type carries no oracle attribute."""
    sys.path.insert(0, HERE)
    import fixture_io  # noqa: E402

    fields = tuple(fixture_io.Stimulus.__dataclass_fields__.keys())
    leaked = [f for f in fields if f in ORACLE_FIELDS]
    # `envelopes` is the normalized form of the input-side `envelope` field.
    expected_fields = ("id", "title", "normalized_input", "start_state", "policy", "envelopes")
    shape_ok = set(fields) == set(expected_fields)
    return {
        "check": "C-structural",
        "passed": not leaked and shape_ok,
        "stimulus_fields": list(fields),
        "oracle_fields_leaked": leaked,
        "field_set_as_declared": shape_ok,
    }


def main() -> int:
    results = [check_textual(), check_imports(), check_structural()]
    print("Anti-circularity check — engine/scenario code vs fixture oracle fields")
    print("  engine/scenario modules : %s" % ", ".join(ENGINE_MODULES))
    print("  oracle-side modules     : %s" % ", ".join(ORACLE_MODULES))
    print("  boundary module         : %s" % BOUNDARY_MODULE)
    print()
    for r in results:
        print("  %-14s %s" % (r["check"], "PASS" if r["passed"] else "FAIL"))
        if r["check"] == "A-textual":
            print("      oracle field names in engine CODE : %d" % len(r["code_hits"]))
            print("      mentions in comments/docstrings   : %d (documentation only)"
                  % r["doc_mentions"])
            for h in r["code_hits"][:10]:
                print("      VIOLATION %s:%d  %s" % (h["module"], h["line"], h["text"]))
        elif r["check"] == "B-imports":
            print("      oracle-side imports in engine     : %d" % len(r["violations"]))
            for v in r["violations"][:10]:
                print("      VIOLATION %s:%d imports %s"
                      % (v["module"], v["line"], v["imports"]))
        else:
            print("      Stimulus fields                   : %s"
                  % ", ".join(r["stimulus_fields"]))
            print("      oracle fields leaked into it      : %d"
                  % len(r["oracle_fields_leaked"]))
    ok = all(r["passed"] for r in results)
    print("\nANTI-CIRCULARITY %s" % ("PASS — the engine has no path to any expected result"
                                     if ok else "FAIL"))
    out_dir = os.path.join(HERE, "out")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "anticircularity.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump({"passed": ok, "checks": results}, fh, indent=2,
                  sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
