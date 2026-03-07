---
stepsCompleted:
  - step-01-init
  - step-02-discovery
  - step-02b-vision
  - step-02c-executive-summary
  - step-03-success
  - step-04-journeys
  - step-05-domain
  - step-06-innovation
  - step-07-project-type
  - step-08-scoping
  - step-09-functional
  - step-10-nonfunctional
  - step-11-polish
  - step-e-01-discovery
  - step-e-02-review
  - step-e-03-edit
inputDocuments:
  - _bmad-output/research/competitive-patterns-2026-03-06.md
  - _bmad-output/research/transcript-to-product-decisions-2026-03-07.md
  - _bmad-output/research/actionable-architecture-decisions-2026-03-06.md
  - docs/archive/research/competitive-patterns.md
  - _bmad-output/brainstorming/brainstorming-session-2026-03-05-19h30.md
  - docs/archive/brainstorming/brainstorming-session-2026-03-05.md
  - docs/README.md
  - docs/decisions/transcript-product-decisions.md
  - docs/decisions/architecture-decisions.md
  - docs/implementation/README.md
documentCounts:
  briefCount: 0
  researchCount: 4
  brainstormingCount: 2
  projectDocsCount: 4
workflowType: prd
workflow: edit
initializedAt: 2026-03-07T00:50:31+01:00
classification:
  projectType: saas_b2b
  domain: general
  complexity: high
  projectContext: brownfield
lastEdited: 2026-03-07T02:15:00+01:00
editHistory:
  - date: 2026-03-07T02:15:00+01:00
    changes: Refined success measurability, narrowed domain classification, clarified domain boundary, strengthened selected FRs, and rewrote NFRs as testable criteria.
---

# Product Requirements Document - DLE-SaaS

**Author:** Axel
**Date:** 2026-03-07T00:50:31+01:00

## Executive Summary

DLE-SaaS is a B2B electronic batch record platform designed for cosmetics manufacturing environments that require ISO 22716-aligned rigor without the deployment weight of a full MES. The product digitizes the dossier de lot workflow for fabrication and conditionnement, with a primary objective of improving dossier completeness, signature quality, review readiness, and audit traceability before QA handoff.

The product is built around a practical operational reality: operators work on shared line workstations, documentation quality failures are frequent, and the main business pain is not process orchestration in the broad MES sense, but incomplete, poorly reviewed, or late-reviewed batch documentation. DLE-SaaS addresses this by turning the batch record into a guided execution workflow with progressive save, structured step completion, explicit signatures, and reviewable state transitions.

The target outcome is a lightweight but credible software product that improves first-pass-right documentation, reduces avoidable QA review friction, and provides a defensible digital audit trail. The first implementation scope is intentionally narrow: one real client flow, one representative dossier template, and a workflow optimized for execution, pre-QA review, quality review, and release readiness.

### What Makes This Special

DLE-SaaS is not positioned as a generic form builder, nor as a broad manufacturing suite. Its differentiator is the combination of operator-speed execution, business-level signature semantics, explicit pre-QA review, separate quality review surfaces, and traceable document state after corrections. This makes it structurally closer to the real needs of dossier discipline than either paper records, generic workflow tools, or heavyweight MES platforms.

The core product insight is that the highest-value problem is documentary reliability, not simple digitization. Users do not primarily need more data capture screens; they need a system that makes missing entries, missing signatures, review gaps, and late corrections visible and manageable before dossier handoff. The product therefore creates value by enforcing completeness, preserving context, and making review operationally usable rather than merely technically auditable.

Users should choose this product because it gives them a rigorous digital batch record workflow that remains narrower, faster to adopt, and easier to operate than enterprise manufacturing suites, while being substantially more structured, reviewable, and audit-ready than spreadsheets, paper, or generic forms tooling.

## Project Classification

- **Project Type:** B2B SaaS web application for regulated industrial workflow execution and review
- **Domain:** Regulated manufacturing documentation / electronic batch record workflow for cosmetics manufacturing
- **Complexity:** High
- **Project Context:** Brownfield planning context with existing product decisions, domain research, and implementation references

