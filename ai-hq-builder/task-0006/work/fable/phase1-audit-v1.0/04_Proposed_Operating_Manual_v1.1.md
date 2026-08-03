# AI Operating System — Phase 1 Operating Manual and System Design Baseline

**Version:** 1.3 — **ACCEPTED BASELINE**

**Status:** Accepted by the owner on 2026-07-25 (decision-trail entry 53) following the complete audit gate process: 7-role independent audit with adversarial verification, consensus synthesis, 10-scenario experience walkthrough, peer verification by ChatGPT (zero dissents; findings G-01/G-02/G-03 incorporated), and the H-08 canonical-state erratum. **The AUD-01 audit gate is passed.** This document, including the v1.2 layer (accepted trail entry 65) and the v1.3 layer (accepted trail entry 73), is the authoritative Phase 1 operating baseline.

**Date:** July 25, 2026 (v1.0 baseline: July 24, 2026)

**Purpose:** Preserve the complete Phase 1 operating model, its governing requirements, and the audit gate required before Decision Engine discovery begins. This revision integrates the consensus issue register (`02_Consensus_Issue_Register`), the verifier's modifications, and the owner's realignment: this is a conceptual operating design, activated in stages measured in days, with the owner's attention — not build capacity — as the governing constraint.

> **Working north star:** Allow natural, nonlinear input while the system enforces organized execution, preserves context, manages protocol, and guides the owner to the next useful decision.

# Document Control

- **Document type:** System design specification and discovery baseline (conceptual operating architecture, not an implementation contract)
- **Version:** 1.3 (accepted baseline — v1.1 trail entry 53; v1.2 trail entry 65; v1.3 trail entry 73)
- **Status:** v1.1 accepted 2026-07-25 (trail entry 53); v1.2 released and accepted 2026-07-27 (trail entries 59, 65); v1.3 released 2026-07-28 (trail entry 72) and accepted 2026-07-28 (trail entry 73)
- **Primary operator:** One owner/operator for the foreseeable future
- **Primary interface:** Discord-first; core operating model remains platform-independent
- **Primary domains:** Business and Personal, presented together but prioritized separately
- **Source material:** Discovery interview and current-state workflow description
- **Change rule:** Future design decisions should update this document or its version-controlled successor rather than remain only in chat history.
- **v1.2 layer *(CP-v1.2-A)*:** This baseline carries the v1.2 layer implementing owner-approved change plan CP-v1.2-A Revision 2 (decision-trail entry 54), built as TASK-0001, released by two-step compare-and-swap (trail entry 59), and **accepted by the owner 2026-07-27 (trail entry 65)**. Every v1.2 addition is tagged *(v1.2 — CP-v1.2-A)*. Homes: sections 12.5, 12.6, 17.3, 20A.3, Appendix A.3, DP-026, ADR-020, and the v1.2 rows of `05_Requirements_Register_v1.1`.

> **How to use this baseline (v1.1 accepted):** Treat this document as the authoritative parent hub for Phase 1. The audit challenge it invited has been completed and the owner accepted the consensus revision (trail entry 53); the authoritative register is `05_Requirements_Register_v1.1`. Phase 2 opens only after the active TASK-0002 / v1.3 cycle completes release, receipt, and owner-acceptance gates, unless a later owner decision explicitly changes sequencing. These gates completed with the owner’s v1.3 acceptance (2026-07-28, trail entry 73); Phase 2 is open.


## Phase 1 Closure Statement

Phase 1 established the operating philosophy, executive experience, recursive hub model, topic lifecycle, navigation, learning governance, approval harness, application-development model, business/personal separation, memory boundaries, Discord-first strategy, delegation model, and initial hardware recommendation.

*(v1.1 accepted status)*: this baseline completed exactly that review — independent multi-agent audit, adversarial verification, consensus synthesis, experience walkthrough, and peer verification — and was **accepted by the owner on 2026-07-25 (trail entry 53)**. The audit gate it prescribed has been passed; the paragraph above is preserved as the original intent it fulfilled.

The accompanying packet contains:

- This Operating Manual.
- A requirements register.
- Design principles.
- Architecture decision records.
- Vocabulary and object model.
- Open questions and the Phase 2 backlog.
- A chronological conversation decision trail.
- An audit brief and consensus protocol.

## Contents

- 1. Executive Summary
- 2. Design Intent, Scope, and Non-Goals
- 3. User and Current Operating Context
- 4. Target Experience
- 5. Conceptual Architecture
- 6. Information Architecture and Object Model
- 7. Topic Lifecycle, State, and Fold-Back
- 8. Interaction, Routing, and Focus Management
- 9. Navigation, Dashboards, and Presentation
- 10. Learning, Preferences, Rules, and Skills
- 11. Automation, Approval, and Verification Harness
- 11A. Protection Layer: Identity, Trust, Data, and Resilience *(v1.1)*
- 12. Application Development Operating Model
- 13. Business Operations, Data, Leads, and Calls
- 14. Personal Operating Domain
- 15. Memory, Context, and Knowledge Architecture
- 16. Discord-First Platform Strategy
- 17. Staged Activation Plan *(v1.1: replaces Recommended MVP and Rollout)*
- 18. Success Measures, Risks, and Guardrails
- 19. Phase 1 Audit Gate and Phase 2 Backlog
- 20. Hardware Baseline
- 20A. Program Governance and Stage Gates *(v1.1)*
- 21. Phase 1 Acceptance and Consensus
- Appendix A. Consolidated Requirements
- Appendix B. Glossary
- Appendix C. Design Principles
- Appendix D. Architecture Decision Summary

# 1. Executive Summary

The current workflow uses capable cloud models and development tools, but continuity, organization, monitoring, and protocol are held together manually by the owner. Planning, implementation, review, context handoffs, status awareness, and prioritization are split across long browser sessions, Cursor, local processes, email, and personal memory. The owner is therefore acting as both vision owner and orchestration layer.

The target system is a persistent AI operating environment with one familiar front door, durable structured state, recursive project hubs, model-independent workflows, and a learning layer that proposes improvements without silently changing behavior. Discord is the preferred first interface because it is familiar and continuously available on phone and PC, but Discord must remain a presentation layer rather than the authoritative system of record.

The design supports three connected operating loops:

| Loop | Purpose | Representative outcome |
| --- | --- | --- |
| Think to Plan | Convert incomplete notes, interruptions, and exploratory conversation into structured decisions and executable plans. | A vague meeting note becomes an initiative with scoped topics, decisions, and a deployment plan. |
| Build to Operate to Improve | Create applications, operate the business through their data and workflows, then feed observed problems back into application and process development. | Lead and call data produces coaching insight, identifies a workflow gap, and opens an improvement topic. |
| System Self-Improvement | Observe recurring preferences, skills, protocol deviations, and successful automation patterns, then mature them through the same governed workflow used for other work. | Repeated requests for click-by-click guidance become a reviewed, scoped skill rather than an informal chat preference. |

> **Primary design outcome:** The owner should be free to think associatively and interrupt naturally. The coordinator is responsible for classification, preservation, routing, stage management, protocol, visibility, and return-to-work context.

## 1.1 First-draft architecture in one view

```text
OWNER ON PHONE OR PC
        |
        v
DISCORD-FIRST EXECUTIVE EXPERIENCE
Reception | Executive Desk | HQs | Project Hubs | Approvals
        |
        v
COORDINATOR AND WORKFLOW ENGINE
Classify | Route | Stage | Prioritize | Link | Fold Back | Coach
        |
        +--------------------+--------------------+
        |                    |                    |
        v                    v                    v
MODEL WORKERS          BUSINESS SYSTEMS      PERSONAL SYSTEMS
Planner/Builder/       Apps, MCP data,        Travel, home,
Reviewer/Auditor       leads, calls, email    writing, planning
        |                    |                    |
        +--------------------+--------------------+
                             |
                             v
DURABLE STATE AND MEMORY
Operational database | Git | artifacts | semantic knowledge layer
```

## 1.2 Key strategic distinction

This is not only a system that builds applications. It is also a system that can use those applications and their connected data as an operational cockpit. A lead application can be designed and maintained by the development workflow while its live data is simultaneously summarized, monitored, reviewed, and converted into new process or development topics.

This closed loop is a core source of future leverage:

```text
BUSINESS ACTIVITY
    -> DATA AND TRANSCRIPTS
    -> INSIGHT AND HUMAN JUDGMENT
    -> PROCESS OR APPLICATION CHANGE
    -> VALIDATED RELEASE
    -> MEASURED BUSINESS ACTIVITY
```

# 2. Design Intent, Scope, and Non-Goals

## 2.1 Design intent

- Replace manual cross-tool orchestration with a persistent coordinator and explicit workflow state.
- Make resumption effortless after interruptions, device changes, travel, or overnight execution.
- Permit messy, nonlinear, incomplete input without requiring the owner to classify it first.
- Preserve one main hub for situational awareness while allowing deep navigation into branches when needed.
- Separate Business and Personal operating queues while presenting both in one unified executive frame.
- Use automated technical verification rather than treating a non-technical owner as a ceremonial implementation approver.
- Learn preferences, skills, automation boundaries, and routing judgment through governed evidence and review.
- Remain portable across model providers, memory providers, and front-end platforms.

## 2.2 In scope for the first design program

- Discord information architecture and clickable prototype.
- Executive Desk, Reception, HQ, project hub, topic, task, approval, and closeout experiences.
- Recursive parent-child organization and fold-back behavior.
- Application development workflow using multiple models and tools.
- Business data access, email triage, leads, advertisements, calls, transcripts, and operational insight.
- Personal planning and assistance as a separate operating domain.
- Context, memory, rules, skills, preferences, and observation governance.
- Automation policy learning, evidence, approval, and technical verification.
- A staged implementation plan that can be prepared before purchasing or commissioning the final host computer.

## 2.3 Explicit non-goals for the Phase 1 baseline

- Final selection of Gbrain or any other knowledge-memory provider.
- Final Discord channel count, permissions, bot commands, or visual formatting.
- Autonomous access to production systems, banking, sensitive communications, or destructive actions.
- A complete local-model strategy or distributed worker-computer network.
- Final agent prompts, model assignments, or subscription routing rules.
- A claim that every discovered feature belongs in the first implementation release.

> **Design discipline:** The operating model should be defined independently of Discord, OpenClaw, Gbrain, Claude, Codex, or any other vendor. Implementation must adapt to provider capabilities, but provider limitations should not silently become the business operating model.

# 3. User and Current Operating Context

## 3.1 Primary user profile

| Dimension | Observed need |
| --- | --- |
| Ownership | One owner/operator is expected to administer and use the private system for a long period. Employees may use applications produced by it, but not the private development and executive environment. |
| Strengths | Problem definition, broad systems thinking, process design, desired outcomes, business acceptance, and result review. |
| Constraints | Organization, detail maintenance, priority classification, repetitive no-progress sessions, protocol upkeep, and technical implementation verification. |
| Input style | Natural, associative, frequently interrupted, often delivered as raw notes or word-vomit rather than a prepared specification. |
| Interview preference | Narrow, comparative, this-or-that, multi-select, or bounded scenario questions; avoid broad open-ended prompts unless a contextual exception is justified. |
| Learning preference | Layman-oriented explanations, click-by-click execution guidance, visible progress, and automation of safe steps rather than delegation back to the user. |
| Device pattern | Frequent switching between PC and mobile, including periods when only mobile status and approval are practical. |

## 3.2 Current AI and development workflow *(v1.4 — CP-P2-A Item 0; trail entries 69/82)*

The present process is powerful but fragmented. The following stage mapping is based on the current description and should be treated as a current-state inventory rather than a final architecture:

| Stage | Current tool or model label | Current operating issue |
| --- | --- | --- |
| Ideation | Claude Code Opus 5 | Exploration occurs in long sessions with state trapped in conversation. |
| Design | Claude Code Opus 5 | Design and implementation context can blend without a formal handoff record. |
| Develop Plan | Claude Code 'Fable' as currently described | Plan quality depends on manually re-establishing context. |
| Execution | Claude Code Opus 5 managing Sonnet agents | The owner monitors multiple windows and remains the dispatcher. |
| Debugging | Cursor | Local editor, indexing, build, and security tooling add PC load and another context boundary. |
| Launch Testing | Hyperagent with Codex connection | Independent review exists, but evidence and feedback must be manually routed. |

The underlying lifecycle is sound: ideation, design, planning, execution, debugging, and validation. The system should preserve that intent while replacing tool-specific stage names with role-based abstractions so future models can be substituted without redesigning the workflow.

## 3.3 Current friction

- Three or four active projects may run in very long chat sessions without durable, structured project state.
- Manual context compaction is deferred because there is no obvious stopping point; handoff messages are created only after the context becomes visibly unusable or after deployment.
- Overnight prompts may make substantial progress, time out, fail, or wait for input without a durable checkpoint or consolidated status view.
- Progress is hidden inside narrative agent output rather than represented as verified milestones and current state.
- The PC becomes a bottleneck because browser sessions, Cursor, indexing, language servers, builds, tests, and security scanning remain local even when model inference is cloud-based.
- Email requires manual priority and effort classification, so messages accumulate until processed in large batches.
- Calls, visitors, and business-process questions interrupt development without a reliable pause-and-resume mechanism.
- The owner cannot confidently see active work while away from the workstation and therefore feels pressure to return and babysit sessions.
- Protocol and housekeeping are skipped when the user must administer them personally.

# 4. Target Experience

## 4.1 Reception

Reception is the universal front door. The owner can submit a question, raw note, meeting fragment, instruction, link, screenshot, voice transcription, business issue, or personal request without choosing a destination first.

> **Reception rule:** The user produces thoughts. The system organizes them. Classification is an operating-system responsibility, not an entry requirement.

## 4.2 Executive Desk

The Executive Desk is the global home view used whenever the owner reconnects. It combines broad situational awareness with immediate resumption context.

```text
EXECUTIVE DESK

RECENT CONTEXT
- Last active hub and topic
- What changed since the owner left
- Suggested next action

BUSINESS PRIORITY LIST
- Needs owner
- Running / Waiting / Blocked
- To-do and to-did

PERSONAL PRIORITY LIST
- Needs owner
- Running / Waiting / Blocked
- To-do and to-did

BACKGROUND ACTIVITY
- Running
- Completed
- Failed or stalled

NAVIGATION
- Business HQs
- Personal HQs
- Operating System HQ
```

Business and Personal remain separate queues so the owner decides which mode to enter only once. Both are visible within one dashboard frame so neither domain disappears from awareness.

## 4.3 Tiered hub experience

Information is presented recursively. The owner can operate at the global level, enter an HQ, inspect a project hub, open a grouped branch, or enter a focused topic. The same structural pattern and summary format applies at each level.

```text
Executive Desk
  -> Business HQ
     -> Application Development HQ
        -> AI Operating System project hub
           -> Memory Architecture topic
              -> Context Compression task
```

The owner is expected to live primarily in the relevant hub summary, monitor child activity, and enter deeper branches only when a decision, review, or close inspection is useful.

## 4.4 Status without babysitting — the canonical state model

*(v1.1: replaces the v1.0 status table, which conflated operational state with attention and whose own example views used undefined values. Consensus C-07 with verifier modification.)*

Every work object carries these independent canonical dimensions. All documents, views, databases, and prompts use these terms; no other state vocabulary is authoritative.

