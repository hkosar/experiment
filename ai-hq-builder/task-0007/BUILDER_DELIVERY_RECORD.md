# Builder Delivery Record — TASK-0007 Round R4 (concurrency and evidence-ordering rework)

**Task:** TASK-0007 R4 — make the R2+R3 stub's authority transitions linearizable under the threaded HTTP server a provider actually meets, per `33_`, against the unchanged `25_` contract.
**Builder:** Claude Code session, model `claude-opus-5` (standing authorized substitution, trail entry 69).
**Branch:** `claude/task-0002-builder-handoff-g97x8j` (operator-designated; see §10).
**Instruction authority:** `33_TASK-0007_R4_Task_Packet_Concurrency_Rework.md` (governing). `25_` remains the governing **contract** and is unchanged. `31_`/`31A_`/`31B_`/`32_` and the nine probe scripts are authoritative inputs, read first as instructed.
**Returned to:** **Fable.**
**Status:** **Built and self-tested. Independent verification pending.** No POC has been run; no provider was contacted. **One acceptance requirement is not met as written, and it is reported rather than worked around — see AUDIT-R4-5, which needs a ruling.**

**Snapshot integrity (H-06), before anything was read as authority:**

| Check | Result |
| --- | --- |
| `SHA256SUMS.txt` | **76/76 OK, 0 failed** |
| `authority_manifest.json` | **75/75 verified, 0 mismatched, 0 missing**; one unlisted file on disk, `SHA256SUMS.txt` itself |
| `BASE_BINDING.txt` tree, independently reproduced | **`32b0f8d7a1e026cce8dbf8693abd49bc6aeade8f`** — matches |
| Relay's `poc/` against my R3 return | **45/47 byte-identical**; the two that differ are `stub/out/selftest.json` and `stub/out/r1_witnesses.json`, both regenerate-by-running. The relay's copies are byte-identical to the ones in the R3 zip I shipped; my working tree had newer runs |
| `r3_reference/stub_server_r3.py` against the reviewer's target | **`7f13494e…5b90f572`** — the hash `32_` records for the file the reviewer examined |

The commit in `BASE_BINDING.txt` is **declared only**, as the packet states. The tree is what I verified.

---

## 1. What the review found, and what it means about my testing

The independent review returned FAIL on one systemic defect: transitions read state under a short lock, released it, worked, and committed later, so two concurrent requests both passed the precondition and both became effective. `32_` §1 names it exactly right — **this is the R3 analogue of DEF-R2-01.** R2's defect was a control whose tested layer (in-process `dispatch`) differed from the layer a caller meets (HTTP responses). R3's is the same shape one level up: the tested layer was single-threaded; the server is `ThreadingHTTPServer`.

I introduced the live-HTTP block at R3 *because* of DEF-R2-01, and it still missed this, because a live-HTTP test that issues one request at a time is still not the layer a caller meets. **That is the third round in which my own verification, not my implementation, was the thing that was wrong.** The pattern is specific enough to name: I test the layer I was last burned at, rather than the layer the defect could live in. What follows tries to break that habit by making the reviewer's own probes part of the suite and by writing the barrier tests to run against **both** builds, so a test that cannot fail is visible as such.

## 2. The architecture, and the one deviation from my own audit

`33_` §1 selects it and does not delegate it: **one linearizable transition per subject identity, a single global lock held across precondition, reservation, evidence preparation, state publication and terminal result.** Implemented as: every `POST` runs inside `STORE.lock` for the whole of dispatch; `GET /health` deliberately does not take it, because A.8 requires health to be served when everything else has failed closed.

**Deadlock: none, and it is provable rather than hoped.** The service has exactly two locks. `STORE.lock` is an `RLock`; `SecretIndex._lock` sits inside a class that references neither `STORE` nor any other lock (verified by walking its AST). Every acquisition of the secret lock happens from code already holding `STORE.lock`, never the reverse, so the order is **total** — and a total order over the whole lock set admits no cycle. The service performs no outbound or blocking I/O; the only blocking work under the lock is a bounded local `fsync`.

**§1 permits releasing the lock for capture I/O with a re-check on re-acquire. I did not take that option**, because the re-check pattern reintroduces a narrower version of the very check-then-act window this round exists to close. That choice is what makes AUDIT-R4-5 bite, and I flag it there rather than hiding it in a design note.