## Success Criteria

### User Success

User success means operators can complete batch record steps on shared line workstations without resorting to paper or side spreadsheets, and production supervisors can catch dossier defects before QA handoff. Over the first 30 pilot batches, at least 95% of mandatory fields and required signatures should be completed before QA handoff as measured by batch completeness reports.

Users should also experience a clearer and safer review process than paper. In pilot review logs, at least 80% of dossiers requiring correction should be sent back by pre-QA review before quality review begins, and quality reviewers should be able to complete at least 90% of standard dossier reviews without consulting external notes or raw audit logs.

### Business Success

Within the first pilot, the product must prove that a real client dossier can be executed end-to-end in software with credible signatures, structured review, and audit-ready traceability. That outcome is achieved when one representative dossier flow runs successfully in a production-like UAT environment for at least 10 consecutive test batches without requiring ERP or WMS integration.

At the business level, success means the pilot answers three customer concerns decisively in a single demonstration: this is a real software product, electronic signatures work in an operator context, and Excel-derived calculations can be integrated in a governed way. A follow-on business success signal is stakeholder approval to continue from pilot to next-scope planning based on the pilot demo and validation evidence.

### Technical Success

Technical success means the system supports versioned MMR templates, batch snapshotting at instantiation, progressive save by step, explicit signature events, visible re-review states after change, and a review workflow separate from operator execution. These invariants should pass automated or integration tests for 100% of covered scenarios before pilot sign-off.

Technical success also means the product preserves trust: no hidden mutation of in-progress batch templates, no ambiguity about what was signed, and no review state buried only in audit data. The architecture must demonstrate that template revision, changed-since-review state, and governed calculation behavior work correctly in local and demo environments without dependence on heavy enterprise infrastructure.

### Measurable Outcomes

- A pilot user can execute a representative fabrication or conditionnement dossier entirely in the application for 10 consecutive UAT test batches.
- At least 95% of mandatory fields and required signatures are completed before QA handoff across the first 30 pilot batches.
- Pre-QA review identifies dossier completeness issues before quality review on at least 80% of batches that require correction.
- Quality review is completed from a dedicated review interface in at least 90% of standard pilot reviews without external notes or raw log reconstruction.
- The pilot demonstrates at least one governed calculation derived from current Excel logic with matching expected output in 100% of approved test cases.
- The system produces a dossier export for a representative batch that management and QA accept as usable for review and audit discussion.
- The first rollout proves operational value without mandatory ERP or WMS integration in UAT or pilot execution.

## Product Scope

### MVP - Minimum Viable Product

The MVP should include one real client template, one representative batch creation and execution workflow, step-based guided data entry for fabrication and/or conditionnement, progressive save, mandatory field enforcement, one or two meaningful signature checkpoints, a pre-QA review stage, a dedicated quality review surface, and a readable dossier export. It must also demonstrate audit-relevant change visibility and at least one Excel-derived calculation handled by the backend.

### Growth Features (Post-MVP)

Post-MVP growth should include a structured exception or deviation workflow, stronger review-by-exception capabilities, improved PDF/review artifact output, broader template reuse across product variants, optional equipment references, label references or scans, and richer collaboration between production and QA during review and correction.

### Vision (Future)

The long-term vision is a configurable electronic batch record platform that can support multiple templates, multiple sites within a group, governed template propagation, richer traceability objects, and a stronger quality operating model while remaining operationally lighter than a full MES. Over time, the platform can expand toward multilingual support, site-level governance, more advanced calculation logic, and selective integrations where they create clear operational value.

## User Journeys

### Journey 1: Line Operator Executes a Batch Record Successfully

Nadia is an operator on a production line working during a busy shift. Today, she is responsible for completing a fabrication step on a shared workstation that several team members may use over the course of the batch. On paper, this kind of work often leads to missing entries, delayed signatures, and uncertainty about whether the dossier is really complete. Her goal is not to "use software"; her goal is to complete her production work correctly without creating documentation problems for the next person or for QA.

