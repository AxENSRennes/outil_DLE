---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
---

# DLE-SaaS - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for DLE-SaaS, decomposing the requirements from the PRD, UX Design, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: Internal configurators can create a master manufacturing record template for a defined dossier workflow.
FR2: Internal configurators can structure a template into ordered execution steps.
FR3: Internal configurators can define required and optional data fields within a template step.
FR4: Internal configurators can associate instructions, references, and supporting context with a template step.
FR5: Internal configurators can define signature checkpoints within a template.
FR6: Internal configurators can version templates without overwriting previously approved versions.
FR7: Internal configurators can activate a specific template version for operational use.
FR8: The system can instantiate a batch record from the active template version while preserving the originating version reference.
FR9: Operators can access an assigned or relevant batch record and execute it step by step.
FR10: Operators can enter production data for a batch step.
FR11: Operators can save progress on an incomplete batch step and resume later.
FR12: Operators can complete a batch step only when required information for that step is provided or explicitly addressed.
FR13: Operators can view the current status of each batch step within a dossier.
FR14: Operators can sign designated execution checkpoints with their own user identity.
FR15: Up to three authorized production contributors and one production reviewer can contribute to the same batch record over time while preserving user attribution, timestamps, and signed checkpoints for every contribution.
FR16: The system can record who created, modified, reviewed, or signed dossier data.
FR17: The system can preserve an audit trail of changes to regulated batch record data.
FR18: Users can correct previously entered dossier data through a controlled change flow.
FR19: Users can provide a reason for change when modifying data that requires traceable justification.
FR20: The system can mark a record or step as requiring re-review after relevant changes.
FR21: The system can distinguish incomplete, completed, signed, changed, and review-relevant dossier states.
FR22: Users with review responsibilities can view the history of changes relevant to the dossier.
FR23: The system can preserve the integrity of in-progress batch records when template versions change later.
FR24: Production reviewers can assess dossier completeness before handoff to quality.
FR25: Production reviewers can identify missing data, missing signatures, or inconsistent dossier elements requiring correction.
FR26: The system can represent a pre-QA review state distinct from execution and quality review states.
FR27: Quality reviewers can review a dossier independently of the operator execution flow.
FR28: Quality reviewers can inspect signatures, corrections, and review-relevant dossier history.
FR29: Quality reviewers can accept, reject, or return a dossier for correction based on review findings.
FR30: The system can represent release readiness and review outcome states for a batch dossier.
FR31: Quality reviewers can review and disposition dossier-linked issues, deviations, or exception records in MVP by seeing issue status, affected step, author, timestamps, and resolution notes before making a release decision.
FR32: The system can manage distinct role-based permissions for operators, production reviewers, quality reviewers, and internal configurators.
FR33: Users can access only the dossier actions and data appropriate to their role.
FR34: The system can restrict signature actions to authorized users acting under their own identity.
FR35: Internal configurators can govern which template versions are available for operational use.
FR36: The system can associate batches, templates, and permissions with an operational site context.
FR37: The core domain model can add organization- and site-scoped governance later without changing the meaning of batch, template, step, signature, review event, or release state records created in MVP.
FR38: Users can access a dossier view that shows current step status, signatures, corrections, review state, and release-relevant notes for batch review and audit discussion.
FR39: Users can generate or access a dossier output or export representing the current batch record state.
FR40: The system can support governed calculations referenced from dossier templates.
FR41: Users can open the procedures, work instructions, and supporting references linked to the current step or review context within two clicks from the active workflow screen.
FR42: The MVP can associate dossier records with label references, equipment references, and supporting attachments as structured reference fields or attachments without requiring live scanner or equipment integration.
FR43: The system can operate without mandatory ERP or WMS integration for the MVP workflow.
FR44: The system can expose versioned batch, step, signature, review, and export data through documented interfaces or exports so future ERP, WMS, or archival integrations do not require redesign of the core dossier workflow model.
FR45: The system can determine which dossier sub-documents are required for a batch based on contextual attributes such as machine or line, format family, and paillette presence.
FR46: The system can model repeated in-process and box-level controls as repeated records within a batch dossier rather than as single static form instances.
FR47: The system can evaluate cross-document dossier rules including required-document presence and consistency checks between fabrication data and governed weighing calculations.
FR48: Production and quality reviewers can see dossier completeness against the expected document checklist for the current batch context before disposition.
FR49: The system does not require reviewer approval or formal release between ordinary production steps in MVP unless a later client-specific critical-control gate is explicitly configured.
FR50: The system can block step completion, signature, and review handoff when applicable required controls are incomplete without blocking unrelated production execution steps.
FR51: The system can mark a control or document as not applicable based on batch context so non-applicable requirements do not block operators or reviewers.

### NonFunctional Requirements

NFR1: User-facing step navigation, form save, and dossier status updates shall complete within 2 seconds for the 95th percentile under normal pilot load, as measured by browser telemetry and API monitoring.
NFR2: Standard execution and review actions shall complete within 3 seconds for the 95th percentile under 25 concurrent active users, as measured by load testing.
NFR3: The system shall support 25 concurrent pilot-site users across operator, production review, and quality review roles with less than 1% failed requests during a 30-minute load test.
NFR4: Review screens displaying step status, signatures, and change history for a representative batch shall load within 4 seconds for the 95th percentile during UAT with pilot-like data volume.
NFR5: One hundred percent of authenticated actions shall be attributable to a unique user identity and server timestamp in the audit trail, as verified by integration tests and audit-log sampling.
NFR6: Role-based access control shall deny unauthorized actions for every approved role and action pair in the permission matrix, as verified by automated authorization tests.
NFR7: One hundred percent of electronic signature events shall require an authenticated signer, explicit signature meaning, server timestamp, and signed-state record, as verified by integration tests.
NFR8: One hundred percent of regulated dossier data shall be encrypted in transit and stored using approved at-rest protection controls, as verified by deployment review and security testing.
NFR9: Audit records for creation, modification, review, and signature actions shall be retained for one hundred percent of controlled-record events generated in integration tests.
NFR10: One hundred percent of template activation, permission changes, and administrative configuration changes shall be restricted to authorized roles, as verified by automated access-control tests.
NFR11: The system shall achieve 99.5% availability during defined pilot operating hours, as measured monthly by uptime monitoring.
NFR12: The system shall preserve committed step data with zero confirmed data loss in session interruption and failed-save recovery tests across 20 consecutive scenarios.
NFR13: Backups of active and historical dossier records shall run at least daily with recovery point objective less than or equal to 24 hours and documented restore verification at least once per month.
NFR14: The degraded-mode procedure shall be documented, approved, and successfully rehearsed end-to-end before pilot go-live and after each material workflow change.
NFR15: After routine restart or recovery events, one hundred percent of in-progress record state, signature state, and review state shall be restored consistently in recovery tests.
NFR16: In moderated pilot usability tests, 90% of operators and reviewers shall complete their primary workflow without facilitator intervention after role-based training.
NFR17: The execution interface shall present only current-step data, actions, and signatures by default, as verified in UX review for one hundred percent of MVP execution screens.
NFR18: One hundred percent of critical operator and reviewer actions shall be executable by keyboard on shared workstations, as verified by accessibility test scripts.
NFR19: One hundred percent of validation errors, missing signatures, and review-required changes shall display a clear action message and affected context in UI acceptance tests.
NFR20: The UI shall remain usable at 1280x800 and 1920x1080 resolutions in supported desktop browsers, as verified during UAT.
NFR21: The MVP shall run end-to-end in UAT without live ERP or WMS connectivity, as verified before pilot sign-off.
NFR22: Core integration objects for batch, step, signature, review event, and dossier export shall have versioned documented data contracts before external integration work begins.
NFR23: A standard dossier export for a representative batch shall be generated within 60 seconds and accepted as usable in internal review and archival checks.
NFR24: New integration extensions shall consume documented interfaces around core dossier objects without changing the canonical batch state model, as verified by architecture review before implementation.

