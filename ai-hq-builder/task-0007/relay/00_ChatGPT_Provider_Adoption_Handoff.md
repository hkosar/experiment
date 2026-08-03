# AI Operating System — Provider and Capability Adoption Handoff

**Document type:** Architecture handoff and proposed change request  
**Status:** Proposed; not an accepted baseline change  
**Prepared for:** Fable — Architect, Designer, and Project Manager  
**Prepared by:** ChatGPT — Independent Auditor/Reviewer  
**Owner:** Hunter  
**Date:** July 30, 2026  
**Working title for the new topic:** **Provider & Capability Adoption Review**  

---

## 1. Purpose

This handoff records a material architectural issue discovered during Decision Engine design:

> The AI Operating System has intentionally remained provider-independent, but it has not yet selected the provider class that will supply broad application connections, authentication, triggers, schedules, workflow execution, human approvals, retries, and routine external actions.

Because that slot remained open, the design began specifying mechanisms that could become a partial custom recreation of Zapier, n8n, Pipedream, Make, Activepieces, Temporal, or similar products.

The correction is **not** to replace the AI Operating System with an automation platform. The correction is to add a formal **adopt-before-build provider review** before provider-dependent architecture and implementation are finalized.

This document does not select Zapier, n8n, or any other provider. It defines the discovery work required to make that selection responsibly and to revise the development plan around the capabilities that can be adopted.

---

## 2. Current Architectural Position

The accepted operating model already separates the system into distinct layers:

1. Executive experience and Discord presentation
2. Operating model and recursive work organization
3. Coordination, recommendation, and policy intelligence
4. Durable operational state and memory
5. Integration with external applications and data
6. Infrastructure and execution hosting

It also intentionally keeps providers replaceable rather than allowing a vendor to become the operating model.

That principle remains correct.

However, **provider independence is not the same as provider avoidance**. The system should define stable provider interfaces, then adopt mature services where they meet the requirements.

### What has not been selected

No authoritative decision has yet selected:

- A default integration and action-execution fabric
- A default managed-auth and connector provider
- A default durable workflow/scheduler implementation
- A secrets and credential-management provider
- An execution-observability and receipt provider
- A knowledge-memory provider
- A complete provider portfolio or fallback policy

MCP was identified as an important interface, but MCP is a protocol—the plug shape—not a complete automation platform.

OpenClaw was discussed as an agent gateway and coordinator runtime, not as a full Zapier-class integration fabric.

Gbrain was discussed as a memory candidate, not as an exact-state workflow engine or general connector platform.

Supabase/Postgres has been considered for operational state, not as the provider of thousands of external application actions.

---

## 3. Problem Discovered

The Decision Engine and protection-layer work has begun specifying:

- Connector registries
- Credential onboarding and refresh
- Triggers and schedules
- Retry and reconciliation behavior
- Human approval pauses
- Idempotency and duplicate suppression
- Action requests and execution receipts
- Connector-health monitoring
- Run history and observability
- Watchdogs and missed-run detection
- External application adapters
- Routine workflow branching

Some of these are core governance requirements that the AI Operating System must own.

Others are mature commodity capabilities already available through automation and integration platforms.

Without a provider review, the project risks:

1. Rebuilding expensive commodity infrastructure.
2. Designing around assumptions that a selected provider handles differently.
3. Choosing abstractions that do not map cleanly to real provider capabilities.
4. Increasing security and maintenance burden unnecessarily.
5. Delaying useful business workflows while generic infrastructure is built.
6. Producing a development plan whose scope changes materially once providers are finally selected.

---

## 4. Architectural Conclusion

The correct architecture is:

```text
HUNTER
Phone or PC
        |
        v
DISCORD / EXECUTIVE EXPERIENCE
Reception, briefing, approvals, navigation, status
        |
        v
AI OPERATING SYSTEM CORE
Topics, checkpoints, hierarchy, policy, authority,
Business/Personal partitions, recommendations, evidence requirements
        |
        v
PROVIDER-NEUTRAL ACTION REQUEST
What may be done, under which authority, with which limits,
and what evidence must be returned
        |
        v
ADOPTED ACTION / INTEGRATION PROVIDER
Zapier, n8n, Pipedream, Make, Activepieces,
custom controlled service, or another approved executor
        |
        v
EXTERNAL APPLICATIONS
Email, calendar, CallRail, Meta, CRM, internal web tool,
files, forms, messaging, advertising, and other systems
        |
        v
EXECUTION RECEIPT / PROVIDER RESULT
What actually happened, provider identifiers, timing,
side-effect status, uncertainty, and evidence references
        |
        v
AI OPERATING SYSTEM CORE
Reconcile, verify, update the topic, notify Hunter,
close or reopen work, and fold results upward
```

