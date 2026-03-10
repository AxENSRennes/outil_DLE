# Actionable Architecture Decisions

**Date:** 2026-03-06  
**Scope:** DLE / eBR SaaS for cosmetics with pharma-like rigor  
**Goal:** Convert external research and client discovery into concrete architecture decisions that can drive implementation immediately.

## Decision Framing

This document is not a market scan. It is a decision memo.

Each section answers one question:
- what is being frozen now
- why it is being frozen now
- what it implies for the product build
- what is intentionally not being built yet

## Product Objective

The first product objective is not to build a full MES.

The first product objective is to deliver a credible electronic batch record workflow that:
- guides execution better than paper
- improves dossier completeness
- adds a real pre-QA review step before quality release
- supports review and release
- produces an audit-ready digital trail
- can be demonstrated quickly to management on a real client flow

## Decision 1: Freeze the Core Stack

### Decision

Freeze the stack as:
- Django 5.2 LTS
- Django REST Framework
- drf-spectacular
- React + TypeScript + Vite
- PostgreSQL
- Docker Compose as the canonical runtime definition

### Why

This stack gives the best combination of:
- domain modeling strength
- rapid internal tooling
- API discipline
- schema-driven UI potential
- long-term maintainability
- portability between local, demo, and production environments

### Build Implication

Start implementation with a monolithic backend and a separate React frontend.

Do not re-open framework choice unless a hard blocker appears.

## Decision 2: Model the Product Around MMR, MMRVersion, Batch, BatchStep

### Decision

The domain model must be centered around:
- `MMR`
- `MMRVersion`
- `Batch`
- `BatchStep`
- `Signature`
- `ReviewEvent`
- `ReleaseEvent`
- `Exception`
- `AuditEvent`

### Why

Research across eBR competitors, regulated form systems, and form engines converges on versioned templates instantiated into immutable execution records.

### Build Implication

Do not model the system as:
- a generic form submission app
- a flat JSON document only
- a free-form workflow engine

The database must preserve explicit business semantics for:
- version activation
- batch status
- step status
- signature state
- review state
- release state

## Decision 3: Snapshot the Template at Batch Creation

### Decision

When a batch starts, the active `MMRVersion` must be snapshotted into the batch context.

### Why

This is one of the most stable patterns observed across the market and adjacent regulated systems.

### Build Implication

Implementation must guarantee:
- changing a template later does not change an in-progress batch
- the batch always knows which version created it
- review and audit can reconstruct the exact rules in force at execution time

## Decision 4: Use a Hybrid Relational + JSONB Data Model

### Decision

Use relational tables for critical business entities and `jsonb` for configurable template and answer structures.

### Why

The product needs both:
- strong invariants and queryability on key entities
- flexibility for step definitions, fields, and conditional logic

### Build Implication

Relational first-class entities should include:
- batches
- steps
- signatures
- exceptions
- review events
- release events
- audit events
- attachments

`jsonb` should be used for:
- step definitions
- field definitions
- declarative validation rules
- step payload details

## Decision 5: Keep Calculation Logic on the Backend

### Decision

Any calculation coming from Excel must be represented as backend-controlled logic, not as ad hoc frontend logic.

### Why

Calculated fields can affect release decisions and record integrity.

### Build Implication

The implementation should support:
- declarative references to calculations from the template
- deterministic execution on the server
- display of results in React
- later extensibility toward an expression DSL or a governed calculation registry

Do not put critical formulas only in the client.

## Decision 6: Treat Signatures as Business Events, Not UI Widgets

### Decision

Electronic signatures must be implemented as explicit business events.

### Why

Research shows that a generic signature pad component is insufficient for a regulated execution workflow.

### Build Implication

A signature must store at minimum:
- signer identity
- server timestamp
- signature meaning
- related batch step
- signed data state reference

The implementation must support re-authentication at the moment of signing.

Do not model signature as only:
- an image
- a boolean field
- a front-end-only artifact

## Decision 7: Add Review States That Survive Corrections

