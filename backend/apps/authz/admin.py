from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.authz.models import SiteRoleAssignment, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("username",)


@admin.register(SiteRoleAssignment)
class SiteRoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ("user", "site", "role", "is_active", "updated_at")
    list_filter = ("role", "is_active", "site")
    search_fields = ("user__username", "site__code", "site__name")
    autocomplete_fields = ("user", "site")
    ordering = ("site__code", "user__username", "role")
