from __future__ import annotations

from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.authz.models import SiteRole, SiteRoleAssignment
from apps.sites.models import Site


@pytest.mark.django_db
def test_custom_user_model_is_configured(settings: Any) -> None:
    user_model = get_user_model()

    assert settings.AUTH_USER_MODEL == "authz.User"
    assert user_model._meta.label == "authz.User"


@pytest.mark.django_db
def test_site_role_assignment_enforces_unique_user_site_role() -> None:
    user = get_user_model().objects.create_user(username="operator-1", password="test-pass-123")
    site = Site.objects.create(code="paris-line-1", name="Paris Line 1")

    SiteRoleAssignment.objects.create(user=user, site=site, role=SiteRole.OPERATOR)

    with pytest.raises(IntegrityError):
        SiteRoleAssignment.objects.create(user=user, site=site, role=SiteRole.OPERATOR)


@pytest.mark.django_db
def test_site_role_assignment_rejects_unknown_role_values() -> None:
    user = get_user_model().objects.create_user(username="reviewer-1", password="test-pass-123")
    site = Site.objects.create(code="berlin-pack", name="Berlin Packaging")
    assignment = SiteRoleAssignment(user=user, site=site, role="super-admin")

    with pytest.raises(ValidationError):
        assignment.full_clean()


@pytest.mark.django_db
def test_user_workstation_pin_is_hashed_and_verifiable() -> None:
    user = get_user_model().objects.create_user(username="pin-user", password="test-pass-123")

    user.set_workstation_pin("2468")
    user.save(update_fields=["workstation_pin"])

    assert user.workstation_pin != "2468"
    assert user.check_workstation_pin("2468") is True
    assert user.check_workstation_pin("9999") is False