She logs into DLE-SaaS, opens the active batch, and sees a step-by-step execution flow rather than a static document. Each step tells her what must be completed, what is optional, and where a signature or confirmation will be required. She enters the required values, sees validation feedback immediately, and saves progress without needing to finish the full dossier in one session. When she reaches a meaningful checkpoint, she signs with clear understanding of what the signature means.

The key value moment is that Nadia does not need to guess whether the record is complete enough to move forward. The system makes missing information visible before the dossier leaves production. She finishes her work with confidence that her part of the batch record is legible, attributable, and review-ready.

This journey reveals requirements for guided step rendering, progressive save, shared-workstation usability, required field validation, checkpoint signatures, and clear status visibility per step.

### Journey 2: Operator or Team Member Handles an Incomplete or Corrected Step

Later in the same batch, Karim resumes work on the line after another operator has already completed part of the dossier. He discovers that a previous step is missing a required value, and one signed section now needs a correction because a number was entered incorrectly. In the paper world, this creates ambiguity: who changed what, why it changed, and whether QA will accept the correction.

In DLE-SaaS, Karim can see that the step is incomplete or has changed after review. The system does not silently overwrite the record. Instead, it surfaces the state clearly, prompts for the appropriate reason for change where needed, and preserves the fact that the dossier may require renewed review. Karim can continue the operational flow without losing traceability or creating undocumented corrections.

The emotional turning point in this journey is recovery without panic. Instead of fearing that a correction will make the dossier harder to defend, the user sees a controlled path for fixing the issue. The product turns a common documentation failure mode into a managed workflow.

This journey reveals requirements for visible incomplete states, correction workflows with reason capture, changed-since-review semantics, attributable edits, and safe continuation after partial or interrupted execution.

### Journey 3: Production Supervisor Performs Pre-QA Review Before Handoff

Sophie is a production supervisor responsible for ensuring that dossiers are reasonably clean before they reach quality. In the current process, many issues are discovered too late, after the dossier has already been handed off. Her real need is not to re-read every line manually from scratch, but to know quickly where the record is incomplete, unsigned, inconsistent, or requires attention.

She opens the batch in a pre-QA review view that is separate from the operator execution flow. Instead of being forced through data entry screens, she sees a review-oriented picture of the dossier: step completion states, missing signatures, changed records, and flagged issues. She can move directly to the areas that need attention, coordinate with production if corrections are needed, and decide whether the dossier is ready for quality handoff.

The critical value moment is that Sophie can stop acting as a human audit parser. The system helps her review by exception and focus only on what threatens dossier completeness. Her success is measured by catching issues before QA receives the dossier.

This journey reveals requirements for a dedicated pre-QA review surface, review-by-exception signals, aggregated dossier status, visibility of missing signatures and changed content, and a clear handoff state from production to quality.

### Journey 4: Quality Reviewer Reviews and Prepares Release Decision

Claire works in quality and receives dossiers after production handoff. Her responsibility is not just to see the final values, but to understand whether the dossier is complete, who signed critical points, what changed after review, and whether any deviation-like issue remains unresolved. On paper or in weak digital systems, this means piecing together context from annotations, scanned documents, or fragmented logs.

In DLE-SaaS, Claire enters a quality review workflow designed for checking rather than doing. She can inspect the batch by step, see signature meaning and timestamps, review correction history, and understand whether the dossier is in a stable reviewable state. She does not need to infer whether the record was modified after signature; the system makes that visible. If the dossier is ready, she can move toward release with confidence. If not, she has enough context to reject or return it with a clear rationale.

The key value moment here is trust. Claire is not simply reading data; she is assessing document integrity. The product succeeds when it makes that integrity visible without forcing her into raw audit-log archaeology.

This journey reveals requirements for a dedicated quality review interface, signature context, change traceability, explicit review states, exception visibility, and support for release-ready dossier inspection.

### Journey 5: Internal Configurator Prepares and Governs a Client Template

