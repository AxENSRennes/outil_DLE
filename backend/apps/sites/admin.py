from __future__ import annotations

from django.contrib import admin

from apps.sites.models import Site


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("code", "name")
    ordering = ("code",)
