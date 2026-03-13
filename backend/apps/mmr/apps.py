from __future__ import annotations

from django.apps import AppConfig


class MmrConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.mmr"
    verbose_name = "Master Manufacturing Records"
