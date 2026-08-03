# Release 1 POC Re-Aim — Scoped Verifier Review

## Verdict

**PASS WITH CHANGES — the Release 1 re-aim is approved in principle; D3 scenario execution is blocked until the bounded corrections below are applied.**

The central product ruling is coherent and improves the provider evaluation: Release 1 should test the actual App-Building Management Platform workload rather than use Release 2 business-operations workflows as stand-ins. The Decision Engine core remains workload-neutral, the provider shortlist and evaluation axes remain valid, and TASK-0007 R1's generic wrapper work may continue unchanged.

The re-aim does not reopen the accepted architecture. It changes what D3 must measure.

## Independent Packet Verification

```text
Uploaded ZIP SHA-256
cb97b9076629faa22936e0f2ae22c4f5770b681488f9e64c67437b93daebb4e7

Archive
Opened successfully

Declared payload checksums
4 / 4 passed

Payloads reviewed
02_Provider_Adoption_Discovery_Plan.md
05_Shortlist_Security_Boundaries_and_Cost_Model.md
06_ChatGPT_D1_D2_Review_PASS.md
09_Release_1_Definition_and_POC_Reaim.md
```

## What Is Approved

The following Release 1 definition is suitable to govern the POC round:

- The first release is the App-Building Management Platform.
- POC-1 tests the Builder-return artifact pipeline, owner stage card, and controlled relay.
- POC-2 tests idea capture, classification, and staging.
- POC-3 tests durable overnight execution through a useful project-integrity sweep.
- Release 2 retains calls, email operations, and broader business-operations autonomy.
- Providers remain transport and execution fabrics; they do not own the policy plane, journal, authoritative receipt ledger, or accepted project state.
- Gate approvals and releases remain owner decisions by design.
- TASK-0007 R1 may remain scenario-neutral; the scenario-specific R2 work follows this corrected re-aim.

## Findings

### R1P-01 — High: The authoritative POC definitions conflict across the packet

`09_Release_1_Definition_and_POC_Reaim.md` re-aims POC-1 and POC-2, but:

- `02_Provider_Adoption_Discovery_Plan.md` still defines POC-1 as call review and POC-2 as email triage.
- `05_Shortlist_Security_Boundaries_and_Cost_Model.md` §4 still instructs D3 to run call review and email triage.

The re-aim says it replaces `00_` §10, but it does not formally supersede these two current-facing definitions. A Builder or later reviewer could therefore select either scenario set and still claim document support.

**Required correction:** update `02_` and `05_` or add a single, explicit supersession table identifying every replaced sentence and the one authoritative D3 scenario definition. The corrected packet must contain no current-facing instruction to run the Release 2 call/email scenarios in D3.

### R1P-02 — High: POC-2 misclassifies an authenticated owner idea as external-untrusted

The proposed flow says:

```text
An owner idea arrives
→ external-untrusted envelope
```

That collapses two distinct trust cases:

1. An idea authenticated as owner-authored.
2. External material forwarded or attached by the owner for consideration.

Owner authorship does not make attached or quoted external content trusted, but the owner's own instruction and the external payload must not share one trust class.

**Required correction:** POC-2 must test at least two envelopes:

```text
Case A — authenticated owner-authored idea
origin: owner
instruction authority: owner-authorized within current session/policy
embedded external content: separately classified

Case B — imported or forwarded note/content
origin: external
trust: external-untrusted
instruction authority: none
semantic use: classification and summary only
```

The POC must prove that external content may inform classification without acquiring instruction authority.

### R1P-03 — High: The cost and capacity model still measures the retired workloads

The D2 model currently uses calls/transcripts and emails per day as the main POC-1 and POC-2 volume assumptions. Those variables no longer describe Release 1.

This materially affects the Zapier-versus-n8n economic comparison because artifact size, binary transfer, workflow-step count, owner-card actions, duplicate rates, and idea-capture volume differ substantially from call/email workloads.

**Required correction:** replace or supplement the D3 variables with Release 1 measures, including at minimum:

```text
Artifact returns per day
Average and maximum artifact size
Manifest/file count per artifact
Duplicate-artifact rate
Owner decision cards per day
Relay actions per accepted/rework decision
Idea captures per day
Ideas linked to existing projects versus new topics
Nightly integrity runs and files/checksums inspected
Provider tasks/steps/executions per completed workflow
Owner-attention minutes per workflow
```

The 1x/3x/10x model must be recalculated from those measured values. Call/email assumptions should be retained only as explicitly parked Release 2 planning inputs.