Axel, acting as internal product operator or configurator, prepares the first client dossier template based on an existing paper master record. He is not trying to give the customer a self-service form builder in v1; he needs a controlled way to define a usable digital template, activate the correct version, and ensure that future batch instances use the right snapshot without affecting in-progress records.

He creates or updates an MMR version, structures the dossier into executable steps, maps required fields and calculations, and marks where signature checkpoints belong. Once the version is ready, he activates it for use in real batches. Later, if the template must change, he creates a new version rather than mutating an in-progress batch context. This lets him improve the product without compromising traceability.

The value moment in this journey is governance. The platform is not just a runtime UI; it is a controlled template system that can evolve client by client and eventually site by site.

This journey reveals requirements for template versioning, controlled activation, batch snapshotting, backend-managed calculations, and admin tooling that preserves trust in live execution records.

### Journey Requirements Summary

These journeys reveal the need for five major capability groups:

- Guided execution capabilities: step-based UI, progressive save, validation, clear completion states, and shared-workstation usability.
- Trust and traceability capabilities: business-level signatures, attributed changes, reason-for-change capture, and visible changed-since-review states.
- Review capabilities: separate pre-QA and quality review surfaces, review-by-exception signals, dossier readiness indicators, and release-oriented inspection flows.
- Recovery capabilities: safe correction handling, incomplete-step visibility, interruption recovery, and controlled continuation after documentation issues.
- Governance capabilities: versioned MMR templates, controlled activation, batch snapshotting, and vendor-operated template administration.

## Domain-Specific Requirements

### Compliance & Regulatory

- The product must support cosmetics manufacturing environments operating with ISO 22716-aligned documentary rigor.
- The system must preserve a defensible audit trail for creation, modification, review, and release-relevant actions.
- Electronic signatures must be captured as business events with signer identity, timestamp, meaning, and signed context.
- Corrections made after review or signature must remain visible and must trigger explicit re-review semantics where applicable.
- The system must support inspection-ready dossier output suitable for internal quality review and external audit discussion.
- The product should be designed for high documentary rigor without assuming full pharmaceutical workflow complexity in v1.
- Audit trail review must be operationally linked to record review and batch-release review, not treated as a separate technical artifact.

### System Boundary & Governance

- The MVP product governs dossier execution, review, signatures, and release readiness; it does not issue real-time commands to PLC, SCADA, DCS, or other plant control systems.
- Equipment, label, ERP, and WMS references are documentary or contextual in MVP unless a later phase adds explicit live integration behavior.
- Template approval, template activation, and regulated workflow changes must be attributable to named internal roles and recorded with approval decision, timestamp, and change summary.
- Site quality and product owners must be able to determine which template version, approval decision, and change summary were in force for every batch instance.
- Cybersecurity requirements in MVP apply to shared workstations, user authentication, audit integrity, and regulated record protection rather than direct control of industrial OT networks.

### Technical Constraints

- The platform must support shared-workstation usage in production environments without losing attribution, continuity, or signature integrity.
- In-progress batch records must be instantiated from a frozen template snapshot so later template edits cannot mutate live execution records.
- Critical calculations derived from existing Excel logic must be governed on the backend rather than trusted to frontend-only execution.
- Access control must support distinct operational roles such as operator, production reviewer, quality reviewer, and internal configurator.
- The system must make review-relevant state explicit, including incomplete steps, missing signatures, changed-after-review records, and unresolved issues.
- The architecture must remain portable and deployable without dependency on heavy enterprise infrastructure.
- The solution must support a degraded operating mode for system outage or infrastructure failure so production documentation can continue in a controlled way.
- The system must be designed with cybersecurity and data integrity controls appropriate for regulated production records.

### UX & Human Factors Constraints

- The operator experience must be faster and clearer than paper for the core workflow, otherwise adoption risk remains high even if compliance is improved.
- The execution UI must be narrow, step-based, and optimized for doing, while review interfaces must be optimized for checking, filtering, and approving.
- The digitalization effort must simplify the dossier where possible before reproducing it electronically; the goal is not to preserve paper complexity by default.
- The product must minimize cognitive load in production by showing only the data, actions, and signatures relevant to the current step.
- The system should surface errors and omissions early, during execution, rather than shifting the detection burden to end-of-batch review.
- Users must have contextual access to work instructions, procedures, or supporting references during execution when needed.
- Training, onboarding, and change management must be role-specific, because operators, supervisors, QA reviewers, and configurators do not adopt the system in the same way.

