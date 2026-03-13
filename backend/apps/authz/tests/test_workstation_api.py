from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from config.settings import base as base_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.test import override_settings
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent, AuditEventType
from apps.authz.domain import workstation
from apps.authz.models import SiteRole, SiteRoleAssignment
from apps.authz.tests.helpers import csrf_client, post_json
from apps.sites.models import Site


@pytest.mark.django_db
def test_workstation_identify_establishes_session_and_returns_active_context() -> None:
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

    client, token = csrf_client()
    response = post_json(
        client,
        "/api/v1/auth/workstation-identify/",
        {"username": user.username, "pin": "2468"},
        csrf_token=token,
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "identified",
        "event": "identify",
        "previous_user": None,
        "user": {
            "id": user.id,
            "username": "alice.operator",
            "first_name": "Alice",
            "last_name": "Operator",
        },
        "site_assignments": [
            {
                "site": {
                    "id": site.id,
                    "code": "paris-line-1",
                    "name": "Paris Line 1",
                },
                "roles": ["operator"],
            }
        ],
    }

    context_response = client.get("/api/v1/auth/context/")

    assert context_response.status_code == 200
    assert context_response.json()["user"]["username"] == "alice.operator"

    event = AuditEvent.objects.get(event_type=AuditEventType.IDENTIFY)
    assert event.actor == user
    assert event.site is None
    assert event.metadata == {"outcome": "identified", "ip_address": "127.0.0.1"}


