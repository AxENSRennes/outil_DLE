from __future__ import annotations

from typing import ClassVar

from django.conf import settings
from django.db import models


class MMR(models.Model):
    site = models.ForeignKey("sites.Site", on_delete=models.PROTECT, related_name="mmrs")
    product = models.ForeignKey("sites.Product", on_delete=models.PROTECT, related_name="mmrs")
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "MMR"
        verbose_name_plural = "MMRs"
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(fields=["site", "code"], name="uniq_mmr_code_per_site"),
        ]
        ordering = ("code",)

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class MMRVersionStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    RETIRED = "retired", "Retired"


class MMRVersion(models.Model):
    mmr = models.ForeignKey(MMR, on_delete=models.PROTECT, related_name="versions")
    version_number = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20,
        choices=MMRVersionStatus.choices,
        default=MMRVersionStatus.DRAFT,
    )
    schema_json = models.JSONField(default=dict, blank=True)
    change_summary = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_mmr_versions",
    )
    activated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="activated_mmr_versions",
        null=True,
        blank=True,
    )
    activated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "MMR Version"
        verbose_name_plural = "MMR Versions"
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["mmr", "version_number"], name="uniq_mmr_version_number"
            ),
        ]
        ordering = ("-version_number",)

    def __str__(self) -> str:
        return f"{self.mmr.code} v{self.version_number} ({self.status})"