### Additional Requirements

- Epic 1 Story 1 must initialize the official split-stack foundation called out in Architecture: Django 5.2 LTS backend plus Vite React TypeScript frontend.
- The backend and frontend must be delivered as a split-stack application with a clear API boundary; the first implementation sequence should scaffold both applications before domain work expands.
- PostgreSQL 17.x is the authoritative system of record for regulated workflow state.
- Docker Compose is the canonical deployment baseline, with separated `dev`, `uat`, and `prod` environments and rollback-safe release discipline for 3x8 operations.
- The API must be REST-first under `/api/v1`, with OpenAPI generated through drf-spectacular and problem-details style error responses.
- Authentication must use Django server-managed sessions with shared-workstation flows for identify, switch user, lock workstation, and step-up re-authentication for signatures.
- PIN-based identification and signature re-authentication are required operational patterns; failed PIN attempts and identity actions must be audited and rate-limited.
- Workflow transitions must be implemented as explicit backend actions such as draft save, complete, sign, correction, pre-QA confirmation, review mark-reviewed, and quality disposition.
- The backend must own dossier composition rules for conditional forms, repeated controls, checklist completeness, and cross-document consistency checks.
- Database evolution must follow additive expand/contract migrations only; destructive schema changes are not acceptable in the same rollout window.
- Structured logging, audit instrumentation, readiness/liveness checks, and release-health observability are first-class implementation requirements.
- The frontend design-system baseline is mandatory: Tailwind CSS 4, shadcn/ui, and Radix UI primitives.
- The UX must follow a desktop-only workstation model for MVP; mobile and tablet support are out of scope.
- Supported workstation targets are minimum 1280x800 and standard 1920x1080 on modern desktop browsers, with compatibility targets aligned to Chrome 70+, Firefox 68+, and Edge 79+.
- The operator surface must use a persistent batch-kiosk pattern with visible batch context, a persistent identity banner, and fast resume on shared workstations.
- The primary execution layout must be step-first, with a persistent sidebar stepper and single-column step content rather than a full-dossier operator view.
- Data entry must remain keyboard-first; critical workflows must not depend on mouse-only interaction.
- Validation must follow the UX rule "reward early, punish late": validate on blur, do not validate on keystroke, and defer empty-required errors until completion attempt.
- Progressive auto-save with visible save feedback is mandatory; the user must always see whether data is saving, saved, or failed.
- Review surfaces must be review-by-exception, with traffic-light summaries and drill-down into only the items needing attention.
- Changed-since-review and changed-since-signature states must be visually explicit in the UI rather than buried in audit logs.
- Signature flows must use a focused signature ceremony with explicit meaning capture, inline re-authentication, and a persistent signature manifest.
- The product must meet WCAG 2.1 AA expectations, including redundant coding for status, visible focus states, and keyboard accessibility for all critical actions.
- No offline mode is required for MVP, but degraded operating procedures for outage continuity remain a documented reliability requirement.

### FR Coverage Map

FR1: Epic 2 - governed MMR creation
FR2: Epic 2 - ordered step structure
FR3: Epic 2 - field definition
FR4: Epic 2 - step references and instructions
FR5: Epic 2 - signature checkpoints in templates
FR6: Epic 2 - template versioning
FR7: Epic 2 - template activation
FR8: Epic 2 - batch instantiation from active version
FR9: Epic 3 - operator batch access
FR10: Epic 3 - step data entry
FR11: Epic 3 - progressive save and resume
FR12: Epic 3 - step completion gating
FR13: Epic 3 - step status visibility
FR14: Epic 3 - execution signatures
FR15: Epic 3 - multi-contributor shared workstation execution
FR16: Epic 4 - attributed regulated actions
FR17: Epic 4 - audit trail preservation
FR18: Epic 4 - controlled correction flow
FR19: Epic 4 - reason for change
FR20: Epic 4 - re-review trigger after change
FR21: Epic 4 - explicit integrity and review states
FR22: Epic 4 - reviewer access to change history
FR23: Epic 4 - live batch integrity across template changes
FR24: Epic 5 - pre-QA completeness assessment
FR25: Epic 5 - missing or inconsistent dossier detection
FR26: Epic 5 - distinct pre-QA state
FR27: Epic 5 - dedicated quality review flow
FR28: Epic 5 - quality inspection of signatures and corrections
FR29: Epic 5 - accept / reject / return disposition
FR30: Epic 5 - release readiness and review outcomes
FR31: Epic 5 - issue / deviation visibility before release decision
FR32: Epic 1 - role-based permissions
FR33: Epic 1 - role-appropriate access
FR34: Epic 1 - authorized signature authority
FR35: Epic 2 - governance of available template versions
FR36: Epic 1 - site context association
FR37: Epic 1 - future organization/site extensibility
FR38: Epic 5 - dossier review and audit view
FR39: Epic 6 - dossier export access
FR40: Epic 6 - governed calculations
FR41: Epic 3 - in-workflow procedures and references
FR42: Epic 6 - structured references and attachments
FR43: Epic 6 - no mandatory ERP/WMS dependency
FR44: Epic 6 - documented interfaces and export readiness
FR45: Epic 6 - conditional sub-document selection
FR46: Epic 6 - repeated control records
FR47: Epic 6 - cross-document consistency rules
FR48: Epic 5 - completeness checklist before disposition
FR49: Epic 3 - no mandatory reviewer gate between ordinary steps
FR50: Epic 3 - blocking only where required controls are incomplete
FR51: Epic 3 - non-applicable controls do not block workflow

