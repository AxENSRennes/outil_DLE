from __future__ import annotations

from typing import Any

from apps.authz.domain.policies import user_has_any_site_role
from apps.sites.models import Site
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import BasePermission


class SiteScopedRolePermission(BasePermission):
    message = "The authenticated user does not have the required role for this site."

    def has_permission(self, request: Any, view: Any) -> bool:
        required_roles = tuple(getattr(view, "required_site_roles", ()))
        if not required_roles:
            return True

        site_lookup_kwarg = getattr(view, "site_lookup_kwarg", "site_code")
        site_code = view.kwargs.get(site_lookup_kwarg)
        if site_code is None:
            raise PermissionDenied(
                detail="A site context is required.",
                code="site_context_missing",
            )

        site = Site.objects.filter(code=site_code, is_active=True).first()
        if site is None:
            raise NotFound(detail="Site not found.", code="site_not_found")

        view.site = site

        if user_has_any_site_role(request.user, site, required_roles):
            return True

        raise PermissionDenied(detail=self.message, code="site_role_required")
