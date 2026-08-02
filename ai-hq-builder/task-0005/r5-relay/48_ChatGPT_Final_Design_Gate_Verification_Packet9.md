# 48 — ChatGPT Final Design-Gate Verification — Final Verdict Packet 9

## Verdict

**FAIL — one item on the owner-arbitrated closed list remains open.**

The packet is mechanically valid, the design correction cycle has converged materially, and three of the four terminal-list contracts are closed:

- **P2Y-02 — Schedule transaction invariants: CLOSED**
- **P2Y-03 — Legal recurrence admission: CLOSED**
- **P2Y-04 — Receipt-occurrence temporal validity: CLOSED**
- **P2Y-01 — Evidence-purpose governance: OPEN, narrowly**

No rediscovery, record-shape reconsideration, or owner-decision reopening is required. The design gate remains failed only because the bound evidence-policy artifact does not yet enforce the authority and version-coherence rules already stated in the ratified P2Y-01 design contract.

This verdict honors the owner-arbitrated termination rule: the review is limited to the prior §8 conditions, P2Y-01 through P2Y-04, preservation of accepted behavior, and any Critical defect in the corrected design itself. One unrelated High residual is routed to the build-gate register rather than used to extend this gate.

---

## 1. Independent Packet Verification

```text
Uploaded ZIP SHA-256
9a272a96b7748314bc99afdc04ea0aee917a04cac984f4b522b4a107c1e0ad1b

Export-manifest payloads
48 / 48 passed

checksums.sha256 entries
49 / 49 passed

Candidate commit
69920ef9214810ff378d26fb9d192afb5c740147

Candidate tree
822c160d7e175fca2540a48d97ab5803df7830d1

Git bundle
Valid; complete history

Fresh checkout
Clean

Supplied patch
Byte-identical to independently generated Git diff

git diff --check
Passed

Accepted v1.3 Manual and Requirements Register
Unchanged
```

All relevant packet files matched the candidate tree. No provenance or integrity defect changes the semantic result.

---

## 2. Prior Terminal Conditions

The previously agreed design-gate conditions now reproduce as follows:

```text
Behavioral gate
21 / 21 criteria passed

Incomplete direct causal basis
8 / 8 cases failed closed

External-basis resolution
50 / 50 negative cases failed closed
Positive independently governed case folded successfully

Schedule-liveness discriminator
17 / 17 behaviors detected

Supersession checker
Passed

Requirements/gate validator
Correctly remains closed while the four P2Y findings are listed open
```

The evidence is now genuinely behavioral rather than a copy of prewritten expected outputs. Candidate execution, fold behavior, mutation witnesses, shuffle invariance, policy-composition tests, and schedule tests reproduced deterministically.

---

## 3. Closed-List Dispositions

### P2Y-02 — CLOSED

The journal refuses all eight required invalid transaction histories and still replays the well-formed positive control. The enforced design includes:

- An in-force predecessor for every change
- One schedule and one adoption per transaction
- Complete retirement sets
- Same-schedule retirement references
- Schedule-scoped transaction identities
- No version both active and retired
- Rejection of missing, duplicated, asymmetric, or cross-schedule histories before state exists

### P2Y-03 — CLOSED

The same normative recurrence constraints now apply at writer admission and journal replay. The design refuses invalid versions, zero/negative periods, invalid logical times, malformed transaction identities, and entry-kind field violations. The required period `0` and `-1` tests fail closed.

### P2Y-04 — CLOSED

Run receipts are now tied to produced occurrences and an explicit admissible window. A receipt at `t0` cannot satisfy a `t10` occurrence under the default zero-early policy. Explicit early-window and on-time positive controls continue to pass, and nonexistent occurrences are refused.

### P2Y-01 — OPEN

The original self-declared-purpose defect is corrected: a `delete-production-data` action cannot ground itself with a `display-monthly-digest` receipt merely by declaring that purpose.

The ratified normative contract, however, states that the bound policy-plane artifact is authored by an authority distinct from **both** the evidence source and the receipt authority. The current implementation checks only that the policy authority differs from the manifest source.

#### Independent authority-separation probe

I created a valid, bound evidence policy whose authority was exactly the receipt-registry authority:

```text
manifest source authority
provider-snapshot-service

receipt authority
control-plane-attestation-service

policy authority
control-plane-attestation-service
```

Result:

```text
validation problems
[]

fold accepted
true
```

The evidence source is separate, but the same actor both defines which receipt purposes authorize an action and issues the receipts. That violates the ratified P2Y-01 authority contract.

