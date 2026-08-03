#!/usr/bin/env python3
"""Cost & capacity model for the POC round (`05_` §3 frame, corrected).

`05_` §3 states the billing arithmetic in prose: Zapier meters per TASK so cost
scales with volume x steps; n8n meters per EXECUTION so cost scales with volume
and is step-insensitive, plus a self-hosting line. This turns that prose into
arithmetic that can be checked, and adds the line no vendor invoice shows — the
owner-attention hours `05_` §3 names explicitly.

EVERY DEFAULT BELOW IS AN UNMEASURED WORKING ESTIMATE carried verbatim from
`05_` §3 and labelled as such in the output. The packet requires V1..V5 to be
corrected with MEASURED values; this program computes, it does not measure.
Feed it `--measured <file.json>` once the owner session produces real numbers.

Usage:
  cost_model.py                        # frame with 05_ §3 unmeasured estimates
  cost_model.py --measured vals.json   # same arithmetic over measured inputs
  cost_model.py --self-test            # the arithmetic proves itself
Exit: 0 ok / 1 self-test failure / 2 usage error
"""
from __future__ import annotations

import json
import sys

BUSINESS_DAYS_PER_MONTH = 21  # stated, not assumed silently

# `05_` §3, verbatim ranges. Unmeasured.
FRAME = {
    "V1_calls_per_day": {"low": 20, "high": 60, "measured": None,
                         "source": "05_ §3 working estimate — POC-1 measures"},
    "V2_emails_per_day": {"low": 50, "high": 150, "measured": None,
                          "source": "05_ §3 working estimate — POC-2 measures"},
    "V3_consequential_actions_per_day": {"low": 20, "high": 20, "measured": None,
                                         "source": "05_ §3 — accepted 20/day cap; DE-R8 growth to 5000/day hard max"},
    "V4_scheduled_runs_per_day": {"low": 5, "high": 20, "measured": None,
                                  "source": "05_ §3 working estimate — POC-3 measures"},
    "V5_avg_steps_per_workflow": {"low": 5, "high": 15, "measured": None,
                                  "source": "05_ §3 working estimate — drives the Zapier-vs-n8n crossover"},
}

# Rate inputs. These are NOT prices — they are named slots the session fills from
# the vendor's own pricing page at POC time (`05_` §3: "revalidated at POC time").
RATES = {
    "zapier_price_per_task": {"value": None, "unit": "currency/task", "status": "NOT MEASURED"},
    "zapier_tasks_per_mcp_call": {"value": 2, "unit": "tasks", "status": "FROM 00_ §17 SNAPSHOT — revalidate"},
    "n8n_price_per_execution": {"value": None, "unit": "currency/execution", "status": "NOT MEASURED"},
    "n8n_self_host_monthly": {"value": None, "unit": "currency/month",
                              "status": "NOT MEASURED — hardware amortisation + electricity"},
    "owner_hourly_value": {"value": None, "unit": "currency/hour", "status": "OWNER INPUT"},
    "owner_maintenance_hours_zapier": {"value": None, "unit": "hours/month", "status": "NOT MEASURED"},
    "owner_maintenance_hours_n8n": {"value": None, "unit": "hours/month", "status": "NOT MEASURED"},
    "model_api_monthly": {"value": None, "unit": "currency/month",
                          "status": "NOT MEASURED — model costs outside the platform"},
}


def point(v: dict, which: str = "high") -> float:
    """Pick a scalar for a variable: measured if present, else the named bound."""
    if v.get("measured") is not None:
        return float(v["measured"])
    return float(v[which])


def monthly_runs(vs: dict, which: str) -> dict:
    """Workflow RUNS per month, per POC, from the volume variables."""
    d = BUSINESS_DAYS_PER_MONTH
    return {
        "POC1_call_review": point(vs["V1_calls_per_day"], which) * d,
        "POC2_email_triage": point(vs["V2_emails_per_day"], which) * d,
        "POC3_durable_overnight": point(vs["V4_scheduled_runs_per_day"], which) * d,
    }