| Dimension | Canonical values | Question answered |
| --- | --- | --- |
| `stage` | Discovery / Design / Planning / Execution / Validation / Integration / Archived | How mature is the work? |
| `work_status` | Queued / Running / Waiting / Blocked / Paused / Failed / Completed | What is happening operationally? |
| `attention` | None / Briefing / Hub / Needs Owner / Critical | How urgently does this reach the owner? |
| `focus` | Foreground / Background / Queued / Parked | How prominent is it in the current interaction? |
| `health` | Healthy / Stale / Unknown / Degraded | Can the current picture be trusted? (derived; used chiefly in rollups) |

Rules that keep the dimensions honest:

- "Needs the owner" is an **attention** value, never a work status: a topic can be `Waiting` on a dependency while `attention: Needs Owner` asks for a decision, and the two facts stay separate.
- User-facing display labels (for example **Active**, **Needs You**, **Working**) are permitted, but each label maps deterministically to underlying canonical values; renderers may not invent states.
- `Queued` appears in two dimensions with different meanings (queued work vs queued interaction focus); any surface showing both must disambiguate ("queued (work)" vs "queued (focus)").
- Rule/preference/skill lifecycles use their own vocabulary (Proposed / Active / Inactive / Retired — section 10.4) and do not overload these dimensions.

> **Visibility requirement:** The owner should never need to open a worker chat solely to determine whether work is progressing, waiting, blocked, failed, completed, or waiting for the owner.


## 4.5 Attention model

The system separates interruption from attention. Most events should be visible without stealing focus.

| Level (canonical `attention` value) | Meaning | Typical presentation |
| --- | --- | --- |
| Critical | Immediate physical, legal, financial, security, or similarly consequential danger. | Direct push/mention and prominent alert. |
| Needs Owner | A response or decision is required, but the current topic does not need to be forcibly interrupted. | Badge, mention, the Needs-You queue (display label), and project-hub prominence. |
| Hub | Useful progress or a non-blocking issue should be visible when the owner next opens the relevant hub. | Recent Events and branch status. |
| Briefing | Routine completion, safe retry, first overdue reminder, and other low-urgency events. | Next briefing or digest. |
| None | Recorded for history only. | Event log. |

*(v1.1: level names aligned to the canonical `attention` enum in 4.4; "Needs Attention" as a term is retired to end its collision with the old status vocabulary.)*

Current default calibration:

- Successful background completion with no owner action: Hub.
- Useful non-blocking improvement: Hub.
- Decision required: Needs Owner, not a forced context switch.
- Failed job already in a safe retry: Briefing.
- First overdue internal assignment: Briefing.

# 5. Conceptual Architecture

## 5.1 Layered architecture

| Layer | Responsibility | Illustrative components |
| --- | --- | --- |
| Executive Experience | What the owner sees and uses. | Reception, Executive Desk, HQ views, project hubs, topic summaries, approvals, mobile/desktop rendering. |
| Operating Model | How work is organized and governed. | Domains, HQs, initiatives, topics, tasks, stages, statuses, focus, fold-back, protocol, to-do/to-did. |
| Coordination and Intelligence | How input becomes routed work and model activity. | Coordinator, recommendation engine, workflow engine, specialist agents, model router, schedulers. |
| Durable State and Memory | What survives sessions, compaction, provider changes, and time. | Operational database, topic checkpoints, decision records, Git, artifacts, semantic memory/knowledge graph. |
| Integration | How external data and actions enter the system. | MCP servers, email, calendar, internal web tools, lead systems, call transcripts, ad platforms, GitHub. |
| Infrastructure | Where services execute and how they are reached. | Dedicated Mac host, cloud models, optional local models, containers, secure networking, backups. |

## 5.2 Source-of-truth separation

| Information type | Recommended authoritative store | Why |
| --- | --- | --- |
| Topic hierarchy, stage, status, assignment, approvals, events | Structured operational database | Requires exact state, queries, rollups, and deterministic transitions. |
| Application code, architecture docs, plans, tests, releases | Git repository | Versioned, auditable, reviewable, and tied to implementation. |
| Semantic relationships, recurring knowledge, observations, preferences, skills | Gbrain or equivalent knowledge-memory layer | Supports retrieval and relationship discovery, but should not be the sole transaction-state store. |
| Conversation and interaction history | Discord/OpenClaw transcripts with references | Useful evidence and continuity, but too unstructured to be the only project record. |
| Files, reports, screenshots, call audio, data extracts | Controlled artifact storage with metadata | Supports provenance, permissions, retention, and linking to topics. |

> **Memory-provider position:** Gbrain may become critical, but the design should first define the memory contract the operating system requires. Gbrain is a candidate implementation of that contract, not the owner of every type of state.

### 5.2.1 Ownership matrix and global identity contract *(v1.1 addition — consensus C-06 with verifier modification)*

Every persistent object type has exactly **one canonical store**; all other appearances are derived copies or references back to the canonical record.

| Object type | Canonical store | Notes |
| --- | --- | --- |
| Topic, Task, stage/status/attention/focus state, Event, Assignment, Checkpoint, review-queue items | Operational database | The workflow brain. Owns all IDs. |
| Decision (choice, rationale, alternatives) | Operational database | May be *mirrored* into Git docs and semantic memory, but the DB record owns the authoritative choice. |
| Rule / Preference / Skill / Automation Policy registries (approved state) | Operational database | The semantic layer holds derived, searchable projections only. |
| Code, plans, design docs, tests, releases | Git repository | Versioned artifacts; referenced by DB records. |
| Observations, semantic relationships, retrieval knowledge | Knowledge-memory layer (Gbrain or equivalent) | Always derived or weak-evidence content with back-references; never the sole home of approved policy or workflow state. |
| Conversation transcripts | Platform transcripts with references | Evidence, not record. |
| Files, reports, audio, exports | Artifact storage with metadata | Provenance and retention rules apply. |

**Global identifier contract:** every persistent object carries a stable, store-independent ID minted by the operational database, plus object type, canonical-store pointer, `schema_version`, provenance, related-object IDs, and synchronization status. IDs survive archive, merge, and correction operations via aliases. Every surface (Discord views, Git artifacts, knowledge entries, logs) references these IDs.

## 5.3 Three operating capabilities

| Capability | What it does |
| --- | --- |
| Create | Designs, builds, tests, launches, and maintains applications and processes. |
| Operate | Uses connected data and applications to brief, classify, monitor, prompt, analyze, and assist daily work. |
| Improve | Observes outcomes and behavior, proposes process/rule/skill/application changes, and routes those proposals through governed workflows. |

# 6. Information Architecture and Object Model

## 6.1 Structural hierarchy — typed roles on an arbitrary-depth tree

