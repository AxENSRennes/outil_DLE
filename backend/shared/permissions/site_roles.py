from __future__ import annotations

from typing import Any

from apps.authz.domain.policies import user_has_any_site_role
from apps.sites.models import Site
from rest_framework.exceptions import NotAuthenticated, NotFound, PermissionDenied
from rest_framework.permissions import BasePermission


def get_active_site_by_code(site_code: str) -> Site:
    site = Site.objects.filter(code=site_code, is_active=True).first()
    if site is None:
        raise NotFound(detail="Site not found.", code="site_not_found")
    return site


class SiteScopedRolePermission(BasePermission):
    message = "The authenticated user does not have the required role for this site."

    def _get_required_roles(self, view: Any) -> tuple[str, ...]:
        return tuple(str(role) for role in getattr(view, "required_site_roles", ()))

    def _require_authenticated_user(self, user: Any) -> None:
        if getattr(user, "is_authenticated", False):
            return

        raise NotAuthenticated(
            detail="Authentication credentials were not provided.",
            code="not_authenticated",
        )

    def _resolve_site_from_view(self, view: Any) -> Site | None:
        existing_site = getattr(view, "site", None)
        if isinstance(existing_site, Site):
            return existing_site

        get_site = getattr(view, "get_site", None)
        if callable(get_site):
            site = get_site()
            if isinstance(site, Site):
                view.site = site
                return site

        site_lookup_kwarg = getattr(view, "site_lookup_kwarg", "site_code")
        site_code = getattr(view, "kwargs", {}).get(site_lookup_kwarg)
        if site_code is None:
            return None

        site = get_active_site_by_code(site_code)
        view.site = site
        return site

    def _resolve_site_from_object(self, view: Any, obj: Any) -> Site | None:
        if isinstance(obj, Site):
            if not obj.is_active:
                raise NotFound(detail="Site not found.", code="site_not_found")
            return obj

        get_site_for_object = getattr(view, "get_site_for_object", None)
        if callable(get_site_for_object):
            site = get_site_for_object(obj)
            if isinstance(site, Site):
                if not site.is_active:
                    raise NotFound(detail="Site not found.", code="site_not_found")
                return site

        site_object_attr = getattr(view, "site_object_attr", "site")
        site = getattr(obj, site_object_attr, None)
        if isinstance(site, Site):
            if not site.is_active:
                raise NotFound(detail="Site not found.", code="site_not_found")
            return site

        site_object_code_attr = getattr(view, "site_object_code_attr", "site_code")
        site_code = getattr(obj, site_object_code_attr, None)
        if isinstance(site_code, str):
            return get_active_site_by_code(site_code)

        return None

    def _require_site_role(self, user: Any, site: Site, required_roles: tuple[str, ...]) -> bool:
        if user_has_any_site_role(user, site, required_roles):
            return True

        raise PermissionDenied(detail=self.message, code="site_role_required")

    def has_permission(self, request: Any, view: Any) -> bool:
        required_roles = self._get_required_roles(view)
        if not required_roles:
            return True

        self._require_authenticated_user(request.user)

        site = self._resolve_site_from_view(view)
        if site is not None:
            return self._require_site_role(request.user, site, required_roles)

        if getattr(view, "allow_object_level_site_resolve", False):
            return True

        raise PermissionDenied(
            detail="A site context is required.",
            code="site_context_missing",
        )

    def has_object_permission(self, request: Any, view: Any, obj: Any) -> bool:
        required_roles = self._get_required_roles(view)
        if not required_roles:
            return True

        self._require_authenticated_user(request.user)

        site = self._resolve_site_from_object(view, obj) or self._resolve_site_from_view(view)
        if site is None:
            raise PermissionDenied(
                detail="A site context is required.",
                code="site_context_missing",
            )

        return self._require_site_role(request.user, site, required_roles)