def compute(vs: dict, rates: dict, which: str = "high", multiplier: float = 1.0) -> dict:
    """The two billing models, side by side, over the same run counts.

    Zapier:  billed_units = runs x steps          (every step meters)
    n8n:     billed_units = runs                  (one run = one execution)
    """
    runs = {k: v * multiplier for k, v in monthly_runs(vs, which).items()}
    steps = point(vs["V5_avg_steps_per_workflow"], which)
    total_runs = sum(runs.values())

    zapier_units = total_runs * steps
    n8n_units = total_runs

    def money(units, rate_key, extra=0.0):
        rate = rates[rate_key]["value"]
        if rate is None:
            return None
        return units * float(rate) + extra

    zap_platform = money(zapier_units, "zapier_price_per_task")
    n8n_host = rates["n8n_self_host_monthly"]["value"]
    n8n_platform = money(n8n_units, "n8n_price_per_execution",
                         float(n8n_host) if n8n_host is not None else 0.0)

    def attention(hours_key):
        h, v = rates[hours_key]["value"], rates["owner_hourly_value"]["value"]
        return None if h is None or v is None else float(h) * float(v)

    model_cost = rates["model_api_monthly"]["value"]
    model_cost = float(model_cost) if model_cost is not None else None

    def total(platform, att):
        parts = [platform, att, model_cost]
        return None if any(p is None for p in parts) else sum(parts)

    zap_att, n8n_att = attention("owner_maintenance_hours_zapier"), attention("owner_maintenance_hours_n8n")
    return {
        "scale": "%gx" % multiplier,
        "bound_used": which,
        "runs_per_month": runs,
        "total_runs_per_month": total_runs,
        "avg_steps_per_run": steps,
        "zapier": {
            "billing_unit": "task (every step meters; an MCP tool call = %s tasks)"
                            % rates["zapier_tasks_per_mcp_call"]["value"],
            "billed_units_per_month": zapier_units,
            "platform_cost": zap_platform,
            "owner_attention_cost": zap_att,
            "model_api_cost": model_cost,
            "total_monthly": total(zap_platform, zap_att),
        },
        "n8n": {
            "billing_unit": "execution (one run = one execution regardless of steps)",
            "billed_units_per_month": n8n_units,
            "platform_plus_hosting_cost": n8n_platform,
            "owner_attention_cost": n8n_att,
            "model_api_cost": model_cost,
            "total_monthly": total(n8n_platform, n8n_att),
        },
        "step_sensitivity_ratio": zapier_units / n8n_units if n8n_units else None,
    }


def crossover_steps(rates: dict) -> float | None:
    """Steps per run at which the two platform lines meet, hosting included.

    zapier_rate * runs * steps  ==  n8n_rate * runs + host
    Independent of run count only when host == 0; otherwise reported per run.
    """
    z, n = rates["zapier_price_per_task"]["value"], rates["n8n_price_per_execution"]["value"]
    if z in (None, 0) or n is None:
        return None
    return float(n) / float(z)


