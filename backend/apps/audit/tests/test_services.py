from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model

from apps.audit.models import AuditEventType
from apps.audit.services import record_audit_event


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