### Integration Requirements

- The MVP must not depend on ERP or WMS integration to prove value.
- The architecture should remain compatible with later integration to ERP, WMS, and site-level systems if the pilot succeeds.
- Template configuration must support translation of existing paper master batch records into governed digital templates.
- The platform should preserve room for future references to labels, equipment, and supporting artifacts without making them blocking in v1.

### Risk Mitigations

- Risk: The product becomes a generic form tool and loses batch-record semantics.
  Mitigation: Keep explicit business objects and workflows for template versions, batch instances, signatures, review states, and issues.

- Risk: Corrections after review become technically logged but operationally invisible.
  Mitigation: Surface changed-since-review and changed-since-signature states directly in the workflow and review UI.

- Risk: Operator UX becomes too heavy for line usage.
  Mitigation: Keep execution step-based, narrow, and optimized for shared workstation realities rather than suite-style navigation.

- Risk: The digital system simply reproduces paper complexity and creates a slower workflow.
  Mitigation: Perform dossier simplification and gap analysis before template digitization, and validate the result with end users.

- Risk: Adoption fails because the transition changes habits too abruptly.
  Mitigation: Plan role-based training, user testing, phased rollout, and explicit change-management support for production and quality teams.

- Risk: Template changes compromise trust in live records.
  Mitigation: Enforce version activation and batch snapshotting so in-progress lots remain historically stable.

- Risk: Review remains as manual and late as in the paper process.
  Mitigation: Introduce a dedicated pre-QA review stage and a separate quality review surface with review-by-exception visibility.

- Risk: System failure or cyber incident blocks documentation continuity.
  Mitigation: Define degraded-mode procedures, backup/recovery expectations, and data-protection controls as part of the operating model.

## SaaS B2B Specific Requirements

### Project-Type Overview

DLE-SaaS is a regulated B2B web application designed for operational execution, review, and governance of electronic batch records in cosmetics manufacturing. Unlike generic SaaS products centered on self-serve growth or broad collaboration, this product is anchored in controlled workflows, role-based access, document integrity, and operational trust. Its SaaS character matters primarily through configurability, portability, maintainability, and future multi-site expansion rather than through marketplace-style packaging or product-led onboarding.

The first product slice should be treated as a focused enterprise workflow application: narrow initial scope, strong role separation, controlled template governance, and a deployment model that starts simply while preserving future extensibility.

### Technical Architecture Considerations

The architecture should support a web-based application with a monolithic backend and separate frontend, optimized for regulated workflow execution rather than consumer-scale interaction patterns. The product does not require full active multi-tenancy in v1, but the data model and permission model should be compatible with future organization and site scoping.

Because the product will likely expand client by client and site by site, the architecture should preserve clear boundaries between:
- platform-level governance
- customer or organization ownership
- site-level operational scope
- template version ownership
- batch execution instances

The system should remain portable in deployment and simple enough for an early pilot while avoiding design choices that would block later segregation by customer, site, or template governance domain.

### Tenant Model

The MVP should not implement complex active multi-tenancy such as tenant provisioning automation, tenant-isolated runtime orchestration, or schema-per-tenant architecture. The preferred initial model is a controlled single-customer deployment with data structures that are already compatible with future `organization` and `site` scoping.

This means the product should be designed so that:
- a batch belongs to a site
- templates can later be scoped to an organization or site
- permissions can later be constrained by organizational boundaries
- future multi-site rollout does not require redesign of the core domain model

### RBAC Matrix

The permission model must separate the responsibilities of execution, review, and governance clearly.