@pytest.mark.django_db
def test_workstation_identify_switches_active_user_and_records_switch_event() -> None:
    previous_user = get_user_model().objects.create_user(
        username="alice.operator",
        password="admin-pass-123",
        first_name="Alice",
        last_name="Operator",
    )
    previous_user.set_workstation_pin("2468")
    previous_user.save(update_fields=["workstation_pin"])

    next_user = get_user_model().objects.create_user(
        username="bob.reviewer",
        password="admin-pass-123",
        first_name="Bob",
        last_name="Reviewer",
    )
    next_user.set_workstation_pin("1357")
    next_user.save(update_fields=["workstation_pin"])

    client, token = csrf_client(user=previous_user)
    response = post_json(
        client,
        "/api/v1/auth/workstation-identify/",
        {"username": next_user.username, "pin": "1357"},
        csrf_token=token,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "identified"
    assert response.json()["event"] == "switch_user"
    assert response.json()["user"]["username"] == "bob.reviewer"
    assert response.json()["previous_user"] == {
        "id": previous_user.id,
        "username": "alice.operator",
        "first_name": "Alice",
        "last_name": "Operator",
    }

    context_response = client.get("/api/v1/auth/context/")

    assert context_response.status_code == 200
    assert context_response.json()["user"]["username"] == "bob.reviewer"

    switch_event = AuditEvent.objects.get(event_type=AuditEventType.SWITCH_USER)
    assert switch_event.actor == next_user
    assert switch_event.metadata == {
        "outcome": "identified",
        "ip_address": "127.0.0.1",
        "previous_user_id": previous_user.id,
        "previous_username": previous_user.username,
    }


@pytest.mark.django_db
def test_workstation_lock_clears_authenticated_authority() -> None:
    user = get_user_model().objects.create_user(
        username="line-user",
        password="admin-pass-123",
    )
    client, token = csrf_client(user=user)

    response = post_json(
        client,
        "/api/v1/auth/workstation-lock/",
        {},
        csrf_token=token,
    )

    assert response.status_code == 200
    assert response.json() == {"status": "locked"}

    context_response = client.get("/api/v1/auth/context/")
    assert context_response.status_code == 403
    assert context_response.json()["code"] == "not_authenticated"

    event = AuditEvent.objects.get(event_type=AuditEventType.LOCK_WORKSTATION)
    assert event.actor == user
    assert event.metadata == {"outcome": "locked", "ip_address": "127.0.0.1"}


@pytest.mark.django_db
def test_workstation_identify_rejects_bad_pin_and_audits_without_pin_leakage() -> None:
    user = get_user_model().objects.create_user(
        username="alice.operator",
        password="admin-pass-123",
    )
    user.set_workstation_pin("2468")
    user.save(update_fields=["workstation_pin"])

    client, token = csrf_client()
    response = post_json(
        client,
        "/api/v1/auth/workstation-identify/",
        {"username": user.username, "pin": "9999"},
        csrf_token=token,
    )

    assert response.status_code == 403
    assert response.json()["code"] == "invalid_workstation_credentials"

    event = AuditEvent.objects.get(event_type=AuditEventType.IDENTIFY_FAILED)
    assert event.actor is None
    assert event.metadata["attempted_username"] == user.username
    assert event.metadata["reason"] == "invalid_credentials"
    assert event.metadata["ip_address"] == "127.0.0.1"
    assert "pin" not in event.metadata
    assert "9999" not in json.dumps(event.metadata)


@pytest.mark.django_db
def test_workstation_identify_unknown_username_runs_dummy_hash_check() -> None:
    client, token = csrf_client()

    with patch(
        "apps.authz.domain.workstation.check_password",
        wraps=check_password,
    ) as mock_check_password:
        response = post_json(
            client,
            "/api/v1/auth/workstation-identify/",
            {"username": "missing.user", "pin": "9999"},
            csrf_token=token,
        )

    assert response.status_code == 403
    assert response.json()["code"] == "invalid_workstation_credentials"
    mock_check_password.assert_called_once_with("9999", workstation._TIMING_DUMMY_PIN_HASH)

    event = AuditEvent.objects.get(event_type=AuditEventType.IDENTIFY_FAILED)
    assert event.actor is None
    assert event.metadata["attempted_username"] == "missing.user"
    assert event.metadata["reason"] == "invalid_credentials"
    assert event.metadata["ip_address"] == "127.0.0.1"


@pytest.mark.django_db
def test_workstation_identify_requires_csrf() -> None:
    user = get_user_model().objects.create_user(
        username="csrf-user",
        password="admin-pass-123",
    )
    user.set_workstation_pin("2468")
    user.save(update_fields=["workstation_pin"])
    client = APIClient(enforce_csrf_checks=True)

    response = client.post(
        "/api/v1/auth/workstation-identify/",
        {"username": user.username, "pin": "2468"},
        format="json",
    )

    assert response.status_code == 403


@pytest.mark.django_db
@override_settings(
    REST_FRAMEWORK={
        **base_settings.REST_FRAMEWORK,
        "DEFAULT_THROTTLE_RATES": {
            "workstation_identify": "1/minute",
            "workstation_lock": "5/minute",
            "signature_reauth": "5/minute",
        },
    }
)
def test_workstation_identify_is_rate_limited_and_audited() -> None:
    user = get_user_model().objects.create_user(
        username="throttle-user",
        password="admin-pass-123",
    )
    user.set_workstation_pin("2468")
    user.save(update_fields=["workstation_pin"])

    client, token = csrf_client()
    forwarded_for = "10.0.0.1, 192.168.1.1"
    first_response = client.post(
        "/api/v1/auth/workstation-identify/",
        {"username": user.username, "pin": "0000"},
        format="json",
        HTTP_X_CSRFTOKEN=token,
        HTTP_X_FORWARDED_FOR=forwarded_for,
    )
    second_response = client.post(
        "/api/v1/auth/workstation-identify/",
        {"username": user.username, "pin": "0000"},
        format="json",
        HTTP_X_CSRFTOKEN=token,
        HTTP_X_FORWARDED_FOR=forwarded_for,
    )

    assert first_response.status_code == 403
    assert second_response.status_code == 429

    invalid_credentials_event = AuditEvent.objects.get(
        event_type=AuditEventType.IDENTIFY_FAILED,
        metadata__reason="invalid_credentials",
    )
    throttled_event = AuditEvent.objects.get(
        event_type=AuditEventType.IDENTIFY_FAILED,
        metadata__reason="rate_limited",
    )
    assert invalid_credentials_event.metadata["ip_address"] == "10.0.0.1"
    assert throttled_event.actor is None
    assert throttled_event.metadata["attempted_username"] == user.username
    assert throttled_event.metadata["ip_address"] == "10.0.0.1"


@pytest.mark.django_db
def test_workstation_lock_requires_csrf() -> None:
    user = get_user_model().objects.create_user(
        username="csrf-lock-user",
        password="admin-pass-123",
    )
    client = APIClient(enforce_csrf_checks=True)
    client.force_login(user)

    response = client.post(
        "/api/v1/auth/workstation-lock/",
        {},
        format="json",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_workstation_lock_requires_authenticated_session() -> None:
    client, token = csrf_client()

    response = post_json(
        client,
        "/api/v1/auth/workstation-lock/",
        {},
        csrf_token=token,
    )

    assert response.status_code == 403
    assert response.json()["code"] == "not_authenticated"


@pytest.mark.django_db
@override_settings(
    REST_FRAMEWORK={
        **base_settings.REST_FRAMEWORK,
        "DEFAULT_THROTTLE_RATES": {
            "workstation_identify": "5/minute",
            "workstation_lock": "1/minute",
            "signature_reauth": "5/minute",
        },
    }
)
def test_workstation_lock_is_rate_limited_and_audited() -> None:
    user = get_user_model().objects.create_user(
        username="lock-throttle-user",
        password="admin-pass-123",
    )
    forwarded_for = "10.0.0.1, 192.168.1.1"

    client, token = csrf_client(user=user)
    first_response = client.post(
        "/api/v1/auth/workstation-lock/",
        {},
        format="json",
        HTTP_X_CSRFTOKEN=token,
        HTTP_X_FORWARDED_FOR=forwarded_for,
    )

    client.force_login(user)
    second_response = client.post(
        "/api/v1/auth/workstation-lock/",
        {},
        format="json",
        HTTP_X_CSRFTOKEN=token,
        HTTP_X_FORWARDED_FOR=forwarded_for,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 429

    locked_event = AuditEvent.objects.get(
        event_type=AuditEventType.LOCK_WORKSTATION,
        metadata__outcome="locked",
    )
    throttled_event = AuditEvent.objects.get(
        event_type=AuditEventType.LOCK_FAILED,
        metadata__reason="rate_limited",
    )
    assert locked_event.actor == user
    assert locked_event.metadata["ip_address"] == "10.0.0.1"
    assert throttled_event.actor == user
    assert throttled_event.metadata == {
        "reason": "rate_limited",
        "ip_address": "10.0.0.1",
    }


@pytest.mark.django_db
def test_workstation_identify_same_user_emits_identify_not_switch() -> None:
    user = get_user_model().objects.create_user(
        username="alice.operator",
        password="admin-pass-123",
        first_name="Alice",
        last_name="Operator",
    )
    user.set_workstation_pin("2468")
    user.save(update_fields=["workstation_pin"])

    client, token = csrf_client(user=user)
    response = post_json(
        client,
        "/api/v1/auth/workstation-identify/",
        {"username": user.username, "pin": "2468"},
        csrf_token=token,
    )

    assert response.status_code == 200
    assert response.json()["event"] == "identify"
    assert response.json()["previous_user"] is None

    assert AuditEvent.objects.filter(event_type=AuditEventType.IDENTIFY).exists()
    assert not AuditEvent.objects.filter(event_type=AuditEventType.SWITCH_USER).exists()


@pytest.mark.django_db
def test_workstation_identify_rolls_back_session_when_audit_write_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = get_user_model().objects.create_user(
        username="rollback-user",
        password="admin-pass-123",
    )
    user.set_workstation_pin("2468")
    user.save(update_fields=["workstation_pin"])

    def fail_record_audit_event(*args: object, **kwargs: object) -> None:
        raise RuntimeError("audit unavailable")

    monkeypatch.setattr(
        "apps.authz.domain.workstation.record_audit_event",
        fail_record_audit_event,
    )

    client, token = csrf_client()
    client.raise_request_exception = False
    response = post_json(
        client,
        "/api/v1/auth/workstation-identify/",
        {"username": user.username, "pin": "2468"},
        csrf_token=token,
    )

    assert response.status_code == 500

    context_response = client.get("/api/v1/auth/context/")
    assert context_response.status_code == 403
    assert context_response.json()["code"] == "not_authenticated"
    assert not AuditEvent.objects.filter(event_type=AuditEventType.IDENTIFY).exists()


@pytest.mark.django_db
def test_workstation_lock_still_logs_out_when_audit_write_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = get_user_model().objects.create_user(
        username="lock-rollback-user",
        password="admin-pass-123",
    )

    def fail_record_audit_event(*args: object, **kwargs: object) -> None:
        raise RuntimeError("audit unavailable")

    monkeypatch.setattr(
        "apps.authz.domain.workstation.record_audit_event",
        fail_record_audit_event,
    )

    client, token = csrf_client(user=user)
    client.raise_request_exception = False
    response = post_json(
        client,
        "/api/v1/auth/workstation-lock/",
        {},
        csrf_token=token,
    )

    assert response.status_code == 500

    context_response = client.get("/api/v1/auth/context/")
    assert context_response.status_code == 403
    assert context_response.json()["code"] == "not_authenticated"
