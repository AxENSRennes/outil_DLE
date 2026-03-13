from __future__ import annotations

from types import SimpleNamespace
from typing import Any, ClassVar

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView
from shared.permissions.site_roles import SiteScopedRolePermission

from apps.authz.models import SiteRole, SiteRoleAssignment
from apps.sites.models import Site


class OperatorOnlySiteView(APIView):
    permission_classes: ClassVar[list[type]] = [IsAuthenticated, SiteScopedRolePermission]
    required_site_roles = (SiteRole.OPERATOR,)
    site_lookup_kwarg = "site_code"

    def get(self, request: Any, site_code: str) -> Response:
        return Response({"site_code": site_code, "status": "ok"})


class PermissionOnlyOperatorSiteView(APIView):
    permission_classes: ClassVar[list[type]] = [SiteScopedRolePermission]
    required_site_roles = (SiteRole.OPERATOR,)
    site_lookup_kwarg = "site_code"

    def get(self, request: Any, site_code: str) -> Response:
        return Response({"site_code": site_code, "status": "ok"})


class EmptyRolesView(APIView):
    permission_classes: ClassVar[list[type]] = [SiteScopedRolePermission]
    required_site_roles: tuple[str, ...] = ()

    def get(self, request: Any) -> Response:
        return Response({"status": "ok"})


class NoRolesAttrView(APIView):
    permission_classes: ClassVar[list[type]] = [SiteScopedRolePermission]

    def get(self, request: Any) -> Response:
        return Response({"status": "ok"})


class PermissionOnlyDeferredSiteView(APIView):
    permission_classes: ClassVar[list[type]] = [SiteScopedRolePermission]
    required_site_roles = (SiteRole.OPERATOR,)
    allow_object_level_site_resolve = True

    def get(self, request: Any) -> Response:
        return Response({"status": "ok"})


@pytest.mark.django_db
def test_site_role_permission_allows_user_with_required_role_for_site() -> None:
    user = get_user_model().objects.create_user(username="allowed-user", password="test-pass-123")
    site = Site.objects.create(code="site-a", name="Site A")
    SiteRoleAssignment.objects.create(user=user, site=site, role=SiteRole.OPERATOR)

    request = APIRequestFactory().get(f"/api/v1/auth/site-access/{site.code}/")
    force_authenticate(request, user=user)
    response = OperatorOnlySiteView.as_view()(request, site_code=site.code)

    assert response.status_code == 200
    assert response.data == {"site_code": site.code, "status": "ok"}


@pytest.mark.django_db
def test_site_role_permission_denies_unauthenticated_requests() -> None:
    site = Site.objects.create(code="site-a", name="Site A")

    request = APIRequestFactory().get(f"/api/v1/auth/site-access/{site.code}/")
    response = OperatorOnlySiteView.as_view()(request, site_code=site.code)

    assert response.status_code == 403
    assert response.data["code"] == "not_authenticated"


@pytest.mark.django_db
def test_site_role_permission_denies_unauthenticated_requests_without_isauthenticated() -> None:
    site = Site.objects.create(code="site-a", name="Site A")

    request = APIRequestFactory().get(f"/api/v1/auth/site-access/{site.code}/")
    response = PermissionOnlyOperatorSiteView.as_view()(request, site_code=site.code)

    assert response.status_code == 403
    assert response.data["code"] == "not_authenticated"


@pytest.mark.django_db
def test_site_role_permission_denies_unauthenticated_deferred_object_resolution() -> None:
    request = APIRequestFactory().get("/api/v1/auth/object-access/")
    response = PermissionOnlyDeferredSiteView.as_view()(request)

    assert response.status_code == 403
    assert response.data["code"] == "not_authenticated"


@pytest.mark.django_db
def test_site_role_permission_denies_unauthenticated_when_roles_empty() -> None:
    request = APIRequestFactory().get("/api/v1/auth/empty-roles/")
    response = EmptyRolesView.as_view()(request)

    assert response.status_code == 403
    assert response.data["code"] == "not_authenticated"


@pytest.mark.django_db
def test_site_role_permission_denies_unauthenticated_when_roles_attr_missing() -> None:
    request = APIRequestFactory().get("/api/v1/auth/no-roles/")
    response = NoRolesAttrView.as_view()(request)

    assert response.status_code == 403
    assert response.data["code"] == "not_authenticated"


@pytest.mark.django_db
def test_site_role_permission_allows_authenticated_when_roles_empty() -> None:
    user = get_user_model().objects.create_user(
        username="empty-roles-user", password="test-pass-123"
    )
    request = APIRequestFactory().get("/api/v1/auth/empty-roles/")
    force_authenticate(request, user=user)
    response = EmptyRolesView.as_view()(request)

    assert response.status_code == 200
    assert response.data == {"status": "ok"}


@pytest.mark.django_db
def test_site_role_permission_object_denies_unauthenticated_when_roles_empty() -> None:
    from rest_framework.exceptions import NotAuthenticated

    permission = SiteScopedRolePermission()
    view = SimpleNamespace(required_site_roles=())
    request = APIRequestFactory().get("/api/v1/auth/empty-roles/")
    # AnonymousUser from DRF (is_authenticated=False)
    request.user = SimpleNamespace(is_authenticated=False)
    obj = SimpleNamespace()

    with pytest.raises(NotAuthenticated):
        permission.has_object_permission(request, view, obj)


