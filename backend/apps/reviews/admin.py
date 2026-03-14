from __future__ import annotations

from typing import Any

from django.contrib import admin
from django.http import HttpRequest

from apps.reviews.models import ReviewEvent


@admin.register(ReviewEvent)
class ReviewEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "batch", "reviewer", "step", "occurred_at")
    list_filter = ("event_type",)
    search_fields = ("batch__reference", "reviewer__username")
    ordering = ("-occurred_at", "-id")
    readonly_fields = (
        "batch",
        "reviewer",
        "event_type",
        "step",
        "note",
        "occurred_at",
        "metadata",
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False