### Decision

A record that was reviewed or signed and then changed must explicitly move to a visible re-review state.

### Why

This pattern appears strongly in adjacent regulated systems and solves a real operational problem.

### Build Implication

The system must support visible states such as:
- `review_required`
- `changed_since_review`
- `changed_since_signature`

Do not hide this only in the audit trail.

## Decision 8: Separate Operator UI and Review UI

### Decision

Execution and review must be treated as different product surfaces.

### Why

The best systems optimize operator speed and review clarity differently.

### Build Implication

The first product architecture should assume at least two front-end flows:
- operator execution flow
- pre-QA review flow
- quality/review flow

Do not design a single giant screen that tries to satisfy both.

## Decision 9: Make Exceptions Structured Objects Early

### Decision

Model deviations / exceptions as explicit records early in the architecture.

### Why

Competitor and adjacent-system research consistently show that out-of-tolerance handling becomes central very quickly.

### Build Implication

An `Exception` entity should be designed with fields for:
- category or type
- severity
- status
- creator
- timestamps
- affected step
- reason
- disposition or resolution

Even if the full workflow is not built in the first demo, the model should exist.

The client currently resolves many dossier issues by derogation. The final domain wording may therefore evolve toward `Derogation` or `Deviation`, but the explicit record model should be introduced immediately.

## Decision 10: Progressive Save by Step

### Decision

Persist execution progressively at step level.

### Why

This is a stable pattern in form systems and execution systems because it supports:
- shared workstations
- partial progress
- interruption recovery
- clearer review boundaries

### Build Implication

Each step should have explicit status, such as:
- not started
- in progress
- completed
- signed
- flagged
- under review

## Decision 11: Design for Multi-Site, But Do Not Implement Full Multi-Tenant Yet

### Decision

The architecture must be compatible with multiple sites and group rollout, but full active multi-tenant complexity is deferred.

### Why

The first customer is one site of a group. Future extension matters, but active multi-tenant isolation is not necessary to prove the product.

### Build Implication

Design now for:
- `organization`
- `site`
- `template ownership`
- permissions that can later be scoped by site

Do not implement now:
- production schema-per-tenant rollout logic
- tenant provisioning automation
- cross-tenant ops complexity

## Decision 12: Keep Deployment Portable

### Decision

Treat Docker Compose as the source of truth and keep the deployment independent from any single ops tool.

### Why

It preserves speed while keeping hosting reversible.

### Build Implication

A first deployment can use:
- Scaleway
- Dokploy

But the application must remain runnable via plain Compose.

## Decision 13: Build the First Demo Around One Real Client Flow

### Decision

The first implementation slice must target one real dossier and one representative flow.

### Why

Research and client discovery both show that operator acceptance and template fidelity matter more than feature breadth in the first demonstration.

### Build Implication

The first slice should include:
- one MMR version
- one batch creation flow
- a handful of steps focused on fabrication and conditionnement
- one or two signatures
- one pre-QA review view
- one review view
- one exportable dossier view

Do not try to prove the whole platform in the first slice.

## Decision 14: Postpone the Following on Purpose

### Decision

The following are explicitly not required before the first credible demonstration:
- visual form builder
- full exception workflow engine
- active multi-tenant architecture
- advanced ERP / WMS integration
- label printing integration
- barcode scanning integration
- custom cryptographic hash-chain
- offline mode
- orchestration engines such as Temporal or Camunda

### Why

These add complexity faster than they add proof of product value.

## Decision 15: Freeze the Shared-Workstation Session Model

### Decision

The MVP must use authenticated Django sessions plus a fast PIN-based workstation identification flow.

### Why

Shared line workstations are a hard operating constraint. The product needs fast identity switching and signature re-authentication without inventing a second security model.

### Build Implication

Implementation must support:
- `identify` by PIN to establish the active authenticated user
- `switch_user` without losing the current batch context
- explicit workstation lock on inactivity or user action
- signature re-authentication for the already active user
- audit events for identify, switch, lock, failed PIN, and signature re-auth