## Epic List

### Epic 1: Platform Spine and Identity Foundation
The product has a minimal executable foundation with the project structure, shared-workstation identity model, baseline RBAC, core API conventions, and site-aware operational context needed to support parallel delivery safely.
**FRs covered:** FR32, FR33, FR34, FR36, FR37

### Epic 2: Governed Template Management
Internal configurators can create, version, activate, and govern MMR templates so real batches can start from trusted operational definitions.
**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR6, FR7, FR8, FR35

### Epic 3: Guided Batch Execution
Operators can identify quickly on a shared workstation, execute the active batch step by step, save and resume safely, sign required checkpoints, and access the instructions they need inside the workflow.
**FRs covered:** FR9, FR10, FR11, FR12, FR13, FR14, FR15, FR41, FR49, FR50, FR51

### Epic 4: Traceability and Controlled Corrections
Production users and reviewers can correct dossier data through controlled flows while preserving attribution, auditability, visible integrity states, and protection of live batch records against later template changes.
**FRs covered:** FR16, FR17, FR18, FR19, FR20, FR21, FR22, FR23

### Epic 5: Review and Release Workflow
Supervisors and quality reviewers can review dossiers by exception, inspect signatures and history, manage issues before release, and make clear disposition decisions from dedicated review surfaces.
**FRs covered:** FR24, FR25, FR26, FR27, FR28, FR29, FR30, FR31, FR38, FR48

### Epic 6: Contextual Dossier Composition and Export
The system can assemble the correct dossier for each batch context, apply governed calculations and checklist rules, support structured references, and produce export and integration-ready outputs without requiring ERP or WMS coupling.
**FRs covered:** FR39, FR40, FR42, FR43, FR44, FR45, FR46, FR47

## Epic 1: Platform Spine and Identity Foundation

The product has a minimal executable foundation with the project structure, shared-workstation identity model, baseline RBAC, core API conventions, and site-aware operational context needed to support parallel delivery safely.

### Story 1.1: Initialize the Split-Stack Foundation

As a product engineering team member,
I want a runnable split-stack workspace with shared backend, frontend, database, and environment conventions,
So that parallel development on later epics can start from a stable and consistent foundation.

**Acceptance Criteria:**

**Given** the repository is prepared for the first implementation slice
**When** the foundation story is completed
**Then** a Django backend project exists under `backend/` and a Vite React TypeScript frontend exists under `frontend/`
**And** both applications start successfully in local development.

**Given** the platform foundation is intended to support regulated workflow development
**When** the backend is scaffolded
**Then** PostgreSQL is configured as the primary application database for local development
**And** the project structure preserves a clean backend/frontend separation aligned with the architecture artifact.

**Given** multiple future epics should be developed in parallel
**When** developers start from this foundation
**Then** a canonical `Docker Compose` development baseline and environment configuration template are available
**And** they can run the stack without inventing local conventions per epic.

**Given** later stories will build APIs and workflow features independently
**When** the initial backend and frontend shells are delivered
**Then** the backend exposes a basic health or readiness endpoint and the frontend exposes a basic application shell
**And** both are ready to accept feature work without restructuring the repository again.

**Given** this project must preserve consistency across future implementation agents
**When** the foundation is reviewed
**Then** the initial file layout matches the approved architecture boundaries at a minimal level
**And** no domain-specific tables, endpoints, or feature modules beyond what this story needs are created prematurely.

### Story 1.2: Establish Site-Aware Roles and Access Policy

As a product engineering team member,
I want a baseline site-aware identity and authorization model,
So that every later feature can rely on consistent role-based access without redesigning the core domain.

**Acceptance Criteria:**

**Given** the platform foundation is already available
**When** this story is completed
**Then** the backend contains the minimal domain structures needed for users, operational sites, and role assignments
**And** those structures support at least the MVP roles `Operator`, `Production Reviewer`, `Quality Reviewer`, and `Internal Configurator`.

**Given** the MVP must control access by operational responsibility
**When** a user is associated with one or more roles
**Then** the system can determine which actions and data are permitted for that user
**And** unauthorized access attempts are denied by backend policy rather than frontend visibility alone.

**Given** the product must remain compatible with future organization and site expansion
**When** the initial authorization model is defined
**Then** site context is part of the core access model from the start
**And** the design leaves room for later organization-scoped governance without changing the meaning of existing batch, template, and review records.

**Given** multiple epics will be developed in parallel
**When** feature teams start building template, execution, review, or export capabilities
**Then** they can depend on a single canonical role and site access convention
**And** they do not need to invent feature-local permission rules.

**Given** this story should remain narrowly scoped
**When** it is implemented
**Then** it delivers the domain model, baseline authorization checks, and documented role-policy conventions only
**And** it does not yet implement full workstation switching or signature ceremony behavior.

### Story 1.3: Implement Shared-Workstation Identification and Signature Authority Guardrails

As an operator or reviewer working on a shared production workstation,
I want the system to identify the active user securely and enforce signature authority rules,
So that work attribution remains correct and only authorized users can perform regulated signature actions.

**Acceptance Criteria:**

**Given** a shared workstation is used by multiple people across shifts
**When** a user identifies on the workstation
**Then** the backend establishes the active authenticated session for that user
**And** the system preserves the current workstation context without requiring full application re-entry.

**Given** one user may leave and another may take over the same workstation
**When** the active user switches or the workstation is locked
**Then** the prior authenticated authority is removed from the active session
**And** a later user must identify again before performing authenticated actions.

**Given** only authorized users may sign regulated actions
**When** a signature-protected action is requested
**Then** the system verifies that the active user holds a role permitted for that signature context
**And** unauthorized signature attempts are rejected server-side.

**Given** the platform must preserve a trustworthy audit trail from the start
**When** identification, switch-user, lock, failed identification, or signature-authorization events occur
**Then** those events are recorded with actor, timestamp, and event type
**And** they are available for later review and troubleshooting.