*(v1.1: reconciles the v1.0 fixed five-level hierarchy with the recursive hub model, which the baseline's own examples exceeded. Consensus C-09 with verifier modification.)*

The structure is one recursive work tree of arbitrary depth. The familiar level names are **semantic roles a node plays, not fixed database slots**:

```text
DOMAIN  (anchoring role: permissions and operating context)
  -> HQ / CATEGORY  (anchoring role: recurring management area)
     -> any depth of INITIATIVE / TOPIC / GROUP nodes
        -> TASK  (leaf role)
```

| Role | Purpose | Obligations the role carries |
| --- | --- | --- |
| Domain | Separates broad operating context and permissions. | Permission boundary; never nested inside another Domain. |
| HQ / Category | Central management area for a recurring functional domain. | Dashboard, registry, and filtered views. |
| Initiative / Project | Committed outcome with a goal and eventual stable or completed state. | Full hub obligations: kickoff, checkpoint, closeout, rollups. |
| Topic / Group | Focused body of work or thought; may supervise children at any depth. | Kickoff record, checkpoint, closeout package. |
| Task / Focused Issue | Concrete executable or decidable unit. | **Leaf by default**: carries only state and completion criteria; no kickoff/closeout overhead; may not supervise children. |

**Promotion rule:** when a Task turns out to need durable context, its own lifecycle, or children, it is *promoted* to a Topic (a recorded correction operation — section 7.6) rather than forced to stay the wrong type. Protocol weight therefore follows node type, and deep nesting (Customer Portal → Launch Audit → Interface Issues → specific defect) is legal without every leaf inheriting heavyweight ceremony.

## 6.2 Recursive hub model

Every meaningful non-leaf object can present a hub-style summary and can supervise children. A topic is therefore both a focused conversation and, when needed, a small project hub.

```text
Houseboat Business
  -> Lead Generation
     -> Advertising Performance
     -> Incoming Call Review
        -> Call Rating Prompt
        -> Handling Insight
     -> Follow-Up Automation

AI Operating System
  -> Discord Interface
  -> Global Rules
  -> Memory Architecture
     -> Context Compression
     -> Topic Checkpoints
  -> Application Audit
     -> Interface Bugs
     -> Data Bugs
     -> Security Bugs
```

## 6.3 Persistent object types

| Object | Definition | Important metadata |
| --- | --- | --- |
| Observation | Weak evidence that something may matter; it does not change behavior by itself. | Source, date, category, confidence, related topics, repetition count. |
| Topic | A body of work or thought that deserves durable context and lifecycle management. | Parent, children, type, stage, status, focus, owner, summary, next action. |
| Task | A concrete action, check, or decision inside a topic. | Assignee, state, due/priority, evidence, completion criteria. |
| Decision | An explicit choice with rationale and impact. Consequential decisions carry a DEC-02 falsifier — the evidence that would reverse them — or a reasoned `unknown` with a review trigger. | Decision maker, alternatives, reason, affected objects, reversal path. |
| Rule | Approved operating constraint or required behavior. | Scope, strength, status, last applied, dependencies, review date. |
| Preference | Approved user preference that shapes experience but may permit exceptions. | Scope, confidence, last applied, exception history, review date. |
| Skill | Approved reusable procedure or ability invoked in recurring situations. | Trigger, inputs, steps, outputs, validation, scope, usage history. |
| Artifact | A durable output linked to work. | Version, owner, provenance, location, related topic, retention. |
| Event | A timestamped change or activity used in recent-history views and audits. | Actor, action, object, previous/new state, evidence. |
| Checkpoint *(v1.1)* | The durable resumption record for a topic (see 15.2–15.3). | Protected vs generated fields, version history, source links, schema_version. |
| Worker Session *(v1.1)* | A model/agent session executing on behalf of a topic. | Identity, credentials scope, assigned topic/task, heartbeat, execution journal, last confirmed side effect. |
| Assignment *(v1.1)* | Delegated work tracked to closeout (human or agent). | Assignee, due date, reminder policy, completion claim, verification state. |
| Automation Policy *(v1.1)* | Approved authority for a class of automatic action within a scope. | Action class, scope, evidence history, expansion state, review date. |

*(v1.1: all persistent objects additionally carry the global ID contract fields of 5.2.1, including `schema_version` — verifier finding G-03.)*

## 6.4 Broader categorization

Topic and state are not sufficient by themselves. Every object also belongs to a broader category and may have subcategories. This supports domain-specific HQs, filtered dashboards, permissions, memory retrieval, and reporting.

- Business versus Personal is the top-level example.
- Business may contain Application Development, Data, Sales and Leads, Operations, Communications, and Company Knowledge.
- Operating System may contain Rules, Preferences, Skills, Automation Policies, Integrations, and System Health.
- Knowledge can be categorized by communication style, formatting, existing applications, business processes, people, data sources, and other future taxonomies.

# 7. Topic Lifecycle, State, and Fold-Back

## 7.1 Stage is state, not location

A topic remains the same topic while its stage changes. The owner does not move between separate Discovery, Design, or Planning locations. The coordinator maintains stage labels as understanding evolves.

```text
Discovery -> Design -> Planning -> Execution -> Validation -> Integration -> Archived
       \         ^          \          ^
        \--------|-----------\---------|

Stages may be skipped, repeated, or revisited when new information changes the work.
```

| Stage | Purpose |
| --- | --- |
| Discovery | Clarify the issue, evidence, desired outcome, boundaries, and unknowns. |
| Design | Define structure, user experience, architecture, process, or operating approach when design is required. |
| Planning | Convert the selected approach into sequenced actions, responsibilities, dependencies, and validation criteria. |
| Execution | Perform implementation, data work, drafting, analysis, or other production activity. |
| Validation | Test, review, audit, compare, or otherwise establish whether the result is acceptable. |
| Integration | Fold the accepted outcome into the parent, update records and artifacts, and recalculate status and next action. |
| Archived | Remove the topic from active workload while retaining history, evidence, and reactivation capability. |

## 7.2 Stage, status, and focus are independent

| Dimension | Question answered | Examples |
| --- | --- | --- |
| Stage | How mature is the work? | Discovery; Planning; Validation. |
| work_status | What is happening operationally? | Running; Waiting; Blocked; Paused; Completed. |
| Focus | How prominent is it in the current interaction? | Foreground; Background; Queued; Parked. |

A topic can therefore be in Planning, working in the background, while another topic is in Discovery and is the foreground focus.

## 7.3 Topic kickoff

When a new topic is created, its initial message must preserve enough context for future continuation without reconstructing the origin conversation.

```text
TOPIC
Responsive Presentation Strategy

ORIGIN
Raised during Discord architecture discussion after noting that desktop and mobile
have different formatting constraints.

WHY THIS EXISTS
The system needs one source of truth with device-appropriate presentation.

CURRENT UNDERSTANDING
Duplicated channels would create synchronization and maintenance problems.

OPEN QUESTIONS
- What can Discord render differently by context?
- When would a companion dashboard justify leaving Discord?

PARENT / RELATED
AI Operating System -> Discord Interface

INITIAL STAGE
Discovery

RECOMMENDED NEXT
Compare Discord-only, Discord Activity, and companion-web approaches.
```

Structured owner interviews (onboarding, kickoff, level-up) checkpoint per MEM-09: each answer persists when given, resumption is from the persisted record, and the record inherits data-class, provenance, versioning, correction, and protected/generated-field rules.

## 7.4 Fold-back

A child topic is not fully complete until its accepted outcome is integrated into its parent. Fold-back maintains low active-topic counts and prevents a hub from accumulating unresolved fragments.

*(v1.1 — consensus C-25):* fold-back has a defined **actor and trigger**: the coordinator proposes fold-back when a child's completion criteria are met; acceptance comes from the owner or from a standing rule that authorizes automatic fold-back for that action class. The coordinator performs the integration and records it as events on both child and parent.

```text
Child work complete
  -> validation evidence attached
  -> closeout summary generated
  -> impact on parent identified
  -> parent summary, decisions, plans, or artifacts updated
  -> follow-up topics created only when justified
  -> child moves to To-Did / archive
  -> parent suggested-next and stability recalculated
```

| Closeout element | Required content |
| --- | --- |
| Outcome | What was decided, created, corrected, or learned. |
| Evidence | Tests, audits, comparisons, reviews, or reasoning supporting the outcome. |
| Parent impact | Exactly what changes in the parent goal, plan, architecture, rules, or state. |
| Unresolved items | Anything deliberately left open. |
| New topics | Any justified follow-up work and its placement. |
| Return state | Where the parent resumes and what the next action becomes. |

## 7.5 Stable state and housekeeping

A hub is stable when completed children are integrated, blockers are resolved or intentionally accepted, summaries match current reality, and the next action is valid. A project with dozens of active topics indicates unintegrated work or excessive branching and should trigger a housekeeping review.

The user should not be responsible for housekeeping. The coordinator should surface unintegrated children, stale topics, missing closeouts, duplicated work, and unresolved decisions, then guide the corrective action.

*(v1.3 — CP-v1.2-B, CPB-03)* Housekeeping has a standing trigger: the AUD-03 scheduled read-only self-audit (default weekly, owner-tunable) scores structural health on a versioned rubric and surfaces the top gaps with next steps. The score is advisory prioritization input — it cannot self-attest independent controls and never passes a gate by itself.

## 7.6 Correction primitives *(v1.1 addition — consensus C-11)*

A recommendation-learning system must expect its own routing to be imperfect, so repair is cheap and first-class. The coordinator supports, as recorded operations that preserve history and repair links and rollups:

- **Re-parent** — move a node elsewhere in the tree.
- **Merge** — combine duplicate or overlapping nodes, aliasing IDs.
- **Split** — divide a node that turned out to contain two bodies of work.
- **Reclassify / Promote / Demote** — change a node's type (including Task→Topic promotion, 6.1).
- **Duplicate-link** — record that two nodes are related without merging them.
- **Archive** — remove from active views with context preserved.

The owner-facing gesture is one action — **"Wrong place"** — which triggers a re-routing recommendation. Every correction optionally feeds a low-weight calibration observation into the WF-11 learning loop; corrections are among the highest-value learning evidence the system receives.

## 7.7 Rejected work is a first-class ending *(v1.1 addition — consensus C-47; decision trail 12)*

Explored-and-declined ideas close as **Rejected (no-build)** — a terminal outcome distinct from Completed and from silent abandonment. The record keeps the reasoning, appears in To-Did history as a decision made (not work lost), and remains searchable so the same idea returning later starts from the prior analysis instead of from zero.

# 8. Interaction, Routing, and Focus Management

## 8.1 Interruptions are routing events

An interruption should not force the owner to choose between losing an idea and derailing the current work. The coordinator evaluates the new input, preserves it, recommends placement, and either continues or creates a linked branch.

| Classification | Typical behavior | Example |
| --- | --- | --- |
| Immediate change | Apply within the current topic and continue. | Rename a section or correct an obvious wording issue. |
| Observation / parked item | Preserve as evidence or future consideration; no active topic yet. | A formatting preference may be emerging. |
| Child topic | Create a local branch required to complete the current topic. | Design a cost display inside the Discord interface. |
| Sibling or parent topic | Create work that affects a broader area or multiple branches. | Usage and cost tracking affects several interfaces and services. |
| Blocking topic | Create a linked topic and recommend resolving it before continuing. | Memory ownership must be decided before finalizing context-resumption behavior. |

## 8.2 Recommendation with alternatives

Multiple classifications may be valid. The coordinator should present its recommendation and the meaningful alternatives, allow the owner to choose, and learn from the rationale when the choice differs.

```text
ROUTING RECOMMENDATION

Recommended: Create sibling topic under AI Operating System
Reason: The issue affects multiple Discord components and future dashboards.

Other valid options:
- Keep inside the current Discord Interface topic
- Create a child topic for cost display only

Choose:
[Use recommendation] [Current topic] [Child topic]
```

The learning target is not a fixed answer such as always create a child. It is the owner’s judgment about scope, impact, urgency, and appropriate granularity.

### 8.2.1 Staged adaptive routing *(v1.1 addition — consensus C-11/D4 with verifier modification; honors decision trail 28)*

Routing prompts are governed in two tiers:

1. **Recommend-and-confirm** (the trail-28 behavior) applies to all routing initially, and permanently to anything high-impact, blocking, irreversible, cross-domain, or poorly calibrated.
2. **Act-with-receipt** — the coordinator files per its own recommendation and shows a one-line receipt with a one-tap "Wrong place" correction — unlocks *per routing class*, only after (a) the correction primitives of 7.6 exist and (b) **measured** correction/reversal rates for that class demonstrate accuracy. Raw model confidence is never the unlock criterion; observed outcomes are.

Routing-prompt volume per captured input is a tracked measure (section 18.1) so this calibration is visible rather than felt.

*(v1.3 — CP-v1.2-B, CPB-11)* Rollout schedule per AUT-12: each eligible action class advances bounded-low-volume-full-review → monitored → unsupervised-where-permitted, on measured correction/reversal/failure outcomes, risk class, and calibrated confidence; raw model confidence never unlocks authority; stage durations are minimized when evidence supports (DP-027). Initial volume is a tunable pilot parameter.

## 8.3 Blocking behavior

Blocking is advisory but explicit. The owner may override, but ordinary design-work overrides use strong informational friction: the system must show the blocker, predicted consequences, likely invalidated work, and expected rework before the owner acknowledges the risk. The friction is understanding the consequence, not repeated confirmation prompts.

```text
BLOCKER IDENTIFIED

This issue must be resolved before the current recommendation can be trusted.
Linked topic: Memory Architecture

Why it blocks:
The current design assumes a durable context owner that has not been selected.

If you continue anyway:
- Some work may be invalidated.
- Expected rework: medium.
- Context-loss risk remains unresolved.

[Open blocker] [Continue anyway] [Park current topic]
```

*(v1.1 — consensus C-36):* overrides are logged with the consequence summary shown, and repeated same-class overrides (initially three) open a lightweight review asking whether that blocker class should stop blocking — the system adapts rather than nags, and override outcomes (rework or none) calibrate future consequence predictions.

## 8.4 Focus and return

One topic is normally foreground, while several others may work in the background. When a blocker requires a focus switch, the system records the pause point and later returns the owner to the exact parent context with the new resolution integrated.

- Record where the owner was and why the topic paused.
- Record which child or sibling must resolve.
- Carry the accepted outcome back to the original topic.
- State what changed because of that outcome.
- Present a direct return link and the next action.

## 8.5 Protocol coaching

The system should actively protect approved protocol because the owner has stated that self-managed process will be skipped. Coaching should focus on meaningful deviations, not generic productivity commentary.

- Detect attempts to bypass required discovery, validation, fold-back, or approval gates.
- Explain the consequence of the deviation and offer an override when permitted.
- Ask why when the owner repeatedly chooses a different classification, scope, or process so the recommendation model improves.
- Do not flood the owner with workflow-management coaching that is already obvious from the dashboard.


Structure additions use the ORG-07 advisory three-question test; capture is never gated.

## 8.6 Decision-prompt quality

The system must not manufacture false choice by presenting a partial option, a better partial option, and an obvious all-inclusive option. Decision prompts should use one of three methods:

1. **Genuine tradeoff:** every option solves the problem but accepts a different cost.
2. **Boundary calibration:** ask where behavior should change rather than whether the owner wants an obviously complete solution.
3. **Expert default:** when one approach is plainly superior and no material preference tradeoff exists, state the default and ask only for exceptions.

When multiple classifications are genuinely valid, the coordinator recommends one, presents the meaningful alternatives, records the owner's selection, and selectively asks for rationale when it will improve future judgment.

Consequential decisions carry a DEC-02 falsifier — the evidence that would reverse them — or a reasoned `unknown` with a review trigger.

# 9. Navigation, Dashboards, and Presentation

## 9.1 Breadcrumb-first navigation

Every coordinator response should show a compact breadcrumb so the owner remains oriented while moving among levels and topics.

```text
Business > Application Development > AI Operating System > Memory Architecture
```

Full navigation controls should appear on operational messages such as summaries, blockers, approvals, handoffs, and closeouts. Ordinary conversation should remain visually light.

## 9.2 Required navigation directions

- Up to the parent hub.
- Down into children and focused tasks.
- Sideways to related topics and sibling dependencies.
- Back to the previously visited location.
- Directly to the global Executive Desk or the nearest HQ.
- Directly to anything that needs the owner and a clear statement of why.
- **Recall-by-description** *(v1.1 addition — consensus C-13)*: from any surface, retrieve any topic, task, decision, or artifact by free-text or semantic description ("the houseboat ad idea from last week", a person, an approximate date, an outcome). Results show why each item matched, its current location and status, and a direct link. A system that files content the owner did not place must support recall without navigation — this is the completion of the capture promise, not a search feature.

## 9.3 Standard project-hub view

*(v1.1 — consensus C-10 with verifier modification: a hub's own `stage`/`work_status` are explicit local state, never mechanically overwritten by children; what rolls up from children are **derived** indicators — counts by status, highest attention level, blocking/stale/failed counts, and an effective hub health value. The mock below uses the canonical model.)*

```text
AI OPERATING SYSTEM

GOAL
Create a persistent AI operating environment accessible from phone and PC.

STAGE Design | STATUS Running | HEALTH Healthy
CHILDREN 4 active: 2 Running, 1 Waiting, 1 Blocked | Highest attention: Needs Owner

RECENT EVENTS
- Memory Architecture identified a blocker.
- Global Rules advanced to Design.
- Mobile Presentation topic was created.

SUGGESTED NEXT
Resolve Memory Architecture because it affects context and resumption.

NEEDS OWNER
2 decisions

ACTIVE BRANCHES                stage      work_status  attention
- Discord Interface            Design     Running      None
- Global Rules                 Design     Running      None (focus: Background)
- Memory Architecture          Discovery  Waiting      Needs Owner
- Installation Plan            Planning   Waiting      None

TO-DO
Memory Architecture
  -> Choose authoritative checkpoint owner

TO-DID
- Defined Reception
- Defined recursive topic model
- Defined fold-back behavior

[Full summary] [Recent log] [Open needs-owner] [View hierarchy]
```

## 9.4 Layered to-do and to-did

The default task list should show the topic and its immediate action together, rather than presenting a flat list of tasks or only topic names.

```text
TO-DO

Memory Architecture
  -> Choose the authoritative memory source

Discord Interface
  -> Review compact mobile summary format

Installation Plan
  -> Waiting on architecture decision

TO-DID

Topic Lifecycle
  -> Stage/status/focus model consolidated
```

## 9.5 Device presentation

Mobile and desktop should display the same underlying state through different render profiles. Duplicated channels or mirrored records should be avoided because they create synchronization and maintenance risk.

| Mobile default | Desktop default |
| --- | --- |
| Compact status, needs-owner items, suggested next, short event log, direct action links. | Full branch table, richer recent log, detailed summary, artifacts, history, and related-topic map. |
| Short cards and progressive disclosure. | Expanded tables and comparative views. |
| Approval and routing decisions. | Detailed technical evidence and artifact inspection. |

A companion dashboard is justified only when Discord cannot provide the required information density, visualization, filtering, or interaction. It should be an extension opened by direct links, not a competing home platform.

# 10. Learning, Preferences, Rules, and Skills

## 10.1 Observations are intentionally weak

The system may automatically observe patterns, but an observation must not silently become a rule, preference, or skill. Observations enter a proposal queue and may mature into a topic when evidence or importance justifies discussion.

```text
OBSERVATION
The owner requested click-by-click technical guidance.

EVIDENCE
11 comparable interactions.

POSSIBLE INTERPRETATION
A reusable guided-deployment skill may be useful.

CURRENT EFFECT
None. Existing behavior remains unchanged.

RECOMMENDATION
Create Skill Topic in Discovery.
```

The LRN-10 default threshold applies: three distinct, verified occurrences of the same normalized manual task within an owner-tunable window raise an automation-candidate observation — weak evidence only, never a direct behavior change.

## 10.2 Shared workflow for system changes

Preferences, rules, skills, and automation policies use the same topic workflow as other work:

```text
Observation or manual proposal
  -> proposal queue
  -> topic created in Discovery
  -> scope and impact review
  -> Design / Planning as applicable
  -> validation or peer/model audit
  -> implementation
  -> active registry
  -> usage monitoring and periodic review
  -> inactive/archive/delete decision
```

## 10.3 Scope is mandatory

Every rule, preference, skill, and automation policy must declare where it applies. Candidate scopes include:

- Global
- Business or Personal
- Interview and discovery work
- Application development
- Writing and communication
- Discord presentation
- Email handling
- Specific HQ, initiative, project, topic type, application, or user population

The system should be able to identify a contextual exception without silently violating the active rule. It may ask to use a one-time exception or reopen the preference topic to refine the rule harness.

## 10.4 Lifecycle and decay

| State | Meaning |
| --- | --- |
| Proposed | An observation or user request has created a candidate topic; no operating effect. |
| Active | Approved and currently used within declared scope. |
| Inactive | Preserved but not applied; may be reactivated. |
| Retired | Retained for history and evidence but removed from normal operational views. *(v1.1: renamed from "Archived," which is now reserved for the topic stage.)* |
| Deleted | Permanently removed when retention is unnecessary or harmful; should not be the default. |

A configurable inactivity threshold, initially proposed as 90 days, should trigger review rather than automatic deletion. The review should consider last application, continuing relevance, overlap, contradictions, recommendations, and whether the item should remain active, become inactive, merge with another item, or archive.

CAP-04 economic retirement-review flags are raised at AUD-03 over a declared evaluation window with the full value model; flags open review, never auto-disable, and protected control classes are exempt from cost-only retirement.

## 10.5 Recommendation-learning loop

```text
Evidence and observations
  -> coordinator recommendation with alternatives
  -> owner decision
  -> optional reason when the decision differs
  -> later outcome and reversal evidence
  -> calibrated future recommendations
```

Rejected ideas are useful evidence. The system may ask why a proposal was rejected and whether it should continue exploring improvements in that area or stop proposing similar changes until conditions change.

*(v1.3 — CP-v1.2-B, CPB-04)* The LRN-09 improvement ritual is the operating cadence of this loop: a system-prepared shortlist, at most one accepted improvement artifact per cycle (zero is valid), smallest-machinery selection, and a decision-log entry. Urgent corrective work is never held for the ritual. Adoption is preferred to building per §17.0.

## 10.6 Knowledge organization

The learning layer should support broad knowledge categories and subcategories such as formatting, speech pattern, interview style, existing applications, business processes, data sources, people, decision history, and model/tool behavior. The taxonomy must be navigable through HQs while also supporting semantic retrieval across categories.

# 11. Automation, Approval, and Verification Harness

## 11.1 Approval should match the owner’s actual judgment

| Stage or decision type | Owner value | Preferred control |
| --- | --- | --- |
| Problem definition and desired outcome | High | Direct owner participation and approval. |
| Business process design and user behavior | High | Direct owner participation, comparisons, and acceptance criteria. |
| Architecture and implementation mechanics | Limited | Independent technical review, tests, and evidence; owner receives consequences in layman terms. |
| Result review and business acceptance | High | Owner reviews visible behavior, process effect, and whether the original problem is solved. |
| Production-risk actions | High consequence even when technical knowledge is limited | Explicit approval with business impact, verification evidence, rollback, and residual risk. |

## 11.2 Approval harness

The system should not ask the owner to certify technical details the owner cannot verify. Technical acceptance should come from a harness that may include:

- Independent model or peer review.
- Automated tests and regression checks.
- Static analysis, linting, type checking, and security scanning.
- Dependency and license checks.
- Database migration and rollback testing.
- Staging deployment and user-path validation.
- Comparison with the approved plan and scope.
- Audit evidence and explicit remaining risk.

*(v1.1 — consensus C-14 with verifier modification):* the harness is not an optional checklist; it is governed:

- **Risk tiers with mandatory minimums.** Each application class (internal tool / employee-facing / customer-facing or sensitive) defines the minimum evidence required before approval cards render. Higher tiers add independent review, staging validation, and rollback rehearsal.
- **A named owner.** The harness is itself a governed system topic — built, versioned, and audited through the same lifecycle it enforces.
- **Tamper-evident evidence.** Deterministic checks write to an append-only evidence store the builder cannot modify; approval cards render **from that store**, never from builder narrative. Hosted CI is the default implementation, but any arrangement achieving independence and tamper resistance qualifies.
- **Honest coverage disclosure.** Every approval card states which checks ran, which did not ("2 of 6 configured"), failures or waivers, evidence source, and residual risk.
- **Verified evidence only.** Evidence counted toward automation-policy expansion (11.3) must be harness-verified, never self-reported. Approval dwell time is recorded so rubber-stamping becomes visible.

```text
DECISION REQUIRED

Business effect
New quotes default to 30-day expiration; existing quotes remain unchanged.

Technical recommendation
Add a nullable expiration field and calculate it for new quotes.

Verification
- Architecture review: passed
- Security review: passed
- Migration test: passed
- Rollback test: passed

What the owner is approving
Business behavior and rollout effect, not the database implementation.

[Approve behavior] [Change behavior] [Open technical evidence]
```

## 11.3 Action-class automation policies

Automation should be learned separately by action class and scope. Initial policies may be conservative, then expand through accumulated evidence rather than one-off success.

| Action class | Initial policy | Potential mature policy |
| --- | --- | --- |
| Update internal topic status | Automatic | Automatic. |
| Create local child task | Automatic within approved scope | Automatic with event log. |
| Fold validated documentation into parent | Review initially | Automatic after repeated clean outcomes. |
| Add dependency or change architecture | Approval required | Likely remains approval-required. |
| Deploy to staging | Approval initially | Automatic after harness passes for low-risk applications. |
| Deploy to production | Approval required | Scope-specific; likely manual for customer-facing or sensitive systems. |
| Modify production data | Approval required | Manual except narrowly defined, reversible maintenance actions. |
| Merge to mainline *(v1.1)* | Interim rule: one active implementation branch per repository; merge requires auditor sign-off | Multi-branch merge/integration authority is an implementation-backlog item with its own release gate (consensus C-18); nothing in this baseline implies autonomous merge/deploy is already governed. |

When evidence is sufficient, the system creates an Automation Policy topic in Discovery. It does not silently widen authority.

Action-class policies define each class's maximum permitted autonomy under AUT-12; classes requiring persistent owner judgment remain so by design.

## 11.4 Branching authority

A topic may create local supporting children automatically when the work is within scope, reversible, low risk, and necessary to complete the parent. It escalates upward when the discovered work changes parent assumptions, affects siblings, expands cost or time materially, creates a new category, or introduces external consequences.


## 11.5 Delegation and accountability

Delegation transfers execution, not accountability. The coordinator continues tracking an assignment until its completion criteria are satisfied, the owner explicitly accepts the result, or the assignment is deliberately cancelled.

Delegation policies are scoped by person and assignment type. They may vary by internal/external recipient, routine/sensitive work, business area, due date, consequence of delay, and approved communication authority.

```text
Assignment created
  -> assignee and due date recorded
  -> reminder policy applied
  -> response monitored
  -> completion claim received
  -> evidence checked when possible
  -> verified, owner-accepted, or review-required closeout
```

## 11.6 Completion claims and verification

A statement such as “Done” is a completion claim, not automatic proof. The system records one of three closeout modes:

| Closeout mode | Meaning |
| --- | --- |
| Verified completion | Objective evidence satisfies the approved completion criteria. |
| Owner-accepted completion | Verification is incomplete, but the owner chooses to trust the assignee and close the item. |
| Needs review | Evidence is missing, contradictory, or operationally concerning. |

Automatic verification is initially read-only. The coordinator may inspect connected systems for expected records, fields, files, dates, or events. If verification would require questioning, correcting, or confronting an assignee, the system prepares the evidence and a proposed action but defers the employee-facing communication to the owner unless a later scoped policy authorizes it.

High-impact assignments may require owner business acceptance even after technical or factual checks pass.

## 11.7 Reconciliation after completion

Completed work remains historically intact but can be reconciled against later evidence:

- Harmless changes update the archived record without reopening the task.
- A clear violation of completion criteria reopens the task and raises its attention level to Needs Owner.
- A material but ambiguous change creates a review item.
- The original To-Did event remains preserved; history is appended, not rewritten.

# 11A. Protection Layer: Identity, Trust, Data, and Resilience *(v1.1 addition)*

The v1.0 baseline trusted everything by default: any message from the owner's Discord account was the owner; any content was safe to reason over; any "passed" was true; and a silent system was assumed healthy. This section completes the concept with its protection layer. These are **concept-level safety constraints** (verifier framing note), not implementation detail — deferring them would poison Phase 2 design. Discord-first survives *because* of this layer, not despite it.

## 11A.1 Identity and authority (consensus C-01 with verifier modification)

- Discord input is a **presentation-layer signal** that binds to an authenticated owner identity with device/session binding; the channel is never the authority itself.
- Consequential action classes (production deploys, outbound communications, money, data deletion, authority expansion) require **risk-tiered step-up confirmation** outside the ordinary Discord message action — a passkey/biometric prompt or protected web confirmation. Routine approvals stay one-tap; "outside Discord" must not mean a cumbersome second device for everything.
- An independent **kill/revoke control** suspends all write authority, delegation, and outbound actions immediately; a documented recovery path restores control after credential loss; an **emergency read-only mode** keeps state visible while authority is suspended.
- Discord account hardening (MFA, session review) is a Stage 0/1 precondition, not advice.

## 11A.2 Input trust (consensus C-02 with verifier modification)

Every input event carries five fields: `origin`, `trust_class`, `instruction_authority`, `sensitivity_class`, `verification_state`. Trust and permission-to-instruct are distinct — internal-system content is not automatically instruction-bearing.

**The trust rule:** external content — email bodies, call transcripts, lead/ad data, web pages, retrieved documents, tool outputs — is *data to be summarized and analyzed, never instructions to follow*, unless an explicit approved policy grants instruction authority. Agents processing untrusted content run with reduced tool scopes and isolated context boundaries, and untrusted content cannot directly trigger rule/skill/policy proposals or outbound actions. Trust class is a first-order dimension of the Phase 2 Decision Engine input schema.

## 11A.3 Data classification and rendering (consensus C-20 with verifier modification)

Data classes (secrets/credentials, health, personal-financial, employee PII, customer PII, business-sensitive, operational/general) each define rules for collection, storage, retention, model access, Discord rendering, redaction, notification preview, export, and deletion. Defaults: operational and status content renders freely; **restricted classes render as masked metadata plus an authenticated deep link** into the controlled store; full rendering of a restricted class requires a scoped, owner-approved policy — never convenience alone. Notification previews are stricter than in-channel views. Enforcement lives in the system's presentation logic, not owner discipline.

## 11A.4 Action log (consensus C-21)

An append-only, tamper-evident action log records identity events, recommendations, approvals, overrides (with the consequence summary shown), tool calls, external communications, data writes, deployments, policy/registry changes, verification results, failures, retries, and correction operations — each with true internal actor/session identity and the applicable model, provider, tool, policy, and schema versions. The central logger owns writes; workers can submit events but never edit or delete history. The log must be sufficient to reconstruct an overnight autonomous session end-to-end, and the hub "Recent log" views render from this same store.

## 11A.5 Resilience (consensus C-22)

Before the system is allowed to become the owner's externalized memory: automated versioned backups of all authoritative stores with **periodic system-verified restore tests** (backup success without restore proof counts as no backup); an **independent watchdog** — outside the host and outside Discord — that notifies the owner's phone when the coordinator stops checking in, so a dead system can never impersonate a quiet one; export capability; a documented recovery runbook; and degraded read-only access to current topics and checkpoints when the coordinator is down. All system-managed per WF-12 — never owner-administered.

## 11A.6 Consequential actions and retries (verifier finding G-02)

Every consequential external action uses an action ID / idempotency key where the target supports it, records preconditions, captures an execution receipt, and reconciles post-state before any retry. When an outcome is uncertain (the worker died between acting and recording), automatic retry **stops** and a Needs-Review item is raised — recovery automation must never duplicate an email, record write, or deployment. Read-only and provably idempotent operations may auto-retry under policy.

## 11A.7 Security gates in the rollout (consensus C-19)

Security requirements form a first-class family (identity, authentication/authorization, secrets, tool scope, input trust, data classes, network exposure, dependency controls, audit evidence, backup/recovery, incident response, kill/revoke). Every activation stage in section 17 declares and passes its applicable security gate before the capabilities it protects switch on; a stage cannot be entered by skipping its gate.

## 11A.8 Outbound identity and owner voice *(v1.3 — CP-v1.2-B, CPB-06; SEC-02)*

Use of the owner's voice is governed by four separated controls: (1) profile creation and use, (2) draft generation, (3) draft approval, and (4) external-send authority. Voice profiles derive only from authentic pre-existing owner samples; no default or fallback voice exists. Measured correction rates may graduate drafting authority per category, beginning with per-draft approval; send authority always remains governed by IDN/DAT/ACT/AUT and step-up policy. Every outbound artifact in the owner's voice binds profile/version, drafting actor, approval event, and send policy; unlocks are owner-visible and reversible.

# 12. Application Development Operating Model

## 12.1 Role-based lifecycle *(v1.4 — CP-P2-A Item 0; trail entries 69/82)*

The current stage model should be preserved while model names are configured separately. This avoids redesign whenever a provider or model changes.

| Lifecycle role | Purpose | Current mapping to validate |
| --- | --- | --- |
| Ideator | Explore the problem, goals, opportunity, and constraints. | Claude Code Opus 5. |
| Designer | Define user experience, system/process design, and architecture options. | Claude Code Opus 5. |
| Planner | Produce implementation-ready plan, dependencies, tests, and rollback. | Claude Code 'Fable' as currently described. |
| Builder | Execute the approved plan using bounded workers and isolated work areas. | Claude Code Opus 5 managing Sonnet agents. |
| Debugger | Diagnose failures, correct defects, and rerun validation. | Cursor. |
| Launch Auditor | Perform independent review, launch testing, and evidence package. | Hyperagent with Codex connection. |

Model/provider assignments are configuration, not workflow identity. A future planner or reviewer can change without changing the lifecycle or Discord organization.

### 12.1.1 Starting configuration and role-to-stage map *(v1.1 — consensus C-17/C-30 with verifier concurrence; owner decision D3)*

Version 1 activates **three operational roles plus the visible Coordinator and a read-only Reader support role**; the six-role abstraction above remains available for later specialization when evidence shows a split helps:

| Active role | Covers stages | Advances the stage? |
| --- | --- | --- |
| Coordinator (with owner) | Discovery, Design (ideation is coordinator-led conversation) | Yes, with owner participation. |
| Planner | Planning | Yes, on plan approval. |
| Builder | Execution, plus repair/debugging as a Builder mode | Yes, to Validation, on harness submission. |
| Independent Auditor | Validation | Yes, to Integration, on evidence package. |
| Reader (support) | All stages, read-only | Never. Assembles context packs, traceability, and version comparisons; no authority to decide, act, or filter adverse evidence. |

**Per-transition artifact contracts** (each stage change produces a named repository artifact with defined inputs, outputs, validation, handoff, and rollback): ideation brief → design record → implementation plan (scope, definition of done, tests, rollback) → build report → defect records → launch-audit evidence package → closeout summary. The Builder ≠ Auditor separation is non-negotiable in every configuration (see 12.4).

## 12.2 Standard application pipeline

```text
Problem / idea
  -> Discovery and ideation
  -> Design
  -> Implementation plan
  -> Owner approves business behavior and scope
  -> Build in isolated branch/worktree
  -> Automated checks
  -> Debugging loop as needed
  -> Independent launch audit
  -> Owner reviews outcome
  -> Merge/deploy according to action policy
  -> Fold release and lessons into application hub
```

## 12.3 Parallel development and grouped branches

A project hub may spawn grouped topics for audits, features, or categories. The owner can manage at the group level or enter a specific defect when useful.

```text
Customer Portal
  -> Launch Audit
     -> Interface Issues
        -> Mobile navigation defect
        -> Quote card overflow
     -> Data and Logic Issues
     -> Performance Issues
     -> Security Issues
        -> Authentication timeout
        -> Missing authorization check
```

Results continually fold upward: focused issue to group, group to audit, audit to application hub. The application hub remains the principal place for status, recent events, suggested next, and stable-state assessment.

## 12.4 Context and artifact requirements

- Every build topic has an objective, approved scope, definition of done, branch/worktree, current checkpoint, tests, and next action.
- Plans, architecture decisions, and closeout summaries become repository artifacts rather than remaining only in chat.
- Review findings route directly to the responsible builder topic and retain reviewer independence.
- Worker sessions may be replaced without replacing the visible topic or losing the task state.
- The owner can monitor and approve from mobile, then inspect detailed evidence from PC when needed.

*(v1.1 — consensus C-15, reviewer independence operationalized):* the Independent Auditor runs in a separate session with distinct worker identity and credentials from the Builder for the same build topic; its inputs are the approved intent, artifacts/diff, and independent harness evidence — never the builder's conversation or narrative. Post-audit corrections above a triviality threshold require scoped re-audit of the changed surface before merge. Plan-versus-scope comparison belongs to the auditor role. Provider/model diversity between builder and auditor is preferred for higher-risk releases; independent execution and evidence authority are the non-negotiable minimum. Mid-build discoveries that change the approved plan raise a scope-change event back through Planning (consensus C-31 disposition: build-backlog detail, principle recorded here).

## 12.5 Release-state profile for release-bearing builds *(v1.2 — CP-v1.2-A; requirement APP-08)*

Release-bearing build topics may carry an **optional, build-specific `release_state`** in addition to — never in place of — the five universal canonical dimensions of section 4.4 (`stage`, `work_status`, `attention`, `focus`, `health`). It exists to give the owner honest release-progress visibility without overloading the universal state model, and it is never a substitute for them.

| `release_state` | Definition | Typical responsible authority |
| --- | --- | --- |
| Developer-complete | The Builder has finished the change set and returned a Builder Delivery Record (12.6, APP-06); no independent verification yet. | Builder |
| Reviewed | Independent audit/verification has run against the pinned candidate and its evidence is in the tamper-evident store. | Independent Auditor / Verifier |
| Approved | Fable, as integration owner, has dispositioned the reviewed candidate as integration-ready. | Fable (integration owner) |
| Merged | The approved candidate has been merged to the target branch. | Release Executor (GOV-03) |
| Deployed | The merged artifact has been released to its production/hosting target. | Release Executor (GOV-03) |
| Live-verified | Post-deployment verification confirms the deployed artifact behaves as approved. | Independent Auditor / Verifier |

Rules that keep the ladder honest:

- **`Rework-required` is a review disposition and return transition, not a forward state.** A finding returns the candidate to the Builder as a Rework Packet (12.6, APP-07); it is never a step "up" the ladder.
- **Deterministic invalidation.** Each transition records the responsible authority, the pinned candidate/base identifiers, an evidence reference, a timestamp, and the action-class authorization. Any relevant candidate or target-head change invalidates every dependent state through a deterministic reset rule (the combined-tree gate, APP-09): a moved target head or rebuilt artifact is a new candidate that must be re-reviewed.
- **Applicability and publication profile.** `release_state` applies only to release-bearing builds. Non-deployable work — a documentation package, or a library that stops at publication — uses an approved **publication profile** or `Not applicable` for `Deployed`/`Live-verified` rather than pretending to have a live runtime. *(The v1.2 documentation build itself uses the artifact-publication profile: `Deployed`/`Live-verified` = Not applicable.)*
- **No premature completion.** Owner-facing renderings never present an unqualified "done," and a parent topic does not reach `work_status: Completed` merely because the Builder is Developer-complete — completion waits for terminal release/publication verification and fold-back.

## 12.6 Task Packet, Builder Delivery Record, and two-lane build safety *(v1.2 — CP-v1.2-A; ADR-020)*

Version 1.2 adopts the peer dual-agent workflow's concrete Application Development mechanisms while preserving the AI OS multi-role governance, operational-database identity/state ownership, independent-evidence authority, provider portability, and risk-selected repository topology (ADR-020). It does **not** adopt reviewer/integrator fusion or a mandatory two-repository topology.

- **Task Packet (APP-05).** Every build assignment is a versioned Task Packet that *projects* the approved plan and stage-gate context to the Builder — it never replaces the design record, plan, or §20A gate packet. It binds the canonical task/topic IDs, parent topic, approved plan/version, accepted requirement and decision IDs, risk class, trust/data classes, authorized action classes, and source/context manifest, together with the objective, required behavior, guardrails, telemetry and prohibited logging, verification, checkable acceptance criteria, a scope-deviation/escalation rule, and handoff requirements. Post-approval changes require a versioned scope/change event. Before the operational database exists, IDs come from the protected atomic bootstrap registry with a mandatory later alias/migration to DB-minted global IDs (5.2.1, finding H-01).
- **Builder Delivery Record (APP-06).** Builder completion requires a Builder Delivery Record — a *completion claim and evidence index*, not independent evidence. It names the task, branch, base/candidate commits, changed files, tool/environment versions, applicable proofs, discriminating proof for defect fixes (or an approved compensating-evidence rationale), diff/format results, external-write disclosures/receipts, and residual risks. Its required proofs must be independently reproduced or verified into the tamper-evident harness store (11.2) before approval; a completion claim without the record is not reviewable, and the Builder never marks its own work accepted.
- **Rework Packet (APP-07).** A review finding becomes a Builder instruction only after Fable dispositions it under §20A, then returns as a versioned Rework Packet (finding ID and authority, reviewed candidate, what passed, exact failing behavior and evidence, why controls missed it, the smallest correction, required new proof, regressions that must stay green, and closure authority). Each accepted behavioral, security, permission, or regression defect becomes a durable automated test or deterministic guard where feasible; otherwise a repeatable check, policy, acceptance criterion, or ADR with rationale.
- **Two-lane trust-boundary invariant (APP-09).** Development and production are separate trust boundaries. The Builder holds **zero production mutation or deployment credentials** and is structurally unable to alter production; any scoped read-only production access is separately authorized, masked, and logged. Repository topology (protected branches in one repository, fork/mirror, or separate repositories) is risk-selected provided that invariant holds, and each task uses a task-specific branch in every affected repository. Before merge authorization the approved change is applied to a **pinned** target head in a disposable least-privilege environment; the resulting candidate tree/commit and deployable artifact digests are recorded, and any drift, rebuild, or conflict resolution invalidates the gate and forces re-test and scoped re-review (the pinned combined-tree gate; see 11.3 and 12.5). Release execution is performed by a controlled actor separate from Builder and Verifier (GOV-03, 20A.3).
- **Sandboxed review execution (APP-10).** Unreviewed branch code, tests, package hooks, workflow files, and browser automation execute only in ephemeral least-privilege environments — no production credentials or data, synthetic or temporary fixtures, external writes denied by default, controlled egress, and tamper-evident action/evidence logging. A disposable Git worktree alone does **not** satisfy execution isolation.

Delivery Records include the APP-06 falsifier element for each material acceptance or evidence claim.

# 13. Business Operations, Data, Leads, and Calls

## 13.1 Business operating system, not only development system

The development workflow creates and maintains applications, but the larger system should also operate through those applications and their data. Business HQs can summarize performance, collect judgments, prompt actions, identify patterns, and create improvement topics.


## 13.2 Hybrid HQ and system-hub organization

Business organization is hybrid. Functional HQs provide cross-system oversight, while each major operating system or application retains one authoritative hub. Functional views link to the same underlying records instead of copying them.

```text
BUSINESS
  -> Sales and Marketing HQ
  -> Operations HQ
  -> Data and Intelligence HQ
  -> Application Development HQ

AUTHORITATIVE SYSTEM HUBS
  -> Lead System Hub
  -> Call Review Hub
  -> Internal Web Tool Hub
  -> Customer Portal Hub
```

A Lead System Hub may own leads, incoming calls, advertising attribution, follow-ups, performance, and application improvements. Sales HQ shows the lead-performance view; Operations HQ shows call handling and follow-up; Data HQ shows import health and definitions; Application Development HQ shows bugs, features, and releases.

## 13.3 Discord and application responsibility split

Discord is the lightweight pilot and administrative attention layer. It should tell the owner that six calls need review, summarize why they matter, allow a simple decision, and create or delegate follow-up work. The purpose-built application remains the structured workspace and system of record for full transcripts, audio, historical context, rating forms, analytics, search, bulk actions, and reporting.

The coordinator tracks the resulting obligation whether the owner handles it personally or assigns it to another person.

## 13.4 Split ownership of operational truth

Connected business applications own business facts; the AI operating system owns coordination.

| Business application owns | AI operating system owns |
| --- | --- |
| Call, transcript, caller, lead, rating, attribution, customer history, recorded outcome, follow-up date. | Why attention is required, workflow stage/status, assignment, due date, decisions, reminders, escalations, verification, and closeout state. |

The two records are bidirectionally linked. The AI operating system should not silently create a competing duplicate of the operational record.


## 13.5 Data HQ

Data HQ is the central operating area for global data imports, data connections, data-quality issues, source health, permissions, lineage, and topics that affect multiple business systems.

| Data HQ view | Representative content |
| --- | --- |
| Connections | Internal web tool MCP, CRM/lead source, call platform, advertising sources, email, application databases. |
| Health | Last sync, failures, stale data, schema changes, authentication status. |
| Permissions | Read/write boundaries, sensitive fields, approved actions, audit requirements. |
| Data topics | Missing call linkage, duplicate leads, attribution logic, transcript quality, metric definitions. |
| Global definitions | Authoritative customer, lead, call, campaign, employee, quote, order, and application identifiers. |

*(v1.3 — CP-v1.2-B, CPB-02)* Data HQ includes the BUS-10 connections registry: operational-database-owned metadata for every configured or discoverable integration (mechanism, scope, auth-health, last-verified, owning domain, trust/data classes, tool/API version, reference-doc pointer), with versioned per-tool reference documents in controlled artifact storage. No secret values live in the registry or reference docs. Connection freshness feeds Data HQ health and the AUD-03 self-audit.

## 13.6 Lead, advertising, and call example

```text
Advertising and lead data arrives
  -> lead and call records are linked
  -> call transcript is available
  -> owner or employee receives a focused rating prompt
  -> rating and handling insight are stored
  -> trends appear in Leads and Calls HQ
  -> system identifies coaching, process, or application opportunity
  -> improvement topic enters Discovery
  -> approved change is built and deployed
  -> performance is measured again
```

The private AI operating system remains owner-only. An employee may rate a call or use a business application without accessing the owner’s private Discord, development topics, rules, or administrative controls.

## 13.7 MCP and connected company data

MCP or an equivalent tool interface can expose selected company data and actions to the coordinator and specialist agents. The first integration should be read-only and narrowly scoped. Write actions should be introduced by action class, evidence, and explicit approval policy.

- Every tool call should declare the source, requested action, permissions, and affected topic.
- Business data access should be logged and auditable.
- Sensitive fields should be minimized and domain-separated.
- Application development agents should not automatically inherit all operational data access.
- Operational insight topics should link back to the data and evidence that created them.

Every wired tool is recorded in the BUS-10 connections registry (§13.5), with a captured-once, versioned reference document refreshed on material tool/API change.

## 13.8 Mailroom

Mailroom should triage work and personal email separately while presenting both through the Executive Desk. It should classify importance, estimated effort, required action, deadline, topic/project relationship, and whether a draft or workflow can be prepared.

```text
WORK EMAIL
Customer complaint
Priority: High
Estimated owner effort: 5-10 minutes
Recommended action: Respond today
Related project: Customer Portal
Draft available: Yes

PERSONAL EMAIL
Mortgage broker requested documents
Priority: High
Estimated owner effort: 15 minutes
Recommended action: Complete tonight
```

# 14. Personal Operating Domain

## 14.1 Scope

The system must remain flexible enough to support personal planning without turning the private operating system into a business-only tool. Representative personal uses include travel planning, house search, cooking, personal writing, administrative tasks, and health-related questions.

## 14.2 Separation model

| Shared | Separated |
| --- | --- |
| Reception and overall Executive Desk frame. | Priority lists, topic hierarchy, memory, permissions, connected accounts, and sensitive records. |
| Navigation principles and workflow engine. | Business and Personal HQs, rules that have domain-specific scope, and data retention policies. |
| Skills that are explicitly global. | Operational data, application repositories, employee information, personal health or financial information. |

The user should be able to choose Business or Personal mode once, then work inside that priority list without evaluating the domain of every line item.

## 14.3 Personal HQ candidates

- Personal Administration HQ
- Travel HQ
- Home and Property HQ
- Personal Writing and Communication HQ
- Health and Wellness HQ with stricter privacy and action limits
- Personal Research and Purchases HQ

These are candidates for later interview, not approved channel or database structures.

# 15. Memory, Context, and Knowledge Architecture

## 15.1 Context should be invisible operationally

The owner should not decide when to compact a conversation or write a handoff message. Context management should occur behind the visible topic while preserving the same Discord location and project identity.

## 15.2 Required memory layers

| Layer | Purpose | Retention behavior |
| --- | --- | --- |
| Live worker context | Recent conversation, file reads, tool output, and immediate reasoning. | Temporary; compacted, pruned, or replaced as needed. |
| Topic checkpoint | Objective, original commitment, decisions, completed work, current state, next action, branch/files, and blockers. | Durable and refreshed at meaningful milestones. |
| Hub summary | Integrated state of children, recent events, suggested next, needs-owner, to-do/to-did, and stable-state assessment. | Durable and recalculated from child events and fold-back. |
| Semantic knowledge | Relevant observations, preferences, skills, relationships, historical decisions, and cross-topic knowledge. | Long-lived, searchable, scoped, and reviewable. |
| Artifact and event archive | Full plans, code, tests, transcripts, reports, evidence, and change history. | Retained according to provenance, sensitivity, and policy. |

## 15.3 Compaction and session replacement

```text
Worker context approaches limit
  -> refresh topic checkpoint
  -> preserve durable decisions and unresolved questions
  -> compact older dialogue or start a fresh worker session
  -> load global rules, scoped preferences/skills, topic checkpoint,
     relevant parent summary, repository/artifacts, and retrieved knowledge
  -> continue in the same visible topic
```

The task should survive even when a model session times out, fails, or is replaced. The operational record, not the model transcript, owns the current state.

### 15.3.1 Checkpoint hardening *(v1.1 — consensus C-16 and verifier finding G-01)*

Graceful context pressure is not the only failure; the founding scenario is the 3 AM crash. Therefore:

- **Cadence:** checkpoints refresh at every stage transition, on recorded decisions, at bounded work-unit completion, on fixed time/heartbeat intervals during active execution, and **before any consequential external action** — never only at graceful context-limit approach.
- **Worker Session record:** every active worker has a session record (identity, heartbeat, execution journal, last confirmed side effect) so the system knows which session held which task when it died.
- **Reconciliation on resume:** a replacement worker reconciles the checkpoint against the work branch and event log before continuing; divergence raises Needs Review instead of silently proceeding. Git commits are the recovery substrate for code and artifacts, not the universal mechanism for non-code work.
- **Protected vs generated fields (G-01):** owner-approved objective, original commitment, scope, decisions, and acceptance criteria change **only** through explicit Decision/fold-back events — never by automated summary refresh. Generated current-state fields refresh automatically but are versioned, source-linked, diffable, and reversible; prior checkpoint versions are preserved, and every change emits a checkpoint-changed audit event. A bad compaction must not be able to silently rewrite what the owner agreed to.

Structured owner interviews (onboarding, kickoff, level-up) checkpoint per MEM-09: each answer persists when given, resumption is from the persisted record, and the record inherits data-class, provenance, versioning, correction, and protected/generated-field rules.

## 15.4 Gbrain or provider-of-choice contract

Before selecting a knowledge provider, the design should specify the capabilities required from it:

- Store observations with provenance, date, category, confidence, and related objects.
- Represent relationships among people, applications, processes, rules, skills, decisions, and topics.
- Retrieve relevant knowledge by semantic meaning and explicit category.
- Respect Business, Personal, project, and sensitivity scopes.
- Track last applied, usage count, status, review date, and conflicts for rules/preferences/skills.
- Support inactive and archived states without deleting history.
- Expose references back to the authoritative topic, decision, artifact, or event.
- Permit export and migration so knowledge is not trapped in one provider.

*(v1.3 — CP-v1.2-B, CPB-01)* Any provider fulfilling this contract is additionally bound by MEM-08: it remains a derived knowledge layer with grounded, provenance-carrying claims, versioned `Disputed` conflict records, and DAT/TRS/PER-governed admission; it is never the canonical store for workflow state, approved decisions, rules, credentials, or action authority (see ADR-021). Provider selection and external-transfer authorization are separate gated decisions.

> **Implementation rule:** The knowledge layer should enrich decisions and retrieval. It should not be allowed to overwrite authoritative workflow state or approved rules without the governed topic process.

# 16. Discord-First Platform Strategy

## 16.1 Why Discord is the preferred first interface

- The owner already understands Discord navigation and keeps it open for other purposes.
- It is available on phone, PC, and browser, reducing the initial interaction learning curve.
- Channels, forum-style posts, threads, links, bots, notifications, and permissions can represent an initial prototype.
- A manual clickable mockup can be built before the backend, host, and agent integrations exist.

Platform familiarity is a valid design advantage. Another platform should be selected only when a specific capability justifies the additional learning and migration cost.

## 16.2 Discord should remain a thin executive layer

Discord should display and control the system, not become its only database. A small number of permanent entrances should be used, while projects and topics are generated as linked posts, threads, or bot-rendered views backed by structured state.

## 16.3 Provisional server information architecture

```text
FRONT OFFICE
- reception
- executive-desk
- approvals
- alerts
- mailroom

BUSINESS
- business-hq
- application-development-hq
- data-hq
- leads-and-calls-hq
- operations-hq

PERSONAL
- personal-hq
- personal topic areas as discovered

OPERATING SYSTEM
- rules-hq
- preferences-hq
- skills-hq
- automation-hq
- system-health
```

This is a conceptual map, not a recommendation to create all channels immediately. The final prototype should minimize permanent channels and use bot-created topic views to prevent channel sprawl.

## 16.4 One visible coordinator

The default visible relationship should be between the owner and one coordinator identity. Specialist agents and providers may work behind the coordinator. The topic card can show the active role or provider without requiring the owner to visit separate Claude, Codex, reviewer, or researcher channels.

*(v1.1 — owner confirmation, decision D9, 2026-07-25):* the owner explicitly ratified this model: *"I would set the agent to use for the category of work and the agent I interact with assigns tasks to agents according to category."* Per-category agent/model assignment is configuration (12.1); the owner toggles between places, never between staff.

## 16.5 Companion dashboard boundary

A companion dashboard should be deferred until a Discord limitation is demonstrated. Valid reasons may include dense branch maps, advanced filtering, drag-and-drop planning, complex charts, timelines, architectural diagrams, or large audit evidence. Every off-platform view should be opened from a direct in-text link and return the user to the correct Discord hub or topic.

# 17. Staged Activation Plan

*(v1.1: replaces the v1.0 Wave 0–5 rollout. Consensus C-03/C-04/C-05 with verifier modifications; owner decisions D1/D2/D6. Nothing is removed from the vision — this section governs the **order in which capabilities switch on**. Build phases are expected to run at LLM-assisted speed — days, not months — an expectation to test with measurement, not a schedule guarantee. The governing constraint is the owner's attention and trust-absorption rate.)*

## 17.0 Capacity and gate rules (apply to every stage)

- **Baseline first:** before Stage 1, capture current-state measures — resumption time after interruption, ideas lost, manual handoff messages, babysitting hours, unread email backlog, owner orchestration hours per change, monthly tool spend, failure rate. Gates are judged against these numbers, not feel.
- **Every stage has a gate:** measurable benefit delivered, acceptable owner burden, security prerequisites passed (11A.7), rollback/recovery point recorded, and an explicit stop/continue decision. Two consecutive missed gates park the program with state preserved.
- **Capacity model:** each stage declares its maximum standing load — active foreground/background work, Needs-You queue size, review-queue aging limits, owner decision-minutes per day, model/API spend, worker concurrency. Expansion pauses when the system creates more administrative demand than it removes.
- **Adopt before build:** each stage begins with a capability-mapping pass (what existing tooling — agent harnesses, scheduled runs, connectors, hosted CI — already covers) so custom build effort goes only where the concept requires it.

*(v1.3 — CP-v1.2-B, CPB-15)* Scheduled/cadence runs execute under SCH-02: minimal task context plus a hashed, versioned, fail-closed control envelope; the full workspace is never loaded by default.

## 17.1 Stage 0 — Baseline, protection slice, and prototype

- Capture the baseline measures above.
- Stand up the minimum protection slice: owner identity + account hardening, secrets handling, the trust rule for any external content, kill-switch, backups of whatever exists.
- Manual Discord clickable prototype (Reception, Executive Desk, one HQ, one hub, nested topics) to validate the experience shape.

*(v1.3 — CP-v1.2-B, CPB-08)* Onboarding follows ONB-01 and ADR-022: one coordinated session collects all currently known grants through the protected secret surface; capabilities activate as their §11A.7 gates pass; no trickle requests for known grants; reauthorization only for the ONB-01 exception classes, batched and explained.

## 17.2 Stage 1 — Live capture, resumption, and visibility (the pain-relief core)

- Minimal LLM-backed coordinator: Reception capture with bounded classification/routing, topic kickoff records, checkpoint maintenance (15.3.1 cadence), automatic status from worker events, the Needs-You queue, recent-event summaries, and direct navigation including recall-by-description.
- Thin substrate (owner decision D2): coordinator over adopted components with a minimal structured state core (Supabase-class store for workflow state and IDs; Git/files authoritative for code and artifacts). Files are durable from day one; the store grows as rendering and rollups need queries.
- Resilience gate before dependence: backups + restore test + watchdog live (11A.5).
- Gate: owner reconnects from phone and reaches current state + next action without rereading history; captured ideas land with zero lost.

*(v1.3 — CP-v1.2-B, CPB-08)* Grant collection for this stage's integrations follows the ONB-01 / ADR-022 onboarding note at §17.1.

## 17.3 Stage 2 — One application-development workflow

- Pilot one real application through Coordinator + Planner + Builder + Independent Auditor (12.1.1), one active implementation branch, harness minimums for its risk tier, artifact contracts per transition.
- *(v1.2 — CP-v1.2-A):* the development/production two-lane trust-boundary invariant (APP-09) and its supporting mechanisms **activate here at Stage 2 — not in Stages 0–1**, which stay as defined. This stage stands up: a Builder identity holding zero production mutation/deployment credentials; a task-specific branch per affected repository with protected target paths; the Task Packet / Builder Delivery Record / Rework Packet artifact contracts (12.6; APP-05, APP-06, APP-07); the pinned combined-tree gate run on a disposable least-privilege candidate before any merge authorization (12.5, APP-09); sandboxed execution for unreviewed code (APP-10); and a constrained Release Executor for the merge/deploy action (GOV-03, 20A.3). The optional build-scoped `release_state` profile (12.5, APP-08) is available to this pilot; non-deployable pilots use the publication profile.
- Security gate (11A.7): the credential-separation and protected-path controls above are Stage 2 prerequisites — the pilot may not merge through an unpinned or unsandboxed path.
- Gate: measured cycle time and owner orchestration-hours beat the Stage 0 baseline on the pilot.

## 17.4 Stage 3 — Read-only email brief *(owner decision D6, verifier condition)*

- Activates only after the minimum protection slice of C-01/C-02/C-20/C-21 exists: display-only triage summaries; no drafting, sending, link-following, attachment execution, or email-derived tool instructions; separately scoped work/personal connectors.
- Full Mailroom (drafts, actions, workflows) remains in Stage 4 behind the complete protection layer — drafting is the most direct injection-to-exfiltration path.
- Gate: the morning brief measurably reduces email batching pain with zero injection-shaped incidents.

## 17.5 Stage 4 — Learning, knowledge, and business operations

- Observation capture and candidate topics for preferences/skills/rules/policies; knowledge provider integrated against the 15.4 contract; usage tracking and lifecycle review.
- Read-only MCP to the internal webtool; Data HQ, Leads and Calls HQ, transcript rating and insight loops; full Mailroom.
- Write actions enter only through scoped automation policies with harness-verified evidence (11.3, 11A.6).
- Gate: one closed operational loop (data → insight → improvement topic → validated change) demonstrated.

## 17.6 Stage 5 — Personal domain depth and expansion

- Personal HQs with strict data boundaries; local models for supporting workloads where proven; companion dashboard only for a demonstrated Discord limitation.

> **Hardware sequencing (owner decision D7):** the concept runs identically on interim hardware through Stages 0–2; the Mac Studio purchase is the owner's call on timing, made with corrected expectations — an always-on orchestration body (persistent coordinator, services, repositories, local supporting models), not a bigger brain; cloud frontier models remain the primary intelligence. Hardware availability is never treated as proof the system is ready.

# 18. Success Measures, Risks, and Guardrails

## 18.1 Success measures

| Measure | Target direction |
| --- | --- |
| Time to resume after interruption or device switch | Decreases; user reaches current state and next action without rereading long chat history. |
| Ideas lost before classification | Approaches zero for captured input. |
| Active topics without a current checkpoint | Approaches zero. |
| Manual context handoff messages written by owner | Approaches zero. |
| Jobs with visible working/waiting/blocked/failed status | Approaches 100 percent. |
| Completed child topics not folded back | Low and automatically surfaced. |
| Approvals where owner can make a meaningful judgment | Increases; ceremonial technical approvals decrease. |
| Protocol steps administered manually by owner | Decreases. |
| Work and personal priority decisions per session | Owner chooses domain once rather than per item. |
| Application changes tied back to measured business insight | Increases over time. |
| Routing prompts per captured input *(v1.1)* | Decreases as calibration matures; visible, not felt. |
| Owner review-queue load: size, oldest item, weekly inflow/outflow, decision-minutes *(v1.1)* | Bounded by the stage capacity model; aging consolidates instead of stacking. |
| System build/maintenance hours and monthly system cost *(v1.1)* | Visible cost side for every gate; the system cannot consume the owner invisibly. |
| Approval dwell time on decision cards *(v1.1)* | Watched for rubber-stamping; feeds attention calibration. |
| Cost posture *(v1.3 — CP-v1.2-B, CPB-07/CPB-12)* | CAP-03 telemetry (coverage-disclosed, billed-vs-estimated, multi-provider) and CAP-04 economic retirement-review flags, evaluated at AUD-03. |

## 18.2 Principal risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Topic and channel sprawl | Observation threshold, recursive fold-back, stable-state review, minimal permanent Discord channels. |
| Automation exceeds trust | Action-class policies, evidence thresholds, explicit scopes, reversible actions, independent verification. |
| False technical confidence | Harness-based evidence, independent review, layman impact summaries, residual-risk statements. |
| Memory contamination across domains | Business/Personal scopes, permission separation, provenance, authoritative-store boundaries. |
| Notification overload | Needs-owner filtering, scheduled summaries, compact breadcrumbs, event importance thresholds. |
| Vendor lock-in | Role-based model configuration, memory contract, structured operational store, exportable artifacts and Git. |
| System becomes a hobby instead of a tool | Pilot application success gate; defer local-model network, broad integrations, and complex dashboards. |
| User overrides protocol repeatedly | Explain consequences, request rationale, log deviations, revisit rule/skill/topic design. |
| Discord reaches presentation limits | Progressive disclosure and direct-linked companion view only when a specific limitation is proven. |

# 19. Phase 1 Audit Gate and Phase 2 Backlog

## 19.1 Reason for the audit gate

The operating model grew through iterative discovery and intentionally allowed nonlinear input. Before the Decision Engine is designed, independent agents should audit the consolidated baseline for contradictions, missing primitives, overengineering, implementation feasibility, security/data-governance risk, and user-experience failure.

Phase 2 should begin only after:

- All critical findings are resolved.
- High-severity findings are resolved or explicitly accepted with rationale.
- Conflicting recommendations are synthesized into a consensus proposal.
- The owner accepts the revised baseline.
- The requirements register and decision records are updated to match.

*(v1.1 status, 2026-07-25):* the audit was executed — seven independent roles, adversarial verification, consensus synthesis — and the assigned peer verifier (ChatGPT) concurred with every Critical/High disposition with zero dissents, contributing findings G-01/G-02/G-03, all incorporated in this revision. **The owner accepted Version 1.1 on 2026-07-25 (trail entry 53); the AUD-01 gate is passed.** Phase 2 remains closed until the release, receipt, and owner-acceptance gates of the active TASK-0002 / v1.3 cycle are satisfied, unless superseded by a later owner decision. These gates completed with the owner’s v1.3 acceptance (2026-07-28, trail entry 73); Phase 2 is open.

## 19.2 Phase 2 parent topic: Decision Engine

The next discovery phase will design the component that handles inputs, classification, recommendation, policy evaluation, attention level, routing, learning, execution authority, verification, and fold-back.

```text
Input
  -> Understanding
  -> Candidate classifications
  -> Recommendation with alternatives
  -> Policy evaluation
  -> Attention and routing
  -> Execution or owner decision
  -> Verification
  -> Learning and fold-back
```

The core hypothesis to test is that intelligent recommendations and deterministic policy decisions should remain separate. Models may improve recommendations without silently changing approved operating behavior.

## 19.3 Deferred design topics

The following are important but should not be treated as completed Phase 1 decisions:

- Exact permanent HQ taxonomy and Discord channel map.
- Decision Engine schema and routing logic.
- Critical-interrupt definition and quiet-hour behavior.
- Gbrain or alternative knowledge-provider selection.
- Operational database schema and event model.
- MCP authorization and production-write boundaries.
- Detailed mailroom behavior.
- Exact personal HQ structures.
- Discord forum/thread/activity implementation.
- Model/provider routing and subscription policy.
- Security architecture, secrets management, backup, and disaster recovery.

# 20. Hardware Baseline

## 20.1 Current recommendation

The current baseline is a **Mac Studio with M4 Max, 16-core CPU, 40-core GPU, 64GB unified memory, and 1-2TB internal SSD**, plus wired Ethernet, external backup storage, and a UPS. Prefer memory over internal SSD capacity if budget requires a tradeoff.

This recommendation assumes cloud Claude, Codex, and other hosted models remain the primary high-intelligence workers while the Mac Studio provides persistent orchestration, application hosting, repositories, builds, tests, databases, browser automation, embeddings, moderate local inference, and several concurrent services.

*(v1.1 — expectations on the record, owner decision D7):* the host is an **always-on body, not a bigger brain**. It adds a permanent unlocked home for the coordinator and gateway services, persistent sessions, and supporting local workloads; it does not make the primary models smarter — those remain the cloud frontier models. Purchase timing is entirely the owner's; the concept runs on interim hardware through Stage 2, and portability (PLAT-04) keeps a later migration cheap.

## 20.2 M4 Max versus M3 Ultra

The M3 Ultra provides substantially more aggregate CPU/GPU capacity, memory bandwidth, and memory ceiling. Its user-visible advantage would be most significant for large local models, heavy local inference, many simultaneous local workloads, or workloads that must remain on-premises. It would not materially accelerate cloud-model reasoning, Discord navigation, approvals, or most executive interactions.

The M4 Max remains the better value for the currently designed cloud-first operating system. Reconsider the M3 Ultra when local inference becomes a production requirement rather than a supporting capability. Recheck the available Apple lineup immediately before purchase because hardware generations and pricing change.

**Source note:** Apple Mac Studio Technical Specifications and Apple Mac Studio launch materials, accessed July 24, 2026.

# 20A. Program Governance and Stage Gates *(v1.1 addition — owner-directed, 2026-07-25, with verifier refinements)*

## 20A.1 Standing roles *(v1.4 — CP-P2-A Item 0; trail entries 69/82)*

| Role | Assigned to | Boundaries |
| --- | --- | --- |
| Architect & Designer; Project Manager; Integration owner; stage-gate approver | **Fable** | Owns the coherent design, backlog, dispositions, and merged baseline; defines stage scope and acceptance criteria before build; may recommend a gate pass; **may not silently waive a Critical/High verifier objection** — unresolved disagreement goes to the owner with both costs stated. |
| Independent verifier / peer reviewer | **ChatGPT** | Evaluates each stage packet against accepted requirements, decisions, and evidence; never implements the work it verifies or edits the authoritative baseline; issues Concur / Concur-with-modification / Dissent with acceptance conditions; re-verifies corrected scope before a gate closes. |
| Builder | **Claude Opus 5** | Implements only the accepted change set; produces a structured implementation/evidence package; cannot resolve requirement conflicts, expand scope without a change request, alter verification evidence, or mark its own work accepted. |
| Reader / context & traceability librarian | **Claude Sonnet** | Read-only ingestion; assembles scoped context packs (with source manifest, scope statement, and disclosure of material exclusions) for Fable, the Builder, and the verifier; maintains traceability and version comparisons; no authority to decide, change state, approve gates, filter adverse evidence, or instruct tools to act. The verifier always retains access to original sources. |
| Owner — final authority | **Hunter** | Final acceptance, business judgment, risk acceptance, and resolution of unresolved disagreements; never asked to certify technical detail without evidence translated to business consequences. |
| Release Executor — pre-authorized merge/deploy execution *(v1.2 — CP-v1.2-A)* | **Constrained actor/service** (deterministic CI/CD, a narrow release service, or owner-invoked automation) | Performs only the pinned, pre-authorized merge/deploy action with narrowly scoped production credentials; **is never the Builder or the Verifier**; cannot change design, candidate content, review disposition, or evidence; uses protected-path and compare-and-swap controls and emits tamper-evident execution receipts with the resulting commit/artifact identifiers (GOV-03, 20A.3). |

## 20A.2 Stage-gate packet and rule

Every gate is judged on a packet containing: (1) stage objective and boundaries; (2) accepted requirements/decisions in scope; (3) acceptance criteria and risk class; (4) source/context pack with manifest and exclusions; (5) implementation or design diff; (6) deterministic and independent evidence; (7) builder disclosure of incomplete/untested areas; (8) verifier response; (9) Fable disposition and recommendation; (10) unresolved disagreements and owner decisions; (11) version/tag and rollback point.

**Gate rule (owner-mandated):** a stage passes only when the agreed acceptance conditions are implemented and independently verified, Fable confirms integration readiness, and the owner accepts any owner-level decision or residual risk. Fable is project manager; the owner is final authority.

## 20A.3 Release execution *(v1.2 — CP-v1.2-A; requirement GOV-03)*

Integration *approval* and integration *execution* are different authority classes, and approval never silently implies execution authority (non-adoption N-1). Fable remains integration owner and approves what integrates; a constrained **Release Executor** performs the merge/deploy action. The executor acts only on a pinned, approved release instruction, holds narrowly scoped production credentials, has no authority over design, candidate content, review disposition, or evidence, uses protected-path and compare-and-swap controls, and emits tamper-evident execution receipts carrying the resulting commit/artifact identifiers. The executor is never the Builder or the Verifier and may be deterministic CI/CD, a narrow release service, or owner-invoked automation. This completes the four-way separation (Builder / Independent Auditor / Verifier / integration owner) with a distinct execution actor, closing verifier finding H-05.

# 21. Phase 1 Acceptance and Consensus

## 21.1 Baseline status

*(v1.1)*: the audit consensus completed and the owner accepted this baseline on 2026-07-25 (trail entry 53); the v1.2 layer was accepted 2026-07-27 (trail entry 65) and the v1.3 layer 2026-07-28 (trail entry 73); together they are the operating model of record.

## 21.2 Required audit perspectives

- Systems architecture and internal consistency.
- ADD-compatible executive experience and cognitive-load reduction.
- Workflow, routing, and Decision Engine readiness.
- Application-development feasibility.
- Security, data governance, permissions, and auditability.
- Implementation complexity and staged delivery.

## 21.3 Consensus output

The audit should produce a single issue register, disposition each material finding, identify any unresolved disagreement, and create a proposed Version 1.1. The owner should receive a concise decision package rather than separate competing essays.

# 22. Decision Engine Design *(v1.4 — CP-P2-A; owner acceptance trail 116)*

## 22.1 Status and authority

The Decision Engine design was carried out under change plan CP-P2-A, verified independently across ten packets, passed the machine design gate with zero open findings (trail entry 114), and was accepted by the owner on 2026-08-02 (trail entry 116). This chapter records that the design exists, is accepted, and is authoritative — **by reference**. It does not restate the design.

The committed design documents are the normative text. Where this chapter and a design document differ, the design document wins. Nothing here re-decides anything settled at trail entry 116, and this chapter creates no requirement of its own: the accepted requirements are DE-R1 through DE-R8 in `05_Requirements_Register_v1.1`.

The design gate proved the **provider-neutral core**. It did not certify production readiness, and it did not perform the build work enumerated in `13B_Build_Gate_Obligations_Register.md`, which remains open as Track B.

## 22.2 The committed design set

Each entry below is the document of record for its subject. Cited by document ID as the amendment package enumerates them.

| Document | Subject |
| --- | --- |
| D-B2 | Field-authority contract |
| D-B3 | Identity and deduplication |
| D-B4 | Concurrency boundaries |
| D-B5 | Degraded-operation matrix |
| `D-B6_Tier_Policy_Function_and_Autonomy.md` | Tier/policy function and autonomy caps — including §2.4 WF-09 dimension coverage, §3 the OD-2 starting-autonomy policy objects, and §4 the DE-R8 cap-policy parameter set |
| D-B7 | Attention and quiet hours |
| D-B8 | Policy objects and the precedence composite, as selected at the gate |
| D-B9 | Event model and replay |
| D-B10 | Partitioned queues |
| D-B11 | Rituals |
| D-B13 | Owner surfaces |
| D-B14 | Schema |
| D-EC_ | Evidence contracts |
| D-ODP_ | Owner decision package — the destination for design values flagged for owner ratification at activation (see `D-B6_` §4) |

## 22.3 What the design settles

Read the documents above for the substance. In outline, the accepted design fixes: which fields carry authority and which are model-proposed; how identity and duplicates are resolved; how the system behaves as its dependencies degrade; how an input envelope becomes a deterministic disposition, with autonomy caps that expand only on independently owned evidence and contract on regression; when the owner is interrupted and when they are not; how policy objects compose and which one wins; the event model and the replay property; how Business and Personal queues stay partitioned; and what evidence must exist before a consequential action is grounded.

## 22.4 Relationship to the rest of this Manual

This chapter closes the forward reference opened at §19.2, which named the Decision Engine as the Phase 2 parent topic and left its schema and routing logic to §19.3's deferred list. Those items are no longer deferred; they are designed, and the documents above are where they live. The protection layer (§11A), the staged activation plan (§17), and the governance model (§20A) are unchanged by the Decision Engine design and continue to bind it.

# Appendix A. Consolidated Requirements

**(v1.1):** the authoritative register is now `05_Requirements_Register_v1.1` (Markdown and CSV), which carries the v1.0 requirements below forward, applies the amendments listed at the end of this appendix, and adds the v1.1 requirement families (identity, trust, data, logging, resilience, checkpoint integrity, actions, capacity, corrections, recall, queue governance, governance). The v1.0 table is retained here for continuity; where it conflicts with the v1.1 register, the register wins.

| ID | Requirement |
| --- | --- |
| APP-01 | Application stages are role-based so models and providers can be replaced independently. |
| APP-02 | Plans, decisions, tests, reviews, and closeouts become durable repository or artifact records. |
| APP-03 | Independent review remains separate from the builder. |
| APP-04 | Worker sessions can fail, compact, or be replaced without losing the visible topic or operational state. |
| ATT-01 | Critical interruption is reserved for immediate physical, legal, financial, security, or comparably consequential danger. |
| ATT-02 | The Needs Owner attention level requests a response through badges, mentions, and queues without forcibly switching the foreground topic. |
| ATT-03 | Successful background completion and useful non-blocking improvements appear as hub updates; safe retries and first overdue reminders default to briefing. |
| AUD-01 | Phase 1 must pass independent multi-agent audit and owner-approved consensus before Decision Engine discovery begins. |
| AUD-02 | Critical audit findings must be resolved; high-severity findings must be resolved or explicitly accepted with rationale. |
| AUT-01 | Approval requirements are learned and configured by action class and scope. |
| AUT-02 | Automation expands through accumulated evidence and a reviewed policy topic, not silent adoption. |
| AUT-03 | Technical verification uses tests, independent review, security checks, staging, rollback, and plan comparison. |
| AUT-04 | Owner approvals focus on problem, process, business effect, outcome, and consequential risk. |
| AUT-05 | Local child tasks may be created automatically within scope; cross-cutting or high-impact work escalates. |
| AUT-06 | The owner may override recommendations when allowed; strong informational friction explains likely consequences before the override is accepted. |
| AUT-07 | Delegation transfers execution but not accountability; the coordinator tracks the assignment through closeout. |
| AUT-08 | Delegation and follow-up policies are scoped by person, assignment type, sensitivity, and consequence. |
| AUT-09 | A completion claim resolves as verified completion, owner-accepted completion, or needs review. |
| AUT-10 | Automatic verification begins as read-only evidence inspection; employee-facing corrective follow-up requires owner control unless a scoped policy authorizes it. |
| AUT-11 | Completed work is reconciled against later evidence without erasing the original To-Did history. |
| BUS-01 | The system both builds applications and operates the business through connected applications and data. |
| BUS-02 | Data HQ manages global connections, health, permissions, definitions, and cross-system data topics. |
| BUS-03 | Lead, ad, call, transcript, rating, insight, and improvement workflows form a closed operational loop. |
| BUS-04 | MCP or equivalent access begins read-only and expands through scoped action policies. |
| BUS-05 | Mailroom triages work and personal email separately while presenting both in the Executive Desk. |
| BUS-06 | Business uses a hybrid organization: functional HQs provide cross-system views while major systems retain authoritative hubs. |
| BUS-07 | Discord is the lightweight pilot and attention layer; purpose-built applications provide full structured workspaces and operational records. |
| BUS-08 | Business applications own operational facts; the AI operating system owns coordination, attention, assignments, decisions, and verification state. |
| BUS-09 | Linked functional views do not create competing copies of source records. |
| DEC-01 | Decision Engine discovery is the Phase 2 parent topic and must separate intelligent recommendations from approved policy decisions as a hypothesis to test. |
| EX-01 | Reception accepts unstructured input without prior classification. |
| EX-02 | The Executive Desk presents recent context, recent events, suggested next, and a full summary path. |
| EX-03 | Business and Personal priority lists remain segregated inside one unified dashboard frame. |
| EX-04 | One visible coordinator represents specialist agents and providers. |
| EX-05 | The owner can operate interchangeably from phone and PC. |
| EX-06 | Mobile and desktop render the same structured data differently; duplicated channels are not the default. |
| EX-07 | Progress is represented through verified stages, status, blockers, and next actions rather than narrative text alone. |
| EX-08 | The owner receives layman-oriented consequences and click-by-click guidance when performing technical work. |
| EX-09 | The interface uses compact breadcrumbs on coordinator messages and richer navigation on operational messages. |
| EX-10 | Every focused view provides direct routes to parent, children, related topics, prior location, and hub. |
| HW-01 | The current hardware baseline is M4 Max Mac Studio with 64GB unified memory and 1-2TB storage, subject to revalidation immediately before purchase. |
| INT-01 | Decision prompts expose genuine tradeoffs, calibrate boundaries, or state an expert default; they do not use an obvious progressive-completeness ladder. |
| LRN-01 | Observations may be automatic but are weak evidence with no immediate operating effect. |
| LRN-02 | Preferences, rules, skills, and automation policies use the same governed topic workflow. |
| LRN-03 | Every preference, rule, skill, and policy declares scope. |
| LRN-04 | The coordinator may propose a contextual exception or reopen a preference topic rather than silently violate a rule. |
| LRN-05 | Active, inactive, archived, and deleted states are supported; deletion is not the default. |
| LRN-06 | Inactivity triggers review rather than automatic removal; 90 days is a provisional initial threshold. |
| LRN-07 | Rejected ideas and owner rationale remain learning evidence. |
| LRN-08 | Knowledge is organized by categories and subcategories while supporting semantic retrieval. |
| MEM-01 | Operational state, Git artifacts, semantic knowledge, transcripts, and files have separate authoritative stores. |
| MEM-02 | The topic checkpoint is the durable resumption record outside live model context. |
| MEM-03 | Context compaction and worker replacement occur behind the same visible topic. |
| MEM-04 | The knowledge provider must support provenance, scope, relationships, usage, status, review, and export. |
| ORG-01 | The hierarchy supports Domain, HQ/Category, Initiative/Project, Topic/Group, and Task/Focused Issue. |
| ORG-02 | Every meaningful object can act as a recursive hub with children and an integrated summary. |
| ORG-03 | Categories and subcategories coexist with hierarchy, stage, status, and focus. |
| ORG-04 | To-do and to-did lists use a layered topic-plus-next-action format. |
| ORG-05 | A hub with excessive unresolved children triggers housekeeping review. |
| ORG-06 | Employees use purpose-built applications, not the private owner operating environment. |
| PER-01 | Personal use remains a first-class domain rather than an afterthought. |
| PER-02 | Personal and Business memory, permissions, records, and priority queues remain separated. |
| PLAT-01 | Discord is the preferred first interface because of familiarity and cross-device availability. |
| PLAT-02 | Discord is not the sole database or source of truth. |
| PLAT-03 | A companion dashboard is added only for demonstrated Discord limitations. |
| PLAT-04 | The operating model remains portable across Discord, model providers, memory providers, and host infrastructure. |
| WF-01 | Topics persist while stage labels change; stages are state rather than separate locations. |
| WF-02 | Stages may skip, repeat, or move backward as understanding changes. |
| WF-03 | Stage, operational status, and interaction focus are independent dimensions. |
| WF-04 | Every new topic receives a context-preserving kickoff record. |
| WF-05 | Every completed child produces a closeout package and folds accepted outcomes into its parent. |
| WF-06 | Blocking is advisory but explicit; an override requires a consequence summary and explicit acknowledgment for ordinary design work. |
| WF-07 | The system preserves pause, return, and impact state during focus switches. |
| WF-08 | One topic is normally foreground while multiple topics may work in background or queue. |
| WF-09 | Interjections are classified as immediate change, observation, child, sibling/parent, or blocker. |
| WF-10 | When multiple classifications are genuinely valid, the system recommends one, presents meaningful alternatives, and records the owner selection. |
| WF-11 | The system requests rationale selectively when the owner chooses differently, then calibrates future recommendations. |
| WF-12 | The coordinator manages protocol and housekeeping rather than relying on the owner to administer them. |

## A.1 v1.1 amendments to carried requirements

- **WF-03:** stage, work_status, attention, focus (and derived health) are independent canonical dimensions per section 4.4.
- **WF-09:** the five-way interjection set is **provisional**; routing is modeled as independent dimensions (placement, relationship, blocking, disposition, attention, authority, confidence) with the final taxonomy assigned to Phase 2.
- **ORG-01/ORG-02:** the hierarchy is an arbitrary-depth typed-role tree (6.1); Tasks are leaves by default with a promotion rule.
- **ATT-02:** "Needs Owner" is the canonical attention value; the term "Needs Attention" is retired.
- **HW-01:** reclassified as an owner-timed purchase decision with body-not-brain expectations (sections 17.6 note and 20.1); the register/ADR contradiction (Confirmed vs provisional-until-purchase) resolves as **provisional**.
- **LRN-05:** rule/preference/skill lifecycle states are Proposed, Active, Inactive, Retired, and Deleted; "Archived" is reserved for the topic stage (section 10.4).

## A.2 v1.1 new requirement families (full text in `05_Requirements_Register_v1.1`)

IDN (identity & authority) · TRS (input trust) · DAT (data classification & rendering) · LOG (action log) · RES (resilience & watchdog) · MEM-05/06/07 (checkpoint cadence, worker sessions, protected fields) · ACT (idempotent consequential actions) · SCH (schema versioning) · CAP (capacity model & cost measures) · COR (correction primitives) · EX-11 (recall-by-description) · QUE (unified review queue) · GOV (program governance & stage gates).

## A.3 v1.2 additions and amendments (CP-v1.2-A — accepted)

Owner-approved change plan CP-v1.2-A Revision 2 (decision-trail entry 54) adds the Application Development dual-agent mechanisms and release-execution governance. Full text is in `05_Requirements_Register_v1.1` (v1.2 rows); the Manual homes are section 12.5 (release-state profile), section 12.6 (Task Packet, Builder Delivery Record, Rework Packet, two-lane invariant, sandboxed execution), and section 20A.3 (release execution).

- **APP-02 (amended):** durable records now explicitly include Task Packets, Builder Delivery Records, independent verification references, and Rework Packets, keyed to operational-database object IDs; repository folders and status labels are non-authoritative projections, never ID allocators or competing state stores.
- **APP-05 (new):** the versioned Task Packet — a projection of the approved plan and stage-gate context, never a replacement.
- **APP-06 (new):** the Builder Delivery Record — a completion claim and evidence index, independently reproduced before approval.
- **APP-07 (new):** the Rework Packet — dispositioned findings returned as scoped, evidence-bearing correction instructions.
- **APP-08 (new):** the optional build-scoped `release_state` profile, separate from the five universal dimensions.
- **APP-09 (new):** the development/production two-lane trust-boundary invariant and pinned combined-tree gate.
- **APP-10 (new):** sandboxed execution for unreviewed code; a disposable worktree is not execution isolation.
- **GOV-03 (new):** the constrained Release Executor for pre-authorized merge/deploy actions.

These entries were post-build verified (TASK-0001), released by two-step compare-and-swap (trail entry 59), and **accepted by the owner 2026-07-27 (trail entry 65)**; the v1.1 acceptance is unaffected.

## A.4 v1.3 additions and amendments (CP-v1.2-B — accepted)

Owner-approved change plan CP-v1.2-B Revision 2 (decision-trail entry 64) adds the Nate Herk idea-register adoptions. Full text is in `05_Requirements_Register_v1.1` (CP-v1.2-B rows); the Manual homes are listed with each entry. All entries below are *(v1.3 — CP-v1.2-B)*: built by TASK-0002, released under the final scoped acknowledgment (trail entry 72), and **accepted by the owner 2026-07-28 (trail entry 73)**.

- **MEM-08 (new):** knowledge-memory providers remain a derived layer, never the canonical store (§15.4; ADR-021).
- **MEM-09 (new):** structured interviews checkpoint per answer; the persisted record is source of truth (§15.3.1, §7.3).
- **BUS-10 (new):** the operational-database connections registry with freshness discipline and no secret values (§13.5, §13.7).
- **AUD-03 (new):** the scheduled read-only scored self-audit on a versioned rubric; advisory, never a gate alone (§7.5, §18.1).
- **LRN-09 (new):** the improvement ritual shipping at most one artifact per cycle on the smallest-machinery ladder (§10.5).
- **LRN-10 (new):** the three-distinct-verified-occurrence automation-candidate threshold; weak evidence only (§10.1).
- **SEC-02 (new):** owner-voice profiles from authentic samples only, with four separated action classes (§11A.8).
- **CAP-03 (new):** coverage-disclosed, multi-provider token/usage/cost telemetry (§18.1).
- **CAP-04 (new):** economic retirement-or-redesign review flags raised at AUD-03; never auto-disable (§10.4, §18.1).
- **ONB-01 (new):** grant-once, activate-staged onboarding through a protected secret surface (§17.1, §17.2; ADR-022).
- **DEC-02 (new):** consequential decision records carry a falsifier or a reasoned `unknown` (§6.3, §8.6).
- **AUT-12 (new):** risk-tiered automation-first rollout; raw model confidence never unlocks authority (§8.2.1, §11.3).
- **ORG-07 (new):** the advisory three-question structure-addition test; capture is never gated (§8.5).
- **SCH-02 (new):** scheduled runs receive a hashed, versioned, fail-closed control envelope (§17.0).
- **APP-06 (amended):** Builder Delivery Records identify plausible disconfirming evidence for each material claim; a reasoned `N/A` is permitted, and the Builder-authored falsifier is review input only (§12.6).
- **ADR-021 / ADR-022 (new):** external managed-memory provider direction; grant-once, activate-staged onboarding (Appendix D).
- **DP-027 (new):** automation-first for eligible execution (Appendix C).
- **§11A.8 (new section):** outbound identity and owner voice — the four separated voice controls.

# Appendix B. Glossary

| Term | Working definition |
| --- | --- |
| Reception | Universal, low-friction entry point for any business or personal input. |
| Executive Desk | Global reconnect and control view combining context, separate priority lists, recent events, suggested next, and navigation. |
| HQ | Central management area for a recurring operational domain, category, or registry. |
| Initiative / Project | Committed outcome that supervises related topics and seeks a stable or completed state. |
| Topic | Durable body of thought or work that retains context while moving among stages. |
| Task | Concrete action, check, or decision within a topic. |
| Observation | Unconfirmed evidence that may later justify a preference, skill, rule, policy, or work topic. |
| Stage | Maturity of work: Discovery, Design, Planning, Execution, Validation, Integration, or Archived. |
| Status (legacy term) | Superseded in v1.1 by the canonical dimensions of section 4.4 — see Work status and Attention level. Legacy display labels map deterministically to canonical values. |
| Focus | Interaction prominence: Foreground, Background, Queued, or Parked. |
| Fold-back | Integration of a completed child outcome into its parent summary, decisions, plans, and next action. |
| Stable state | Condition in which accepted child outcomes are integrated, blockers and needs-owner items are handled, and the hub summary matches reality. |
| Rule | Approved required behavior or operating constraint. |
| Preference | Approved user-experience preference with defined scope and possible exceptions. |
| Skill | Approved reusable procedure or ability with trigger, inputs, steps, outputs, and validation. |
| Harness | Deterministic checks, permissions, tests, reviews, evidence, and rollback that make automation trustworthy. |
| To-Did | Completed work presented as visible progress and retained history. |
| Needs Owner (attention level) | A response or decision is required, but the current foreground topic should not be forcibly interrupted. Replaces the retired term "Needs Attention." |
| Verified completion | Completion supported by objective evidence against approved criteria. |
| Owner-accepted completion | Completion accepted by the owner despite incomplete independent verification. |
| Authoritative system hub | The canonical operational home for one major application or business system, linked into functional HQ views. |
| Work status *(v1.1)* | Canonical operational dimension: Queued, Running, Waiting, Blocked, Paused, Failed, Completed. |
| Attention level *(v1.1)* | Canonical urgency dimension: None, Briefing, Hub, Needs Owner, Critical. |
| Trust class *(v1.1)* | Input dimension declaring who controls content: owner-authored, internal-system, external-untrusted; distinct from instruction authority. |
| Instruction authority *(v1.1)* | Whether content may direct system behavior; external content never carries it without explicit approved policy. |
| Data class *(v1.1)* | Sensitivity category with per-class rules for storage, rendering, previews, retention, export, and deletion. |
| Protected checkpoint fields *(v1.1)* | Owner-approved objective, commitment, scope, decisions, and acceptance criteria — changeable only via explicit Decision/fold-back events. |
| Correction primitives *(v1.1)* | Re-parent, merge, split, reclassify, promote/demote, duplicate-link, archive — history-preserving repair operations behind the "Wrong place" gesture. |
| Recall-by-description *(v1.1)* | Retrieval of any object by free-text/semantic description from any surface, with match explanation and direct link. |
| Watchdog *(v1.1)* | Liveness monitor independent of the host and Discord that alerts the owner when the coordinator stops checking in. |
| Idempotency key *(v1.1)* | Action identifier that prevents a retry from duplicating a consequential external action. |
| Stage-gate packet *(v1.1)* | The eleven-item evidence bundle on which every activation-stage gate is judged (20A.2). |
| WAT (Workflows/Agents/Tools) *(v1.3 — CP-v1.2-B)* | optional teaching vocabulary for explaining the system externally; provenance contested; no design authority; does not replace the system's role, object, or layer vocabulary. |

# Appendix C. Design Principles

| ID | Principle |
| --- | --- |
| DP-001 | The user produces thoughts; the system organizes them. |
| DP-002 | Convert scattered thinking into organized, durable execution. |
| DP-003 | Preserve uncertainty until sufficient evidence supports classification or commitment. |
| DP-004 | Separate information from presentation; mobile and desktop are views of the same state. |
| DP-005 | Business and Personal remain separate priority queues inside one unified status frame. |
| DP-006 | Topics persist while stage, status, and focus change. |
| DP-007 | Allow one foreground context and multiple visible background contexts without losing return state. |
| DP-008 | Every branch preserves origin context and accepted results fold back upward. |
| DP-009 | Optimize for resumption and situational awareness, not notification volume. |
| DP-010 | Embed navigation so the owner can move up, down, sideways, and back through the idea network. |
| DP-011 | Recommendations explain alternatives and improve from owner rationale and later outcomes. |
| DP-012 | Observations are evidence, not automatic rules. |
| DP-013 | Rules, preferences, skills, and automation policies mature through the same governed workflow. |
| DP-014 | Automation expands through demonstrated trust, scope, evidence, and review. |
| DP-015 | Use technical verification harnesses where owner expertise is not a meaningful approval control. |
| DP-016 | Delegation transfers execution, not accountability. |
| DP-017 | Protocol is maintained by the system; permitted overrides require visible consequences. |
| DP-018 | Decision prompts must expose real tradeoffs rather than obvious answer ladders. |
| DP-019 | Discord is the familiar executive interface, not the sole source of truth. |
| DP-020 | Models, memory providers, and tools are replaceable role implementations, not permanent workflow identities. |
| DP-021 *(v1.1)* | Identity stands above the channel: the interface signals intent; authenticated identity authorizes consequence. |
| DP-022 *(v1.1)* | Outside-authored content is data to understand, never instructions to follow. |
| DP-023 *(v1.1)* | Evidence lives where its subject cannot touch it; a claim without independent evidence is a claim. |
| DP-024 *(v1.1)* | The system must detect and report its own death; silence must always mean safe. |
| DP-025 *(v1.1)* | Owner attention is the scarce resource: capacity governs activation, corrections are cheap, and cost is measured alongside benefit. |
| DP-026 *(v1.2 — CP-v1.2-A)* | Structure over vigilance: where enforceable controls exist, protect safety invariants with least-privilege identities, credential separation, protected paths, isolated execution, pinned immutable candidates, and independent evidence. Policy text or an agent's promised behavior is never the sole control. |
| DP-027 *(v1.3 — CP-v1.2-B)* | **Automation-first for eligible execution:** repetitive execution should advance toward the highest safe, evidence-supported autonomy that policy permits. Manual review is transitional where it adds no durable judgment or protection value; persistent owner judgment, approval, or step-up remains a valid designed control for consequential, sensitive, irreversible, legally constrained, or insufficiently evidenced actions. |

# Appendix D. Architecture Decision Summary

| ADR | Decision | Status |
| --- | --- | --- |
| ADR-001 | Use Discord as the preferred first executive interface while preserving platform-independent state. | Accepted for Phase 1. |
| ADR-002 | Use recursive hubs and branches with direct navigation and upward fold-back. | Accepted for Phase 1. |
| ADR-003 | Treat stage as mutable state on a persistent topic rather than as a separate location. | Accepted for Phase 1. |
| ADR-004 | Separate Business and Personal priority queues while showing both on one Executive Desk. | Accepted for Phase 1. |
| ADR-005 | Use a hybrid Business structure: functional HQs plus authoritative system hubs. | Accepted for Phase 1. |
| ADR-006 | Split operational truth: business applications own facts; the AI operating system owns coordination. | Accepted for Phase 1. |
| ADR-007 | Use observation-to-topic governance for preferences, rules, skills, and automation changes. | Accepted for Phase 1. |
| ADR-008 | Expand automation through accumulated evidence and scoped policies. | Accepted for Phase 1. |
| ADR-009 | Reserve forced interruption for critical events and use the Needs Owner attention level for ordinary decisions. | Accepted for Phase 1; terminology aligned v1.1. |
| ADR-010 | Use strong informational friction when overriding identified blockers. | Accepted for Phase 1. |
| ADR-011 | Use M4 Max 64GB as the current host baseline; reconsider M3 Ultra for production local inference. | Provisional until purchase. |
| ADR-012 | Freeze Phase 1 for independent audit before opening Decision Engine discovery. | Accepted. |
| ADR-013 *(v1.1)* | Adopt the five-dimension canonical state model (stage / work_status / attention / focus / health) with deterministic display-label mapping. | Accepted with v1.1 (trail entry 53). |
| ADR-014 *(v1.1)* | Model the structure as an arbitrary-depth typed-role tree; Tasks are leaves with a promotion rule. | Accepted with v1.1 (trail entry 53). |
| ADR-015 *(v1.1)* | One canonical store per object type with a global, store-independent identifier contract. | Accepted with v1.1 (trail entry 53). |
| ADR-016 *(v1.1)* | Add the protection layer: identity above channel, input trust envelope, data classes with render policy, append-only action log, resilience with watchdog, idempotent consequential actions. | Accepted with v1.1 (trail entry 53). |
| ADR-017 *(v1.1)* | Replace the wave rollout with staged activation governed by baselines, per-stage gates, security prerequisites, and a capacity model; nothing is removed from the vision. | Accepted with v1.1 (trail entry 53). |
| ADR-018 *(v1.1)* | Split checkpoints into protected and generated fields; harden recovery with worker-session records and reconciliation-on-resume. | Accepted with v1.1 (trail entry 53). |
| ADR-019 *(v1.1)* | Adopt the program governance model: Fable architect/PM/gate approver, ChatGPT independent verifier, Opus 4.8 builder, Sonnet reader/librarian, owner final authority, with the eleven-item stage-gate packet. | Accepted by owner 2026-07-25. |
| ADR-020 *(v1.2 — CP-v1.2-A)* | Adopt the peer workflow's Task/Delivery/Rework packet contracts, structural development/production trust-boundary invariant, build-specific release-state profile, disposable review/integration worktrees, sandboxed review execution, and pinned final-combined-tree gate as concrete Application Development mechanisms. Preserve the AI OS multi-role governance, operational-DB identity/state ownership, independent evidence authority, provider portability, and risk-selected repository topology; do not adopt reviewer/integrator fusion or a mandatory physical two-repository topology. | Accepted in v1.2 (owner acceptance 2026-07-27, trail entry 65; plan owner-approved trail entry 54; released via TASK-0001, trail entry 59). |
| ADR-021 *(v1.3 — CP-v1.2-B)* | **External managed-memory provider direction.** **Status:** Accepted in v1.3 (owner acceptance 2026-07-28, trail entry 73). **Context:** The owner directed (trail entry 62) that knowledge memory be fulfilled by an external managed-memory application in the G-Brain mold — concept, not product commitment — so memory is automatic and never a user-managed task; the Herk/Karpathy file-wiki pattern is not adopted as the primary memory implementation. **Decision:** The MEM-04 memory contract is fulfilled by an external managed-memory provider bound by MEM-08. The provider remains a derived knowledge layer; canonical ownership under MEM-01 and §5.2.1 is unchanged — workflow state, approved decisions/rules/policies, credentials, and action authority never migrate to the provider. Provider selection and authorization of external data transfer are separate, later gated decisions with their own evidence. **Consequence:** Stage 1–2 memory work targets contract conformance and admission/grounding/dispute mechanics rather than provider integration; ADR-011 (memory-contract-before-provider) is reaffirmed. | Accepted v1.3 (trail entry 73) |
| ADR-022 *(v1.3 — CP-v1.2-B)* | **Grant-once, activate-staged onboarding.** **Status:** Accepted in v1.3 (owner acceptance 2026-07-28, trail entry 73; FLAG-1 confirmed at plan approval, trail entry 64). **Context:** The owner rejects trickle access requests: *"I like to give all access up front so that it isn't a series of trickle requests. I like to be fully set up before I begin using."* (trail entry 62). The accepted baseline requires staged activation behind protection gates (C-03/04/05; §11A.7; §17). **Decision:** Onboarding is one coordinated session per ONB-01: all currently known integration grants are collected once through a protected secret-management surface — secret values never enter Discord, model context, interview records, repositories, or ordinary logs; models receive handles and scopes only. Granted capabilities activate internally as their §11A.7 gates pass, without owner interaction. Later owner action occurs only for credential expiry, revocation, rotation, recovery, new integrations, changed scope, or risk-tiered step-up, batched and explained whenever feasible. **Consequence:** The owner experience is "fully set up before I begin"; staged-activation guarantees are preserved; no accepted v1.1 decision is reopened. | Accepted v1.3 (trail entry 73) |

> *Amendment (v1.4, CP-P2-A Item 0):* the Builder assignment changed from Claude Opus 4.8 to **Claude Opus 5** at trail entry 69 (owner-authorized standing substitution, ratified at trail entry 82); role boundaries unchanged. The 2026-07-25 decision text above is preserved as written.

> **End of Version 1.1 — accepted baseline:** the independent audit and peer verification completed with zero dissents; all Critical/High consensus changes, verifier findings G-01/G-02/G-03, and the H-08 erratum are incorporated above. The owner accepted this baseline on 2026-07-25 (trail entry 53); the AUD-01 gate is passed. Phase 2 (Decision Engine discovery) opens only after TASK-0002's v1.3 release, receipt, and owner-acceptance gates complete, unless superseded by a later owner decision. These gates completed with the owner’s v1.3 acceptance (2026-07-28, trail entry 73); Phase 2 is open.