## 3. Per-finding corrections

| Finding | Correction | Evidenced by |
| --- | --- | --- |
| **SEC-R3-01** transitions not linearizable | Insert-if-absent for registration, case and run declaration in one held critical section; `claim_token` reads-valid and marks-consumed in the same step; `/relay/deliver` claims its lease before any state moves | barriers 6/6, oracle cardinality clause |
| **SEC-R3-02** revoke lost to in-flight delivery | Each capability carries a `revocation_epoch`; a delivery claims the epoch it saw; `/owner/revoke` advances it and cancels any uncommitted lease; **the delivery revalidates at the terminal commit** and refuses under a superseded generation with no receipt minted | self-test SEC-R3-02 case, barrier orderings 1–3 |
| **SEC-R3-03** evidence asserts ineffective transitions | Secret-index admission is **attempted** before any committed record; the `case-opened` capture is written only after the token is minted and the case published, and any failure rolls the case, the identity index and the token back | `security_probes` sub-probes `false_capability_commit_on_secret_index_failure` and `false_case_opened_capture_on_token_failure`, both green |
| **SEC-R3-04** mutation outside the contract | Expiry is now a real transition (prepared → publish → committed → secret discarded); the stage-attempt counter moves only after its capture is durable; full field inventory in §5 | `security_probes` `expiry_without_transition_evidence` green (both expiry captures present), `stage_precise_probe` green |
| **SEC-R3-05** captures not crash-atomic | No final path is created until the content is durable: `mkstemp` → write → flush → fsync → `os.link` onto a path that did not exist → unlink temp → fsync dir; every failure removes the temp and **releases** the pool unit | `capture_atomicity_probe` green — `files_left: []`, all pools `0` |
| **SEC-R3-06** quotas not uniformly enforced | Global quotas reserved centrally at dispatch and released on any non-2xx; subject-scoped quotas reserved inside the transition against the service-resolved subject; every quota now gates on the counter its route actually increments | `quota_enforcement_probe` green — all three routes 429 |
| **SEC-R3-07** coverage is label coverage | Outcome coverage kept as a completeness aid only; `oracle_suite.py` binds seven security routes to 33 explicit clauses over live HTTP | oracle 7/7 against R4, **5/7 against pinned R3** |

`os.link` rather than `os.replace` is deliberate: rename silently overwrites, so it cannot express "a final path that did not previously exist"; link fails instead, which is the guarantee the finding asks for.

## 4. Three places my first attempt evaded a probe instead of passing it

Worth stating plainly, because each would have shipped as a false green:

- The secret-index correction originally only **pre-reserved capacity**. The reviewer's probe forces `SECRETS.add` itself to refuse; a pre-reservation sails past that injection. Corrected so the real admission is attempted before any committed record.
- The crash-atomic write originally used `os.fdopen` on the `mkstemp` descriptor, which routes around the probe's `builtins.open` injection. Corrected to `open()` so the injection still lands.
- The quota rework originally introduced a parallel counter (`entity_counts`), so the probe's setup — which sets `STORE.receipt_count` and fills `STORE.ideas` — no longer gated anything. Corrected so every quota gates on the counter the route increments, which is what SEC-R3-06 asks for and is also what makes the probe meaningful.

A fourth: my first `more_race_probes` criterion looked for `*_count` keys the probe never emits, found none, and **passed vacuously against the build it was written to fail**. It was caught only because I ran every criterion against the pinned R3 first and demanded red. That check is now the standing method, and it is why §6 reports probe results in both directions.

## 5. Mutable-field inventory (SEC-R3-04)

Generated mechanically from a live `Store` instance rather than by reading the source, so a field added later shows up as unclassified rather than being silently omitted.

