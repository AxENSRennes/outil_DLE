# Transcript to Product Decisions

**Date:** 2026-03-07  
**Purpose:** Map the client discovery call to explicit product decisions for the DLE SaaS.

## How to Read This Note

Each item follows the same structure:
- what the client said
- what it means for the product
- what decision follows now

## 1. The scope is batch record digitization, not a full MES

**Client signal**
- The client currently uses paper batch records.
- They want a tool aligned with their existing dossier de lot master.
- They explicitly do not want a heavy ERP-style deployment.

**Product meaning**
- The product must solve dossier execution, completeness, review, and release.
- It should not try to become a broad manufacturing platform in v1.

**Decision**
- Position the product as a lightweight, configurable electronic batch record workflow.
- Keep ERP/WMS integration out of the first implementation slice.

## 2. The first business scope is fabrication and conditionnement

**Client signal**
- The client explicitly mentioned:
  - fabrication batch record
  - conditionnement batch record
- They did not describe a separate, mature QC module to digitize first.

**Product meaning**
- The first workflow must cover the dossier around fabrication and packaging.
- Finished product control can exist as a section, but should not dominate v1.

**Decision**
- Build the first template and demo around fabrication + conditionnement.
- Treat finished product control as an optional terminal section of the dossier.

## 3. The paper dossier is composite, not a single form

**Client signal**
- They have a formalized dossier de lot.
- They add forms progressively.
- They also use verification checklists.

**Product meaning**
- The product must support a dossier composed of:
  - core steps
  - attached checklists
  - supporting forms / worksheets
- A single flat form model would be too weak.

**Decision**
- Model the MMR as a structured dossier with step-level attachments and optional supporting artifacts.
- Keep attachment support in the data model from the start.

## 4. The regulatory target is ISO 22716 with pharma-like rigor

**Client signal**
- They confirmed ISO 22716 as their reference.
- They said their dossier philosophy is close to pharma discipline.
- They also confirmed they do not manufacture pharma products.

**Product meaning**
- The product must be rigorous and audit-friendly.
- It must not impose unnecessary pharma-only complexity in v1.

**Decision**
- Build for cosmetics GMP with high documentary rigor.
- Keep signature, audit, and review strong.
- Do not force pharma-style countersignature or critical-step release logic in v1.

## 5. The main pain is dossier completeness before QA handoff

**Client signal**
- Their main issue is not a product safety recall scenario.
- Their main issue is that dossiers are not always filled correctly.
- They explicitly said they do not perform the needed dossier review before passing to quality.

**Product meaning**
- The central product capability is not only data capture.
- It is the ability to ensure dossier completeness before QA release.

**Decision**
- Introduce a dedicated `pre-QA review` stage.
- Separate operator execution from review UI.
- Treat review workflow as a core feature, not a later enhancement.

## 6. First-pass-right documentation is the real KPI

**Client signal**
- The client explicitly cares about the percentage of dossiers that are right the first time.
- Inspection readiness is the main driver.

**Product meaning**
- Success should be measured by documentary quality and review efficiency.
- Fancy features that do not improve first-pass-right are secondary.

**Decision**
- Optimize the first version for:
  - completeness
  - legibility
  - mandatory field enforcement
  - signature clarity
  - review traceability

## 7. The current handling of issues is close to derogation / deviation logic

**Client signal**
- Missing marks or signatures are often handled by derogation.

**Product meaning**
- Dossier issues already have a business handling path.
- This path must become visible and structured in the product.

**Decision**
- Keep an explicit issue record in the model from day one.
- The current generic name `Exception` can later be renamed to `Derogation` or `Deviation` once client terminology is confirmed.

## 8. Shared workstations and multiple contributors are real constraints

**Client signal**
- One to two people can work on fabrication.
- Up to three teams can intervene on conditionnement.
- Operators have one computer per line.

**Product meaning**
- The system must support progressive save, continuity, and attribution across multiple users.
- The operator experience must be simple on shared workstations.

**Decision**
- Persist data at step level.
- Keep the UI step-by-step.
- Design authentication and signatures around shared workstation reality.

## 9. No double signatures and no critical-step release in the current process

**Client signal**
- They explicitly said they do not require double signatures.
- They also said they do not currently manage critical-step releases.

**Product meaning**
- A heavyweight signature workflow would be misaligned with current operations.