**Given** this story is part of the platform spine rather than full workflow execution
**When** it is implemented
**Then** it provides the shared-workstation session and signature-guardrail backend behavior plus minimal API support
**And** it does not yet require full operator execution UI, step signing UI, or batch-specific workflow logic.

## Epic 2: Governed Template Management

Internal configurators can create, version, activate, and govern MMR templates so real batches can start from trusted operational definitions.

### Story 2.1: Create the MMR and Draft Version Lifecycle Baseline

As an internal configurator,
I want to create a master manufacturing record and open a draft version for it,
So that template work starts in a governed structure instead of ad hoc documents or uncontrolled edits.

**Acceptance Criteria:**

**Given** a configurator needs to prepare a new dossier workflow
**When** they create a new MMR
**Then** the system stores a master template record with its core identifying information
**And** that record can own multiple governed versions over time.

**Given** template changes must be controlled from the start
**When** a configurator creates a working version for an MMR
**Then** the system creates that version in a draft state
**And** the version is clearly linked to its parent MMR.

**Given** approved history must never be overwritten
**When** a configurator starts a new version for an existing MMR
**Then** the system creates a separate version record rather than mutating a prior governed version
**And** earlier versions remain historically intact.

**Given** later stories will add step definitions, fields, and activation behavior
**When** this story is implemented
**Then** the draft version lifecycle is available as a minimal governed backbone
**And** no step structure, field schema, or activation workflow is required yet.

**Given** multiple epics and stories will later depend on trusted template identity
**When** this story is completed
**Then** template and version identifiers are stable and usable by later stories
**And** they establish the canonical foundation for activation and batch instantiation.

### Story 2.2: Define Ordered Template Steps and Step-Level Guidance

As an internal configurator,
I want to define the ordered steps of a template and attach operational guidance to each step,
So that operators later execute a structured dossier flow instead of a flat uncontrolled form.

**Acceptance Criteria:**

**Given** a draft template version already exists
**When** a configurator adds step definitions to that version
**Then** the system stores an ordered list of execution steps for that template version
**And** the order is explicit and stable for later execution use.

**Given** operators need contextual support while working
**When** a configurator edits a template step
**Then** they can associate that step with instructions, references, or supporting context
**And** that guidance remains attached to the specific step definition.

**Given** template structure must remain governable
**When** a configurator reorders, adds, or removes draft steps
**Then** the system updates only the current draft version structure
**And** no previously governed version is modified.

**Given** later stories will add fields and signature checkpoints
**When** this story is completed
**Then** step structure and guidance are available as a standalone capability
**And** field schemas and signature definitions are still out of scope for this story.

**Given** later execution stories will rely on a predictable template sequence
**When** this story is reviewed
**Then** the step model is sufficient to drive future step-by-step execution ordering
**And** no future story inside this epic is required to make the ordered step list itself valid.

### Story 2.3: Configure Step Fields and Signature Checkpoints

As an internal configurator,
I want to define the required data fields and signature checkpoints inside a draft template,
So that each step contains the structured inputs and approval moments needed for governed execution.

**Acceptance Criteria:**

**Given** a draft template version already contains ordered steps
**When** a configurator edits a step
**Then** they can add field definitions to that step
**And** each field can be marked with the basic properties needed for later execution, including whether it is required or optional.

**Given** later execution depends on predictable field structure
**When** a configurator saves field definitions
**Then** the system stores them as part of the current draft version only
**And** existing governed versions remain unchanged.

**Given** some steps require regulated confirmation
**When** a configurator marks a point in the template as requiring signature
**Then** the system records a signature checkpoint linked to the relevant step or step transition
**And** that checkpoint is available for later execution and review flows.

**Given** the product must support guided execution without implementing all runtime logic yet
**When** this story is completed
**Then** the template contains enough governed metadata to describe step inputs and signature locations
**And** it does not yet require live batch execution, step completion rules, or signature ceremony UI.

**Given** future stories will instantiate live batches from template definitions
**When** this story is reviewed
**Then** the stored step-field and signature-checkpoint definitions are sufficient for downstream batch snapshotting and workflow implementation
**And** no later story in this epic is needed to make the draft template structurally complete.

### Story 2.4: Activate a Governed Template Version for Operational Use

As an internal configurator,
I want to activate a specific template version for operational use,
So that batch creation always starts from an explicitly governed and selectable version.

**Acceptance Criteria:**

**Given** an MMR has one or more versions
**When** a configurator activates a version
**Then** the system marks that version as operationally active for its intended context
**And** later batch creation can resolve that version as the authoritative starting point.

**Given** governed templates must not be ambiguous in operation
**When** a version becomes active
**Then** the system enforces a clear activation rule for the relevant template scope
**And** users cannot accidentally create new batches from an inactive draft version.

**Given** historical control is required
**When** a configurator activates a newer version
**Then** earlier versions remain preserved as historical records
**And** activation does not retroactively mutate previously created batches or prior governed versions.

**Given** template governance is role-restricted
**When** an unauthorized user attempts activation or activation changes
**Then** the system denies the action server-side
**And** the active operational version remains unchanged.

**Given** this story should remain focused on governance rather than runtime batch creation
**When** it is completed
**Then** activation behavior is fully available as a standalone governed capability
**And** batch instantiation itself is still deferred to a separate story.

### Story 2.5: Instantiate a Batch from the Active Template Snapshot

As an internal configurator or authorized operational user,
I want a new batch to be created from the currently active template version as a frozen snapshot,
So that live execution starts from a trusted definition that will not change if the template evolves later.

**Acceptance Criteria:**

**Given** a template version is active for the intended operational context
**When** a new batch is instantiated from that template
**Then** the system creates a batch record linked to the originating template version
**And** the batch stores a frozen snapshot of the template structure needed for later execution.

**Given** template evolution must not mutate live operational records
**When** the source template is edited or a newer version is activated after batch creation
**Then** the already-created batch remains based on its original snapshot
**And** its execution structure does not change retroactively.

**Given** later execution stories will depend on predictable runtime structure
**When** a batch is created from the active version
**Then** the resulting batch contains enough initial step and template context to support future execution workflows
**And** later stories do not need to reconstruct runtime structure from the current template definition.

**Given** batch creation must respect governed operational setup
**When** a user attempts to instantiate a batch from a non-active or unauthorized template context
**Then** the system rejects the request
**And** only valid active template contexts can be used for batch creation.

**Given** this story belongs to template governance rather than operator execution
**When** it is completed
**Then** the product can reliably create governed batch instances from template snapshots
**And** full step-by-step execution, completion, and signing behavior remain outside the scope of this story.

