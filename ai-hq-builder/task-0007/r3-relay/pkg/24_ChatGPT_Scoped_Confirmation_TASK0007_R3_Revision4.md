# 24 — ChatGPT Scoped Confirmation: TASK-0007 R3 Task Packet Revision 4

**Role:** Independent verifier / plan-gate reviewer  
**Review target:** `22_TASK-0007_R3_Task_Packet_Revision4.md`  
**Packet:** `TASK0007_R3_Revision4_Packet.zip`  
**Scope:** Narrow confirmation of R3Q-01 through R3Q-09 before Builder release

## 1. Verdict

# **FAIL — Revision 4 is not yet implementation-ready; Builder release remains blocked**

Revision 4 materially improves the packet. The snapshot contract is now honest and independently reproducible, Fable correctly owns authority classification, provider-reported destination fidelity is no longer misrepresented as verified evidence, owner capacity is separated from provider-generated refusal traffic, and the live-secret ceiling now matches the redaction guarantee.

Four remaining defects prevent release to the Builder. Three affect authority or duplicate-side-effect safety; one affects the validity of the provider-selection evidence. They are bounded Task-Packet corrections and do not reopen Release 1, the provider shortlist, the Decision Engine baseline, or prior owner decisions.

---

## 2. Independent packet verification

```text
Uploaded ZIP SHA-256
887fbccc0fd8c6d1aecab23a355189d1d497f63b05b387fea4776b889a11bbe3

SHA256SUMS payloads
61 / 61 passed

Authority-manifest entries
60 / 60 referenced files present
60 / 60 declared hashes passed
No duplicate paths
All required classification fields present

Authority classifications
1 governing
10 reference
5 evidence-only
1 superseded
43 none

Governing instruction
22_TASK-0007_R3_Task_Packet_Revision4.md

Declared base commit
145ccbd1a6484afb5447afcc923890436e222895
Declared only, as disclosed

Declared base tree
404d1914945494272c2f2304dc2ca5fb14887452

Tree independently reconstructed from base_snapshot.tar
404d1914945494272c2f2304dc2ca5fb14887452
MATCH

Integrated R2 stub self-test
56 / 56 passed

Pinned R1 witness suite
21 / 21 passed

Python compilation of shipped stub and harness modules
Passed
```

The snapshot-only correction is accepted on its stated boundary: it proves the exact tree contents, not commit ancestry.

---

## 3. Prior-finding status

| Prior finding | Scoped result |
| --- | --- |
| **R3Q-01 — Self-contained Git snapshot** | **Closed.** The tree is independently reproducible and the unprovable commit/ancestry boundary is disclosed accurately. |
| **R3Q-02 — Artifact-fidelity authority** | **Substantially closed.** Provider-reported destination fidelity is now explicitly non-authoritative, impossible tests are withdrawn honestly, and `target_role` is added to registration identity. Retained registration semantics must still be moved into the governing packet under R4Q-01. |
| **R3Q-03 — Uncertain-result reconciliation** | **Open under R4Q-03.** The packet correctly states that local absence is not proof, then still uses local absence to permit `RECONCILED_NOT_DELIVERED`. |
| **R3Q-04 — Reachable state machine and route policy** | **Partially closed.** Reconcile and revoke routes now exist and route metadata is much more complete, but the normative transition/route effects are not self-contained. |
| **R3Q-05 — Split owner/external authority** | **Open under R4Q-02.** Per-item external envelopes are added, but the owner-authorized content is not bound to the owner-minted reference. |
| **R3Q-06 — Fault-safe evidence** | **Closed at plan level.** Provisional state is non-authoritative, committed-write failure fails closed, and six fault-injection boundaries are required. Runtime correctness remains subject to the final security review. |
| **R3Q-07 — Quotas and secret coverage** | **Closed at plan level.** Provider traffic cannot consume the owner pool, and every live token/capability must remain inside the bounded redaction index. |
| **R3Q-08 — Measurement evidence contract** | **Open under R4Q-04.** Matrix completeness is defined, but an evidence reference is treated as proven merely because a file exists. |
| **R3Q-09 — Builder-owned authority manifest** | **Closed.** Builder evidence and Fable authority classification are separated correctly. |

