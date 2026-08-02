# D-KR — Independent Kill/Revoke Control Plane and Resilience Mechanisms (P2G-06)

**Serves:** B5's correction — IDN-03, RES-01, RES-02, RES-03, DE-R3's kill clause. **Evidence classes used:** structural/schema validation + deterministic design contracts; runtime drills are explicitly `design-complete / build-verification pending` with their later gate named. **Replaces** D-B5's withdrawn "independent by construction" assertion with the actual design.

## 1. Kill/revoke control plane — designed separately from the engine data path

### 1.1 Placement and transport

A **minimal external control service** deployed independently of: the engine host, Discord, and any single model provider. Contract (product selection at build): reachable by the owner through **two independent paths** (authenticated web endpoint + a non-internet-dependent fallback channel selected at activation); holds its **own credential store** (no shared secrets with the engine); no inbound dependency on engine liveness. This same service hosts the RES-02 watchdog (§3) — one deliberately shared, deliberately tiny external footprint.

### 1.2 Exact authorities revoked (enumerated)

| # | Authority | Enforcement mechanism | Works when engine is dead? |
| --- | --- | --- | --- |
| 1 | Executor/provider credentials (model APIs, integration tokens) | Control service commands the secret manager to disable/rotate — **provider-side hard stop**, no executor cooperation needed | **Yes** |
| 2 | Engine write authority | Kill flag in the policy plane; every executor's P2G-05 pre-execution check reads kill-flag + epoch — one seam, two signals; flag set ⇒ every pending authorization fails its CAS | Yes (and #1 backstops if the engine ignores it) |
| 3 | Delegation grants | Delegation records carry `revocable_by=kill`; suspension event voids active grants | Yes via #1 for external delegates |
| 4 | Outbound channels | Channel tokens live in the secret manager ⇒ #1 mechanism | **Yes** |
| 5 | Scheduler | Kill flag suspends dispatch; ExpectedRun deadlines keep accruing so the watchdog documents the suspension window | Yes |

### 1.3 Authentication, recovery, and abuse control (replacing the withdrawn weaker-auth rule)