### R1P-04 — High: Duplicate suppression is underspecified

POC-1 correctly turns a real program problem—uploading the same ZIP twice—into a provider test. But a raw ZIP hash alone is not a sufficient universal idempotency key.

Two different tasks may legitimately use byte-identical artifacts, while the same task may be resubmitted with changed routing metadata. The POC must distinguish a duplicate delivery from a valid reuse.

**Required correction:** define and test an idempotency identity such as:

```text
workflow / task ID
+ stage or expected transition
+ artifact content digest
+ route or target role
+ submission epoch / accepted retry policy
```

Required tests:

- Same artifact, same task, same transition: suppress reprocessing and return the prior receipt.
- Same artifact, different task: process independently.
- Same task and artifact, different unauthorized target: reject rather than treat as a duplicate success.
- Replayed owner decision token: no second relay.
- Safe retry after an uncertain provider result: reconcile before any second side effect.

### R1P-05 — Medium: Artifact handling needs provider-discriminating boundaries

The security delta correctly limits repository credentials and protected-branch writes, but the provider evaluation now depends on handling code and project archives rather than ordinary business records.

The POC should measure capabilities that can materially change the provider decision:

- Maximum practical upload and webhook payload size
- Binary fidelity and digest preservation
- File-count and archive limits
- Safe treatment of nested archives, symlinks, traversal paths, and malformed archives
- Secret and restricted-file detection before provider transit
- Whether a provider stores, inspects, or retains artifact contents
- Retention/deletion controls
- Relay of the original artifact versus reconstituted content
- Mobile owner-card latency without placing the artifact itself in Discord

These are provider-selection measurements, not a demand for production-grade archive security in the POC. Unsafe or unsupported cases may fail closed and be recorded as capability gaps.

## Required Corrected D3 Definition

The corrected plan should establish one authoritative scenario set:

```text
POC-1 — Builder-return pipeline
Receive artifact → bind task/transition identity → hash and validate →
create owner card → accept/rework/inspect → controlled relay → receipt →
duplicate/replay/revocation/uncertain-result tests.

POC-2 — Idea capture and staging
Authenticated owner idea or separately enveloped external note →
classify as new topic versus existing-project addition → write staged record →
show mobile briefing and suggested next → no external action.

POC-3 — Durable nightly integrity sweep
Read designated project integrity inputs → checkpoint → deliberate kill →
safe retry → reconcile uncertain side effects → independently detect missed run →
report drift without making the provider authoritative for project truth.

POC-4 — Optional provider-neutral on-demand action
Unchanged if D2 still establishes that it adds discriminating evidence.
```

All shortlisted providers must receive equivalent scenario inputs, limits, success criteria, and measurement methods.

## Authorization and Sequencing

Fable may apply these corrections without another full D1–D2 review when:

1. The provider shortlist and per-axis evaluation method remain unchanged.
2. The capability-ownership work remains unchanged.
3. The accepted AI OS core and Decision Engine contracts remain unchanged.
4. Release 2 content is parked rather than deleted.
5. All current-facing POC definitions agree.
6. The trust-envelope and idempotency tests above are incorporated into the D3 Task Packet.
7. The cost model is re-based on Release 1 measurements.
8. The corrected files receive a new manifest and hashes.

A narrow verifier recheck is not required before TASK-0007 R1 continues because R1 is scenario-neutral. The corrected scenario definition must be incorporated before TASK-0007 R2 or any provider-specific POC run is authorized.

## Gate State

```text
Release 1 product ruling:              ACCEPTED FOR POC PLANNING
Release 2 parking decision:            ACCEPTED
Provider-review architecture:          UNCHANGED
D1–D2 provider discovery:              VALID
TASK-0007 R1 generic stub:              MAY CONTINUE
D3 re-aim direction:                    PASS WITH CHANGES
TASK-0007 R2 scenario work:             BLOCKED UNTIL CORRECTIONS
Provider POC execution:                 BLOCKED UNTIL CORRECTIONS
Provider selection:                     NOT MADE
Production implementation authority:    NOT GRANTED
Next actor:                              Fable
Hunter action required now:             None
```

## Final Verifier Position

The re-aim should proceed. Testing the actual App-Building Management Platform workload will produce more useful provider evidence than testing Release 2 call and email flows.

The correction set is necessary because the product ruling changes more than scenario names: it changes the trust cases, idempotency problem, artifact-security surface, and cost drivers that the provider comparison must measure.
