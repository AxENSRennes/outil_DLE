from __future__ import annotations

from typing import Any

from django.contrib import admin
from django.http import HttpRequest

from apps.batches.models import Batch, BatchStep, DossierChecklistItem, StepSignature


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("batch_number", "site", "status", "created_by", "created_at")
    list_filter = ("status", "site")
    search_fields = ("batch_number",)
    ordering = ("-created_at",)
    readonly_fields = ("snapshot_json", "batch_context_json", "created_at", "updated_at")

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False


@admin.register(BatchStep)
class BatchStepAdmin(admin.ModelAdmin):
    list_display = ("batch", "step_key", "title", "sequence_order", "status", "is_applicable")
    list_filter = ("status", "is_applicable")
    search_fields = ("step_key", "title", "batch__batch_number")
    ordering = ("batch", "sequence_order")
    readonly_fields = ("data_json", "meta_json", "created_at", "updated_at")

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False


@admin.register(StepSignature)
class StepSignatureAdmin(admin.ModelAdmin):
    list_display = ("step", "signer", "meaning", "signed_at")
    readonly_fields = ("step", "signer", "meaning", "signed_at")

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False


@admin.register(DossierChecklistItem)
class DossierChecklistItemAdmin(admin.ModelAdmin):
    list_display = ("document_name", "batch", "is_present")

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False