### Core policy

> **Adopt before build.** Use an established provider when it safely, reliably, economically, and portably satisfies the accepted requirement. Build custom connectors or execution services only when the adopted provider cannot meet the requirement or when data, reliability, latency, control, or cost justifies custom implementation.

---

## 5. Proposed New Stage

### Topic

**Provider & Capability Adoption Review**

### Parent

AI Operating System initiative

### Stage

Discovery, followed by bounded evaluation and proof-of-capability testing

### Relationship to Decision Engine work

This topic is a **blocking dependency for provider-dependent execution architecture**, but not for the provider-neutral Decision Engine core.

### Work that may continue

The following can continue without a provider selection:

- Topic and hierarchy model
- Decision Case and linked-record semantics
- Recommendation-versus-policy boundary
- Owner identity and authority rules
- Business/Personal separation
- Attention and interruption policies
- ActionRequest contract at an abstract level
- Evidence and receipt requirements at an abstract level
- Checkpoint and fold-back behavior
- Provider-portability requirements
- Protection floors and non-overridable owner controls

### Work that should remain provisional or pause

The following should not be finalized as custom implementation before provider evaluation:

- Generic connector framework
- OAuth and credential-refresh infrastructure
- Default workflow scheduler
- Generic retry engine
- Human-in-the-loop implementation
- Connector-specific execution receipts
- Generic application adapters
- Connector-health registry implementation
- Provider run-history and observability implementation
- Cost accounting based on an assumed executor
- Mac Studio service topology for automation workloads
- Generic webhook intake and polling infrastructure
- Custom no-code or low-code workflow builder

---

## 6. Immediate Provider Classes to Evaluate

The review should distinguish provider classes rather than force one product to perform every job.

### 6.1 Integration and Action Fabric — immediate priority

Purpose:

- Connect common applications
- Handle OAuth and credentials
- Receive triggers and webhooks
- Execute application actions
- Run schedules and routine workflows
- Provide human approvals and basic run history

Initial candidates:

- Zapier
- n8n
- Pipedream
- Make
- Activepieces
- Direct MCP providers and application-specific MCP servers
- Custom controlled services where needed

### 6.2 Durable Workflow Execution — immediate for high-assurance workflows

Purpose:

- Preserve workflow state through failures
- Support timers, retries, signals, and recovery
- Provide deterministic or replayable execution where necessary

Initial candidates:

- Provider-native workflow engines
- n8n for ordinary automation workflows
- Temporal for code-defined, high-assurance durable execution
- Other durable-job products if justified during discovery

This class may complement an integration provider rather than replace it.

### 6.3 Managed Authentication and Embedded Connections — immediate

Purpose:

- Connect Hunter's accounts securely
- Potentially connect employee or future end-user accounts
- Handle token refresh and revocation
- Keep credentials away from model prompts

Initial candidates:

- Zapier MCP / developer platform
- Pipedream Connect and MCP
- n8n-managed or self-hosted credentials
- Direct OAuth for sensitive or unsupported systems

### 6.4 Operational State — already important; selection still requires confirmation

Purpose:

- Topics, hierarchy, stages, statuses, assignments, approvals, events, and checkpoints

Leading candidate already discussed:

- Supabase/Postgres

The provider review should confirm whether this remains the correct canonical exact-state store after the action fabric is selected.

### 6.5 Secrets, Identity, Evidence, and Observability — must be explicitly selected

Purpose:

- Secrets storage and rotation
- Owner identity and step-up authorization
- Tamper-evident action logs
- Provider execution evidence
- Error monitoring and operational health

These may require more than one provider. They should not be left as generic future implementation details once consequential actions are enabled.

### 6.6 Later provider reviews

These can remain provider-contract-first unless they become blocking:

