from __future__ import annotations

from django.contrib import admin

from apps.batches.models import Batch, BatchDocumentRequirement, BatchStep


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("batch_number", "site", "status", "review_state", "created_at")
    list_filter = ("status", "review_state", "site")
    search_fields = ("batch_number",)
    ordering = ("-created_at",)
    readonly_fields = ("snapshot_json", "batch_context_json")


@admin.register(BatchStep)
class BatchStepAdmin(admin.ModelAdmin):
    list_display = (
        "batch",
        "step_key",
        "occurrence_key",
        "status",
        "is_applicable",
        "sequence_order",
    )
    list_filter = ("status", "is_applicable", "step_key")
    search_fields = ("batch__batch_number", "step_key", "occurrence_key")
    ordering = ("batch", "sequence_order")
    readonly_fields = ("data_json", "meta_json", "applicability_basis_json")


@admin.register(BatchDocumentRequirement)
class BatchDocumentRequirementAdmin(admin.ModelAdmin):
    list_display = (
        "batch",
        "document_code",
        "repeat_mode",
        "expected_count",
        "actual_count",
        "status",
        "is_applicable",
    )
    list_filter = ("status", "repeat_mode", "is_applicable")
    search_fields = ("batch__batch_number", "document_code")
    ordering = ("batch", "document_code")
    readonly_fields = ("applicability_basis_json", "meta_json")