---

## 4. New findings

### R4Q-01 — High: The only governing packet depends on an instruction it declares fully superseded

**Problem:** Revision 4 says it supersedes Revision 3 **in full**. The authority manifest classifies `20_TASK-0007_R3_Task_Packet_Revision3.md` as `superseded`, `required_for_task: false`, while identifying Revision 4 as the only governing instruction.

Revision 4 nevertheless relies on Revision 3 for material implementation requirements:

- “The transition matrix is otherwise as Revision 3 specified.”
- “Other bounds unchanged from Revision 3.”
- “Everything Revision 3 required” for the retained test set.
- Several artifact-registration, idempotency, capability-binding, and route-state effects exist only in Revision 3.

A Builder following the authority manifest must not treat the superseded packet as instruction. A Builder following Revision 4 cannot implement the full contract without doing so.

**Required correction:** make Revision 5 self-contained. It must include, directly or in a new normative appendix inside the governing artifact:

1. The immutable artifact-registration record and lookup/refusal semantics.
2. The complete five-component submission/idempotency identity.
3. The full capability transition table, including every valid and invalid transition.
4. Exact state effects for every POC-1 route—especially that provider result/refusal records are corroborating evidence only and cannot mark an action delivered.
5. Every retained limit, descriptor-HMAC rule, and required test.

Remove “otherwise as Revision 3 specified” and “everything Revision 3 required,” or replace them with an exact incorporated appendix that is classified as governing. A superseded document may remain history, not executable instruction.

---

### R4Q-02 — High: A valid `idea_ref` authorizes provider-supplied owner content that the owner never approved

**Problem:** `/owner/idea` accepts and records:

```text
title
project
metadata
```

But `/poc2/triage` may later receive, from the provider:

```text
owner_content { title, body, project, tags }
```

The packet grants that entire `owner_content` object `instruction_authority: owner-authorized` whenever a valid `idea_ref` is present. It does not require the triaged content to equal, hash-match, or be loaded from the content the owner actually submitted.

A provider holding a valid reference can therefore alter the body, tags, title, or project and have the changed material recorded as owner-authorized. The reference authenticates the existence of an owner intake event, not the content presented later.

**Required correction:** bind the reference to immutable canonical owner content.

Recommended contract:

```text
POST /owner/idea
  accepts the complete owner_content schema
  canonicalizes it
  stores it server-side
  records owner_content_digest
  mints idea_ref bound to that record and digest

POST /poc2/triage
  accepts idea_ref plus separately enveloped external_items
  loads owner_content server-side
  does not accept provider-authored replacement owner_content
```

If a content copy is carried for workflow convenience, it must canonicalize to the stored digest or be refused. Provider-supplied metadata may remain corroborating material but cannot alter the owner-authorized component.

Add negative tests proving that a valid `idea_ref` paired with altered `body`, `tags`, `title`, or `project` is refused and never appears as owner-authorized.

---

### R4Q-03 — High: The proposed “positive negative evidence” still reduces to absence of local evidence

**Problem:** Revision 4 correctly states:

> Absence of a local record is not proof that no external action occurred.

It then defines the stub’s positive-negative check as:

```text
its own delivery ledger
PLUS
absence of any relay-delivered capture in its own capture log
```

That is still two forms of local absence. It does not rule out the exact failure being addressed: an external provider or destination completed the side effect, while the local service failed before recording it.

The packet itself acknowledges that the stub has no external system and that the check reduces to “this service has no record, durably.” That cannot safely authorize a second real-world side effect.

**Required correction:** for this apparatus, local absence may produce only `UNCERTAIN`.

`RECONCILED_NOT_DELIVERED` may be reached only through:

1. An owner attestation through the protected owner surface; or
2. A separately defined, independently authoritative downstream idempotency/status query that positively reports no delivery for the exact idempotency identity.

If the POC does not include such a downstream authority, the provider-facing `/poc1/reconcile` route may return:

- `RECONCILED_DELIVERED` when a service-owned receipt exists; or
- `UNCERTAIN` otherwise.

It must not return `RECONCILED_NOT_DELIVERED` from local non-observation. Add a negative test that removes every local receipt after a simulated uncertain external completion and proves that no retry becomes authorized.

---

### R4Q-04 — Medium: `evidence_ref` proves file existence, not the measurement it is cited to support

**Problem:** Revision 4 defines a `MEASURED` evidence reference as resolvable when the named file merely exists under `poc/data` or `poc/harness/out`.

That permits this invalid record to pass the stated validator:

```text
candidate: n8n
poc: POC-1
measure: owner_attention_minutes
value: 0
status: MEASURED
evidence_ref: poc/data/captures/README.md
```

The file exists, but it does not establish the candidate, POC, measure, value, observation, or provenance. The same unrelated file could be cited for every result.

**Required correction:** define a measurement-evidence record and bind the measure to it. At minimum, a resolvable evidence record must contain or point unambiguously to:

```text
candidate
poc
measure_id
observed value
unit
observed_at
collector / source
artifact or capture hash
```

The validator must confirm that the evidence record matches the measurement tuple and value. For `UNSUPPORTED`, the referenced capability-gap evidence must name the same candidate, POC, and capability/measure. A path-only existence check may remain a preliminary integrity check, not the complete provenance rule.

---

## 5. Accepted Revision 4 mechanisms

The following directions are accepted and should be preserved:

- Truthful snapshot-only provenance rather than a broken complete-history claim.
- Fable-owned authority classification and Builder-owned evidence-only return manifests.
- Provider-reported destination digest explicitly excluded from security gates.
- `target_role` included in artifact-registration identity.
- Per-item external-untrusted envelopes and per-component authority capture.
- Explicit reconcile and revoke routes.
- Provisional state excluded from authority checks.
- Disjoint general, security-refusal, and owner capture pools.
- A hard live-secret ceiling equal to the redaction index capacity.
- Full candidate × POC × measure enumeration with explicit `NOT_TESTED` and `UNSUPPORTED` outcomes.

These findings require correction of the boundaries above, not replacement of the selected direction.

---

## 6. Required Revision 5 contents

Fable should issue one final narrow Task-Packet revision containing:

1. A self-contained governing contract with no normative dependency on superseded Revision 3.
2. An owner idea reference bound to immutable canonical owner content.
3. Reconciliation that never treats local absence as positive proof of external non-delivery.
4. A measurement-evidence schema and validator that binds evidence to the exact result.
5. Updated negative tests for each correction.
6. A regenerated Fable-owned authority manifest, packet checksums, and the same independently reproducible base tree.

No new provider decision, Release-1 decision, Decision Engine decision, or owner approval is needed. No Builder work is authorized until the corrected packet receives narrow confirmation.

---

## 7. Gate state

```text
Release-1 product definition:            VALID
Capability Portfolio discovery:          VALID
Integrated R2 implementation baseline:   STRUCTURALLY VALID
R2 security claims:                      NOT YET INDEPENDENTLY ACCEPTED
Revision 4 snapshot contract:            PASS
Revision 4 manifest ownership:            PASS
Revision 4 direction:                     CONCUR
Revision 4 Task Packet gate:              FAIL
Builder release:                          BLOCKED
Owner POC session:                        BLOCKED
Provider selection:                       NOT MADE
Decision Engine baseline:                 NOT REOPENED
Hunter action required now:               NONE
Next actor:                               FABLE
Next artifact:                            TASK-0007 R3 Task Packet Revision 5
```

The review remains within the standing owner-authorized separation: Fable owns architecture and project management, the Builder implements only the accepted contract, ChatGPT independently verifies, and Hunter retains final authority.