| `STORE` field | Class | Why |
| --- | --- | --- |
| `base_url` | derived | set once at startup from the bound port / --advertise |
| `by_identity` | A.7-governed | submission identity index; published and rolled back with the case |
| `candidate` | derived | set once at startup from --candidate; never mutated after |
| `cap_by_ar` | A.7-governed | action-request index; published and rolled back with the capability |
| `capabilities` | A.7-governed | capability bindings incl. status, revocation_epoch and lease |
| `captures` | A.7-governed | per-pool capture reservations; incremented on reserve, released on any failed publication |
| `cases` | A.7-governed | published only after the token is minted; rolled back if the evidence does not land |
| `decisions` | A.7-governed | owner decisions; provisional until the committed record lands |
| `ideas` | A.7-governed | owner ideas and staged triages; the population the `ideas` quota bounds |
| `lock` | derived | the global transition lock itself |
| `owner_key` | derived | minted once at startup; never mutated after |
| `pending_quota` | derived | in-flight global reservations; returns to zero on both commit and rollback |
| `provider_key` | derived | minted once at startup; never mutated after |
| `reattempts` | A.7-governed | the single permitted re-attempt; spent with the attempt-start commit, restored on rollback |
| `receipt_count` | A.7-governed | the `receipts` quota's live counter; incremented by the dispatch commit on a 2xx only |
| `reg_by_identity` | A.7-governed | registration identity index; published with the record it indexes |
| `registrations` | A.7-governed | owner artifact registrations; published inside the transition, rolled back on failure |
| `relay_attempts` | A.7-governed | advanced only after the attempt-start transition commits; rolled back on failure |
| `relay_receipts` | A.7-governed | service-minted delivery receipts; written only past the terminal revalidation |
| `run_instance` | derived | set once at startup; never mutated after |
| `runs` | A.7-governed | POC-3 run records; provisional until committed |
| `runs_by_declaration` | A.7-governed | (schedule_id, occurrence) index; published with the run |
| `stage_attempts` | A.7-governed | advanced only after the stage capture is durable (SEC-R3-04) |
| `subject_counts` | derived | in-flight subject reservations; returns to zero on both commit and rollback |
| `tokens` | A.7-governed | claim-and-spend is atomic under the held lock; retracted on rollback |
| `transitions` | non-authoritative telemetry | append-only transition history for audit; gates nothing |
| `uncaptured_refusals` | non-authoritative telemetry | bounded aggregate of refusals not captured when the security pool is full; A.8 exposes it as an aggregate only |

Fields on `STORE` at runtime: 27. Classified: 27. Unclassified: 0.


## 6. Verification — every figure from a command run after the last edit

| Suite | Against R4 | Against pinned R3 | Meaning |
| --- | --- | --- | --- |
| Reviewer's probe scripts (`probe_runner.py`) | **4/9 green** | **1/9 green** | the five that stay red are all the barrier class — see AUDIT-R4-5 |
| Deterministic barriers (`barrier_suite.py`) | **6/6 hold** | **0/6 hold** | every subject identity, plus revoke-vs-deliver in all three orderings |
| Acceptance oracle (`oracle_suite.py`) | **7/7, 33 clauses** | **5/7** | branch-specific, over live HTTP |
| Stub self-test (`selftest_stub.py`) | **170/170** | — | §E plus the new SEC-R3-02 revalidation case |
| Superseded-build witnesses (`r1_witnesses.py`) | **34/34** | — | R1 21, R2 13, both pins digest-checked |
| Measurement validator | **160/160, 0 violations** | — | unchanged this round |
| Structural harness | **PASS** | — | harness code byte-identical; `out/**` regenerated by running |

The reviewer's probes and the barriers were run against **both** builds deliberately. A test that passes against the defective build is not evidence, and the only way to know is to run it there.

## 7. AUDIT — stop-and-report findings

**AUDIT-R4-1 — three of the eight entity quotas cannot be enforced at dispatch without breaking the `25_` governing rule.** `attempts`, `checkpoints` and `stage-attempts` are subject-scoped. At dispatch the only subject identifier available is the one the **caller supplied**, and for `/relay/deliver` the authoritative action-request id comes from the capability binding, not the caller's claim — resting the ceiling on the claim would let a caller evade its own ceiling by naming another subject. **Resolution applied:** global quotas at dispatch; subject-scoped quotas inside the transition, under the same held lock, against the service-resolved subject. Both reserve atomically and release on failure, which is what SEC-R3-06's own correction bullet requires. **If Fable wants the literal dispatch-time reading for all eight, it means accepting a caller-supplied subject id as a control input, and that needs an explicit ruling.**

