from __future__ import annotations

from typing import Any

from django.contrib import admin
from django.http import HttpRequest

from apps.audit.models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "actor", "site", "target_type", "target_id", "occurred_at")
    list_filter = ("event_type", "site", "target_type")
    search_fields = ("actor__username", "site__code")
    ordering = ("-occurred_at", "-id")
    autocomplete_fields = ("actor", "site")

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False