## Epic 3: Guided Batch Execution

Operators can identify quickly on a shared workstation, execute the active batch step by step, save and resume safely, sign required checkpoints, and access the instructions they need inside the workflow.

### Story 3.1: Open a Batch and Navigate Its Step-by-Step Execution Flow

As an operator on a shared workstation,
I want to open the active batch and move through its ordered execution steps with clear status visibility,
So that I can immediately understand where the dossier stands and continue work without searching through the full record.

**Acceptance Criteria:**

**Given** a governed batch has already been instantiated from a template snapshot
**When** an authorized operator accesses that batch
**Then** the system returns the batch execution view for that operator
**And** the ordered execution steps are presented from the batch snapshot rather than from the current live template definition.

**Given** operators need immediate clarity on shared workstations
**When** the execution flow is displayed
**Then** each batch step shows a visible execution status
**And** the operator can identify the current step and overall progression without opening the entire dossier.

**Given** execution must follow the governed step sequence
**When** the operator navigates between available steps
**Then** the system allows navigation within the batch’s defined execution structure
**And** the active step context is loaded consistently from the batch record.

**Given** the MVP should avoid introducing unnecessary reviewer gates during ordinary production flow
**When** the execution shell is implemented
**Then** the batch navigation model supports normal progression across ordinary steps without requiring pre-QA or quality approval between them
**And** later blocking rules can be applied only where specific required controls demand it.

**Given** this story should remain focused on the base execution shell
**When** it is completed
**Then** operators can access a batch and navigate its step sequence with status visibility
**And** draft save behavior, completion gating, instructions access, and signature actions remain outside the scope of this story.

### Story 3.2: Enter Step Data with Progressive Save and Safe Resume

As an operator on a shared workstation,
I want to enter data into the current batch step and have my progress saved automatically,
So that I can resume work safely after interruptions or user changes without losing what has already been recorded.

**Acceptance Criteria:**

**Given** an operator is working inside an execution step
**When** they enter or update allowed step data
**Then** the system records those draft values against the current batch step
**And** the saved draft remains attached to the live batch record rather than the template.

**Given** production work on shared workstations is frequently interrupted
**When** the operator leaves the step and later returns to it
**Then** previously saved draft values are restored from the batch record
**And** the operator can continue from the last saved state without re-entering completed draft data.

**Given** the UX requires visible save confidence
**When** draft data is saved successfully
**Then** the execution experience exposes a clear saved state indicator
**And** the operator is not forced to use a manual save button for normal progress preservation.

**Given** multiple authorized contributors may work on the same batch over time
**When** one contributor resumes a step previously edited by another
**Then** the saved draft state remains available to continue the work
**And** the batch record preserves who last updated the draft content and when.

**Given** this story should remain separate from completion and signature logic
**When** it is implemented
**Then** operators can enter, auto-save, and resume draft step data reliably
**And** step completion gating, signature checkpoints, and correction workflows remain outside the scope of this story.

### Story 3.3: Complete a Step with Applicable-Control Validation

As an operator on a shared workstation,
I want the system to let me complete a step only when the required applicable controls are satisfied,
So that ordinary production can continue smoothly while dossier completeness is enforced where it actually matters.

**Acceptance Criteria:**

**Given** a batch step contains required and optional controls from the batch snapshot
**When** an operator attempts to complete that step
**Then** the system evaluates only the controls that are applicable to the current batch context
**And** non-applicable controls do not block completion.

**Given** documentary completeness must be enforced at meaningful points
**When** required applicable fields or controls are still incomplete
**Then** the system prevents step completion
**And** it returns clear information about what still needs attention.

**Given** the MVP must not insert reviewer approvals between ordinary execution steps by default
**When** a step is successfully completed
**Then** the operator can continue normal production progression to the next relevant step
**And** no pre-QA or quality approval is required just to move through ordinary execution flow.

**Given** some controls should block only local step outcomes rather than unrelated work
**When** the system detects an incomplete required control
**Then** blocking is applied to the relevant step completion or later review handoff as appropriate
**And** unrelated steps are not globally blocked unless the governed rules explicitly require it.

**Given** this story is focused on step completion behavior rather than signatures
**When** it is implemented
**Then** the product supports governed completion gating for applicable controls
**And** signature-required checkpoints are still handled by a separate story.

### Story 3.4: Access Step Instructions and Supporting References In Context

As an operator on a shared workstation,
I want to open the instructions and supporting references linked to my current step without leaving the workflow,
So that I can complete the batch correctly without searching external folders or paper binders.

**Acceptance Criteria:**

**Given** a batch step inherits instructions or references from its template snapshot
**When** an operator is viewing that step
**Then** the execution experience exposes the linked guidance in context
**And** the operator can access it within the active workflow screen.

**Given** operators need fast access during execution
**When** they request a linked procedure, work instruction, or supporting reference
**Then** the system opens the associated resource in no more than two interactions from the current step
**And** the operator retains their current batch context.

**Given** references may differ by step
**When** the operator moves to another step
**Then** the available instructions and supporting links update to match the active step context
**And** irrelevant references are not shown as if they belonged to the current step.

**Given** this story should remain separate from completion and signature behavior
**When** it is completed
**Then** in-context access to step guidance is fully available as a standalone capability
**And** it does not require implementing completion gating, signature execution, or correction workflows.

**Given** the UX goal is to reduce cognitive load during production
**When** this story is reviewed
**Then** the access pattern supports the step-first execution model
**And** operators are not forced into a full-dossier or off-flow navigation pattern to find guidance.

### Story 3.5: Sign Required Execution Checkpoints with Attributed Identity

As an operator on a shared workstation,
I want to sign the execution checkpoints required by the current step using my own authenticated identity,
So that regulated confirmations are explicit, attributable, and visible in the live batch record.

**Acceptance Criteria:**

**Given** a batch step contains a required execution signature checkpoint
**When** an authorized operator initiates the signature action
**Then** the system requires signature confirmation under that operator’s active identity
**And** the resulting signature is attached to the correct batch step context.

**Given** regulated signatures must be attributable and meaningful
**When** a signature is completed
**Then** the system records the signer identity, timestamp, signature meaning, and signed context
**And** that signature becomes visible in the batch record for later review.

**Given** signature authority is role-restricted
**When** a user without the required permission attempts to sign a protected checkpoint
**Then** the system rejects the action server-side
**And** no signature record is created.

