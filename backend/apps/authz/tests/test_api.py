from __future__ import annotations

import base64
from typing import Any

import pytest
from django.contrib.auth import get_user_model

from apps.authz.models import SiteRole, SiteRoleAssignment
from apps.sites.models import Site


@pytest.mark.django_db
def test_auth_context_requires_authentication(client: Any) -> None:
    response = client.get("/api/v1/auth/context/")

    assert response.status_code == 403
    assert response.json()["code"] == "not_authenticated"


@pytest.mark.django_db
def test_auth_context_returns_authenticated_user_site_assignments(client: Any) -> None:
    user = get_user_model().objects.create_user(
        username="alice.operator",
        password="test-pass-123",
        first_name="Alice",
        last_name="Operator",
    )
    other_user = get_user_model().objects.create_user(
        username="bob.qa",
        password="test-pass-123",
    )
    site_alpha = Site.objects.create(code="paris-line-1", name="Paris Line 1")
    site_beta = Site.objects.create(code="lyon-qc", name="Lyon QC")

    SiteRoleAssignment.objects.create(user=user, site=site_alpha, role=SiteRole.OPERATOR)
    SiteRoleAssignment.objects.create(
        user=user,
        site=site_alpha,
        role=SiteRole.PRODUCTION_REVIEWER,
    )
    SiteRoleAssignment.objects.create(
        user=user,
        site=site_beta,
        role=SiteRole.QUALITY_REVIEWER,
    )
    SiteRoleAssignment.objects.create(
        user=other_user,
        site=site_beta,
        role=SiteRole.INTERNAL_CONFIGURATOR,
    )

    client.force_login(user)
    response = client.get("/api/v1/auth/context/")

    assert response.status_code == 200
    assert response.json() == {
        "user": {
            "id": user.id,
            "username": "alice.operator",
            "first_name": "Alice",
            "last_name": "Operator",
        },
        "site_assignments": [
            {
                "site": {
                    "id": site_beta.id,
                    "code": "lyon-qc",
                    "name": "Lyon QC",
                },
                "roles": ["quality_reviewer"],
            },
            {
                "site": {
                    "id": site_alpha.id,
                    "code": "paris-line-1",
                    "name": "Paris Line 1",
                },
                "roles": ["operator", "production_reviewer"],
            },
        ],
    }


@pytest.mark.django_db
def test_auth_context_rejects_basic_auth_when_session_is_missing(client: Any) -> None:
    get_user_model().objects.create_user(
        username="basic-auth-user",
        password="test-pass-123",
    )
    credentials = base64.b64encode(b"basic-auth-user:test-pass-123").decode()

    response = client.get(
        "/api/v1/auth/context/",
        HTTP_AUTHORIZATION=f"Basic {credentials}",
    )

    assert response.status_code == 403
    assert response.json()["code"] == "not_authenticated"


@pytest.mark.django_db
def test_operator_access_probe_allows_user_with_operator_role_for_site(client: Any) -> None:
    user = get_user_model().objects.create_user(
        username="site-operator",
        password="test-pass-123",
    )
    site = Site.objects.create(code="paris-line-1", name="Paris Line 1")
    SiteRoleAssignment.objects.create(user=user, site=site, role=SiteRole.OPERATOR)

    client.force_login(user)
    response = client.get(f"/api/v1/auth/sites/{site.code}/operator-access/")

    assert response.status_code == 200
    assert response.json() == {
        "site": {
            "id": site.id,
            "code": site.code,
            "name": "Paris Line 1",
        },
        "required_role": "operator",
        "status": "authorized",
    }


@pytest.mark.django_db
def test_operator_access_probe_denies_wrong_role_for_site(client: Any) -> None:
    user = get_user_model().objects.create_user(
        username="qa-user",
        password="test-pass-123",
    )
    site = Site.objects.create(code="lyon-qc", name="Lyon QC")
    SiteRoleAssignment.objects.create(user=user, site=site, role=SiteRole.QUALITY_REVIEWER)

    client.force_login(user)
    response = client.get(f"/api/v1/auth/sites/{site.code}/operator-access/")

    assert response.status_code == 403
    assert response.json()["code"] == "site_role_required"


@pytest.mark.django_db
def test_operator_access_probe_denies_same_role_for_other_site(client: Any) -> None:
    user = get_user_model().objects.create_user(
        username="wrong-site-operator",
        password="test-pass-123",
    )
    assigned_site = Site.objects.create(code="paris-line-1", name="Paris Line 1")
    requested_site = Site.objects.create(code="lyon-qc", name="Lyon QC")
    SiteRoleAssignment.objects.create(user=user, site=assigned_site, role=SiteRole.OPERATOR)

    client.force_login(user)
    response = client.get(f"/api/v1/auth/sites/{requested_site.code}/operator-access/")

    assert response.status_code == 403
    assert response.json()["code"] == "site_role_required"
