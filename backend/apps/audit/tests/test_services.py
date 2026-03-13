from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.db.models import ProtectedError

from apps.audit.models import AuditEvent, AuditEventType
from apps.audit.services import record_audit_event
from apps.sites.models import Site


@pytest.mark.django_db
def test_record_audit_event_strips_sensitive_metadata_keys() -> None:
    user = get_user_model().objects.create_user(username="audit-user", password="test-pass-123")

    event = record_audit_event(
        AuditEventType.IDENTIFY_FAILED,
        actor=user,
        metadata={
            "reason": "invalid_credentials",
            "attempted_username": "audit-user",
            "pin": "2468",
            "nested": {
                "password": "secret",
                "kept": "value",
            },
        },
    )

    assert event.metadata == {
        "reason": "invalid_credentials",
        "attempted_username": "audit-user",
        "nested": {
            "kept": "value",
        },
    }


@pytest.mark.django_db
def test_record_audit_event_strips_broader_secret_metadata_keys() -> None:
    event = record_audit_event(
        AuditEventType.SIGNATURE_REAUTH_FAILED,
        metadata={
            "token": "secret-token",
            "authorization": "Bearer abc",
            "nested": {
                "api_key": "api-key",
                "private_key": "private-key",
                "kept": "value",
            },
            "list": [
                {"refresh_token": "refresh-token", "kept": "list-value"},
            ],
        },
    )

    assert event.metadata == {
        "nested": {
            "kept": "value",
        },
        "list": [
            {"kept": "list-value"},
        ],
    }


@pytest.mark.django_db
def test_record_audit_event_rejects_invalid_event_type() -> None:
    with pytest.raises(ValueError, match="not_a_real_audit_event"):
        record_audit_event("not_a_real_audit_event")  # type: ignore[arg-type]

    assert AuditEvent.objects.count() == 0


@pytest.mark.django_db
def test_deleting_user_with_audit_events_raises_protected_error() -> None:
    user = get_user_model().objects.create_user(username="protected-user", password="test-pass-123")
    record_audit_event(AuditEventType.IDENTIFY, actor=user)

    with pytest.raises(ProtectedError):
        user.delete()


@pytest.mark.django_db
def test_deleting_site_with_audit_events_raises_protected_error() -> None:
    site = Site.objects.create(code="protected-site", name="Protected Site")
    record_audit_event(AuditEventType.LOCK_WORKSTATION, site=site)

    with pytest.raises(ProtectedError):
        site.delete()


@pytest.mark.django_db
def test_record_audit_event_accepts_lock_failed_event_type() -> None:
    event = record_audit_event(
        AuditEventType.LOCK_FAILED,
        metadata={"reason": "rate_limited"},
    )

    assert event.event_type == AuditEventType.LOCK_FAILED
    assert event.metadata == {"reason": "rate_limited"}
