# Competitive and Adjacent Research Notes

**Date:** 2026-03-06  
**Subject:** Good practices and reusable patterns for a DLE / eBR SaaS in cosmetics with pharma-like rigor

## Research Goal

Identify technical and product patterns already proven in the market or in adjacent regulated systems that can improve the architecture and roadmap of the DLE SaaS.

The research intentionally covers:
- direct eBR / MES competitors
- digital work instruction platforms
- adjacent regulated form systems
- open-source form engines and audit libraries

## Key Takeaways

1. The market converges on a few stable patterns.
2. The real product differentiator is not raw feature count but the combination of:
   - guided execution
   - strong auditability
   - usable review workflows
   - template maintainability
3. Several adjacent domains have already solved parts of the problem better than eBR vendors explain publicly:
   - clinical form versioning
   - schema-driven conditional logic
   - plugin-based integration
   - immutable history models
4. Most systems fail in practice when template maintenance, review UX, or operator speed are poor.

## Direct Competitors and Near Competitors

### MasterControl

Observed patterns:
- strong emphasis on **review by exception**
- digital batch records positioned around eliminating line-by-line post-production review
- connected suite story: quality + manufacturing + release

What matters for us:
- review by exception is a real market pattern, not a speculative idea
- the value proposition is always framed around **fixing issues during execution**, not after the fact
- the suite model is powerful commercially but can create operational heaviness

Caution:
- third-party user feedback suggests operator UX and configurability can become painful if the system is too heavy or inflexible
- this reinforces the need to keep the first operator UX extremely fast and narrow

## BatchLine

Observed patterns:
- explicit promise of **modern app UX** for GMP manufacturing
- focus on low implementation effort and batch approval speed
- product language emphasizes:
  - smart workflows
  - formula automation
  - lists and calculations
  - in-process controls
  - review and approval collaboration
- release notes show real product evolution around:
  - referencing previous EBR values in calculations
  - collaborative exception review between supervisors and QA
  - showing either latest exception comments or full history in PDF reports
  - preserving full audit trail during review collaboration

What matters for us:
- review collaboration is not an afterthought; it becomes a real product area quickly
- exception handling must support both an edited latest view and a full historical view
- PDF output is not just an archive artifact, but part of the review and audit experience
- UX improvements are explicitly shipped as product changes, not decorative polish

## Tulip

Observed patterns:
- Tulip’s GxP requirements and app suites expose a very granular operating model
- the platform supports:
  - exception capture with reason, risk category, and comments
  - configurable exception review
  - tolerance checks with authorized overrides
  - logged deviations blocking completion until handled
  - photos and videos during execution
  - label printing
  - scanning and device integrations
  - historical review filtered by date, step, and operator
  - release via signature widget

What matters for us:
- exception handling should be treated as a first-class workflow, not a text note
- out-of-tolerance behavior should eventually support:
  - block
  - override
  - log deviation
  - require signature
- labels and scanning are not edge cases; they appear naturally in real execution flows
- “review app” separation is a useful pattern: execution UI and review UI should not be the same surface

## Azumuta

Observed patterns:
- strong focus on digital work instructions and quality procedures embedded directly into execution
- explicit support for:
  - variants and templates
  - revision history and approval flow
  - workspace scaling
  - traceability and issue ticketing
  - multilingual replication across sites
  - scanner-assisted confirmation of correct parts

What matters for us:
- template reuse and central control across multiple sites is a strong multi-site pattern
- work instructions are not separate from execution quality; they are part of the same operator experience
- scanner-assisted confirmation should stay on the roadmap because it solves physical traceability problems without forcing full MES complexity

## Adjacent Regulated Systems

### OpenClinica

Observed patterns:
- very strong discipline around **form versioning**
- once a form is published to production, changes require a new version
- verified data becomes **changed since verified** if edited later
- signatures, countersignatures, consent state, and re-consent are modeled explicitly as statuses
- role-based review and query workflows are granular
- rule systems support both field-level and cross-form validation logic

What matters for us:
- the strongest reusable idea is not the clinical domain itself but the discipline:
  - version explicitly
  - do not overwrite production forms
  - surface “changed since verified” as a visible state
  - make re-review explicit after changes
- this is directly reusable for batch record review and release

## Open Forms

Observed patterns:
- form = composition of reusable step definitions
- submission starts when form starts and saves progressively per step
- completed submissions become non-editable in content
- plugin-based architecture for registration / downstream integration
- reusable step definitions and multiple forms built from them
- admin-driven form configuration with import/export and maintenance mode
- extensive changelog evidence of ongoing complexity around plugins, submission data shape, audit logs, and upgrades

What matters for us:
- progressive step persistence is a validated pattern
- reusable step definitions are powerful, but they create complexity in change propagation and migration
- plugin architecture for downstream systems is useful, but must be introduced carefully
- import/export and maintenance mode are underrated product capabilities for enterprise operations

## Open Source Form Engines

### SurveyJS

Observed patterns from codebase:
- schema-first definition model
- mature support for:
  - `visibleIf`
  - `requiredIf`
  - `triggers`
  - `calculatedValues`
  - expression validators