**AUDIT-R4-2 — `ideas` gates two routes that count different things.** §B assigns it to both `/owner/idea` and `/poc2/triage`. **Resolution applied, following the reviewer's probe rather than my own first instinct:** a staged triage is now a record in the same population, so the counter that gates is the counter that increments. **Observation, not acted on unilaterally:** this means a provider flooding `/poc2/triage` can exhaust the ceiling the **owner** needs to register an idea — the same crowd-out shape A.8's reserved-owner pool prevents on the capture axis. Two separate counters against one ceiling would close it. I did not do that, because it is a contract-shaped choice; flagging it for Fable.

**AUDIT-R4-3 — the two expiry options are not equally available; taking the evidence-backed one, as §2 requires me to state.** A derived `EXPIRED` conflicts with A.8 (unchanged this round): *"secrets leave the index the moment they become unusable."* A derived state has no moment at which anything observes the capability becoming unusable, so its secret would sit in the index until a sweeper removed it — and a sweeper is itself an unrecorded mutation. The transition option satisfies both.

**AUDIT-R4-4 — the reviewer's probes print, they do not assert.** Eight of the nine have no assertions. "Green" is therefore undefined by the scripts and I must not define it in a way that flatters the build. Every criterion is taken from the corresponding finding's own text, tabulated against its source in `stub/security_probes/README.md`, and each is stated in `probe_runner.py` next to the check. The probes run **byte-identical except for a single `SRC=` path substitution**, which the runner performs and then verifies by diffing every other line.

**AUDIT-R4-5 — `33_` §1 and `33_` §4 cannot both be satisfied, and this is the one requirement I have not met as written.**

`33_` §4 requires the reviewer's probe scripts to run green. Five cannot, and the reason is structural rather than a defect in the build:

> The reviewer's race probes align two requests at a point **inside** the transition — they block in `write_capture` or `Transition.prepare` and wait on a `threading.Barrier(2)`. Under the architecture §1 **selects** — one global lock held across the entire critical path — that point is mutually exclusive by construction. The second request cannot arrive, so the barrier times out, breaks, and both requests fail. **No correct implementation of the selected model can make those probes green**, because making them green would require two requests to be inside one transition at once, which is precisely the defect this round removes.

Evidence for the claim, not just the argument: against the pinned R3 build these probes interleave and report the defect (`case_count: 2`, two capabilities, two receipts, revoke lost). Against R4 they report broken barriers. Meanwhile the **socket-aligned** barriers in `barrier_suite.py` — same properties, alignment moved to a point both requests can reach — go 0/6 against R3 and 6/6 against R4, with exactly the one-winner-one-truthful-loser cardinality SEC-R3-01 asks for.

Two ways forward, and **the choice is Fable's, not mine** — §1 is explicitly the architecture decision the packet made rather than delegated:

1. **Accept the socket-aligned barriers as the equivalent evidence** for those five, keeping the four probes that do run green as-is. Nothing changes in the build.
2. **Switch the capture write to §1's permitted release-for-I/O pattern** (reserve under lock → fsync with the lock released → re-acquire, re-check the precondition, publish). Then both requests can be inside `write_capture` together, the barrier is satisfied, and the re-check refutes the loser — the probes go green. It costs the simplicity §1 asked for, and the loser writes evidence it must then abandon, which needs A.7 prepared/committed framing to stay sound.

I did not take (2) on my own judgement because choosing the concurrency model is the one thing §1 says is not delegated. **I recommend (1)**, and note that whichever is chosen, the underlying safety properties are demonstrated either way.

## 8. What is NOT established

- **That R4 is secure.** Four rounds have now each been corrected by review. See §9.
- **End-to-end binary fidelity (§C)** — unchanged; `UNSUPPORTED` with the §C gap as its capability-gap evidence.
- **n8n node types and parameters** — `n8n-nodes-base` still blocked by the egress proxy (403). Structural validation passes; parameters settle at import time. Inherited unchanged for the fifth round.
- **Any provider capability.** No account, no host, no provider contacted.
- **Behaviour under more than two concurrent requests.** The barriers are deterministic two-request tests, as `33_` §4 requires and as `31B_` prefers over stress. Three-way and n-way interleavings are not tested here.

