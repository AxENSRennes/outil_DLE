from __future__ import annotations

from django.contrib import admin

from apps.batches.models import Batch


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("batch_number", "site", "mmr_version", "status", "created_at")
    list_filter = ("status", "site")
    search_fields = ("batch_number",)
