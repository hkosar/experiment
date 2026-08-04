# TASK-0007 R3 Revision 5 — Narrow Plan-Gate Confirmation

## Verdict: PASS WITH ONE PRE-AUTHORIZED CONTROL CLARIFICATION

Revision 5 materially closes R4Q-01 through R4Q-04. The packet is sufficiently complete and authority-bounded to proceed to Builder implementation after Fable applies the exact `/owner/reconcile` clarification in R5Q-01 below and regenerates the packet integrity records.

No additional verifier round is required if the correction is applied exactly, the governing packet is otherwise byte-identical, and the regenerated hashes validate completely.

## Independent packet verification

```text
Uploaded ZIP SHA-256
a54b6175ec1ba9edaacaa24ff7ebdedfedd5a4cc47f4eda695f712f28e17a9f7

Matches Fable's supplied fingerprint
YES

SHA256SUMS.txt
60 / 60 passed

Fable authority manifest
59 / 59 file hashes passed
Exactly one governing instruction
No superseded packet has instruction authority

Declared base tree
ef8036d1f6d24671079106375906fec140440c3b

Independently reconstructed base tree
ef8036d1f6d24671079106375906fec140440c3b

Base snapshot archive safety
325 members
No absolute paths, parent traversal, symlinks, or hard links

Integrated R2 stub self-test
56 / 56 passed

Pinned R1 witness suite
21 / 21 passed
```

The full structural harness could not execute its n8n parser because `n8n-workflow` is unavailable in the review environment. Revision 5 already identifies that limitation and prohibits working around it. The remaining baseline harness checks reproduced as disclosed; this is not a Revision 5 defect.

## Prior-finding status

### R4Q-01 — Closed

Revision 5 no longer relies on Revision 3 or Revision 4 for executable requirements. It directly includes:

- the five-part submission identity and duplicate/rejection behavior;
- immutable artifact registration and binding rules;
- the complete capability state model, valid transitions, invalid transitions, replay behavior, and binding fields;
- route-level POC-1 effects, including the non-authoritative status of provider receipt/refusal claims;
- all retained limits, redaction/HMAC rules, quota behavior, and required tests.

Revisions 3 and 4 are correctly classified as superseded history. Accepted owner/program records such as `08_` and `09_` remain reference context rather than substitute implementation instructions. No missing Revision 3 or Revision 4 clause is needed to implement the R3 correction contract.

### R4Q-02 — Closed

The owner-idea path now binds authority to immutable canonical content established on the owner surface:

```text
POST /owner/idea
→ accepts complete owner_content
→ canonicalizes and stores it server-side
→ records owner_content_digest
→ mints idea_ref bound to that record

POST /poc2/triage
→ loads owner_content server-side
→ refuses a provider-carried copy whose canonical digest differs
→ preserves separate external-untrusted envelopes per external item
```

The required negative tests cover altered body, tags, title, and project, plus missing references and authority-escalation attempts.

### R4Q-03 — Substantively closed; exact schema clarification required

Revision 5 correctly establishes that local non-observation can produce only `UNCERTAIN`. The provider-facing reconciliation route cannot create `RECONCILED_NOT_DELIVERED`, and no retry is authorized without owner attestation or an independently authoritative downstream negative result.

The remaining issue is an internal schema ambiguity: the route-policy table still defines the owner route as:

```text
action_request_id, delivered (bool), note
```

while the state model permits the owner route to establish only `RECONCILED_NOT_DELIVERED`; `RECONCILED_DELIVERED` requires a service-owned receipt. A Boolean field asks the Builder to decide what `delivered: true` means.

R5Q-01 below removes that authority decision from the Builder.

### R4Q-04 — Closed

Revision 5 replaces path existence with a measurement-evidence record carrying:

```text
candidate
poc
measure_id
observed_value
unit
observed_at
collector
artifact_or_capture_hash
```

The required validator must match candidate, POC, measure ID, and observed value; enforce status-specific fields; require matching capability-gap evidence for `UNSUPPORTED`; and enumerate the complete candidate × POC × measure matrix so omitted combinations fail.

That satisfies the scoped correction. The later verifier must still test the Builder's actual validator rather than treating the contract text as execution evidence.

## R5Q-01 — High: `/owner/reconcile` exposes an undefined authority branch

### Problem

The governing transition table permits:

```text
UNCERTAIN
→ RECONCILED_NOT_DELIVERED
→ owner attestation
```

and reserves `RECONCILED_DELIVERED` for a service-owned receipt. The route-policy schema nevertheless accepts an unrestricted Boolean named `delivered`.

That leaves the Builder to choose among incompatible behaviors for `delivered: true`: accept it as delivered, reject it, revoke the capability, or preserve uncertainty. Because this is an authority-bearing transition, the governing packet must choose.

### Pre-authorized correction

Fable may make these exact text changes without another verifier round.

1. Replace the `/owner/reconcile` route fields with:

```text
action_request_id,
outcome (literal "not_delivered"),
note
```

2. Add this normative rule to A.5:

> `/owner/reconcile` is valid only while the subject is `UNCERTAIN` and only when `outcome` is the literal `not_delivered`. A valid request records the owner attestation and transitions to `RECONCILED_NOT_DELIVERED`. Any other outcome value, any other source state, or any attempt to use the route to create `RECONCILED_DELIVERED` is a captured refusal with no state change. An owner who wants to prevent further action without attesting non-delivery uses `/owner/revoke`.

3. Add the following negative tests:

```text
owner reconcile with outcome="delivered" → refused, no state change
owner reconcile from a non-UNCERTAIN state → refused, no state change
owner reconcile with outcome="not_delivered" from UNCERTAIN → accepted once
replay of the same owner reconciliation → prior result or refusal, never a second transition
```

### Why no further round is required

This correction does not change the accepted reconciliation policy. It merely makes the already-selected policy executable without delegating an authority decision to the Builder.

## Builder-release conditions

Fable may release Revision 5 to the Builder when all of the following are true:

1. R5Q-01 is applied exactly.
2. `25_TASK-0007_R3_Task_Packet_Revision5.md` is otherwise unchanged.
3. The authority manifest still identifies exactly one governing instruction and keeps Revisions 3 and 4 superseded.
4. `SHA256SUMS.txt` and `authority_manifest.json` are regenerated and validate 100%.
5. The base snapshot and declared base tree remain unchanged.
6. No Builder-authored document is granted instruction authority.
7. The Builder receives the corrected Revision 5 packet, not any superseded revision.

## Gate state

```text
Release-1 product definition:          VALID
Capability Portfolio discovery:        VALID
Integrated R2 baseline:                 STRUCTURALLY VALID
Revision 5 R3 direction:                PASS
R4Q-01:                                 CLOSED
R4Q-02:                                 CLOSED
R4Q-03:                                 CLOSED AFTER R5Q-01 TEXT CORRECTION
R4Q-04:                                 CLOSED
Additional verifier round:              NOT REQUIRED IF EXACT
Builder release:                         AUTHORIZED AFTER CORRECTION
Owner POC session:                       BLOCKED PENDING BUILD + SECURITY REVIEW
Provider selection:                      NOT MADE
Decision Engine baseline:                NOT REOPENED
Hunter action required now:              NONE
Next actor:                               FABLE → BUILDER
```

Revision 5 preserves the established separation: Fable owns architecture, task authority, and project management; the Builder implements the accepted contract; ChatGPT independently verifies the eventual return; and Hunter retains final authority.