- Semantic memory and knowledge graph
- Local-model runtime
- Model gateway and routing
- Browser automation
- Voice and telephony AI
- Companion dashboard
- Search and research services
- Vector storage
- Document processing

---

## 7. Initial Candidate Observations — Not Selections

These notes are a current-market starting point, not architectural decisions.

### Zapier

Current official materials describe:

- More than 9,000 connected applications
- More than 30,000 searches and actions exposed through MCP
- On-demand AI tool calls and conventional trigger-based Zaps
- Human-in-the-loop approval steps
- A task-based pricing model; Zapier MCP tool calls currently consume two tasks each

Likely strengths:

- Fastest setup
- Very broad SaaS connector coverage
- Low maintenance
- Familiar visual automation
- Strong candidate for immediate prototypes and long-tail app coverage

Likely tradeoffs to test:

- Task-based cost at high volume
- Hosted-cloud dependence
- Portability and depth of execution evidence
- Limits on high-assurance or highly customized workflows

### n8n

Current official materials describe:

- Cloud and self-hosted deployment
- Fair-code workflow automation with native AI capabilities
- Visual workflows plus JavaScript, Python, custom API requests, webhooks, queues, CLI/API control, and custom nodes
- Approximately 1,500 integrations in its current repository description
- Pricing based primarily on workflow executions, with unlimited workflow steps on paid plans

Likely strengths:

- Strong fit for the Mac Studio and hybrid/private deployment
- Greater code-level control
- Potentially favorable economics for multi-step workflows because one full run counts as one execution rather than charging each step
- Better control over data placement and custom nodes

Likely tradeoffs to test:

- Self-hosting and maintenance burden
- Security hardening and upgrade responsibility
- Connector maturity relative to Zapier
- Operations, backup, monitoring, and recovery burden

### Pipedream

Current official materials describe:

- Managed authentication and connected accounts
- MCP access to more than 10,000 tools across more than 3,000 APIs
- Prebuilt actions plus Node.js, Python, Go, Bash, HTTP, webhooks, flow control, concurrency, error handling, and key-value storage
- A developer-oriented Connect product for embedding integrations into an application or AI agent
- Compute-credit workflow pricing rather than per-step pricing

Likely strengths:

- Strong candidate when the AI Operating System needs embedded, programmatic integrations
- Managed OAuth without surrendering all code-level control
- Good bridge between no-code actions and custom development

Likely tradeoffs to test:

- Greater technical complexity than Zapier
- Hosted-service dependency
- Production Connect pricing and operational fit

### Activepieces

Current official materials describe:

- Self-hosting
- MIT-licensed open-source software
- More than 750 connector pieces
- Custom TypeScript pieces

Likely strengths:

- Open-source ownership and portability
- Self-hosted alternative worth testing

Likely tradeoffs to test:

- Smaller connector ecosystem and maturity compared with larger providers
- Maintenance and support expectations

### Temporal

Temporal is not primarily a Zapier replacement. It is a durable execution platform for code-defined workflows with persistent event history, retries, timers, task queues, recovery, and replay.

Likely role:

- Complement an action provider for the highest-assurance, long-running, failure-sensitive workflows

Likely tradeoff:

- Substantially greater engineering and operating complexity than ordinary automation platforms

### Make

Make remains a legitimate visual-automation candidate and should be included in the capability and cost comparison. No selection should be inferred without the same proof-of-capability testing applied to the other candidates.

---

## 8. Required Classification: Adopt / Wrap / Build / Defer / Reject

Every capability currently contemplated by the AI Operating System should be classified.

### ADOPT

The provider satisfies the requirement with acceptable cost, security, reliability, evidence, and portability.

### WRAP

The provider performs the execution, but the AI Operating System must apply its own policy, identity, data, approval, or evidence controls around it.

### BUILD

The requirement cannot be met safely or effectively through the provider, or custom implementation is justified by sensitivity, economics, reliability, latency, or strategic value.

### DEFER

The capability is valuable but is not required for the first useful release.

### REJECT

The provider's implementation conflicts with an accepted requirement or creates an unacceptable dependency.

Examples likely to emerge:

| Capability | Likely preliminary classification |
| --- | --- |
| Common SaaS OAuth and actions | Adopt or Wrap |
| Webhooks and routine schedules | Adopt or Wrap |
| Email, calendar, CRM, lead, and call actions | Adopt or Wrap |
| Generic retries and workflow branching | Adopt or Wrap |
| AI OS topic hierarchy and checkpoint state | Build |
| Decision and authority policy | Build |
| Business/Personal partition enforcement | Build, then Wrap provider actions |
| Git-based dual-verification development system | Keep custom/current |
| Sensitive internal database writes | Wrap or Build |
| High-assurance durable business transactions | Build on a durable engine or specialized service |
| Long-term semantic memory governance | Build provider-neutral contract; adopt implementation later |

---

## 9. Evaluation Criteria

Each candidate should be scored using evidence rather than impression.

### Capability

- Required connectors and actions
- Webhooks, schedules, queues, delays, and event triggers
- Human-in-the-loop support
- Branching and stateful workflows
- Custom code and custom connectors
- MCP and AI-agent compatibility
- Embedded/end-user connection support

### Governance and security

- Credential storage and refresh
- Permission scoping
- Business/Personal separation support
- Data residency and retention
- Audit and run history
- Revocation
- Role-based access
- Step-up approval integration
- Handling of external-untrusted content
- Export and deletion

### Reliability

- Retry semantics
- Idempotency support
- Uncertain-side-effect handling
- Durable waits and long-running workflows
- Missed-schedule detection
- Failure recovery
- Provider outage behavior
- Receipt and execution-evidence quality

### Economics

- Billing unit: task, step, execution, compute, user, or connection
- Expected cost for real Hunter workflows
- Cost at 10x volume
- Overage behavior
- API/model costs outside the platform
- Infrastructure and maintenance cost for self-hosted options
- Cost of owner attention and troubleshooting

### Operations

- Setup effort
- Learning curve
- Monitoring
- Version control and environments
- Backup and restore
- Upgrade burden
- Debugging experience
- Support and community
- Mac Studio compatibility

### Portability

- Exportability of workflows
- Provider-neutral ActionRequest and Receipt compatibility
- Ability to replace the provider without rewriting the operating model
- Availability of direct APIs, webhooks, or MCP
- Lock-in risk

---

## 10. Required Proof-of-Capability Workflows

At least two serious candidates should implement the same workflows. One candidate should be managed/SaaS-first and one should support self-hosting or deeper developer control.

### POC-1 — Call Review and Delegation

```text
Call/transcript arrives
→ record or event reaches the AI OS
→ Discord shows review queue
→ Hunter reviews or delegates to Cole
→ approved assignment is sent
→ response is monitored
→ completion is verified when possible
→ unresolved evidence returns to Hunter
→ workflow closes or reopens
```

Measure:

- Connector coverage
- Setup time
- Human approval support
- Response monitoring
- Evidence quality
- Duplicate-send prevention
- Monthly cost at expected volume

### POC-2 — Read-Only Email Triage

```text
Email arrives
→ external-untrusted envelope applied
→ work/personal classification
→ priority and effort recommendation
→ separate Business and Personal queues
→ no links followed and no action sent
→ Hunter sees a concise briefing
```

Measure:

- Trust isolation
- Data handling
- Classification handoff
- Queue update
- Mobile visibility
- Cost and latency

### POC-3 — Durable Overnight Workflow

```text
Scheduled work starts
→ bounded stage executes
→ checkpoint saved
→ safe retry occurs after a failure
→ uncertain external side effect is reconciled
→ status remains visible from phone
→ independent missed-run detection alerts Hunter
→ execution receipt returns to AI OS
```

Measure:

- Durability
- Retry semantics
- Side-effect uncertainty
- Checkpoint integration
- Watchdog independence
- Evidence and replay

### Optional POC-4 — On-Demand AI Action via MCP

```text
Hunter requests an action in Discord
→ Decision Engine produces approved ActionRequest
→ provider exposes the exact allowed tool through MCP
→ action executes
→ provider result is transformed into an AI OS receipt
```

Measure:

- Tool scoping
- Credential exposure
- Action logs
- Revocation
- Cross-model portability

---

## 11. Required Deliverables

Fable should produce:

1. **Provider Capability Inventory**  
   Every relevant accepted requirement and planned mechanism mapped to provider capabilities.

