# 31B — Reproduction Notes

The verifier bundle includes the exact independent probe scripts and raw JSON outputs used for the controlling review. They expect a copy of the reviewed `poc/stub` package and Python 3. The deterministic race scripts use barriers to align requests at the vulnerable check/use boundaries; those barriers alter scheduling only and do not bypass the route or authority checks being evaluated.

Primary evidence scripts:

- `http_race_probes.py` — concurrent review-case creation over live HTTP.
- `http_authority_races.py` — concurrent resume-token and capability spend over live HTTP.
- `http_revoke_race.py` — owner revoke versus in-flight delivery.
- `more_race_probes.py` — registration and POC-3 run-declaration races.
- `security_probes.py` — evidence-ordering and transition-boundary fault injection.
- `stage_precise_probe.py` — stage-attempt mutation after capture failure.
- `capture_atomicity_probe.py` — capture publication failure and quota leakage.
- `quota_enforcement_probe.py` — route-policy entity-quota enforcement.
- `control_probes.py` — positive controls for `Disclose` and the A.4 amendment.

The 50-thread token stress probe was corroborating only and is not used as the controlling race evidence because connection saturation prevented all threads from returning. The deterministic two-request barrier probe is the controlling evidence.