**Given** some steps may require signature before they are considered fully confirmed
**When** a signed checkpoint is successfully completed
**Then** the step status reflects that the required signature has been satisfied
**And** later review flows can distinguish signed steps from merely completed draft steps.

**Given** this story belongs to execution rather than correction or review workflows
**When** it is implemented
**Then** operators can complete required execution signatures as part of the batch flow
**And** post-signature corrections, changed-since-signature handling, and review disposition remain outside the scope of this story.

## Epic 4: Traceability and Controlled Corrections

Production users and reviewers can correct dossier data through controlled flows while preserving attribution, auditability, visible integrity states, and protection of live batch records against later template changes.

### Story 4.1: Record Attributed Audit Events for Regulated Batch Actions

As a reviewer or regulated-system stakeholder,
I want the system to record attributed audit events for creation, update, completion, and signature-related actions on batch records,
So that dossier integrity can be reconstructed and trusted without relying on implicit or hidden state changes.

**Acceptance Criteria:**

**Given** a user performs a regulated action on a batch or batch step
**When** that action is accepted by the system
**Then** an audit event is recorded with the actor identity, timestamp, action type, and relevant batch context
**And** the event is linked to the affected regulated record.

**Given** multiple contributors may act on the same batch over time
**When** audit events are stored
**Then** the system preserves the sequence of attributable actions across contributors
**And** later stories can use that history without reconstructing authorship from unrelated data.

**Given** trust depends on complete traceability for important workflow actions
**When** step draft updates, step completion, signature actions, or other governed state transitions occur
**Then** the corresponding audit events are captured consistently
**And** the platform does not rely on silent record mutation without trace output.

**Given** auditability must support later review and correction flows
**When** this story is completed
**Then** later stories can read audit history from a canonical source tied to the batch domain
**And** they do not need to invent feature-local logging approaches.

**Given** this story is focused on foundational traceability rather than correction UX
**When** it is implemented
**Then** the system provides attributable audit event capture as a standalone capability
**And** reason-for-change flows, changed-since-review flags, and reviewer history views remain outside the scope of this story.

### Story 4.2: Correct Previously Entered Batch Data with Required Reason for Change

As an operator or authorized production user,
I want to correct previously entered batch data through a controlled change flow with a required reason,
So that dossier errors can be fixed without losing traceability or creating silent overwrites.

**Acceptance Criteria:**

**Given** a batch step already contains saved or completed data
**When** an authorized user initiates a correction on an editable regulated value
**Then** the system creates a controlled correction action rather than silently replacing the prior value
**And** the corrected record remains linked to the affected batch context.

**Given** regulated corrections require justification
**When** a user submits a correction
**Then** the system requires a reason for change before accepting it
**And** the reason is stored with the correction event.

**Given** attribution must remain explicit
**When** a correction is accepted
**Then** the system records who made the correction and when it was made
**And** the corrected value can be distinguished from the prior value in later traceability views.

**Given** some users may not be authorized to modify regulated data
**When** an unauthorized user attempts to submit a correction
**Then** the system rejects the action server-side
**And** the original regulated value remains unchanged.

**Given** this story is focused on the correction transaction itself
**When** it is implemented
**Then** authorized users can submit controlled corrections with required justification
**And** changed-since-review flags, reviewer history surfaces, and post-correction disposition workflows remain outside the scope of this story.

### Story 4.3: Surface Integrity States and Re-Review Flags After Relevant Changes

As a reviewer or production user,
I want the dossier to show explicit integrity states after relevant changes,
So that everyone can immediately see whether a step is incomplete, changed, signed, or requires renewed review.

**Acceptance Criteria:**

**Given** a batch record can be drafted, completed, signed, corrected, and reviewed over time
**When** the system derives the state of a step or dossier element
**Then** it exposes explicit integrity and review-relevant states for that element
**And** those states do not need to be inferred manually from raw audit history.

**Given** a correction may affect trust in a previously reviewed or signed record
**When** a relevant post-review or post-signature change is accepted
**Then** the affected record is marked with the appropriate changed or re-review-required state
**And** later review workflows can detect that status directly.

**Given** production users also need visible recovery states
**When** a step is incomplete, completed, signed, changed, or review-relevant
**Then** the system can distinguish those states consistently at the batch-step level
**And** they are available to both execution and review experiences.

**Given** integrity states should be stable backend concepts rather than UI-only labels
**When** this story is implemented
**Then** canonical state flags or derived read models exist on the backend
**And** future UI stories consume those states instead of inventing local interpretations.

**Given** this story is focused on state semantics rather than reviewer navigation
**When** it is completed
**Then** the platform provides explicit integrity-state and re-review signaling
**And** dedicated reviewer history views and disposition workflows remain outside the scope of this story.

### Story 4.4: Provide Reviewers with Change History for the Dossier Context

As a production or quality reviewer,
I want to inspect the relevant change history for a batch or step,
So that I can understand what changed, who changed it, and why before deciding whether additional review is required.

**Acceptance Criteria:**

**Given** audit events and controlled corrections exist for a batch record
**When** a reviewer requests the history for a step or dossier area
**Then** the system returns the relevant change history in that context
**And** the reviewer can see the actor, timestamp, action type, and reason for change where applicable.

**Given** reviewers should not have to reconstruct context from raw low-level records
**When** change history is presented for review use
**Then** it is scoped to the affected batch or step context
**And** it distinguishes meaningful regulated changes from unrelated background activity.

**Given** corrections may affect already reviewed or signed content
**When** a reviewer inspects a changed record
**Then** the history makes it possible to understand the prior value, the updated value, and the rationale for the change
**And** the reviewer can use that context in later review decisions.

**Given** history visibility is a separate concern from review disposition
**When** this story is implemented
**Then** reviewers can access relevant dossier history as a standalone capability
**And** confirming review, returning for correction, rejecting, or releasing remain outside the scope of this story.

**Given** execution and review surfaces will both rely on shared traceability concepts
**When** this story is completed
**Then** the history view is built on canonical audit and correction data
**And** future review stories do not need to define a separate interpretation of change history.

## Epic 5: Review and Release Workflow

Supervisors and quality reviewers can review dossiers by exception, inspect signatures and history, manage issues before release, and make clear disposition decisions from dedicated review surfaces.

### Story 5.1: Provide a Dedicated Review Summary for Batch Completeness

As a production or quality reviewer,
I want a dedicated review-oriented summary of the batch dossier,
So that I can see completeness, missing signatures, and review-relevant issues without entering the operator execution flow.

**Acceptance Criteria:**