What matters for us:
- expression-based declarative logic is a proven pattern and should inspire the MMR schema
- conditional display, conditional requirement, and calculated values should be declarative, not custom frontend code per template
- this is a strong argument for a schema-driven React renderer

### Form.io

Observed patterns from codebase:
- component-centric schema model
- wizard / page-based execution model
- built-in signature component exists, but it is essentially a UI capture primitive
- strong builder/component architecture

What matters for us:
- wizard navigation and component abstraction are useful references
- a generic “signature component” is not enough for regulated execution; signature needs domain semantics
- this confirms that our signature system should be modeled at the business level, not as a mere drawn widget

## Audit and History Patterns

### django-pghistory

Observed patterns from codebase and docs:
- history capture through PostgreSQL triggers
- optional append-only protection via DB-level trigger protection
- configurable context storage:
  - foreign-key context
  - denormalized JSON context
- middleware-assisted request context capture
- support for denormalized context when partitioning/performance matter

What matters for us:
- trigger-based history is still the right direction for critical entities
- append-only should be used where it provides real integrity value
- denormalized JSON context is attractive for long-term audit query performance
- a context model including request/user metadata is worth keeping from day one

## Patterns Worth Reusing

### 1. Step-Based Execution with Progressive Save

Seen in:
- Open Forms
- Form.io wizard concepts
- Tulip app templates
- BatchLine product behavior

Recommendation:
- save data at step granularity
- expose explicit step status in the batch record
- allow partial progress without pretending the lot is complete

### 2. Template Snapshot at Batch Start

Seen across market logic and adjacent systems.

Recommendation:
- snapshot the active MMR version into the batch at instantiation
- never mutate the effective template of an in-progress lot

### 3. Explicit Re-Review State After Changes

Seen strongly in OpenClinica.

Recommendation:
- if a reviewed or signed record is modified, surface a state like:
  - changed since reviewed
  - changed since signed
  - review required
- do not hide this in the audit trail only

### 4. Declarative Conditional Logic

Seen strongly in SurveyJS.

Recommendation:
- use declarative expressions for:
  - visibility
  - requirement
  - calculations
  - conditional warnings
- avoid custom handwritten UI logic per template

### 5. Separate Execution and Review Surfaces

Seen in Tulip and implied by MasterControl / BatchLine.

Recommendation:
- operator view optimized for doing
- quality/review view optimized for checking, filtering, comparing, approving

### 6. Exception and Deviation as Structured Objects

Seen in Tulip and BatchLine patterns.

Recommendation:
- exception log entries should not be plain comments
- they should carry at least:
  - reason
  - category or severity
  - timestamps
  - author
  - review state
  - resolution or disposition

### 7. PDF as Review Artifact, Not Just Archive

Seen in BatchLine’s release behavior and OpenClinica consent/document flows.

Recommendation:
- PDF output should support management review and audit review
- it should present both current view and traceability context where needed

### 8. Reusable Step Definitions with Caution

Seen in Open Forms and Azumuta-like template systems.

Recommendation:
- reuse is valuable
- but shared steps increase migration/version complexity
- do not over-engineer global reusable steps in the first delivery

## Risks and Anti-Patterns Found in the Market

### 1. Generic Form Builder Thinking

Risk:
- treating the product as a generic form engine instead of a batch-record system

Consequence:
- you miss business semantics like review, release, signature meaning, changed-since-reviewed, exception workflow

### 2. Overloaded Suite Design

Risk:
- bundling too many quality/manufacturing domains into one UX too early

Consequence:
- operator UX becomes slow and difficult

### 3. Weak Template Governance

Risk:
- templates can be edited too loosely or too opaquely

Consequence:
- production trust collapses, especially after audit findings

### 4. Signature as Mere Image Capture

Risk:
- using a canvas signature widget as if it were the regulated signature model

Consequence:
- visually impressive, legally and operationally weak

### 5. Audit Trail Hidden but Not Actionable

Risk:
- history exists, but users cannot understand what changed and what must be re-reviewed

Consequence:
- auditors may be satisfied on paper, but QA operations remain inefficient

## Practical Recommendations for the DLE SaaS

### Freeze Now

- Django backend
- React frontend
- PostgreSQL
- hybrid relational + JSONB model
- step-based batch execution
- explicit MMR versioning and batch snapshotting
- business-level signature model
- review state machine including “changed since review” semantics

### Build Soon

- structured exception / deviation object model
- review UI separate from operator UI
- PDF designed for review as well as archive
- calculation engine on backend with declarative references from templates

### Keep on the Roadmap

- label printing
- barcode scanning
- multilingual templates or site-specific language layers
- workspace or site-level template propagation
- integration plugin architecture

### Delay Until Proven Necessary

- full visual form builder
- custom cryptographic hash-chain in v1
- active multi-tenant production architecture
- orchestration engines like Temporal or Camunda

## Final Insight

The strongest lesson from the market is not “copy a competitor.”

It is:
- keep execution simple
- keep review powerful
- keep templates governable
- keep history explicit
- keep signatures meaningful

The systems that look strongest conceptually all converge on these patterns, even when their stacks, domains, and marketing language differ.