#### Independent policy-version-coherence probe

I then supplied a bound policy artifact declaring:

```text
policy artifact version
P999

contract version
P1

action-context version
P1
```

Result:

```text
validation problems
[]

fold accepted
true
```

The mapping is defined as policy-version keyed, but the bound artifact can claim one version while applying contract rows from another. That leaves the policy identity ambiguous and permits the artifact’s declared version to become non-load-bearing.

These are two manifestations of one remaining defect: **the governed mapping is behaviorally enforced, but the authority and version identity of the policy artifact that owns the mapping are not fully enforced.**

---

## 4. Exact Final Correction Contract

One narrow correction cycle is required. It must do only the following.

### 4.1 Authority separation

`governed_purposes` or the equivalent policy-validation boundary must receive the receipt-registry authority context and refuse when:

```text
policy.authority_id == manifest.source_id
or
policy.authority_id == receipt_registry.authority_id
```

Absence of the required authority context must fail closed when external evidence is used.

### 4.2 Policy-version coherence

The bound policy artifact must represent one coherent version. At minimum:

```text
every contract.policy_version == policy.policy_version
and
action_context.policy_version == policy.policy_version
```

If the future design needs a multi-version policy set, that must be represented as separately bound versioned policy artifacts or an explicitly versioned policy-set schema—not by silently mixing versions inside one artifact.

### 4.3 Required negative tests

The gate must include machine-runnable tests proving refusal when:

1. The evidence-policy authority equals the receipt-registry authority.
2. The policy artifact version differs from its contract version.
3. The consuming action context requests a version different from the supplied policy artifact.

The existing three-distinct-authority positive control and all prior P2Y-01 through P2Y-04 tests must continue to pass.

### 4.4 Normative and gate records

Fable must:

- Keep `D-EC` as the controlling normative statement.
- Preserve P2Y-02 through P2Y-04 as closed.
- Keep P2Y-01 open until the corrected behavior passes independent re-verification.
- Update the requirements/evidence matrix only after that pass.

---

## 5. Non-Blocking Build-Gate Residual

Independent testing also confirmed a separate High residual:

> The consuming event’s `ActionContext` keys are trusted as declared and are not yet bound to the canonical `ActionRequest` payload or real effect.

A caller can describe an action as `render-digest / record-only` while its payload describes `delete-production-data`, obtain the benign display contract, and fold successfully.

Under the owner-arbitrated terminal rule, this is **not** used to extend the current design gate because it is outside the four-item closed list and is not Critical. It must be added to `13B_` as a build-gate obligation:

```text
B-12 — Bind action classification to canonical effect

The executor must derive or independently validate action_class, scope,
policy version, risk class, and data class against the canonical
ActionRequest/effect contract before acting. A caller or model cannot obtain
a benign evidence contract for a more consequential effect by mislabeling
those fields.
```

This disposition is intentionally non-blocking for the design gate.

---

## 6. Termination Rule for the Next Review

The next verifier review is limited to:

1. The P2Y-01 authority-separation correction.
2. The P2Y-01 policy-version-coherence correction.
3. The three new negative tests.
4. Regression of the existing positive case and the already accepted terminal evidence.
5. Packet integrity and exact candidate identity.

No new High-or-lower observation outside that correction may extend this design gate. Such items go to the build-gate backlog under the owner’s ruling. Only a Critical contradiction in the corrected design itself may reopen scope.

If the exact correction contract above passes and the prior terminal evidence remains green, the next verifier response should close P2Y-01 and pass the Decision Engine design gate.

---

## 7. Gate State

```text
Accepted v1.3 baseline:             UNCHANGED
Accepted Phase 2 discovery:         VALID
Approved CP-P2-A plan:              VALID
Packet integrity:                   PASS
Prior §8 terminal conditions:       PASS
P2Y-02:                             CLOSED
P2Y-03:                             CLOSED
P2Y-04:                             CLOSED
P2Y-01:                             OPEN — NARROW AUTHORITY/VERSION BINDING
Decision Engine design gate:        FAIL
Record-shape selection:             NOT MADE
DE-R1 through DE-R8 acceptance:     NOT AUTHORIZED
Owner decision package:             BLOCKED
Hunter action required now:          NONE
Next actor:                         FABLE
Required Builder scope:             ONE NARROW P2Y-01 CORRECTION
```

The standing separation remains unchanged: Fable owns architecture, dispositions, and project management; the Builder performs only the authorized correction; ChatGPT independently verifies; and Hunter retains final authority.