**Given** a batch exists with execution, signature, and integrity-state data
**When** a reviewer opens the batch for review
**Then** the system returns a dedicated review-oriented summary for that batch
**And** that summary is distinct from the operator execution experience.

**Given** reviewers need to assess dossier readiness quickly
**When** the summary is displayed
**Then** it shows the current completeness state of the dossier against the expected checklist
**And** it highlights missing data, missing signatures, and review-relevant changed states.

**Given** review should be driven by trusted backend semantics
**When** the summary is generated
**Then** it is built from canonical batch, signature, checklist, and integrity-state data
**And** the reviewer does not need to infer dossier health from raw execution details.

**Given** pre-QA and quality review will later diverge in behavior
**When** this story is implemented
**Then** the platform provides a shared review summary foundation usable by both review roles
**And** pre-QA confirmation, quality disposition, and release decisions remain outside the scope of this story.

**Given** this story should unlock later review surfaces in parallel
**When** it is completed
**Then** the review summary becomes a reusable read model for subsequent pre-QA and quality stories
**And** later stories can build on it without redefining completeness semantics.

### Story 5.2: Perform Pre-QA Review and Confirm Readiness for Quality Handoff

As a production supervisor or pre-QA reviewer,
I want a dedicated pre-QA review action over the dossier summary and exceptions,
So that I can confirm readiness for quality handoff or stop the dossier before it reaches quality with obvious issues.

**Acceptance Criteria:**

**Given** a batch has reached the point where production wants to hand it off
**When** a pre-QA reviewer opens the dedicated review surface
**Then** they can assess dossier completeness from a review-oriented interface
**And** they are not forced through the operator execution workflow to perform review.

**Given** the pre-QA reviewer needs to catch obvious dossier defects early
**When** the reviewer inspects the batch summary and exceptions
**Then** they can identify missing data, missing signatures, changed records, and other visible review-relevant issues
**And** they can use that information before confirming handoff readiness.

**Given** pre-QA is a distinct workflow state from execution and quality review
**When** the reviewer confirms the dossier as ready
**Then** the system records a pre-QA review action and moves the batch into the appropriate pre-QA-confirmed handoff state
**And** that state is distinguishable from both ordinary execution and quality review states.

**Given** a dossier may still require correction before quality receives it
**When** the reviewer determines the dossier is not ready
**Then** the system does not confirm quality handoff readiness
**And** later correction or return workflows remain possible without pretending the dossier passed pre-QA.

**Given** this story is focused on pre-QA confirmation rather than full quality disposition
**When** it is completed
**Then** production review can confirm or withhold readiness for quality handoff as a standalone capability
**And** quality decision-making, rejection, release, and final disposition remain outside the scope of this story.

### Story 5.3: Inspect Dossier Integrity from a Dedicated Quality Review Surface

As a quality reviewer,
I want a dedicated quality review surface for inspecting dossier integrity, signatures, corrections, and issue context,
So that I can evaluate the batch from a trust and release-readiness perspective without reusing the operator or pre-QA interface.

**Acceptance Criteria:**

**Given** a batch is available for quality review
**When** a quality reviewer opens it
**Then** the system presents a quality-specific review surface
**And** that surface is distinct from both the operator execution flow and the pre-QA confirmation flow.

**Given** quality review requires trust-oriented inspection rather than data entry
**When** the reviewer inspects the dossier
**Then** they can view the current step states, signatures, correction history, review-relevant flags, and linked issue context
**And** the information is presented as a review artifact rather than an execution form.

**Given** quality decisions depend on understanding changes after signature or review
**When** the reviewer inspects a changed dossier element
**Then** they can access the associated integrity state and relevant change history
**And** they do not need raw audit-log archaeology to understand what happened.

**Given** issue or deviation context may influence final disposition
**When** the reviewer examines the dossier before deciding
**Then** the system exposes dossier-linked issue information relevant to the batch context
**And** the reviewer can inspect that context before final disposition.

**Given** this story is focused on quality inspection rather than final decision
**When** it is implemented
**Then** the quality review surface supports full inspection of dossier integrity as a standalone capability
**And** release, rejection, or return-for-correction decisions remain outside the scope of this story.

### Story 5.4: Make Quality Disposition Decisions for Release, Rejection, or Return for Correction

As a quality reviewer,
I want to record a final disposition decision on the batch dossier,
So that the system represents whether the batch is released, rejected, or returned for correction with an explicit and trustworthy outcome state.

**Acceptance Criteria:**

**Given** a quality reviewer has inspected the dossier in the quality review surface
**When** they choose a final disposition
**Then** the system supports the allowed outcomes `release`, `reject`, and `return for correction`
**And** the batch moves into the corresponding governed outcome state.

**Given** release readiness is a distinct business outcome
**When** the reviewer releases the batch
**Then** the system records a release-oriented decision with reviewer identity, timestamp, and relevant decision context
**And** the batch becomes visibly represented as release-ready or released according to the governed state model.

**Given** some dossiers are not acceptable for release
**When** the reviewer rejects the batch or returns it for correction
**Then** the system records the chosen disposition and associated rationale or note where required
**And** later users can distinguish rejection from return-for-correction in both state and review history.

**Given** quality decisions may depend on unresolved issues, missing completeness, or recent changes
**When** the reviewer attempts final disposition
**Then** the system evaluates the governed conditions for the requested outcome
**And** it prevents invalid release decisions when blocking review conditions remain unresolved.

**Given** this story should close the quality workflow without absorbing unrelated functionality
**When** it is implemented
**Then** quality reviewers can make final dossier disposition decisions as a standalone capability
**And** broader export, archival, or external integration workflows remain outside the scope of this story.

## Epic 6: Contextual Dossier Composition and Export

The system can assemble the correct dossier for each batch context, apply governed calculations and checklist rules, support structured references, and produce export and integration-ready outputs without requiring ERP or WMS coupling.

### Story 6.1: Compose the Required Dossier Structure from Batch Context

As a production or quality user,
I want the system to determine which dossier elements are required for a batch based on its operational context,
So that execution and review are driven by the right document set instead of a generic one-size-fits-all packet.

**Acceptance Criteria:**

**Given** a batch contains contextual attributes such as line, machine, format family, or paillette relevance
**When** the system resolves the dossier structure for that batch
**Then** it determines which sub-documents and controls are required for that batch context
**And** the required structure is attached to the batch as a governed operational expectation.

**Given** not all dossier elements are applicable in every situation
**When** the system evaluates the batch context
**Then** non-applicable controls or documents are excluded or marked not applicable according to governed rules
**And** they do not behave as if they were mandatory by default.