Do not leave workstation behavior to ad hoc frontend conventions.

## Decision 16: Freeze Canonical Workflow States and Review Severity

### Decision

The MVP must expose canonical lifecycle states, step states, and derived review severity from the backend.

### Why

Operator, pre-QA, and quality surfaces all depend on the same state semantics. If the frontend invents its own badges or review summaries, trust breaks immediately.

### Build Implication

Implementation must expose:
- batch lifecycle states such as in-progress, pre-QA, quality review, returned for correction, released, rejected
- step states such as not started, in progress, complete, signed
- explicit flags for changed-since-review, changed-since-signature, review-required, and missing requirements
- a derived severity summary of green, amber, or red for dashboard-style review surfaces

Do not require the UI to reconstruct review status from raw audit history.

## Decision 17: Freeze MVP Workflow Contracts Around Actions, Not Generic CRUD

### Decision

The first public API must center workflow actions such as save step, sign, request correction, confirm pre-QA review, and quality disposition.

### Why

This product is workflow-driven, not a generic record editor. Action contracts keep state transitions explicit and auditable.

### Build Implication

The first OpenAPI contract must cover:
- workstation identify and lock
- step draft save
- step completion
- step signing
- step correction
- pre-QA confirmation
- review-item acknowledgement
- quality release / return / rejection
- dossier execution and review summary read models

Do not hide state transitions behind broad status PATCH endpoints.

## Decision 18: Make Dossier Composition and Completeness Backend-Owned

### Decision

Conditional dossier structure, repeated controls, checklist completeness, and cross-document consistency must be computed by backend services.

### Why

These rules determine what is required for execution and release. They are core regulated business logic, not presentation logic.

### Build Implication

The implementation should provide services that:
- resolve required sub-documents from batch context
- instantiate repeated controls as records
- compute the expected dossier checklist
- evaluate cross-document consistency before review disposition

Do not put document-composition rules only in React components or template JSON consumers.

## Decision 19: Keep MVP Export Synchronous

### Decision

The representative dossier export in MVP should be generated synchronously by backend services.

### Why

Export is a core credibility moment in the pilot, but queue infrastructure is not yet justified.

### Build Implication

The first slice should:
- generate the representative dossier export in-request
- return a current dossier snapshot suitable for review discussion
- defer background workers until volume or archival integration makes them necessary

Do not introduce Redis or job infrastructure only to support the first exportable dossier.

## First Build Sequence

### Phase 1: Domain Spine

Implement first:
- MMR
- MMRVersion
- Batch
- BatchStep
- Signature
- ReviewEvent
- Audit hooks

### Phase 2: Template Rendering Spine

Implement next:
- JSONB-based step schema
- React step renderer
- declarative field validation
- batch step persistence

### Phase 3: Trust Spine

Implement next:
- signature re-auth flow
- reason-for-change
- review-required after change
- shared-workstation identify / switch / lock behavior
- dossier export

### Phase 4: Quality Workflow Spine

Implement next:
- review screen
- pre-QA dashboard and dossier completeness summary
- release decision
- exception model activation

## Architecture Success Criteria

The architecture is considered successful if it enables:
- fast creation of a new client template without rewriting the product
- clear distinction between template version and batch instance
- clear visibility of what changed and what must be reviewed again
- traceable signatures with business meaning
- a fast operator flow on shared workstations
- a pre-QA review flow usable by production before handoff to quality
- a review flow usable by quality without reading raw audit logs
- backend-owned dossier completeness and export behavior that match what UX presents

## Final Position

The architecture should now be considered frozen on the following points:
- Django backend
- React frontend
- PostgreSQL
- Tailwind CSS + shadcn/ui + Radix UI frontend baseline
- versioned template model
- batch snapshotting
- business-level signatures
- shared-workstation session model
- backend-owned workflow state and dossier composition
- explicit re-review states
- progressive save by step
- portable deployment

This is enough structure to start building immediately without creating avoidable long-term debt.