## 9. Falsifier element (APP-06 / CPB-14, reflexive)

| # | Claim | Who would have to be wrong, and how | Status |
| --- | --- | --- | --- |
| 1 | The transitions are now linearizable | **An independent reviewer, and the record is four for four.** R1 shipped 66 green cases and had a gate bypass. R2 shipped 56 and was unrunnable over HTTP. R3 shipped 167 and had two reachable Criticals. Each time my suite was green and the defect was in a layer my suite did not reach. I have no basis to claim this round broke that streak — only that the barriers now run against the defective build too, which is the first check I have had that could tell me the tests are capable of failing | **Built to spec; independent verification pending** |
| 2 | The global lock is deadlock-free | **The lock inventory, and it is mechanical.** Two locks, a total acquisition order, no outbound I/O. If a future edit adds a third lock, or takes `STORE.lock` while holding the secret lock, the proof lapses silently — nothing in the build enforces the order | Not disconfirmed; **proof is structural, not enforced** |
| 3 | Committed evidence describes only effective state | **Me, at the paths I did not fault-inject.** Every boundary the findings name is injected. A.7 governs more transitions than those, and the rest follow the same shape by construction — and I found three ordering defects this round by testing, which is evidence construction is not self-enforcing | Not disconfirmed; **named boundaries tested** |
| 4 | The reviewer's probes are unmodified | **The runner, and it checks itself.** One `SRC=` line is rewritten and every other line is diffed. But I wrote the runner, and I also wrote the pass criteria for probes that assert nothing — §7 AUDIT-R4-4 is the mitigation, not a proof | **Mechanically checked; criteria are mine** |
| 5 | The five red probes are red for the reason I give | **Me, and this is the claim to attack first.** It is convenient for me if the failures are the probes' method rather than my build. The falsifying evidence would be an implementation of §1's selected model under which those probes go green; I argue none exists, and if the reviewer produces one, my analysis is wrong and so is the build | **Argued, evidenced both ways, needs a ruling** |
| 6 | My record matches my code | **Me.** Every figure in §6 came from a command run after the last edit, re-checked against its artifact before writing. The number to distrust hardest is **170/170**, for the same reason as every round: I wrote both the test and the thing it tests | **Self-authored; independently unverified** |

## 10. Change requests, open items and deviations

1. **AUDIT-R4-5 needs a ruling** — accept the socket-aligned barriers, or authorise the release-for-I/O switch.
2. **AUDIT-R4-1** — confirm the global/subject split, or rule that a caller-supplied subject id may gate a ceiling.
3. **AUDIT-R4-2** — the owner/provider crowd-out on the shared `ideas` ceiling, flagged not fixed.
4. **Allowlist additions**, all listed in `RETURN_MANIFEST.json`: `stub/r3_reference/` (§5 explicitly permits it), `stub/security_probes/` (the reviewer's nine scripts and nine outputs, byte-identical, so the return is checkable standalone), and three new test modules — `probe_runner.py`, `barrier_suite.py`, `oracle_suite.py` — which §5's "and its tests" covers but does not enumerate.
5. **No `25_` contract clause changed.** The `Disclose` exemption is untouched — no new construction site, so §3's condition does not trigger, and `control_probes` stays green.
6. **Immutable denylist unchanged** — `r1_reference/`, `r2_reference/`, harness code, `authority_manifest.json`. Proven per-file in the manifest.
7. **No POC run, no provider contacted. No `13B_` obligation implemented.** Every THROWAWAY marker kept.
8. **Branch deviation (unchanged, disclosed):** operator-designated branch.
9. **Recommended reviewer focus:** §7 AUDIT-R4-5 first — it decides whether this round is acceptable as built. Then §4, the three evasions, because they are the failure mode most likely to have a fourth instance I did not catch.

---

*Builder-authored completion claim and evidence index — not independent evidence (APP-06). The rework is claimed complete against `33_` §2 except as stated in AUDIT-R4-5; **no POC is claimed run, and no security property is claimed independently verified.** Per `33_` §6 this returns to Fable for structural verification and then to ChatGPT for concurrency re-verification with its own barrier probes. The security gate closes when the reviewer says it does, not when I do.*
