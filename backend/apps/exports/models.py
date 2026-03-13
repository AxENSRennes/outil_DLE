from __future__ import annotations

from typing import ClassVar

from django.db import models


class DossierProfile(models.Model):
    """Reusable composition rule set linked to an MMR template version.

    Stores the governed rules that determine which sub-documents and controls
    are required based on batch contextual attributes.  The ``rules`` JSONB field
    holds conditional rule definitions while ``elements`` lists every possible
    sub-document / control identifier the template can produce.

    Rule format (``rules`` field)::

        {
          "conditions": [
            {
              "context_key": "paillette_present",
              "operator": "eq",
              "value": true,
              "include_elements": ["paillette-control-1", "paillette-checklist"],
              "exclude_elements": []
            },
            {
              "context_key": "format_family",
              "operator": "in",
              "value": ["CREAM", "GEL"],
              "include_elements": ["viscosity-control"],
              "exclude_elements": []
            }
          ],
          "default_required": ["batch-header", "weighing-record", "release-checklist"]
        }
    """

    mmr_version = models.OneToOneField(
        "mmr.MMRVersion",
        on_delete=models.PROTECT,
        related_name="dossier_profile",
    )
    name = models.CharField(max_length=255)
    rules = models.JSONField(
        default=dict,
        blank=True,
        help_text="Conditional composition rules (JSONB).",
    )
    elements = models.JSONField(
        default=list,
        blank=True,
        help_text="Complete list of possible element identifiers for the template.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "dossier profile"
        verbose_name_plural = "dossier profiles"

    def __str__(self) -> str:
        return f"{self.name} (MMRVersion {self.mmr_version_id})"


class ApplicabilityStatus(models.TextChoices):
    REQUIRED = "required", "Required"
    NOT_APPLICABLE = "not_applicable", "Not applicable"


class DossierElementType(models.TextChoices):
    SUB_DOCUMENT = "sub_document", "Sub-document"
    IN_PROCESS_CONTROL = "in_process_control", "In-process control"
    BOX_LEVEL_CONTROL = "box_level_control", "Box-level control"
    CHECKLIST_ITEM = "checklist_item", "Checklist item"


class BatchDossierStructure(models.Model):
    """Resolved dossier expectation for a specific batch.

    Immutable once generated — append-only semantics for audit traceability.
    If composition rules change, a new resolution is created with a fresh
    ``resolved_at`` timestamp while the previous record is preserved.
    """

    batch = models.ForeignKey(
        "batches.Batch",
        on_delete=models.PROTECT,
        related_name="dossier_structures",
    )
    dossier_profile = models.ForeignKey(
        DossierProfile,
        on_delete=models.PROTECT,
        related_name="resolved_structures",
    )
    context_snapshot = models.JSONField(
        help_text="Batch context attributes evaluated at resolution time.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Only the latest active resolution is used. Old ones are kept for audit.",
    )
    resolved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "batch dossier structure"
        verbose_name_plural = "batch dossier structures"
        ordering: ClassVar[list[str]] = ["-resolved_at"]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=["batch", "is_active"],
                name="exports_bds_batch_active_idx",
            ),
        ]
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["batch"],
                condition=models.Q(is_active=True),
                name="exports_bds_one_active_per_batch",
            ),
        ]

    def __str__(self) -> str:
        return f"DossierStructure for {self.batch} (active={self.is_active})"


class DossierElement(models.Model):
    """Individual item within a resolved BatchDossierStructure."""

    structure = models.ForeignKey(
        BatchDossierStructure,
        on_delete=models.PROTECT,
        related_name="elements",
    )
    element_identifier = models.CharField(
        max_length=200,
        help_text="Reference identifier linking back to the template definition.",
    )
    element_type = models.CharField(
        max_length=32,
        choices=DossierElementType.choices,
    )
    display_order = models.PositiveIntegerField()
    applicability = models.CharField(
        max_length=20,
        choices=ApplicabilityStatus.choices,
        default=ApplicabilityStatus.REQUIRED,
    )
    title = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional element-level metadata from the composition rules.",
    )

    class Meta:
        verbose_name = "dossier element"
        verbose_name_plural = "dossier elements"
        ordering: ClassVar[list[str]] = ["display_order"]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=["structure", "display_order"],
                name="exports_de_struct_order_idx",
            ),
        ]
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["structure", "element_identifier"],
                name="exports_de_unique_element_per_structure",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.element_identifier} ({self.applicability})"