2. **Adopt / Wrap / Build / Defer / Reject Matrix**  
   One disposition for every capability with rationale and evidence.

3. **Candidate Shortlist**  
   Products selected for proof-of-capability testing and why.

4. **POC Task Packets and Results**  
   Same workflows, same success criteria, measured setup effort, maintenance, cost, reliability, and owner friction.

5. **Security and Data Boundary Matrix**  
   What data may enter each provider, what must remain local, and which actions require the AI OS wrapper.

6. **Cost and Capacity Model**  
   Expected monthly cost at current, 3x, and 10x usage—including platform, model, hosting, and owner-maintenance costs.

7. **Provider-Neutral Interface Contract**  
   ActionRequest, provider capability declaration, execution result, receipt, error, retry, and revocation interfaces.

8. **Recommended Provider Portfolio**  
   Default provider, secondary/fallback provider, and custom-service exceptions.

9. **Revised Decision Engine Design Impact**  
   Which current design mechanisms remain core, which become wrappers, and which are removed from custom scope.

10. **Revised Development and Deployment Plan**  
    Updated build order, Mac Studio service plan, proof gates, and deferred custom code.

11. **Owner Decision Package**  
    Concise tradeoffs and recommendation in business language.

---

## 12. Acceptance Criteria for This New Stage

The Provider & Capability Adoption Review is complete when:

- No provider is selected from reputation alone.
- At least two candidates complete the same POCs.
- One managed platform and one self-hosted/developer-controlled option are tested.
- Every provider-dependent design mechanism is classified.
- The exact AI OS/provider boundary is documented.
- Data, trust, identity, and approval boundaries are explicit.
- Cost and operational burden are measured with real workflows.
- Failure, retry, idempotency, and receipt behavior are demonstrated or transparently deferred.
- The selected architecture remains replaceable at the Action Provider interface.
- Custom build work is justified requirement by requirement.
- Fable produces a revised plan.
- ChatGPT verifies the provider-selection evidence and revised architecture impact.
- Hunter approves the resulting provider portfolio and development-plan changes.

---

## 13. Immediate Project Instructions

### Fable

1. Open **Provider & Capability Adoption Review** as a new linked topic.
2. Classify it as blocking the final provider-dependent execution architecture.
3. Preserve the current Decision Engine correction work rather than discarding it.
4. Split current mechanisms into:
   - Provider-neutral core requirement
   - Provider interface contract
   - Candidate provider capability
   - Custom implementation only if required
5. Prepare a bounded discovery/change plan for verifier review.
6. Do not select or implement a provider before Hunter approves that plan.

### ChatGPT

- Audit the provider-review plan.
- Verify the capability matrix and POC evidence.
- Challenge any claim that a provider fully satisfies a requirement when it only provides a partial mechanism.
- Verify that provider adoption does not weaken accepted identity, trust, data, approval, evidence, portability, or owner-control requirements.

### Claude Opus 5

- No provider implementation authority yet.
- After an approved Task Packet, build only bounded POCs and integration adapters.
- Do not alter the AI OS core architecture to match a preferred provider without an accepted change.

### Hunter

Owner decisions should be limited to genuine tradeoffs such as:

- Convenience versus control
- Hosted versus self-hosted responsibility
- Operating cost versus maintenance burden
- Data exposure versus connector coverage
- One default provider versus a portfolio
- How much custom development is strategically worthwhile

Hunter should not be asked to certify technical connector safety or retry correctness without verifier evidence.

---

## 14. Initial Hypothesis to Test — Not a Decision

The likely end state is a **provider portfolio**, not one universal provider.

A plausible hypothesis is:

```text
n8n
Primary self-hosted/hybrid workflow and automation fabric
for owned workflows and cost-sensitive multi-step execution

Zapier
Fast managed coverage for broad SaaS integrations,
prototypes, and long-tail applications

Pipedream
Developer-focused managed authentication, embedded integrations,
and MCP/API access when custom applications need deeper control

Custom controlled services
Sensitive, unsupported, low-latency, or high-assurance actions

Temporal or another durable engine
Only for workflows whose failure and recovery requirements justify it
```

This hypothesis must be tested. It is not an authorization to adopt all five products or to install n8n immediately.

