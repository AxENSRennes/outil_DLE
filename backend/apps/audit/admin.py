from __future__ import annotations

from django.contrib import admin

from apps.audit.models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "actor", "site", "occurred_at")
    list_filter = ("event_type", "site")
    search_fields = ("actor__username", "site__code")
    ordering = ("-occurred_at", "-id")
    autocomplete_fields = ("actor", "site")
