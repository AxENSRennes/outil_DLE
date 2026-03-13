from __future__ import annotations

import json

import pytest
from config.settings import base as base_settings
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent, AuditEventType
from apps.authz.models import SiteRole, SiteRoleAssignment
from apps.authz.tests.helpers import csrf_client, post_json
from apps.sites.models import Site


@pytest.mark.django_db
def test_signature_reauth_requires_authenticated_session() -> None:
    client, token = csrf_client()

    response = post_json(
        client,
        "/api/v1/auth/signature-reauth/",
        {
            "site_code": "paris-line-1",
            "required_roles": ["operator"],
            "pin": "2468",
        },
        csrf_token=token,
    )

    assert response.status_code == 403
    assert response.json()["code"] == "not_authenticated"


@pytest.mark.django_db
def test_signature_reauth_authorizes_active_user_with_valid_pin_and_role() -> None:
    user = get_user_model().objects.create_user(
        username="alice.operator",
        password="admin-pass-123",
        first_name="Alice",
        last_name="Operator",
    )
    user.set_workstation_pin("2468")
    user.save(update_fields=["workstation_pin"])
    site = Site.objects.create(code="paris-line-1", name="Paris Line 1")
    SiteRoleAssignment.objects.create(user=user, site=site, role=SiteRole.OPERATOR)

    client, token = csrf_client(user=user)
    response = post_json(
        client,
        "/api/v1/auth/signature-reauth/",
        {
            "site_code": site.code,
            "required_roles": ["operator"],
            "pin": "2468",
        },
        csrf_token=token,
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "authorized",
        "site": {
            "id": site.id,
            "code": site.code,
            "name": site.name,
        },
        "signer": {
            "id": user.id,
            "username": user.username,
            "first_name": "Alice",
            "last_name": "Operator",
        },
        "authorized_roles": ["operator"],
    }

    event = AuditEvent.objects.get(event_type=AuditEventType.SIGNATURE_REAUTH_SUCCEEDED)
    assert event.actor == user
    assert event.site == site
    assert event.metadata == {
        "required_roles": ["operator"],
        "outcome": "authorized",
        "ip_address": "127.0.0.1",
    }


@pytest.mark.django_db
def test_signature_reauth_rejects_wrong_role_and_audits_failure() -> None:
    user = get_user_model().objects.create_user(
        username="qa-user",
        password="admin-pass-123",
    )
    user.set_workstation_pin("2468")
    user.save(update_fields=["workstation_pin"])
    site = Site.objects.create(code="lyon-qc", name="Lyon QC")
    SiteRoleAssignment.objects.create(user=user, site=site, role=SiteRole.QUALITY_REVIEWER)

    client, token = csrf_client(user=user)
    response = post_json(
        client,
        "/api/v1/auth/signature-reauth/",
        {
            "site_code": site.code,
            "required_roles": ["operator"],
            "pin": "2468",
        },
        csrf_token=token,
    )

    assert response.status_code == 403
    assert response.json()["code"] == "signature_role_not_authorized"

    event = AuditEvent.objects.get(event_type=AuditEventType.SIGNATURE_REAUTH_FAILED)
    assert event.actor == user
    assert event.site == site
    assert event.metadata == {
        "required_roles": ["operator"],
        "reason": "missing_required_role",
        "ip_address": "127.0.0.1",
    }


@pytest.mark.django_db
def test_signature_reauth_rejects_wrong_site_and_audits_failure() -> None:
    user = get_user_model().objects.create_user(
        username="operator-user",
        password="admin-pass-123",
    )
    user.set_workstation_pin("2468")
    user.save(update_fields=["workstation_pin"])
    assigned_site = Site.objects.create(code="paris-line-1", name="Paris Line 1")
    requested_site = Site.objects.create(code="lyon-qc", name="Lyon QC")
    SiteRoleAssignment.objects.create(user=user, site=assigned_site, role=SiteRole.OPERATOR)

    client, token = csrf_client(user=user)
    response = post_json(
        client,
        "/api/v1/auth/signature-reauth/",
        {
            "site_code": requested_site.code,
            "required_roles": ["operator"],
            "pin": "2468",
        },
        csrf_token=token,
    )

    assert response.status_code == 403
    assert response.json()["code"] == "signature_role_not_authorized"

    event = AuditEvent.objects.get(event_type=AuditEventType.SIGNATURE_REAUTH_FAILED)
    assert event.actor == user
    assert event.site == requested_site
    assert event.metadata == {
        "required_roles": ["operator"],
        "reason": "missing_required_role",
        "ip_address": "127.0.0.1",
    }


