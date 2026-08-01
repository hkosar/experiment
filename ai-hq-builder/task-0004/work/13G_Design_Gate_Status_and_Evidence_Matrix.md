# 13G — Design Gate Status and Evidence Matrix (rebuilt from exact accepted text per P2G-01)

**Status enum:** `Not started / Complete / Binding invariant / Incomplete / Blocked / Build-gate deferred / Deliberately deferred / N/A`. **Final-gate rule:** every required row (13M treatment Binding or Design subject, and every proposed DE-R row) must be `Complete`, `Binding invariant`, plan-permitted `Build-gate deferred` (citing §7), or `Deliberately deferred` with recorded rationale; `Not started`, `Incomplete`, and `Blocked` block the gate. `13V_` enforces structure/order/text-hash/referential integrity and the final-gate rule under `--final-gate`; **it does not and cannot judge semantic sufficiency — that is the human verifier's role.** Current state: correction cycle after the design-gate FAIL (`17_`, trail 88) — statuses below are the honest current audit, including every row the corrections have not yet reached.

| ID | Text hash | Gate status | Actual result | Remaining dependency |
| --- | --- | --- | --- | --- |
| ACT-01 | `0153e101d5f4` | Complete | aik + attempt_epoch + preconditions + authorization-epoch fields in schema (D-B14 P2G-12); halt + receipt linkage traced (D-B3 T5, D-B9); pre-execution re-check designed (D-B4 §2.3) | — |
| APP-01 | `47473bfc4d60` | Complete | Structural invariant holds by construction; evidence class: structural, so labeled | — |
| APP-02 | `2283a2bf14c9` | Binding invariant | Process invariant held throughout; no new engine design required | — |
| APP-03 | `060f90a7f4dd` | Build-gate deferred | No Builder task issued during design (plan §7) | — |
| APP-04 | `5d339d777ffe` | Incomplete | Store matrix + WorkerSession designed; behavioral multi-store fold EXECUTED (TASK-0003 simulator, trail 98: 81/81 combinations order-invariant across 6 seeded causal-preserving permutations; receipt ownership enforced at fold and post-hoc; `design/traces/behavioral/out/results.json`, `p2s06_shuffle_invariance.json`) | P2T-02: fold must fail closed on a missing causal basis |
| APP-05 | `374d3729b6be` | Build-gate deferred | No Builder task issued during design (plan §7) | — |
| APP-06 | `824c48898734` | Build-gate deferred | No Builder task issued during design (plan §7) | — |
| APP-07 | `12ba73db888a` | Build-gate deferred | No Builder task issued during design (plan §7) | — |
| APP-08 | `a98e4063ef89` | Build-gate deferred | No Builder task issued during design (plan §7) | — |
| APP-09 | `c0725b6e2fb8` | Build-gate deferred | No Builder task issued during design (plan §7) | — |
| APP-10 | `ef88fd7b3de0` | Build-gate deferred | No Builder task issued during design (plan §7) | — |
| ATT-01 | `1296bb515bbd` | Complete | P2G-07 corrected: verified qualifying danger in every ATT-01 category interrupts through quiet hours; ambiguity fallback separated; ten boundary traces (verified + ambiguous × five categories) recorded — D-B7 §3 | — |
| ATT-02 | `b7b6cdb7bd82` | Complete | Band semantics + non-modal rendering designed and instantiated from fixtures | — |
| ATT-03 | `d67b856afc6f` | Complete | Explicit class→band mappings added (completions → hub update; safe retries and first overdue → Briefing; later steps → aging ladder) — D-B7 §3 | — |
| AUD-01 | `8349d75dfe9c` | N/A | Historical; no design-phase obligation | — |
| AUD-02 | `52d449894523` | N/A | Historical; no design-phase obligation | — |
| AUD-03 | `34f81bae5d37` | Complete | Rubric object with dimensions/weights/denominators/missing-data treatment; unknown ≠ zero; no self-attestation of independent controls; one-screen output fields; complete envelope + watchdog liveness (D-B11 small-item + P2G-08 sections) | — |
| AUT-01 | `248a8958bca5` | Complete | Class/scope-keyed policy objects carry approval requirements; changes via PolicyVersionEvents | — |
| AUT-02 | `5a0b24a0f9df` | Complete | Evidence-driven expansion now mathematically reachable and witnessed; no-silent-adoption held by PolicyVersionEvents + LRN-10 rule | — |
| AUT-03 | `c5a3dff3cc7e` | Binding invariant | Satisfied by accepted build/verification requirements; engine adds rollback pointers + staged activation | — |
| AUT-04 | `650c6cf4293d` | Complete | Card standard carries exactly these fields; 7/7 fixture instantiations | — |
| AUT-05 | `e0e449a8f4d8` | Complete | Explicit in-subtree-auto vs cross-cutting-escalate disposition rule with fixture test case (D-B6 small-item section) | — |
| AUT-06 | `175b2eb5ce36` | Complete | Exceptions only where legal, floors immune, friction on the card — traces pass | — |
| AUT-07 | `256ca6fdf38f` | Complete | AssignmentRecord linked to CloseoutPackage with completion mode — delegation tracked to closeout (D-B9 small-item section) | — |
| AUT-08 | `562ddffc9e0b` | Complete | Scope-key vocabulary fixed: person/assignment_type/sensitivity_class/consequence_class; unkeyed delegation policies rejected at authoring (D-B6 + D-B8 §2) | — |
| AUT-09 | `1ad3d41c48af` | Complete | Three-mode completion enum (verified / owner-accepted / needs-review) on closeout linkage + schema field (D-B9, D-B14) | — |
| AUT-10 | `5fe4b37885e9` | Complete | verification-read-only and employee-facing-followup as separate action classes; ceiling machinery enforces owner control absent a scoped policy (D-B6 small-item section) | — |
| AUT-11 | `d991e2952761` | Complete | Non-destructive reconciliation designed and traced; history never erased | — |
| AUT-12 | `d0e79a5bc9db` | Complete | Three-stage ladder mapped to policy objects with governed stage advancement; DE-R8 evidence machinery drives it; statistics reachable (P2G-09) | — |
| BUS-01 | `7d2768cb7d8a` | Binding invariant | Architectural posture; no engine mechanism required | — |
| BUS-02 | `33f66972063f` | Deliberately deferred | Engine consumes registry events (BUS-10 row); Data HQ subsystem design is outside the Decision Engine surface | Assign to a future change plan under its own topic; plan §12 defers integration detail |
| BUS-03 | `58cda6a4bb06` | Deliberately deferred | Business-workflow subsystem; engine ingests its events and routes its review items | Future business-workflow change plan; not Decision Engine surface |
| BUS-04 | `72dd4b9d0db6` | Deliberately deferred | Plan §12 explicitly defers MCP write boundaries; engine-side ceiling invariant noted | MCP boundary design at its deferred gate |
| BUS-05 | `ca66977d027b` | Complete | Engine-side separation + one-frame presentation designed and traced; mailroom internals deferred per plan §12 | — |
| BUS-06 | `beabf7c10352` | Binding invariant | Organizational posture; engine placement honors hub authority via evidence boundary | — |
| BUS-07 | `955bfb5fd482` | Binding invariant | Held by PLAT-02 design (no authority in interface layers) | — |
| BUS-08 | `f62e0c24beba` | Complete | Exactly the designed evidence-authority split; check 4 passes | — |
| BUS-09 | `23fc9e9aa626` | Complete | Projections declared non-authoritative and rebuildable | — |
| BUS-10 | `e08b5b9ff2d1` | Complete | connections_registry record with the full accepted field set, no-secrets constraint, freshness events to Data HQ health + AUD-03, RES-02 non-replacement noted (D-B14 P2G-12) | — |
| CAP-01 | `23373d33d001` | Complete | Declared and reported for this stage; recurs per activation stage | — |
| CAP-02 | `2d585990e127` | Complete | This stage's record: all caps within bounds, CONTINUE; recurs per stage | — |
| CAP-03 | `2d980837df71` | Complete | cost_evidence_records with quantity/unit/currency/amount-class/provider/account/coverage-window/missing-sources/provenance/event-linkage; no-content-ingestion constraint (D-B14 P2G-12); live provider collection remains the declared build-gate obligation | — |
| CAP-04 | `e2db25e8119c` | Complete | Flag-never-disable behavior + protected-class exemption traced (D-B9/D-B10/D-B11); CAP-03 evidence fields now complete (D-B14) making the comparison executable at build | — |
| COR-01 | `539ce4991e27` | Complete | All seven operations enumerated as typed history-preserving CorrectionEvents behind the one-tap gesture; calibration feed as weak evidence (D-B9 small-item section) | — |
| DAT-01 | `5b44ae146ea4` | Complete | Per-class lifecycle policy objects (collection/storage/retention/model-access/rendering/redaction/preview/export/deletion) with named enforcement points (D-B2 P2G-13 §6, D-B14 P2G-12) | — |
| DAT-02 | `144d8d0a58b6` | Complete | Masking/tap-through/preview-stricter designed and instantiated | — |
| DEC-01 | `da765e2536a9` | Complete | Process fact: discovery ran as parent topic; hypothesis carried through six checks | — |
| DEC-02 | `88cac0a1b77d` | Complete | Falsifier contract (status/statement/evidence-refs/review-trigger/rationale/last-evaluated) on consequential decision records through taxonomy, schema, replay basis, and card tap-through; positive + unknown cases simulated (D-B9 P2G-03, D-B13, D-B14) | — |
| EX-01 | `a14ecc9e8c94` | Complete | Pre-placement capture is the designed Boundary 1; no-case/no-ID paths traced (corrected citation) | — |
| EX-02 | `56f98f57c567` | Complete | Desk content contract fixed: recent context / recent events / suggested next / full summary path as named projections per partition; rendering deferred per plan §12 (D-B13 addition) | — |
| EX-03 | `b028987aee56` | Complete | Designed and traced | — |
| EX-04 | `9a153109e947` | Binding invariant | Configuration posture; no engine mechanism | — |
| EX-05 | `dfc93d8ac640` | Binding invariant | Held by architecture (projections + no interface authority); UI implementation deferred per plan §12 | — |
| EX-06 | `e60da966cf3a` | Binding invariant | Same basis as EX-05; render implementation deferred | — |
| EX-07 | `195e28ede76d` | Complete | Cards render recorded state fields, not narrative | — |
| EX-08 | `dddc679b9ad4` | Complete | Card standard encodes it; calibrated by trail-77 precedent | — |
| EX-09 | `9ac21a874240` | Deliberately deferred | Presentation detail of the Discord surface | Plan §12 defers Discord implementation |
| EX-10 | `a1603c29ac52` | Deliberately deferred | Relationship links are recorded by design; navigation rendering deferred | Plan §12 Discord implementation |
| EX-11 | `b8dbe6c3fe7e` | Deliberately deferred | Semantic recall is a memory-provider capability | ADR-021 provider gate + plan §12; engine records carry the IDs/links retrieval will use |
| GOV-01 | `ff9c983ce86f` | Complete | Item 0 package built with executed 26-file scan; applies at build | — |
| GOV-02 | `df6a9f470e60` | Binding invariant | Process invariant — being enforced by the verifier in this very cycle | — |
| GOV-03 | `3efcb4ba1548` | Build-gate deferred | Release mechanics execute at the v1.4 release (plan §7) | — |
| HW-01 | `1c2f0a44e3e6` | Deliberately deferred | No design dependency | §19.3 deferral; owner-timed |
| IDN-01 | `7e3ad98a94fc` | Complete | Envelope authority model implements it; owner-origin unknown identity fails closed | — |
| IDN-02 | `a2e0b17cd1a9` | Complete | Per-class step_up_required constraint in the policy constraints[] model, enforced by the executor pre-execution CAS alongside epoch + kill flag; routine classes one-tap (D-B14 IDN-02 note, D-B4 §2.3); step-up is an accepted floor — never an owner option (P2G-14 honored) | — |
| IDN-03 | `7ee720d62e1f` | Complete | Independent kill/revoke control plane designed — external service, two owner paths, provider-side credential disable working with engine dead, suspend-easy/re-enable-hard auth with DoS bounds, receipts, staged re-enable; kill-in-every-F-mode re-grounded on mechanisms (D-KR §1); runtime drills = design-complete / build-verification pending (SEC-01 gate) | — |
| INT-01 | `5cbfc03b1076` | Complete | Card standard meets INT-01; owner-package misuse corrected separately (P2G-14) | — |
| LOG-01 | `2e8d06e62891` | Complete | Every event carries true actor/session/component identity + versions; tool-call/outbound/write/deploy detail fields; full event-kind list typed (D-B14 P2G-12, D-B9) | — |
| LOG-02 | `80e5130a820a` | Complete | Single-logger writer isolation (workers hold no log-write credential) + per-partition hash-chain tamper evidence; log reconstructs sessions via the expanded replay basis; Recent-log projection feeds hub views (D-B14 P2G-12) | — |
| LRN-01 | `eb7c778c6495` | Complete | Typed as authority-less; traced | — |
| LRN-02 | `20f4569b52f2` | Complete | Single governed change path designed; check 2 enforces | — |
| LRN-03 | `1915cb5a7679` | Complete | Scope is a mandatory attribute | — |
| LRN-04 | `1f52a7506105` | Complete | Conflicts surface as owner items; no silent-violation path | — |
| LRN-05 | `a8e5e40bc1d0` | Complete | Lifecycle states (active/inactive/archived/deleted) on all learned objects; deletion never default (D-B14 P2G-12) | — |
| LRN-06 | `cf84ea98f55e` | Complete | Inactivity-review rule (90-day provisional, owner-tunable) raising AUD-03 sweep items; never auto-removed (D-B11 small-item section) | — |
| LRN-07 | `d75e64fa1594` | Complete | Append-only retention; rejections recorded as events | — |
| LRN-08 | `0cb1432f9f6e` | Deliberately deferred | Semantic retrieval is the ADR-021 provider capability; category structure lives in placement records | ADR-021 gate |
| LRN-09 | `d3c26bce527d` | Complete | Behavior rules (≤1 artifact/cycle, smallest-machinery ladder, urgent-work exemption, CAP-01 owner-time measurement) ride in the complete P2G-08 envelope with independent missed-run detection | — |
| LRN-10 | `a1aede1ef1a4` | Complete | Three-verified-occurrence threshold, exclusion list, weak-evidence-only rule in the complete envelope (D-B11 §3 + P2G-08 section) | — |
| MEM-01 | `fa8ac84cc531` | Complete | Store-ownership matrix: every authoritative store has exactly one owner and one recoverable event path (D-B9 P2G-11) | — |
| MEM-02 | `99ba08da4be2` | Complete | Checkpoint record with protected/generated field split in schema; durable resumption via recovery reconciliation (D-B14, D-B5 §5) | — |
| MEM-03 | `a88b515ac2d3` | Complete | WorkerSession + checkpoint + event-log reconciliation keeps the visible topic stable across compaction/replacement (D-B9 small-item, D-B14) | — |
| MEM-04 | `7c84ede584f7` | Deliberately deferred | Provider selection is the ADR-021 gate | ADR-021 |
| MEM-05 | `68a863192e16` | Complete | Five checkpoint refresh triggers as CheckpointEvents (stage transition, decision, work unit, heartbeat, pre-consequential) (D-B9 small-item section) | — |
| MEM-06 | `a9128189af99` | Complete | WorkerSession record (identity/heartbeat/journal/last side effect); replacement reconciliation; divergence raises Needs Review (D-B9, D-B14) | — |
| MEM-07 | `f014b2c07f3f` | Complete | Protected vs generated checkpoint field classes with version retention and audit events (D-B14 P2G-12) | — |
| MEM-08 | `d36f22e7f321` | Complete | Knowledge layer never canonical (store matrix); provenance-required admission; versioned Disputed records into governed resolution; DAT/TRS/PER enforcement points named; provider selection remains ADR-021-gated (D-B9) | — |
| MEM-09 | `c60b7eb742b4` | Deliberately deferred | Structured-interview surface is onboarding-layer design, not the engine; the engine consumes persisted records | Onboarding-surface change plan; previously overclaimed via the plan-§1.4 shorthand — corrected |
| ONB-01 | `c9726f01ce8d` | Deliberately deferred | Onboarding-surface design with a policy-plane touchpoint only | Onboarding-surface change plan; engine keeps grant-once/activate-staged data posture |
| ORG-01 | `f67bfc9e616a` | Complete | Arbitrary-depth typed-role tree: semantic role_type, parent refs, roles-not-slots (D-B14 P2G-12) | — |
| ORG-02 | `7fee3d18a87e` | Complete | hub_capable flag + recorded promotion_rule; tasks default leaves (D-B14 P2G-12) | — |
| ORG-03 | `154cbb2525a6` | Complete | categories[] orthogonal to the WF-03 canonical dimensions (D-B14 P2G-12) | — |
| ORG-04 | `50cd62407c64` | Complete | To-Do/To-Did layered topic+next-action projections, derived and non-authoritative, To-Did preserved by AUT-11 reconciliation (D-B9 small-item section) | — |
| ORG-05 | `7e057a2ef945` | Complete | Unresolved-children threshold raises housekeeping review into the quarterly sweep (D-B11 small-item section) | — |
| ORG-06 | `9f8047330286` | Binding invariant | Access-boundary posture; no engine mechanism | — |
| ORG-07 | `5e592e13da1b` | Complete | Three-question advisory coaching on structure proposals; capture never gated (structural); quarterly sweeps via AUD-03 (D-B11 small-item section) | — |
| PER-01 | `17f6a4de1615` | Complete | Personal partition has identical mechanism standing to Business | — |
| PER-02 | `97a2d3d8d79e` | Complete | Hard partition design traced | — |
| PLAT-01 | `f67c42daf206` | Deliberately deferred | Interface implementation deferred | Plan §12 |
| PLAT-02 | `81db94fbce88` | Complete | No authority in any interface layer under any shape | — |
| PLAT-03 | `a010c8b422bc` | Deliberately deferred | Evidence-gated later decision | Plan §12 |
| PLAT-04 | `90f994570913` | Complete | Product-specific notation replaced by conceptual document type with explicit portability constraint (D-B14 P2G-12); portability posture unchanged | — |
| QUE-01 | `092c4637865d` | Complete | Full field set: caps, batching, dedup links, snooze, escalation, due dates, aging, per-partition load metrics (D-B10 + D-B14 P2G-12) | — |
| RES-01 | `1ea9f096ba22` | Complete | Backup + verified-restore contract per store with scheduled isolated restore drills, fold smoke-replay, RestoreDrillEvents feeding AUD-03; backup-without-restore-proof explicitly insufficient (D-KR §2); first live drill = build-verification pending | — |
| RES-02 | `d931d286feb2` | Incomplete | Two-leg dead-man designed (phone-side alarm + heartbeat-fresh expiring leases; P2S-03) + watchdog-owned schedules (P2S-04); lease leg EXECUTED (P2S-05 trace 4 lease-expiry fail-closed, discriminating under seeded defect; `design/traces/behavioral/out/p2s05_linearization.json`) + watchdog heartbeat/staleness behavioral evidence (S1 WatchdogHeartbeatEvent, stale-heartbeat and watchdog-silent witnesses; `design/traces/behavioral/out/seeded_defects.json`); phone-side alarm leg is a live-system mechanism — build-gate verification per plan §7 | P2T-03: scheduler-death/horizon/schedule-change tests |
| RES-03 | `9a15ef00801d` | Complete | Degraded read snapshots + on-demand export + versioned recovery runbook, drill-tested on RES-01 cadence (D-KR §4) | — |
| SCH-01 | `19bc57988692` | Complete | schema_version on every persistent object/event/checkpoint; versioned reversible migrations with backward-readable exports in the schema contract (D-B14; export surface D-KR §4) | — |
| SCH-02 | `5b110206d776` | Incomplete | Complete envelope + watchdog-owned schedule liveness designed; expired-envelope fail-closed path EXECUTED (A14: SCH-02 expired control envelope refuses fail-closed, Record-only + hub-visibility per the `27_` ruling; schedule-liveness predicates read computed WatchdogHeartbeatEvents; `design/traces/behavioral/out/results.json`) | P2T-03: scheduler-death/horizon/schedule-change tests |
| SEC-01 | `7a94322e569e` | Binding invariant | Design phase's security posture = §8 sandbox contract; activation gates bind at build stages | — |
| SEC-02 | `587cd73b462e` | Deliberately deferred | Outbound-voice subsystem design; engine ceilings keep its action classes separated | Voice-subsystem change plan; prior Complete via ceilings was non-responsive — corrected |
| TRS-01 | `17e806d30553` | Complete | Fields mandatory and tested (27/27 structural; twin trace) | — |
| TRS-02 | `a991d93defba` | Complete | Isolation + bounded extraction + corrected no-proposal-without-policy default (P2S-07); both required tests EXECUTED against the real engine (negative: no policy ⇒ zero proposals of any class; positive: approved filing-only policy permits filing, outbound stays blocked; skip-eligibility defect flips 12 combinations; `design/traces/behavioral/out/p2s07_eligibility.json`) | — |
| TRS-03 | `aa92563d5412` | Complete | First-order mandatory controls | — |
| WF-01 | `7ed4ea904a6c` | Complete | Stage as a canonical state dimension on persistent topics — stages are state, not locations (D-B14 P2G-12) | — |
| WF-02 | `7f2bf6060b34` | Complete | Free stage transitions incl. skip/repeat/backward in the dimension contract (D-B14 P2G-12) | — |
| WF-03 | `bfd91c58b9e5` | Complete | stage/work_status/attention/focus independent canonical dimensions + derived health (D-B14 P2G-12) | — |
| WF-04 | `7a4b5e25684f` | Complete | KickoffRecord typed event on topic creation (D-B9 small-item section) | — |
| WF-05 | `ca520e8bf56a` | Complete | CloseoutPackage record (outcome, evidence, completion mode, fold-back targets) + Fold-BackEvent mechanics (D-B9, D-B4 §2.4) | — |
| WF-06 | `f766c52dcdde` | Complete | Blocking recorded, override evented, friction on the card | — |
| WF-07 | `de8f4218d5d0` | Complete | pause_state {return_context, impact_refs} preserved across focus switches (D-B14 P2G-12) | — |
| WF-08 | `1515729abfa8` | Complete | focus dimension + owner-mode input support one-foreground/many-background (D-B14, D-B7) | — |
| WF-09 | `8dcbd04bad21` | Complete | Taxonomy resolved by authority class; coverage tested | — |
| WF-10 | `44326723484b` | Complete | Recommendation+alternatives+recorded selection designed | — |
| WF-11 | `d4a3d2f6a7f4` | Complete | Selective rationale-request rule (rate-limited, non-blocking) on owner divergence; responses as LearningEvents feeding calibration (D-B9 small-item section) | — |
| WF-12 | `e739d82b45da` | Complete | Rituals, sweeps, aging, and reviews run scheduler-side under envelopes with watchdog liveness — no owner administration dependency (D-B11 small-item section) | — |