def self_test() -> int:
    """The arithmetic proves itself on inputs whose answers are known by hand."""
    vs = {k: dict(v) for k, v in FRAME.items()}
    for k, m in (("V1_calls_per_day", 10), ("V2_emails_per_day", 20),
                 ("V4_scheduled_runs_per_day", 1), ("V5_avg_steps_per_workflow", 4)):
        vs[k]["measured"] = m
    rates = {k: dict(v) for k, v in RATES.items()}
    rates["zapier_price_per_task"]["value"] = 0.01
    rates["n8n_price_per_execution"]["value"] = 0.05
    rates["n8n_self_host_monthly"]["value"] = 100.0
    rates["owner_hourly_value"]["value"] = 50.0
    rates["owner_maintenance_hours_zapier"]["value"] = 1.0
    rates["owner_maintenance_hours_n8n"]["value"] = 4.0
    rates["model_api_monthly"]["value"] = 25.0

    r = compute(vs, rates, "high", 1.0)
    d = BUSINESS_DAYS_PER_MONTH
    exp_runs = (10 + 20 + 1) * d                      # 31 * 21 = 651
    checks = [
        ("total runs", r["total_runs_per_month"], exp_runs),
        ("zapier units = runs x steps", r["zapier"]["billed_units_per_month"], exp_runs * 4),
        ("n8n units = runs", r["n8n"]["billed_units_per_month"], exp_runs),
        ("zapier platform", r["zapier"]["platform_cost"], exp_runs * 4 * 0.01),
        ("n8n platform + host", r["n8n"]["platform_plus_hosting_cost"], exp_runs * 0.05 + 100.0),
        ("zapier attention", r["zapier"]["owner_attention_cost"], 50.0),
        ("n8n attention", r["n8n"]["owner_attention_cost"], 200.0),
        ("zapier total", r["zapier"]["total_monthly"], exp_runs * 4 * 0.01 + 50.0 + 25.0),
        ("n8n total", r["n8n"]["total_monthly"], exp_runs * 0.05 + 100.0 + 200.0 + 25.0),
        ("step sensitivity", r["step_sensitivity_ratio"], 4.0),
        ("crossover steps", crossover_steps(rates), 5.0),
    ]
    r10 = compute(vs, rates, "high", 10.0)
    checks.append(("10x scales runs linearly", r10["total_runs_per_month"], exp_runs * 10))
    checks.append(("10x scales zapier units linearly",
                   r10["zapier"]["billed_units_per_month"], exp_runs * 4 * 10))
    # Unmeasured rates must yield None, never a silent zero.
    bare = compute(vs, {k: dict(v) for k, v in RATES.items()}, "high", 1.0)
    checks.append(("unpriced -> None, not 0", bare["zapier"]["total_monthly"], None))

    rows, passed = [], 0
    for label, got, want in checks:
        ok = (got is None and want is None) or (
            got is not None and want is not None and abs(float(got) - float(want)) < 1e-9)
        passed += ok
        rows.append({"check": label, "got": got, "expected": want, "ok": ok})
        sys.stderr.write("  [%s] %s: got %s, expected %s\n"
                         % ("ok  " if ok else "FAIL", label, got, want))
    print(json.dumps({"check": "cost-model self-test", "cases": rows,
                      "passed": passed, "total": len(checks)}, indent=2))
    sys.stderr.write("COST MODEL SELF-TEST %s — %d/%d\n"
                     % ("PASS" if passed == len(checks) else "FAIL", passed, len(checks)))
    return 0 if passed == len(checks) else 1


def main(argv):
    if argv and argv[0] == "--self-test":
        return self_test()
    vs = {k: dict(v) for k, v in FRAME.items()}
    rates = {k: dict(v) for k, v in RATES.items()}
    if argv:
        if len(argv) != 2 or argv[0] != "--measured":
            sys.stderr.write(__doc__)
            return 2
        with open(argv[1], encoding="utf-8") as fh:
            supplied = json.load(fh)
        for k, v in (supplied.get("variables") or {}).items():
            if k in vs:
                vs[k]["measured"] = v
        for k, v in (supplied.get("rates") or {}).items():
            if k in rates:
                rates[k]["value"] = v
                rates[k]["status"] = "MEASURED"

    any_measured = any(v.get("measured") is not None for v in vs.values())
    out = {
        "model": "05_ §3 cost & capacity frame, arithmetic form",
        "business_days_per_month": BUSINESS_DAYS_PER_MONTH,
        "variables": vs,
        "rates": rates,
        "measurement_status": "MEASURED INPUTS PRESENT" if any_measured
                              else "NO MEASURED INPUT — every number below is derived from "
                                   "05_ §3 working estimates and is NOT a measurement",
        "scenarios": [compute(vs, rates, "low", 1.0),
                      compute(vs, rates, "high", 1.0),
                      compute(vs, rates, "high", 3.0),
                      compute(vs, rates, "high", 10.0)],
        "crossover_steps_per_run": crossover_steps(rates),
        "crossover_note": "steps/run at which zapier task-billing equals n8n "
                          "execution-billing, hosting excluded; None until both "
                          "rates are supplied",
    }
    print(json.dumps(out, indent=2))
    sys.stderr.write("COST MODEL EMITTED — %s\n" % out["measurement_status"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
