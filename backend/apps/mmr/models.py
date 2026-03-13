"""Foundation models for Master Manufacturing Records.

These are minimal models introduced as FK targets for Epic 6 (dossier composition).
Epic 2 will expand them with full governance, versioning, and lifecycle features.
"""

from __future__ import annotations

from typing import ClassVar

from django.conf import settings
from django.db import models


class MMR(models.Model):
    """Master Manufacturing Record — a governed dossier template owned by a site."""

    site = models.ForeignKey(
        "sites.Site",
        on_delete=models.PROTECT,
        related_name="mmrs",
    )
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "MMR"
        verbose_name_plural = "MMRs"
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["site", "code"],
                name="mmr_unique_code_per_site",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"


class MMRVersionStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    RETIRED = "retired", "Retired"


class MMRVersion(models.Model):
    """An immutable version of an MMR template.

    Stores the full template schema as JSONB.  Batches are instantiated from
    the currently active version; template changes require a new version.
    """

    mmr = models.ForeignKey(
        MMR,
        on_delete=models.PROTECT,
        related_name="versions",
    )
    version_number = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20,
        choices=MMRVersionStatus.choices,
        default=MMRVersionStatus.DRAFT,
    )
    schema_json = models.JSONField(default=dict)
    change_summary = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_mmr_versions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["-version_number"]
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["mmr", "version_number"],
                name="mmr_unique_version_number",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.mmr.code} v{self.version_number}"