@pytest.mark.django_db
def test_site_role_permission_denies_user_with_wrong_role() -> None:
    user = get_user_model().objects.create_user(
        username="wrong-role-user",
        password="test-pass-123",
    )
    site = Site.objects.create(code="site-a", name="Site A")
    SiteRoleAssignment.objects.create(
        user=user,
        site=site,
        role=SiteRole.QUALITY_REVIEWER,
    )

    request = APIRequestFactory().get(f"/api/v1/auth/site-access/{site.code}/")
    force_authenticate(request, user=user)
    response = OperatorOnlySiteView.as_view()(request, site_code=site.code)

    assert response.status_code == 403
    assert response.data["code"] == "site_role_required"


@pytest.mark.django_db
def test_site_role_permission_denies_user_for_other_site() -> None:
    user = get_user_model().objects.create_user(
        username="wrong-site-user",
        password="test-pass-123",
    )
    assigned_site = Site.objects.create(code="site-a", name="Site A")
    requested_site = Site.objects.create(code="site-b", name="Site B")
    SiteRoleAssignment.objects.create(user=user, site=assigned_site, role=SiteRole.OPERATOR)

    request = APIRequestFactory().get(f"/api/v1/auth/site-access/{requested_site.code}/")
    force_authenticate(request, user=user)
    response = OperatorOnlySiteView.as_view()(request, site_code=requested_site.code)

    assert response.status_code == 403
    assert response.data["code"] == "site_role_required"


@pytest.mark.django_db
def test_site_role_permission_can_defer_site_resolution_to_object_level() -> None:
    user = get_user_model().objects.create_user(
        username="object-level-user",
        password="test-pass-123",
    )
    site = Site.objects.create(code="site-a", name="Site A")
    SiteRoleAssignment.objects.create(user=user, site=site, role=SiteRole.OPERATOR)
    permission = SiteScopedRolePermission()
    view = SimpleNamespace(
        required_site_roles=(SiteRole.OPERATOR,),
        kwargs={},
        allow_object_level_site_resolve=True,
    )
    request = APIRequestFactory().get("/api/v1/auth/object-access/")
    request.user = user
    obj = SimpleNamespace(site=site)

    assert permission.has_permission(request, view) is True
    assert permission.has_object_permission(request, view, obj) is True


@pytest.mark.django_db
def test_site_role_permission_resolves_site_from_object_code() -> None:
    user = get_user_model().objects.create_user(
        username="object-code-user",
        password="test-pass-123",
    )
    site = Site.objects.create(code="site-a", name="Site A")
    SiteRoleAssignment.objects.create(user=user, site=site, role=SiteRole.OPERATOR)
    permission = SiteScopedRolePermission()
    view = SimpleNamespace(
        required_site_roles=(SiteRole.OPERATOR,),
        kwargs={},
        allow_object_level_site_resolve=True,
    )
    request = APIRequestFactory().get("/api/v1/auth/object-access/")
    request.user = user
    obj = SimpleNamespace(site_code=site.code)

    assert permission.has_permission(request, view) is True
    assert permission.has_object_permission(request, view, obj) is True


@pytest.mark.django_db
def test_explicit_resolver_returning_none_does_not_fall_through_to_attribute() -> None:
    """get_site_for_object returning None must NOT fall through to obj.site attribute."""
    user = get_user_model().objects.create_user(
        username="no-fallthrough",
        password="test-pass-123",
    )
    site = Site.objects.create(code="site-a", name="Site A")
    SiteRoleAssignment.objects.create(user=user, site=site, role=SiteRole.OPERATOR)
    permission = SiteScopedRolePermission()
    view = SimpleNamespace(
        required_site_roles=(SiteRole.OPERATOR,),
        kwargs={},
        allow_object_level_site_resolve=True,
        get_site_for_object=lambda obj: None,  # explicitly returns None
    )
    request = APIRequestFactory().get("/api/v1/auth/object-access/")
    request.user = user
    obj = SimpleNamespace(site=site)  # has .site but resolver says None

    assert permission.has_permission(request, view) is True
    with pytest.raises(PermissionDenied):
        permission.has_object_permission(request, view, obj)


@pytest.mark.django_db
def test_explicit_resolver_returning_none_does_not_fall_through_to_view_kwargs() -> None:
    """get_site_for_object returning None must NOT fall through to view kwargs."""
    user = get_user_model().objects.create_user(
        username="no-fallthrough-kwargs",
        password="test-pass-123",
    )
    site = Site.objects.create(code="site-a", name="Site A")
    SiteRoleAssignment.objects.create(user=user, site=site, role=SiteRole.OPERATOR)
    permission = SiteScopedRolePermission()
    view = SimpleNamespace(
        required_site_roles=(SiteRole.OPERATOR,),
        kwargs={"site_code": site.code},
        allow_object_level_site_resolve=True,
        get_site_for_object=lambda obj: None,  # explicitly returns None
    )
    request = APIRequestFactory().get("/api/v1/auth/object-access/")
    request.user = user
    obj = SimpleNamespace(site=site)  # has .site but resolver says None

    assert permission.has_permission(request, view) is True
    with pytest.raises(PermissionDenied):
        permission.has_object_permission(request, view, obj)
