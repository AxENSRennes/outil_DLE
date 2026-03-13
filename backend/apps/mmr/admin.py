from __future__ import annotations

from typing import Any

from django.contrib import admin

from apps.mmr.models import MMR, MMRVersion


@admin.register(MMR)
class MMRAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "site", "product", "is_active", "updated_at")
    list_filter = ("is_active", "site")
    search_fields = ("code", "name")
    ordering = ("code",)

    def has_delete_permission(self, request: Any, obj: Any = None) -> bool:
        return False


@admin.register(MMRVersion)
class MMRVersionAdmin(admin.ModelAdmin):
    list_display = (
        "mmr",
        "version_number",
        "status",
        "created_by",
        "created_at",
    )
    list_filter = ("status", "mmr__site")
    search_fields = ("mmr__code", "mmr__name")
    readonly_fields = ("schema_json", "activated_by", "activated_at")
    ordering = ("-created_at",)

    def has_delete_permission(self, request: Any, obj: Any = None) -> bool:
        return False
