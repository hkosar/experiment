# TASK-0007 — findings produced by building the apparatus

> **R2 note.** F-1..F-6 below were produced at R0 and still stand. What R2 added is
> not a new finding about the providers but a finding about the apparatus: an
> independent security review (`12_`) returned FAIL with eight findings, and Fable's
> disposition (`13_`) added seventeen more, **most of them evidence-integrity defects
> rather than security defects**. The corpus the round exists to produce would have
> been unattributable between candidates (FAB-02), self-overwriting (FAB-03), and
> silent on the two properties the POC exists to demonstrate (FAB-01). All are
> corrected in the R2 build; `stub/r1_witnesses.py` reproduces each against the
> pinned R1 artifact. **The scenarios are also re-aimed** to `09_` §2's Release-1
> workload — POC-1 is the Builder-return pipeline, POC-2 idea capture and staging,
> POC-3 the nightly integrity sweep. The Release-2 call and email scenarios are
> parked, not deleted.
>
> **F-2 is the one to carry forward into D4/D5** — it is unchanged and unaffected.

**Read the status line first: the POC round has NOT been run.** No Zapier account exists, no n8n host exists, no OAuth grant has been made, no provider has been contacted, and no measurement in `data/measurements.template.json` has a value. Everything below was produced by *authoring* the deliverables, not by running them — and each finding says which.

Packet `07_` §4 applies to the Builder: *"Every claim of the form 'provider X supports Y' must carry a demonstrated instance or be marked NOT TESTED."* Nothing here claims a provider supports anything.

---

## F-1 — Zapier has no public import format; n8n workflows are files

**Evidence class:** produced by attempting to build the deliverable.

Packet §5 asks for "workflow exports (Zapier zap definitions / n8n workflow JSON)". n8n workflows are portable JSON — three are shipped in `workflows/n8n/`, structurally validated against the real `n8n-workflow` library. **Zapier exposes no public import format for arbitrary Zaps**, so the equivalent deliverable could only be produced as a build *specification* (`workflows/zapier/POC_zap_build_specs.json`) to be followed by hand in the editor.

**Why it matters beyond packaging.** `04_` §7 lists "workflow definitions exported per run" as the exit strategy for the durable-execution row, and `02_` §4 makes portability one of the fourteen axes. If workflows on one candidate are files and on the other are only editor state, the two are not equally exitable — and the asymmetry shows up before any measurement.

**What is NOT established:** whether Zapier's own export/backup facilities, or any partner API, close this gap. That is a measurement for the session, and it is why the Zapier runbook asks the owner to record the manual build wall-clock against n8n's import time.

## F-2 — a provider can supply only 4 of the 16 D-EC_ receipt fields

**Evidence class:** derived from the ratified contract, mechanically, before any provider is chosen.

`harness/receipt_conformance.py --fields` enumerates what a D-EC_-conformant receipt requires and who may supply each field:

| Owner | Count | Meaning |
| --- | --- | --- |
| provider | 4 | The executing fabric can legitimately carry it |
| wrapper | 9 | Only the AI OS can mint it; a provider-supplied value is corroborating raw material at best |
| authority | 3 | Must come from a party structurally distinct from the provider |

**Why it matters.** It bounds the adoption question independently of which candidate wins: **whatever fabric is adopted, the wrapper carries three quarters of the receipt.** `04_` §2 already classifies "execution receipts / run history" as WRAP — this quantifies it. It also means "provider evidence quality" cannot be a selection criterion on its own; the discriminating question is narrower, namely how good the provider's 4 fields are and how much work its result format makes the other 12.

The checker also refuses to treat a provider-supplied *authority* field as conformance — it flags it, because a provider attesting to its own execution under its own purpose is the P2Y-01 defect in a new location.

## F-3 — the approval-authority constraint shapes the workflow, not just the policy

**Evidence class:** produced by designing the flows against the constraint.