| ID | Text hash | Gate status | Actual result | Remaining dependency |
| --- | --- | --- | --- | --- |
| DE-R1 | `25f115850486` | Complete | Identity concepts carried through the schema (identity fields, attempt_epoch, absence markers — D-B14 P2G-12); acceptance traces in D-B3 §4; machine re-execution rides in the P2G-02 trace set | — |
| DE-R2 | `75d505062296` | Complete | Boundaries + P2S-05 linearization contract designed; all five linearization traces EXECUTED with computed verdicts, each discriminating under a seeded defect in its own mechanism (`design/traces/behavioral/out/p2s05_linearization.json`) | — |
| DE-R3 | `cf31054a94dc` | Complete | Dependency-by-capability matrix + kill/resilience mechanisms now actually designed (D-B5 + D-KR); C8 column re-grounded; runtime drills build-verification pending | — |
| DE-R4 | `73375b7bdab2` | Complete | Staged evaluation + P2S-07-corrected eligibility default designed; eligibility tests EXECUTED (see TRS-02 row); model-free ceiling precedes proposals in every combination; E2E-1 two-normalizer authority invariance EXECUTED with seeded-leak falsifier (`design/traces/behavioral/out/results.json`, `seeded_defects.json`) | — |
| DE-R5 | `100168f039d7` | Complete | Band function within ATT-01 with the P2G-07 two-rule correction and full category boundary traces — D-B7 §2–§4 | — |
| DE-R6 | `984e8966ddef` | Complete | Policy objects + composition semantics corrected per P2G-10: per-output resolution, floors intersect, constraints conjoin, ceilings min-combine, output-ownership excludes cross-domain contradiction; PC-1..12 simulated; selection reserved to re-review | — |
| DE-R7 | `1b2a131b1a4e` | Incomplete | Store coverage + P2S-06 deterministic fold order declared (incl. the control-journal position ratified by the D-B9 amendment, D-SM row 13); fold + shuffle-invariance EXECUTED (81/81 order-invariant; declared ordering keys, causal deps, fold phases; 13 registered-never-emitted event types disclosed; `design/traces/behavioral/out/p2s06_shuffle_invariance.json`) | P2T-02: causal-basis validation must fail closed |
| DE-R8 | `650997c6d0e2` | Complete | P2G-09 mathematics fully specified (one-sided Clopper-Pearson, outcome/denominator semantics, maturity arithmetic, scope-key taxonomy, delayed-correction rule) with six machine-executed witnesses incl. reachable first expansion 20→24 and the old-parameter HOLD reproduction (traces/der8_witnesses.json) | — |

**Accepted-row status counts (regenerated from the rows above; P2T-05):** Binding invariant: 11; Build-gate deferred: 8; Complete: 87; Deliberately deferred: 14; Incomplete: 3; N/A: 2 — total 125. Proposed DE-R rows: Complete: 7; Incomplete: 1 — total 8. This block is derived, never hand-written; `13V_` must fail on any summary/row disagreement (P2T-05 correction, TASK-0004).
