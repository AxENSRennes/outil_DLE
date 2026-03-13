from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.audit.models import AuditEventType
from apps.audit.selectors import (
    get_audit_events_by_actor,
    get_audit_events_for_batch_context,
    get_audit_events_for_target,
)
from apps.audit.services import record_audit_event

User = get_user_model()


@pytest.fixture
def batch_actor() -> Any:
    return User.objects.create_user(username="batch-actor", password="pass-123")


@pytest.mark.django_db
def test_get_audit_events_for_target_returns_matching_events(batch_actor: Any) -> None:
    record_audit_event(
        AuditEventType.BATCH_CREATED, actor=batch_actor, target_type="batch", target_id=1
    )
    record_audit_event(
        AuditEventType.STEP_COMPLETED, actor=batch_actor, target_type="batch_step", target_id=10
    )
    record_audit_event(
        AuditEventType.STEP_DRAFT_SAVED, actor=batch_actor, target_type="batch_step", target_id=10
    )

    result = list(get_audit_events_for_target("batch_step", 10))
    assert len(result) == 2
    assert all(e.target_type == "batch_step" and e.target_id == 10 for e in result)


@pytest.mark.django_db
def test_get_audit_events_for_target_chronological_order(batch_actor: Any) -> None:
    e1 = record_audit_event(
        AuditEventType.STEP_DRAFT_SAVED, actor=batch_actor, target_type="batch_step", target_id=5
    )
    e2 = record_audit_event(
        AuditEventType.STEP_COMPLETED, actor=batch_actor, target_type="batch_step", target_id=5
    )

    result = list(get_audit_events_for_target("batch_step", 5))
    assert result == [e1, e2]


@pytest.mark.django_db
def test_get_audit_events_for_target_empty_when_no_match(batch_actor: Any) -> None:
    record_audit_event(
        AuditEventType.BATCH_CREATED, actor=batch_actor, target_type="batch", target_id=1
    )
    assert get_audit_events_for_target("batch", 999).count() == 0


@pytest.mark.django_db
def test_get_audit_events_for_batch_context_includes_batch_and_step_events(
    batch_actor: Any,
) -> None:
    # Direct batch-level event
    record_audit_event(
        AuditEventType.BATCH_CREATED, actor=batch_actor, target_type="batch", target_id=1
    )
    # Step-level event that carries batch_id in metadata
    record_audit_event(
        AuditEventType.STEP_DRAFT_SAVED,
        actor=batch_actor,
        target_type="batch_step",
        target_id=10,
        metadata={"batch_id": 1, "field_count": 3},
    )
    # Unrelated batch
    record_audit_event(
        AuditEventType.BATCH_CREATED, actor=batch_actor, target_type="batch", target_id=2
    )

    result = list(get_audit_events_for_batch_context(1))
    assert len(result) == 2
    event_types = {e.event_type for e in result}
    assert event_types == {"batch_created", "step_draft_saved"}


@pytest.mark.django_db
def test_get_audit_events_for_batch_context_empty() -> None:
    assert get_audit_events_for_batch_context(999).count() == 0


@pytest.mark.django_db
def test_get_audit_events_by_actor_returns_actor_events() -> None:
    user = User.objects.create_user(username="actor-user", password="pass-123")
    record_audit_event(AuditEventType.IDENTIFY, actor=user)
    record_audit_event(
        AuditEventType.BATCH_CREATED,
        actor=user,
        target_type="batch",
        target_id=1,
    )
    # Event by another user
    other = User.objects.create_user(username="other-user", password="pass-123")
    record_audit_event(AuditEventType.IDENTIFY, actor=other)

    result = list(get_audit_events_by_actor(user.pk))
    assert len(result) == 2
    assert all(e.actor_id == user.pk for e in result)


@pytest.mark.django_db
def test_get_audit_events_by_actor_with_since_filter() -> None:
    user = User.objects.create_user(username="since-user", password="pass-123")
    record_audit_event(AuditEventType.IDENTIFY, actor=user)

    future = timezone.now() + timedelta(hours=1)
    result = list(get_audit_events_by_actor(user.pk, since=future))
    assert len(result) == 0

    past = timezone.now() - timedelta(hours=1)
    result = list(get_audit_events_by_actor(user.pk, since=past))
    assert len(result) == 1


@pytest.mark.django_db
def test_get_audit_events_by_actor_empty() -> None:
    assert get_audit_events_by_actor(99999).count() == 0
