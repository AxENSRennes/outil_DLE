from __future__ import annotations

from typing import Any

from django.contrib import admin

from apps.batches.models import Batch, BatchStep, DossierChecklistItem, StepSignature


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("batch_number", "site", "mmr_version", "status", "created_at")
    list_filter = ("status", "site")
    search_fields = ("batch_number",)


@admin.register(BatchStep)
class BatchStepAdmin(admin.ModelAdmin):
    list_display = ("reference", "batch", "order", "status")
    list_filter = ("status",)


@admin.register(StepSignature)
class StepSignatureAdmin(admin.ModelAdmin):
    list_display = ("step", "signer", "meaning", "signed_at")
    readonly_fields = ("step", "signer", "meaning", "signed_at")

    def has_add_permission(self, request: Any) -> bool:
        return False

    def has_change_permission(self, request: Any, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: Any, obj: Any = None) -> bool:
        return False


@admin.register(DossierChecklistItem)
class DossierChecklistItemAdmin(admin.ModelAdmin):
    list_display = ("document_name", "batch", "is_present")
    list_filter = ("is_present",)
