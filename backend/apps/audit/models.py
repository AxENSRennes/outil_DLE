from __future__ import annotations

from typing import ClassVar

from django.conf import settings
from django.db import models


class AuditEventType(models.TextChoices):
    IDENTIFY = "identify", "Identify"
    SWITCH_USER = "switch_user", "Switch User"
    LOCK_WORKSTATION = "lock_workstation", "Lock Workstation"
    IDENTIFY_FAILED = "identify_failed", "Identify Failed"
    SIGNATURE_REAUTH_SUCCEEDED = "signature_reauth_succeeded", "Signature Reauth Succeeded"
    SIGNATURE_REAUTH_FAILED = "signature_reauth_failed", "Signature Reauth Failed"


class AuditEvent(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="audit_events",
        null=True,
        blank=True,
    )
    site = models.ForeignKey(
        "sites.Site",
        on_delete=models.SET_NULL,
        related_name="audit_events",
        null=True,
        blank=True,
    )
    event_type = models.CharField(max_length=64, choices=AuditEventType.choices)
    occurred_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("-occurred_at", "-id")
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=["event_type", "occurred_at"],
                name="audit_event_type_occurred_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} @ {self.occurred_at.isoformat()}"
