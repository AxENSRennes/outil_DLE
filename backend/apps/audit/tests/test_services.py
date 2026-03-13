from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.db.models import ProtectedError

from apps.audit.models import AuditEventType
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