Initial roles should include:
- `Operator`: completes assigned execution steps, enters production data, signs authorized checkpoints
- `Production Reviewer / Supervisor`: reviews dossier completeness before QA handoff, identifies missing or inconsistent elements, coordinates corrections
- `Quality Reviewer`: performs quality review, evaluates review-readiness, accepts, rejects, or returns dossier for correction, and handles release decision in the current cosmetics context
- `Internal Configurator / Admin`: manages template structure, versioning, activation, controlled configuration, and administrative oversight

The permission model should prevent ambiguous authority. Users should only see and act on the functions needed for their role, especially around signatures, corrections after review, template changes, and release-related actions.

### Subscription Tiers

No formal subscription-tier model is defined at this stage. The current product context is a focused pilot and early enterprise delivery model rather than a packaged SaaS pricing strategy.

The PRD should therefore avoid inventing commercial tiers and instead note that:
- packaging and pricing are out of scope for the MVP definition
- the immediate concern is proving operational and product value on a real client workflow
- future commercial packaging can be defined after pilot validation and clearer go-to-market structure

### Integration List

The MVP must operate without mandatory ERP or WMS integration. This is a deliberate product decision intended to reduce deployment friction and validate the core workflow independently.

However, the architecture should preserve compatibility with future integrations for:
- ERP context synchronization
- WMS or stock-related reference data
- equipment or instrument references
- label or traceability references
- document export and archival workflows

Integrations should be treated as future capability extensions, not as prerequisites for the first successful delivery.

### Compliance Requirements

As a B2B SaaS product in a regulated manufacturing documentation context, DLE-SaaS must prioritize:
- role-based access control
- attributable user actions
- durable audit trail
- signature integrity
- review traceability
- controlled template versioning
- stable execution records after batch instantiation

The system must support enterprise expectations of trust and governance even before it supports full enterprise integration breadth. In this product category, operational credibility matters more than breadth of features.

### Implementation Considerations

Implementation should favor explicit domain modeling over generic workflow abstractions. The product will be more credible if it exposes clear concepts such as template version, batch, step, signature, review event, release status, and issue record rather than reducing the system to generic forms and permissions.

The first implementation should also assume a vendor-operated product model:
- template design is internal, not self-service
- controlled rollout matters more than broad configurability
- user administration should remain simple and role-driven
- enterprise trust is built through correctness, clarity, and governance rather than through feature abundance

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP Approach:** Problem-solving MVP focused on proving that a real cosmetics batch record workflow can be executed, reviewed, and prepared for release digitally with higher documentary reliability than paper.

The strategic goal of the MVP is not to prove a full manufacturing platform. It is to prove that one real dossier flow can be digitized credibly enough that production and quality users trust it more than the current paper process.

### MVP Feature Set (Phase 1)

**Core User Journeys Supported:**
- Line operator completes a representative fabrication or conditionnement dossier step-by-step
- Operator or team member resumes and corrects incomplete or changed steps with traceability
- Production supervisor performs pre-QA completeness review before handoff
- Quality reviewer reviews dossier state and prepares release decision
- Internal configurator creates and activates a governed template version for the pilot flow

**Must-Have Capabilities:**
- Versioned MMR template with controlled activation
- Batch instantiation from frozen template snapshot
- Step-based execution UI optimized for shared workstation usage
- Progressive save and explicit step status
- Mandatory field validation and missing-data visibility
- One or two meaningful electronic signature checkpoints
- Reason-for-change capture and changed-since-review visibility
- Dedicated pre-QA review surface
- Dedicated quality review surface
- Readable dossier output/export for review and audit discussion
- At least one governed backend-managed calculation derived from current Excel logic
- Role-based access for operator, production reviewer, quality reviewer, and internal configurator

### Post-MVP Features

**Phase 2 (Post-MVP):**
- Structured deviation / exception workflow
- Stronger review-by-exception tooling
- Richer PDF or dossier review artifacts
- Additional dossier templates and product variants
- Equipment references and richer traceability objects
- Label references or scan-assisted traceability
- Improved collaboration loop between production and quality during correction