Packet §3 says a provider human-in-loop feature "may carry the pause, never decide it." Building POC-1 to satisfy that forced a specific shape: the provider's wait/HIL step carries **an opaque resume token only**, and a subsequent wrapper call (`/poc1/verify-decision`) validates the token and returns the authorized ActionRequest or refuses. The provider never learns what was decided, only that it may continue.

**Consequence for the session:** if either candidate's HIL feature cannot be configured to carry a pause without also carrying the decision — for example if its approval outcome is what routes the branch — then that candidate cannot express POC-1 as specified. The Zapier runbook makes that an explicit stop-and-record point.

**What is NOT established:** whether either product actually permits this shape. NOT TESTED.

**R2 strengthened this.** The pause now carries only an opaque token; the owner surface is
key-protected; the provider never learns the case id; and `/poc1/verify-decision` is an
allowlist that accepts the token and nothing else. An independent reviewer defeated the R1
version of this control by having the provider record the decision through the *owner* door
— see `r1_witnesses.py` finding SEC-R1-03 and the Delivery Record.

## F-4 — the boundary constraints are machine-checkable, and now are

**Evidence class:** built and demonstrated failing.

`05_` §2 and packet §3 say violations "are findings, not judgment calls". `harness/check_boundaries.py` checks the authored definitions for Personal-partition data paths, policy/journal artifacts crossing to a provider, secret material in a definition, classification before the external-untrusted envelope, and a provider deciding an approval. All three shipped workflows are clean; **the checker's self-test proves each rule by making it fire — 9/9 cases.**

**Scope limit, stated plainly:** this checks *definitions*, not runtime. A definition that reads clean can still be pointed at a Personal mailbox by whoever attaches the credential. Runtime boundary behaviour is NOT TESTED.

## F-5 — the cost model's crossover is a single number, and it is currently unknown

**Evidence class:** arithmetic, self-tested; inputs unmeasured.

`05_` §3's prose — Zapier meters per task so cost scales with volume × steps, n8n meters per execution so cost scales with volume alone — reduces to one comparison: the two platform lines cross at **`n8n_price_per_execution / zapier_price_per_task` steps per run**. Below that step count Zapier is cheaper on platform fees; above it n8n is, before hosting and owner-attention are added.

`05_` §3's own working estimate for V5 is 5–15 steps per workflow, and the shipped POC flows are 4, 7 and 9 nodes — so **this workload sits squarely in the region where the answer depends on the exact rates**, which is precisely why the hypothesis needs measuring rather than reasoning about. The model computes it (`harness/cost_model.py`, self-test 14/14) and returns `None` rather than a fabricated number while the rates are unmeasured.

**What is NOT established:** every rate. No price was read from any vendor page during this task; `00_` §17's snapshot is explicitly marked for revalidation at POC time and was not revalidated here.

## F-6 — the Builder environment cannot validate node types

**Evidence class:** encountered.

`n8n-workflow` installed and the three workflow definitions construct as real `Workflow` objects. **`n8n-nodes-base` — the node-type registry — is blocked by this environment's egress proxy (403)**, so node types and their parameters could not be validated. `api.zapier.com` is likewise unreachable (proxy refuses CONNECT).

This is why the n8n runbook makes the import step (Part B, step 6) a recorded measurement rather than a formality: **the first real test of the parameter correctness of these definitions happens on the owner's host**, and node-level errors there are expected findings, not failures of the definitions.

---

## What the session must produce that this cannot

Every measure in `data/measurements.template.json`: setup wall-clock, owner-friction steps and minutes, connector coverage, approval-transport behaviour, duplicate-send prevention, the **induced mid-flight kill** in POC-3 and each fabric's actual recovery, the **connection-level revocation test** and its time-to-effect in POC-1, real billing units consumed, and the raw provider result captures that turn F-2 from a contract-derived count into a per-candidate measurement.

None of it is inferable from documentation. That is the point of the round.
