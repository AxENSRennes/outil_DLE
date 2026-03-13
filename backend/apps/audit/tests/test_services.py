from __future__ import annotations

from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError

from apps.audit.models import AuditEvent, AuditEventType
from apps.audit.services import record_audit_event
from apps.sites.models import Site


@pytest.fixture
def batch_actor() -> Any:
    return get_user_model().objects.create_user(username="batch-actor", password="test-pass-123")


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
def test_record_audit_event_with_target_linkage(batch_actor: Any) -> None:
    event = record_audit_event(
        AuditEventType.BATCH_CREATED,
        actor=batch_actor,
        target_type="batch",
        target_id=42,
        metadata={"mmr_version_id": 1, "batch_number": "B-001"},
    )
    assert event.target_type == "batch"
    assert event.target_id == 42
    assert event.metadata == {"mmr_version_id": 1, "batch_number": "B-001"}


@pytest.mark.django_db
def test_record_audit_event_target_id_without_target_type_raises(batch_actor: Any) -> None:
    with pytest.raises(ValueError, match="target_type is required"):
        record_audit_event(AuditEventType.BATCH_CREATED, actor=batch_actor, target_id=1)
    assert AuditEvent.objects.count() == 0


@pytest.mark.django_db
def test_record_audit_event_target_type_without_target_id_raises(batch_actor: Any) -> None:
    with pytest.raises(ValueError, match="target_id is required"):
        record_audit_event(AuditEventType.BATCH_CREATED, actor=batch_actor, target_type="batch")
    assert AuditEvent.objects.count() == 0


@pytest.mark.django_db
def test_record_audit_event_sanitizes_batch_domain_metadata(batch_actor: Any) -> None:
    event = record_audit_event(
        AuditEventType.STEP_DRAFT_SAVED,
        actor=batch_actor,
        target_type="batch_step",
        target_id=7,
        metadata={
            "batch_id": 1,
            "field_count": 5,
            "password": "should-be-stripped",
        },
    )
    assert "password" not in event.metadata
    assert event.metadata["batch_id"] == 1
    assert event.metadata["field_count"] == 5


@pytest.mark.django_db
def test_record_audit_event_without_target_leaves_defaults() -> None:
    event = record_audit_event(AuditEventType.IDENTIFY)
    assert event.target_type == ""
    assert event.target_id is None


@pytest.mark.django_db
def test_deleting_user_with_audit_events_raises_protected_error() -> None:
    user = get_user_model().objects.create_user(username="protected-user", password="test-pass-123")
    record_audit_event(AuditEventType.IDENTIFY, actor=user)

    with pytest.raises(ProtectedError):
        user.delete()


BATCH_DOMAIN_EVENT_TYPES = [
    (
        "batch_created",
        "batch",
        {"mmr_version_id": 1, "batch_number": "B-001"},
    ),
    (
        "step_draft_saved",
        "batch_step",
        {"batch_id": 1, "field_count": 3},
    ),
    (
        "step_completed",
        "batch_step",
        {"batch_id": 1, "completion_note": "done"},
    ),
    (
        "step_signed",
        "batch_step",
        {"batch_id": 1, "signature_meaning": "executed"},
    ),
    (
        "batch_submitted_for_pre_qa",
        "batch",
        {"step_count": 4, "completed_count": 4},
    ),
    (
        "pre_qa_review_confirmed",
        "batch",
        {"review_note": "ready"},
    ),
    (
        "quality_review_started",
        "batch",
        {"reviewer_note": "started"},
    ),
    (
        "batch_released",
        "batch",
        {"release_note": "approved"},
    ),
    (
        "batch_rejected",
        "batch",
        {"rejection_reason": "missing-data"},
    ),
    (
        "batch_returned_for_correction",
        "batch",
        {"return_note": "fix-step-2"},
    ),
    (
        "correction_submitted",
        "batch_step",
        {"batch_id": 1, "reason_for_change": "typo"},
    ),
    (
        "change_reviewed",
        "batch_step",
        {"batch_id": 1, "reviewer_note": "checked"},
    ),
]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("event_type_value", "target_type", "metadata"),
    BATCH_DOMAIN_EVENT_TYPES,
)
def test_batch_domain_event_type_can_be_recorded(
    event_type_value: str,
    target_type: str,
    metadata: dict[str, Any],
    batch_actor: Any,
) -> None:
    event = record_audit_event(
        AuditEventType(event_type_value),
        actor=batch_actor,
        target_type=target_type,
        target_id=1,
        metadata=metadata,
    )
    assert event.event_type == event_type_value
    assert event.target_type == target_type
    assert event.target_id == 1
    assert event.metadata == metadata
    assert AuditEvent.objects.filter(event_type=event_type_value).exists()