**Phase 3 (Expansion):**
- Multi-site governance and template propagation
- Broader organization/site scoping across customers or group entities
- More advanced calculation framework
- Selective ERP/WMS integrations
- Multilingual support
- Broader reporting and operational oversight capabilities
- Advanced assistance for review prioritization or exception analysis

### Risk Mitigation Strategy

**Technical Risks:** The highest technical risk is preserving trust semantics across template versioning, signatures, corrections, and review states. Mitigation: keep the first implementation narrow, use explicit domain entities, and avoid generic workflow abstractions.

**Market Risks:** The main market risk is that the software is credible to management but not accepted by operators or production reviewers. Mitigation: validate on one real dossier, optimize the operator path aggressively, and prove review value before expanding scope.

**Resource Risks:** The main resource risk is underestimating the effort required to translate a real paper dossier into a usable digital template with acceptable UX and traceability. Mitigation: limit the first release to one representative workflow, one client context, and a tightly controlled feature set.

## Functional Requirements

### Template Governance

- FR1: Internal configurators can create a master manufacturing record template for a defined dossier workflow.
- FR2: Internal configurators can structure a template into ordered execution steps.
- FR3: Internal configurators can define required and optional data fields within a template step.
- FR4: Internal configurators can associate instructions, references, and supporting context with a template step.
- FR5: Internal configurators can define signature checkpoints within a template.
- FR6: Internal configurators can version templates without overwriting previously approved versions.
- FR7: Internal configurators can activate a specific template version for operational use.
- FR8: The system can instantiate a batch record from the active template version while preserving the originating version reference.

### Batch Execution

- FR9: Operators can access an assigned or relevant batch record and execute it step by step.
- FR10: Operators can enter production data for a batch step.
- FR11: Operators can save progress on an incomplete batch step and resume later.
- FR12: Operators can complete a batch step only when required information for that step is provided or explicitly addressed.
- FR13: Operators can view the current status of each batch step within a dossier.
- FR14: Operators can sign designated execution checkpoints with their own user identity.
- FR15: Up to three authorized production contributors and one production reviewer can contribute to the same batch record over time while preserving user attribution, timestamps, and signed checkpoints for every contribution.

### Data Integrity, Corrections & Traceability

- FR16: The system can record who created, modified, reviewed, or signed dossier data.
- FR17: The system can preserve an audit trail of changes to regulated batch record data.
- FR18: Users can correct previously entered dossier data through a controlled change flow.
- FR19: Users can provide a reason for change when modifying data that requires traceable justification.
- FR20: The system can mark a record or step as requiring re-review after relevant changes.
- FR21: The system can distinguish incomplete, completed, signed, changed, and review-relevant dossier states.
- FR22: Users with review responsibilities can view the history of changes relevant to the dossier.
- FR23: The system can preserve the integrity of in-progress batch records when template versions change later.

### Review, Quality Control & Release Readiness

- FR24: Production reviewers can assess dossier completeness before handoff to quality.
- FR25: Production reviewers can identify missing data, missing signatures, or inconsistent dossier elements requiring correction.
- FR26: The system can represent a pre-QA review state distinct from execution and quality review states.
- FR27: Quality reviewers can review a dossier independently of the operator execution flow.
- FR28: Quality reviewers can inspect signatures, corrections, and review-relevant dossier history.
- FR29: Quality reviewers can accept, reject, or return a dossier for correction based on review findings.
- FR30: The system can represent release readiness and review outcome states for a batch dossier.
- FR31: Quality reviewers can review and disposition dossier-linked issues, deviations, or exception records in MVP by seeing issue status, affected step, author, timestamps, and resolution notes before making a release decision.

### Access Control & Operational Governance

- FR32: The system can manage distinct role-based permissions for operators, production reviewers, quality reviewers, and internal configurators.
- FR33: Users can access only the dossier actions and data appropriate to their role.
- FR34: The system can restrict signature actions to authorized users acting under their own identity.
- FR35: Internal configurators can govern which template versions are available for operational use.
- FR36: The system can associate batches, templates, and permissions with an operational site context.
- FR37: The core domain model can add organization- and site-scoped governance later without changing the meaning of batch, template, step, signature, review event, or release state records created in MVP.

