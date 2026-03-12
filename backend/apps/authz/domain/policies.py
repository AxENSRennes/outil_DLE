from __future__ import annotations

from typing import Any

from django.db.models import QuerySet

from apps.authz.models import SiteRole, SiteRoleAssignment
from apps.sites.models import Site


def get_active_site_role_assignments(user: Any) -> QuerySet[SiteRoleAssignment]:
    if not getattr(user, "is_authenticated", False):
        return SiteRoleAssignment.objects.none()

    return SiteRoleAssignment.objects.filter(
        user=user,
        is_active=True,
        site__is_active=True,
    ).select_related("site")


def get_user_site_roles(user: Any, site: Site) -> tuple[str, ...]:
    assignments = get_active_site_role_assignments(user).filter(site=site).order_by("role")
    return tuple(assignments.values_list("role", flat=True))


def user_has_site_role(user: Any, site: Site, role: str | SiteRole) -> bool:
    return role in get_user_site_roles(user, site)


def user_has_any_site_role(user: Any, site: Site, roles: tuple[str | SiteRole, ...]) -> bool:
    if not roles:
        return False

    normalized_roles = {str(role) for role in roles}
    return any(role in normalized_roles for role in get_user_site_roles(user, site))


def get_authorized_sites(user: Any) -> QuerySet[Site]:
    assignment_ids = get_active_site_role_assignments(user).values_list("site_id", flat=True)
    return Site.objects.filter(id__in=assignment_ids).order_by("code")
