from __future__ import annotations

from typing import Any, ClassVar

from django.contrib import admin
from django.http import HttpRequest

from apps.exports.models import BatchDossierStructure, DossierElement, DossierProfile


@admin.register(DossierProfile)
class DossierProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "mmr_version", "created_at", "updated_at")
    search_fields = ("name", "mmr_version__mmr__code")
    autocomplete_fields = ("mmr_version",)


class DossierElementInline(admin.TabularInline):
    model = DossierElement
    extra = 0
    fields = (
        "element_identifier",
        "element_type",
        "display_order",
        "applicability",
        "title",
    )
    readonly_fields = fields

    def has_add_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False


@admin.register(BatchDossierStructure)
class BatchDossierStructureAdmin(admin.ModelAdmin):
    list_display = ("batch", "dossier_profile", "is_active", "resolved_at")
    list_filter = ("is_active",)
    search_fields = ("batch__batch_number",)
    inlines: ClassVar[list[type]] = [DossierElementInline]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False