**Decision**
- Use single-signature checkpoints on meaningful step completions in v1.
- Keep the architecture extensible for stricter workflows later.

## 10. Equipment traceability exists as a possible future need, not a v1 requirement

**Client signal**
- They have measurement equipment.
- They do not currently trace which instrument was used in the dossier.
- They are not yet at the stage of formal equipment traceability in the batch record.

**Product meaning**
- Equipment references should exist in the model.
- They should not be mandatory for the first rollout.

**Decision**
- Support `equipment_ref` as an optional field type.
- Do not make equipment traceability a blocking requirement in v1.

## 11. Labels are likely a real traceability signal

**Client signal**
- The client described a dossier with labels attached at beginning, middle, and end.

**Product meaning**
- The process includes physical traceability artifacts.
- This may later map to label references, scans, or supporting attachments.

**Decision**
- Keep label references in the schema and model.
- Do not force barcode or printer integration in the first slice.

## 12. Quality release is local to the site

**Client signal**
- Release is done on their side, not centrally at headquarters.

**Product meaning**
- Review and release workflow must be site-level.

**Decision**
- Model review and release around the site team.
- Keep any future group-level governance outside the v1 critical path.

## 13. The plant context favors simplicity and gradual rollout

**Client signal**
- The site is in growth.
- They hired around 40 people last year.
- They run 3x8.
- Quality routines need to be stabilized again.
- They want something that can be implemented progressively.

**Product meaning**
- Training burden and operational simplicity are major success factors.

**Decision**
- Keep the first rollout narrow and easy to explain.
- Avoid broad process redesign in the first product slice.

## 14. Existing systems matter, but do not need immediate integration

**Client signal**
- They have an ERP.
- They recently connected a WMS called EGO.
- Cloud use is acceptable.
- IT validation exists at headquarters.

**Product meaning**
- The product can be cloud-hosted.
- Future integration is plausible.
- Integration is not required to prove the concept.

**Decision**
- Keep deployment cloud-compatible.
- Defer ERP/WMS integration from the first demonstration.
- Prepare for later discussion with the group IT contact.

## 15. No historical paper migration is required

**Client signal**
- They do not want to digitize archived paper records.

**Product meaning**
- There is no need for a legacy migration workstream.

**Decision**
- Start with electronic records for future lots only.

## 16. Product family variability exists, but a pilot can stay narrow

**Client signal**
- They have around 150 juices.
- They use 4 or 5 bottle formats.
- One format represents 85% of volume.

**Product meaning**
- There is real product variability.
- But there is also a natural candidate for a pilot template.

**Decision**
- Use the dominant format as the first implementation target.
- Design the template system for later reuse and parameterization.

## 17. The demo must answer three explicit customer questions

**Client signal**
The client explicitly asked:
- is it a real software product?
- how does electronic signature work for operators?
- can Excel-based calculations be integrated?

**Product meaning**
- The first demonstration must answer these points unambiguously.

**Decision**
- The demo must show:
  - a real web application
  - a login and signing flow
  - a calculation reproduced from source Excel logic
  - a resulting digital dossier / data record

## 18. The product must be configurable by the vendor first

**Client signal**
- The client asked for a tool that can be parameterized according to their paper dossier.
- They did not ask for self-service form building.

**Product meaning**
- Internal configuration by the vendor is enough for the first phase.

**Decision**
- Keep template editing vendor-driven first.
- Delay the visual self-service builder.

## Final Product Consequences

The transcript supports the following product shape for v1:
- a lightweight software product, not a macro and not an ERP
- built around fabrication + conditionnement dossier flows
- step-by-step operator execution on fixed workstation per line
- explicit pre-QA review before quality handoff
- QA review and release as a separate surface
- strong but simple signatures
- optional equipment traceability
- label and supporting-document references prepared in the model
- no historical paper migration
- no mandatory ERP/WMS integration in the first slice

## Final Build Consequences

The transcript justifies the current architecture choices:
- versioned MMR -> batch snapshot
- relational domain entities + JSONB template payloads
- React step renderer
- business-level signatures
- review states that survive later edits
- explicit issue / derogation object
- separate operator and review flows

The transcript does **not** justify at this stage:
- full pharma workflow complexity
- double signatures by default
- mandatory equipment traceability
- broad QMS scope
- immediate multi-tenant complexity
