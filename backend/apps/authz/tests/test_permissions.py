from __future__ import annotations

from typing import Any, ClassVar

import pytest
from django.contrib.auth import get_user_model
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
