from __future__ import annotations

from django.contrib import admin

from apps.mmr.models import MMR, MMRVersion


@admin.register(MMR)
class MMRAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "site", "is_active")
    list_filter = ("is_active", "site")
    search_fields = ("code", "name")


@admin.register(MMRVersion)
class MMRVersionAdmin(admin.ModelAdmin):
    list_display = ("mmr", "version_number", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("mmr__code",)