**Given** execution and review both depend on the same dossier expectation
**When** the required dossier structure is generated
**Then** it can be reused by both workflow execution and completeness review
**And** later stories do not need to recompute separate versions of the required document set.

**Given** dossier composition must remain backend-owned business logic
**When** this story is implemented
**Then** the conditional composition rules are enforced from a canonical backend service or read model
**And** frontend features consume the result instead of implementing document-selection logic locally.

**Given** this story should provide a standalone business capability
**When** it is completed
**Then** the system can resolve the correct dossier structure from batch context
**And** repeated control generation, governed calculations, and export behavior remain outside the scope of this story.

### Story 6.2: Generate Repeated In-Process and Box-Level Controls for the Batch

As a production or quality user,
I want repeated dossier controls to be generated as structured batch records rather than static placeholders,
So that recurring checks can be executed and reviewed as real governed records within the batch.

**Acceptance Criteria:**

**Given** the batch dossier structure includes controls that repeat by process, box, or other governed context
**When** the batch structure is generated or refreshed for operational use
**Then** the system creates repeated control records as structured batch elements
**And** those controls are not represented only as a single static form instance.

**Given** repeated controls may depend on the resolved dossier context
**When** the system determines how many repeated records are needed
**Then** it uses governed batch rules and context inputs to create the correct repeated set
**And** later execution and review flows can address each repeated control individually.

**Given** review and completeness logic must account for repeated records explicitly
**When** repeated controls exist in the batch
**Then** they contribute to completeness and review expectations as distinct governed elements
**And** the platform can identify which repeated item is complete, incomplete, or reviewed.

**Given** this story is about repeated control modeling rather than calculations or export
**When** it is completed
**Then** the batch dossier supports repeated structured control instances as a standalone capability
**And** calculation validation, external references, and dossier export remain outside the scope of this story.

**Given** execution and review features will rely on stable repeated-control semantics
**When** this story is reviewed
**Then** the generated control instances are backed by canonical batch data structures
**And** later UI stories do not need to simulate repetition with frontend-only constructs.

### Story 6.3: Apply Governed Backend Calculations and Cross-Document Consistency Rules

As a production or quality user,
I want governed calculations and cross-document consistency checks to be evaluated by the backend,
So that critical dossier logic is trustworthy and not dependent on manual reconciliation or frontend-only behavior.

**Acceptance Criteria:**

**Given** a batch contains fields or controls that require governed calculation logic
**When** the relevant calculation inputs are available
**Then** the system computes the required calculated values on the backend
**And** those values are stored or exposed as governed dossier results.

**Given** some dossier rules depend on consistency between multiple document areas
**When** the system evaluates dossier integrity for execution or review
**Then** it can apply cross-document consistency checks across the affected governed records
**And** it surfaces the outcome of those checks as part of the batch’s dossier semantics.

**Given** the MVP must not depend on executing client Excel logic directly in production
**When** this story is implemented
**Then** the governed calculation behavior is represented as server-side application logic
**And** the batch workflow does not require live Excel macro execution.

**Given** calculation and consistency results influence downstream completion and review
**When** a rule fails or a required calculated outcome is missing
**Then** the system can expose that condition to later execution or review features
**And** those features do not need to reimplement the underlying business logic.

**Given** this story is focused on calculation and rule evaluation rather than export or reference attachment
**When** it is completed
**Then** governed backend calculation and consistency validation are available as a standalone capability
**And** dossier export formatting and structured external references remain outside the scope of this story.

### Story 6.4: Attach Structured References and Supporting Artifacts to the Batch Dossier

As a production or quality user,
I want the batch dossier to carry structured references such as labels, equipment references, and supporting attachments,
So that relevant external context is available inside the governed record without requiring live equipment or scanner integration.

**Acceptance Criteria:**

**Given** a batch dossier may need contextual external references
**When** an authorized user or upstream process associates label, equipment, or supporting reference data with the batch
**Then** the system stores those references as structured dossier-linked data or attachments
**And** they remain accessible from the governed batch context.

**Given** the MVP must not depend on live external integrations
**When** this story is implemented
**Then** the dossier can carry those references without requiring real-time scanner, equipment, ERP, or WMS connectivity
**And** the batch workflow remains operational without those live integrations.

**Given** review and audit discussions may need those supporting references
**When** a user inspects the batch dossier
**Then** the associated references are visible in the batch context
**And** they can be distinguished from core regulated batch data while remaining linked to it.

**Given** future integrations may later enrich these references
**When** the reference model is designed
**Then** it preserves a clean contract for future system integration
**And** it does not hard-code the MVP to a scanner- or ERP-dependent workflow.

**Given** this story is focused on structured reference attachment rather than export generation
**When** it is completed
**Then** the product supports dossier-linked structured references as a standalone capability
**And** versioned external contracts and final export formatting remain outside the scope of this story.

### Story 6.5: Export the Governed Dossier and Expose Integration-Ready Contracts

As a production or quality user,
I want to generate an exportable governed dossier and rely on documented integration-ready contracts,
So that the batch record can be consumed outside the application without requiring mandatory ERP or WMS coupling.

**Acceptance Criteria:**

**Given** a batch dossier has been composed with its required records, calculations, and supporting references
**When** an authorized user requests dossier export
**Then** the system generates an exportable dossier artifact from the governed batch record
**And** the export reflects the batch snapshot and current governed dossier state rather than an ad hoc reconstruction.

**Given** the MVP must remain operational without mandatory enterprise-system dependency
**When** export capability is implemented
**Then** the dossier can be produced without requiring live ERP or WMS connectivity
**And** the absence of those external systems does not block core dossier completion or review workflows.

**Given** future external consumers may need stable machine-readable access
**When** the export and integration behavior is defined
**Then** the system provides documented interface or payload contracts for downstream consumption
**And** those contracts are clear enough for later ERP, WMS, or document-management integration without redesigning the core batch model.

**Given** export is a governed capability rather than open-ended file access
**When** a user without the required permission attempts to export or retrieve integration-oriented dossier outputs
**Then** the system rejects the request server-side
**And** only authorized roles can access governed dossier export behavior.

**Given** this story should close the epic without absorbing unrelated archival concerns
**When** it is completed
**Then** the product supports governed dossier export and integration-ready contract definition as a standalone capability
**And** long-term archival, third-party synchronization orchestration, or live bidirectional integrations remain outside the scope of this story.