def test_all_batch_domain_event_types_are_valid_enum_members() -> None:
    for event_type_value, _, _ in BATCH_DOMAIN_EVENT_TYPES:
        member = AuditEventType(event_type_value)
        assert member.value == event_type_value


@pytest.mark.django_db
def test_existing_auth_event_types_still_work() -> None:
    """Regression: existing auth-event types remain functional."""
    auth_types = [
        AuditEventType.IDENTIFY,
        AuditEventType.SWITCH_USER,
        AuditEventType.LOCK_WORKSTATION,
        AuditEventType.IDENTIFY_FAILED,
        AuditEventType.SIGNATURE_REAUTH_SUCCEEDED,
        AuditEventType.SIGNATURE_REAUTH_FAILED,
        AuditEventType.LOCK_FAILED,
    ]
    for et in auth_types:
        event = record_audit_event(et)
        assert event.event_type == et.value


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


@pytest.mark.django_db
def test_record_audit_event_batch_domain_without_actor_raises() -> None:
    """Batch-domain events are attributed — actor is mandatory."""
    with pytest.raises(ValueError, match="actor is required for batch-domain"):
        record_audit_event(AuditEventType.BATCH_CREATED)
    assert AuditEvent.objects.count() == 0


@pytest.mark.django_db
def test_record_audit_event_whitespace_only_target_type_rejected(batch_actor: Any) -> None:
    """Whitespace-only target_type is stripped to empty, triggering validation."""
    with pytest.raises(ValueError, match="target_type is required"):
        record_audit_event(
            AuditEventType.BATCH_CREATED,
            actor=batch_actor,
            target_type="   ",
            target_id=1,
        )


@pytest.mark.django_db
def test_audit_event_clean_rejects_mismatched_target_fields() -> None:
    """Model-level clean() validates target_type/target_id consistency."""
    event = AuditEvent(
        event_type=AuditEventType.BATCH_CREATED,
        target_type="batch",
    )
    with pytest.raises(ValidationError):
        event.full_clean()


@pytest.mark.django_db
def test_audit_event_clean_requires_actor_for_batch_domain_events() -> None:
    event = AuditEvent(
        event_type=AuditEventType.BATCH_CREATED,
        target_type="batch",
        target_id=1,
    )

    with pytest.raises(ValidationError, match="actor"):
        event.full_clean()


@pytest.mark.django_db
def test_audit_event_save_normalizes_target_type_whitespace(batch_actor: Any) -> None:
    event = AuditEvent.objects.create(
        event_type=AuditEventType.STEP_COMPLETED,
        actor=batch_actor,
        target_type="  batch_step  ",
        target_id=7,
    )

    assert event.target_type == "batch_step"


@pytest.mark.django_db
def test_audit_event_clean_rejects_whitespace_only_target_type(batch_actor: Any) -> None:
    event = AuditEvent(
        event_type=AuditEventType.STEP_COMPLETED,
        actor=batch_actor,
        target_type="   ",
        target_id=7,
    )

    with pytest.raises(ValidationError, match="target_type"):
        event.full_clean()