### Dossier Output, References & External Context

- FR38: Users can access a dossier view that shows current step status, signatures, corrections, review state, and release-relevant notes for batch review and audit discussion.
- FR39: Users can generate or access a dossier output or export representing the current batch record state.
- FR40: The system can support governed calculations referenced from dossier templates.
- FR41: Users can open the procedures, work instructions, and supporting references linked to the current step or review context within two clicks from the active workflow screen.
- FR42: The MVP can associate dossier records with label references, equipment references, and supporting attachments as structured reference fields or attachments without requiring live scanner or equipment integration.
- FR43: The system can operate without mandatory ERP or WMS integration for the MVP workflow.
- FR44: The system can expose versioned batch, step, signature, review, and export data through documented interfaces or exports so future ERP, WMS, or archival integrations do not require redesign of the core dossier workflow model.

## Non-Functional Requirements

### Performance

- User-facing step navigation, form save, and dossier status updates shall complete within 2 seconds for the 95th percentile under normal pilot load, as measured by browser telemetry and API monitoring.
- Standard execution and review actions shall complete within 3 seconds for the 95th percentile under 25 concurrent active users, as measured by load testing.
- The system shall support 25 concurrent pilot-site users across operator, production review, and quality review roles with less than 1% failed requests during a 30-minute load test.
- Review screens displaying step status, signatures, and change history for a representative batch shall load within 4 seconds for the 95th percentile during UAT with pilot-like data volume.

### Security

- One hundred percent of authenticated actions shall be attributable to a unique user identity and server timestamp in the audit trail, as verified by integration tests and audit-log sampling.
- Role-based access control shall deny unauthorized actions for every approved role and action pair in the permission matrix, as verified by automated authorization tests.
- One hundred percent of electronic signature events shall require an authenticated signer, explicit signature meaning, server timestamp, and signed-state record, as verified by integration tests.
- One hundred percent of regulated dossier data shall be encrypted in transit and stored using approved at-rest protection controls, as verified by deployment review and security testing.
- Audit records for creation, modification, review, and signature actions shall be retained for one hundred percent of controlled-record events generated in integration tests.
- One hundred percent of template activation, permission changes, and administrative configuration changes shall be restricted to authorized roles, as verified by automated access-control tests.

### Reliability

- The system shall achieve 99.5% availability during defined pilot operating hours, as measured monthly by uptime monitoring.
- The system shall preserve committed step data with zero confirmed data loss in session interruption and failed-save recovery tests across 20 consecutive scenarios.
- Backups of active and historical dossier records shall run at least daily with recovery point objective less than or equal to 24 hours and documented restore verification at least once per month.
- The degraded-mode procedure shall be documented, approved, and successfully rehearsed end-to-end before pilot go-live and after each material workflow change.
- After routine restart or recovery events, one hundred percent of in-progress record state, signature state, and review state shall be restored consistently in recovery tests.

### Accessibility & Usability

- In moderated pilot usability tests, 90% of operators and reviewers shall complete their primary workflow without facilitator intervention after role-based training.
- The execution interface shall present only current-step data, actions, and signatures by default, as verified in UX review for one hundred percent of MVP execution screens.
- One hundred percent of critical operator and reviewer actions shall be executable by keyboard on shared workstations, as verified by accessibility test scripts.
- One hundred percent of validation errors, missing signatures, and review-required changes shall display a clear action message and affected context in UI acceptance tests.
- The UI shall remain usable at 1280x800 and 1920x1080 resolutions in supported desktop browsers, as verified during UAT.

### Integration & Interoperability

- The MVP shall run end-to-end in UAT without live ERP or WMS connectivity, as verified before pilot sign-off.
- Core integration objects for batch, step, signature, review event, and dossier export shall have versioned documented data contracts before external integration work begins.
- A standard dossier export for a representative batch shall be generated within 60 seconds and accepted as usable in internal review and archival checks.
- New integration extensions shall consume documented interfaces around core dossier objects without changing the canonical batch state model, as verified by architecture review before implementation.
