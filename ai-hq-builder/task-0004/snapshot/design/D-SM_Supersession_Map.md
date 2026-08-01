# D-SM — Authoritative Supersession Map (P2S-02)

One row per superseded normative statement. Superseded text survives only inside blocks carrying an explicit `SUPERSEDED` marker; the authoritative rule is the named replacement. `design/traces/check_supersessions.py` fails if a superseded phrase/parameter appears outside a marked block.

| # | Artifact + location | Superseded statement | Authoritative replacement |
| --- | --- | --- | --- |
| 1 | D-B4 §4 scenario 4 | Stale-policy race "closed by flag-for-later-review" | D-B4 §2.3 linearization contract (P2G-05 + P2S-05) |
| 2 | D-B4 §2.3 (earlier wording) | "authorization that lost its epoch cannot produce the side effect" | §2.3 linearization contract — provable claims only (policy-first blocks; in-flight bounded by lease) |
| 3 | D-B5 §2 invariants | Kill "independent by construction" | D-KR §1 designed mechanisms |
| 4 | D-B5 §3 F5 | "revocation accepts weaker authentication, by design" | D-KR §1.3 suspend-easy / re-enable-hard with DoS bounds |
| 5 | D-B6 §4 table | Min sample 100; rolling 14-day window | P2G-09 section: n_min 149; 28-day mature window (machine-witnessed) |
| 6 | D-B8 §5 layer 3 | Global "authority domain class, then explicit priority" winner-take-all | D-B8 P2G-10 section: per-output composition; priority only for same-domain same-output |
| 7 | D-B11 A14 row | Due run "emits its own failure notice" | D-KR P2S-04: watchdog computes deadlines from schedule definitions it holds |
| 8 | D-KR §3 | Watchdog outage "surfaced at next owner contact" residual acceptance; per-occurrence ExpectedRun dependency | D-KR P2S-03 two-leg dead-man; P2S-04 watchdog-owned schedules |
| 9 | D-B14 §2/§6 | `JSONB` product notation; "100% coverage" claim | P2G-12 section: conceptual `document` type; row-audited coverage table |
| 10 | D-B2 P2G-13 §4 (earlier wording) | Default filing/summary/placement eligibility for untrusted claims | P2S-07 corrected rule: no proposal class without an explicit approved eligibility policy |
| 11 | D-B1 (prior revision) | Scored comparison 18/17/13 + near-tie deferral; later "machine-verified" stage-1 claims resting on the circular comparator | D-B1 two-stage rebuild; stage-1 machine claims suspended pending the P2S-01 behavioral simulator |
| 12 | D-B12 completion update | "machine-executed (corpus)" labels resting on the circular comparator | Pending relabel from P2S-01 simulator outputs; D-B12 P2S note |
| 13 | D-B9 P2S-06 tie-break (earlier list) | Store-priority list omitting the control-service journal (kill-plane fold position undeclared) | D-B9 P2S-06 amended list (2026-07-30): `control-journal` first, ahead of policy — kill-plane supremacy per IDN-03/D-KR §1.2; gap surfaced by TASK-0003 R1 review |