---

## 15. Effect on the Current Decision Engine Design Gate

The current failed design-gate corrections should not be abandoned. They should be divided into two groups.

### Continue and complete as core design

- Authority and policy semantics
- Trust and data envelopes
- Current-policy re-evaluation before execution
- Critical-interrupt behavior
- Event identity and idempotency concepts
- ActionRequest and Receipt ownership boundaries
- Business/Personal queue separation
- Evidence independence
- Protection floors
- Owner control and kill/revoke requirements

### Hold as provisional pending provider review

- Exact scheduler implementation
- Generic connector framework
- Generic retry and workflow runtime
- Credential and token infrastructure
- Human-approval mechanics
- Receipt extraction from providers
- Watchdog implementation
- Connector observability
- Workflow versioning and deployment implementation
- Exact cost and capacity assumptions

The provider review may substantially simplify or alter these mechanisms. It should occur **before the design gate claims that the execution architecture is complete**.

---

## 16. Handoff Message for Fable

> A provider-selection gap has been identified. The AI OS was correctly designed to remain provider-independent, but no default Zapier-class integration/action fabric or durable execution provider was ever selected. Because that slot remained open, the Decision Engine design began specifying capabilities that may be adoptable from Zapier, n8n, Pipedream, Make, Activepieces, Temporal, or similar services. Open a linked **Provider & Capability Adoption Review** topic now. It blocks final provider-dependent execution architecture but does not block provider-neutral Decision Engine semantics. Produce an Adopt/Wrap/Build/Defer/Reject capability matrix, shortlist, security/data boundary, cost model, provider-neutral ActionRequest/Receipt contract, and identical proof-of-capability tests across at least one managed and one self-hosted/developer-controlled candidate. Preserve current core design work; do not select a provider or authorize Builder implementation until the plan is reviewed by ChatGPT and approved by Hunter.

---

## 17. Current Official-Market Evidence Snapshot

This section is informational and must be revalidated at the provider-review date.

1. **Zapier MCP** currently advertises access to 9,000+ apps and 30,000+ actions, with MCP tool calls consuming two Zapier tasks. Zapier distinguishes on-demand MCP actions from trigger-based Zaps and provides Human in the Loop approval actions.
2. **n8n** currently supports cloud and self-hosted deployment, custom code and nodes, AI workflows, and an execution-based pricing model in which a complete workflow run counts as one execution regardless of the number of steps. Its current repository description advertises roughly 1,500 integrations.
3. **Pipedream Connect/MCP** currently advertises 10,000+ tools across 3,000+ APIs, managed authentication, prebuilt actions, custom code, and workflow execution.
4. **Activepieces** currently advertises self-hosting, an MIT-licensed open-source platform, and more than 750 connector pieces.
5. **Temporal** provides durable code-defined workflows through persisted event history, retries, timers, queues, signals, recovery, and replay; it is a durability engine rather than a broad no-code connector marketplace.

### Official source references

- [Zapier MCP](https://zapier.com/mcp)
- [Zapier task usage rates](https://zapier.com/pricing/rates)
- [Zapier Human in the Loop MCP](https://zapier.com/mcp/human-in-the-loop)
- [n8n GitHub repository](https://github.com/n8n-io/n8n)
- [n8n pricing and execution model](https://n8n.io/pricing/)
- [Pipedream Connect overview](https://pipedream.com/docs/connect)
- [Pipedream MCP](https://pipedream.com/docs/connect/mcp)
- [Pipedream workflows](https://pipedream.com/docs/workflows)
- [Activepieces open-source overview](https://www.activepieces.com/open-source)
- [Temporal durable execution](https://temporal.io/)

---

## 18. Final Recommendation

Insert the **Provider & Capability Adoption Review now**, before the project completes the provider-dependent Decision Engine design and before it publishes a final implementation plan.

Do not pause the entire AI OS project. Continue provider-neutral operating-model and decision-policy work, but explicitly stop custom-build assumptions from hardening around an unselected execution stack.

The intended outcome is:

> Build the AI Operating System core that is unique to Hunter. Adopt the mature platforms that supply generic connections and workflow execution. Wrap those platforms in the AI OS policy and evidence layer. Build custom capabilities only where the accepted requirements make them necessary.
