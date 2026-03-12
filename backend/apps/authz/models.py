from __future__ import annotations

from typing import ClassVar

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    class Meta:
        ordering = ("username",)


class SiteRole(models.TextChoices):
    OPERATOR = "operator", _("Operator")
    PRODUCTION_REVIEWER = "production_reviewer", _("Production Reviewer")
    QUALITY_REVIEWER = "quality_reviewer", _("Quality Reviewer")
    INTERNAL_CONFIGURATOR = "internal_configurator", _("Internal Configurator")


class SiteRoleAssignment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="site_role_assignments",
    )
    site = models.ForeignKey(
        "sites.Site",
        on_delete=models.CASCADE,
        related_name="role_assignments",
    )
    role = models.CharField(max_length=64, choices=SiteRole.choices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("site__code", "role", "user__username")
        constraints: ClassVar[tuple[models.BaseConstraint, ...]] = (
            models.UniqueConstraint(
                fields=("user", "site", "role"),
                name="authz_unique_site_role_assignment",
            ),
        )

    def __str__(self) -> str:
        return f"{self.user.username} -> {self.site.code} ({self.role})"