@pytest.mark.django_db
def test_signature_reauth_rejects_bad_pin_without_leaking_secret() -> None:
    user = get_user_model().objects.create_user(
        username="operator-user",
        password="admin-pass-123",
    )
    user.set_workstation_pin("2468")
    user.save(update_fields=["workstation_pin"])
    site = Site.objects.create(code="paris-line-1", name="Paris Line 1")
    SiteRoleAssignment.objects.create(user=user, site=site, role=SiteRole.OPERATOR)

    client, token = csrf_client(user=user)
    response = post_json(
        client,
        "/api/v1/auth/signature-reauth/",
        {
            "site_code": site.code,
            "required_roles": ["operator"],
            "pin": "9999",
        },
        csrf_token=token,
    )

    assert response.status_code == 403
    assert response.json()["code"] == "invalid_signature_reauth_credentials"

    event = AuditEvent.objects.get(event_type=AuditEventType.SIGNATURE_REAUTH_FAILED)
    assert event.actor == user
    assert event.site == site
    assert event.metadata["required_roles"] == ["operator"]
    assert event.metadata["reason"] == "invalid_credentials"
    assert event.metadata["ip_address"] == "127.0.0.1"
    assert "pin" not in event.metadata
    assert "9999" not in json.dumps(event.metadata)


@pytest.mark.django_db
def test_signature_reauth_rejects_unknown_site_and_audits_failure() -> None:
    user = get_user_model().objects.create_user(
        username="missing-site-user",
        password="admin-pass-123",
    )
    user.set_workstation_pin("2468")
    user.save(update_fields=["workstation_pin"])

    client, token = csrf_client(user=user)
    response = post_json(
        client,
        "/api/v1/auth/signature-reauth/",
        {
            "site_code": "missing-site",
            "required_roles": ["operator"],
            "pin": "2468",
        },
        csrf_token=token,
    )

    assert response.status_code == 404
    assert response.json()["code"] == "site_not_found"

    event = AuditEvent.objects.get(event_type=AuditEventType.SIGNATURE_REAUTH_FAILED)
    assert event.actor == user
    assert event.site is None
    assert event.metadata == {
        "required_roles": ["operator"],
        "reason": "site_not_found",
        "site_code": "missing-site",
        "ip_address": "127.0.0.1",
    }


@pytest.mark.django_db
def test_signature_reauth_requires_csrf() -> None:
    user = get_user_model().objects.create_user(
        username="csrf-user",
        password="admin-pass-123",
    )
    user.set_workstation_pin("2468")
    user.save(update_fields=["workstation_pin"])
    site = Site.objects.create(code="paris-line-1", name="Paris Line 1")
    SiteRoleAssignment.objects.create(user=user, site=site, role=SiteRole.OPERATOR)
    client = APIClient(enforce_csrf_checks=True)
    client.force_login(user)

    response = client.post(
        "/api/v1/auth/signature-reauth/",
        {"site_code": site.code, "required_roles": ["operator"], "pin": "2468"},
        format="json",
    )

    assert response.status_code == 403


@pytest.mark.django_db
@override_settings(
    REST_FRAMEWORK={
        **base_settings.REST_FRAMEWORK,
        "DEFAULT_THROTTLE_RATES": {
            "workstation_identify": "5/minute",
            "signature_reauth": "1/minute",
        },
    }
)
def test_signature_reauth_is_rate_limited_and_audited() -> None:
    user = get_user_model().objects.create_user(
        username="throttle-user",
        password="admin-pass-123",
    )
    user.set_workstation_pin("2468")
    user.save(update_fields=["workstation_pin"])
    site = Site.objects.create(code="paris-line-1", name="Paris Line 1")
    SiteRoleAssignment.objects.create(user=user, site=site, role=SiteRole.OPERATOR)

    client, token = csrf_client(user=user)
    forwarded_for = "10.0.0.1, 192.168.1.1"
    first_response = client.post(
        "/api/v1/auth/signature-reauth/",
        {
            "site_code": site.code,
            "required_roles": ["operator"],
            "pin": "0000",
        },
        format="json",
        HTTP_X_CSRFTOKEN=token,
        HTTP_X_FORWARDED_FOR=forwarded_for,
    )
    second_response = client.post(
        "/api/v1/auth/signature-reauth/",
        {
            "site_code": site.code,
            "required_roles": ["operator"],
            "pin": "0000",
        },
        format="json",
        HTTP_X_CSRFTOKEN=token,
        HTTP_X_FORWARDED_FOR=forwarded_for,
    )

    assert first_response.status_code == 403
    assert second_response.status_code == 429

    invalid_credentials_event = AuditEvent.objects.get(
        event_type=AuditEventType.SIGNATURE_REAUTH_FAILED,
        metadata__reason="invalid_credentials",
    )
    throttled_event = AuditEvent.objects.get(
        event_type=AuditEventType.SIGNATURE_REAUTH_FAILED,
        metadata__reason="rate_limited",
    )
    assert invalid_credentials_event.metadata["ip_address"] == "10.0.0.1"
    assert throttled_event.actor == user
    assert throttled_event.site == site
    assert throttled_event.metadata["ip_address"] == "10.0.0.1"