- **SUSPEND (fail-safe direction):** any single pre-registered owner factor may trigger suspension — because a wrongful suspension has bounded, recoverable harm. Rate-limited (3 suspension commands/24 h per factor), every use receipted and owner-notified on the independent channel.
- **RE-ENABLE (fail-secure direction):** requires full IDN-02 step-up + a declared cooldown + the §1.5 sequence. A weak factor can never re-enable, never read data, never change policy — so the suspend path cannot be escalated into control.
- **DoS analysis:** the worst an attacker with one stolen weak factor achieves is bounded downtime (rate-limited suspends), never data access or authority; the owner-notification-on-use makes repeated abuse visible; factor revocation is itself a control-service function. Documented **credential recovery**: pre-registered recovery factors + a printed recovery procedure stored offline (runbook §4); recovery of control-service access follows the same fail-secure re-enable bar.
- **Emergency read-only mode** (IDN-03's third clause): suspension leaves the RES-03 read/export surface (§4) available.

### 1.4 Receipts and the log

The control service journals every command in its own append-only store (independent of D5). Receipts mirror into the engine event log on reconnection (D-B5 F6 reconciliation, §5 step 2). Kill efficacy never depends on the engine log being writable.

### 1.5 Controlled re-enable sequence

Owner step-up → integrity verification (D-B5 §5 recovery reconciliation completes; backup/restore state green per §2) → staged re-activation: read surfaces → internal T0/T1 → T2 last, each stage receipted. No single command re-arms external action.

### 1.6 Tests

Design-stage (deterministic simulation over the contract): kill during each D-B5 F-row (C8 column now backed by §1.2 mechanisms, not assertion); kill with engine host fully down (path #1 — provider-side disable — succeeds with the engine unreachable); weak-factor abuse (rate limit + suspend-only bound holds; notification fires); re-enable without step-up refused; receipts present in the control journal for every command. **Build-verification pending:** live kill drill against real provider credentials, two-path reachability test, recovery-procedure walkthrough — gate: pre-activation security gate (SEC-01).

## 2. RES-01 — Backup and verified-restore contract

Every authoritative store (intake log, canonical state, policy plane, event log, schedule/ExpectedRun store, queue state, identity/config, control-service journal) has: automated versioned backups on a per-store schedule; retention per DAT-01 class; and **scheduled restore drills** — restore into an isolated environment, verify checksums, run the fold/projection smoke replay (P2G-02 comparator) against the restored set, emit a `RestoreDrillEvent` with pass/fail feeding AUD-03. **Backup success without restore proof explicitly does not satisfy RES-01** (the requirement's own words — now a scheduled, evidenced drill, not an aspiration). Drill cadence: owner-tunable, default monthly per store, staggered. Build-verification pending: first live drill at activation gate.

## 3. RES-02 — Independent watchdog

Hosted on the §1.1 control service (outside host and Discord). Two monitored signals: (a) **coordinator heartbeats** — engine emits at MEM-05 heartbeat intervals; missed threshold (default 2× interval) ⇒ owner notification on the independent channel; (b) **schedule deadlines — computed by the watchdog itself from the authoritative schedule definitions it holds (P2S-04 section below, authoritative)**; a computed deadline passing without a matching `RunStarted` receipt ⇒ missed-run notice. *(SUPERSEDED per P2S-02/P2S-04: the earlier per-occurrence "writes ExpectedRun at scheduling time" dependency — a scheduler dying before registering the next occurrence left no record to inspect; ExpectedRun records remain as the corroborating horizon signal only.)* "Silence must always mean safe": the watchdog alarms on silence; **its own silence is covered by the P2S-03 two-leg dead-man contract below (phone-side alarm + heartbeat-fresh lease expiry)**. *(SUPERSEDED per P2S-02/P2S-03: the earlier "externally observable page + surfaced at next owner contact" residual-acceptance — a disclosed silent window does not satisfy RES-02 and is withdrawn.)*

## 4. RES-03 — Degraded read access, export, and recovery runbook

- **Read surface:** periodic snapshot export (topics, checkpoints, queue summaries, current policy versions) to portable files in owner-accessible storage, refreshed on checkpoint cadence; readable with no engine dependency; sensitive fields masked per DAT-01 class.
- **Export:** on-demand full export per store (backward-readable format per SCH-01), owner-triggered from the control service.
- **Recovery runbook** (design deliverable, kept with the snapshots): assess (watchdog/journal evidence) → suspend if not already → restore stores from RES-01 backups (order: policy plane → canonical → events → queues) → run D-B5 §5 reconciliation → verify via restore-drill checks → staged re-enable per §1.5. Maintained under version control; drill-tested with RES-01 cadence.

## 5. Ledger effect

IDN-03, RES-01, RES-02, RES-03 → mechanisms now designed (this artifact); D-B5's C8 column re-grounded on §1.2. Runtime drills carried as `design-complete / build-verification pending` rows in §7 of the plan's gate table. Falsifier: any failure mode where both kill paths (#1 provider-side and #2 flag) are simultaneously unavailable while external action remains possible ⇒ design defect, gate blocker.

## P2S-03 correction — the two-leg dead-man contract (common-mode failure closed)

**The §3 residual-risk acceptance is withdrawn** — RES-02's silence-means-safe is not satisfiable by a disclosed gap. The corrected liveness chain has two independent legs plus a fail-closed authority bound:

1. **Phone-side heartbeat alarm (second leg, no shared infrastructure):** the owner's phone runs a local dead-man alarm — it expects a signed heartbeat from the control service every ≤ 5 minutes and **alarms locally on the device** when heartbeats stop for > 10 minutes. Detection lives on hardware the owner already carries, sharing nothing with the engine host or the control service. Engine dead → control service alarms (leg 1, §3). Control service dead (or both dead) → the phone alarms (leg 2). No silent combination remains: any total-silence state is itself the alarm condition.
2. **Heartbeat-fresh executor leases (fail-closed authority):** every executor authorization lease (D-B4 §2.3) is valid only while the executor holds a control-plane heartbeat ≤ 5 minutes old. Control service unreachable ⇒ no fresh heartbeats ⇒ no new leases, and in-flight leases expire on their ≤ 60 s bound ⇒ **all external action stops within a declared ≤ 6-minute bound of control-plane loss** — engine alive or not, kill command sent or not. Automation authority cannot outlive the infrastructure that could revoke it.
3. **Explicit chain:** liveness = engine→control-service heartbeats (leg 1) + control-service→phone heartbeats (leg 2); notification = control-service alerts (leg 1) and local phone alarm (leg 2); expiry = 5-min heartbeat / 60-s lease / 6-min total stop bound; provider-side revocation = §1.2 row 1, independent of both legs; degraded reads = §4 snapshots, available throughout.
4. **Tests (simulator, P2S-03 set):** engine-only failure (leg-1 notice; leases keep external action stopped per D-B5 C6 anyway); control-service-only failure (leg-2 phone alarm + lease expiry stops external action ≤ 6 min); simultaneous engine + control-service failure (leg-2 alarm + no live authority anywhere — the formerly silent window now both alarms and fails closed); phone-offline edge (leg 1 unaffected; on reconnect the phone alarms on the stale heartbeat backlog — late, bounded, disclosed as the one residual timing gap, which suspends nothing since leases already expired).

## P2S-04 correction — recurring-schedule liveness (watchdog owns the schedule)

**The ExpectedRun-at-scheduling-time model is superseded for liveness purposes:** it could not detect a scheduler that dies before registering the next occurrence. Corrected:

1. **The watchdog holds the authoritative schedule definitions.** Schedule creation/change is a governed event (SCH-01 versioned) that registers the recurrence spec with the D-KR watchdog itself; the watchdog **computes expected deadlines from the spec** — it does not depend on the scheduler announcing each occurrence. A dead scheduler changes nothing about the watchdog's expectations; the next computed deadline simply passes unanswered and alarms.
2. **Rolling ExpectedRun horizon (corroboration, not the primary):** the scheduler still materializes future-dated ExpectedRun records (≥ 7 days ahead); the watchdog alarms on **horizon exhaustion** (the scheduler stopped extending) as an early-warning signal that fires before any run is even due.
3. **Tests (simulator, P2S-04 set):** scheduler death immediately after completing a run and before registering the next occurrence — the watchdog's spec-computed deadline still fires ⇒ detected; horizon exhaustion — the horizon shrinks below threshold with the scheduler silent ⇒ early alarm; schedule *change* racing a computed deadline — the governed change event re-registers the spec atomically with the watchdog, no orphaned expectation.
