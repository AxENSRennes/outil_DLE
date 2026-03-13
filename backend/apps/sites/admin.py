from __future__ import annotations

from typing import Any

from django.contrib import admin

from apps.sites.models import Product, Site


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("code", "name")
    ordering = ("code",)

    def has_delete_permission(self, request: Any, obj: Any = None) -> bool:
        return False


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "site", "family", "is_active", "updated_at")
    list_filter = ("is_active", "site")
    search_fields = ("code", "name", "family")
    ordering = ("code",)

    def has_delete_permission(self, request: Any, obj: Any = None) -> bool:
        return False
