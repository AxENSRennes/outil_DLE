from __future__ import annotations

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
