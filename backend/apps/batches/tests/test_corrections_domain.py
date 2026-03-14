from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model

from apps.audit.models import AuditEvent, AuditEventType
from apps.batches.domain.corrections import submit_correction
from apps.batches.models import Batch, BatchStep, StepStatus
from apps.batches.tests.factories import BatchFactory
from apps.sites.models import Site

_UserModel = get_user_model()


@pytest.fixture()
def site(db: None) -> Site:
    return Site.objects.create(code="factory-1", name="Factory 1")


@pytest.fixture()
def actor(db: None) -> Any:
    return _UserModel.objects.create_user(username="operator", password="test-pass-123")


@pytest.fixture()
def batch(site: Site) -> Batch:
    return BatchFactory(site=site)  # type: ignore[return-value]


def _make_step(batch: Batch, status: str, data: dict[str, Any] | None = None) -> BatchStep:
    return BatchStep.objects.create(
        batch=batch,
        order=1,
        reference="Step 1 - Mixing",
        status=status,
        data_json=data or {},
    )


@pytest.mark.django_db
class TestSubmitCorrectionHappyPath:
    def test_correction_on_in_progress_step_succeeds(self, batch: Batch, actor: Any) -> None:
        step = _make_step(batch, StepStatus.IN_PROGRESS, {"temperature": "22.5"})

        event = submit_correction(
            step=step,
            actor=actor,
            corrections=[{"field_name": "temperature", "new_value": "23.1"}],
            reason_for_change="Transcription error",
        )

        assert isinstance(event, AuditEvent)
        assert event.event_type == AuditEventType.CORRECTION_SUBMITTED
        step.refresh_from_db()
        assert step.data_json["temperature"] == "23.1"

    def test_correction_on_complete_step_succeeds(self, batch: Batch, actor: Any) -> None:
        step = _make_step(batch, StepStatus.COMPLETE, {"pressure": "1.013"})

        event = submit_correction(
            step=step,
            actor=actor,
            corrections=[{"field_name": "pressure", "new_value": "1.015"}],
            reason_for_change="Measurement correction",
        )

        assert isinstance(event, AuditEvent)
        step.refresh_from_db()
        assert step.data_json["pressure"] == "1.015"

    def test_correction_on_signed_step_succeeds(self, batch: Batch, actor: Any) -> None:
        step = _make_step(batch, StepStatus.SIGNED, {"weight": "100"})

        event = submit_correction(
            step=step,
            actor=actor,
            corrections=[{"field_name": "weight", "new_value": "101"}],
            reason_for_change="Post-signature correction",
        )

        assert isinstance(event, AuditEvent)
        step.refresh_from_db()
        assert step.data_json["weight"] == "101"

    def test_old_value_captured_in_audit_metadata(self, batch: Batch, actor: Any) -> None:
        step = _make_step(batch, StepStatus.IN_PROGRESS, {"temperature": "22.5"})

        event = submit_correction(
            step=step,
            actor=actor,
            corrections=[{"field_name": "temperature", "new_value": "23.1"}],
            reason_for_change="Transcription error",
        )

        corrections = event.metadata["corrections"]
        assert len(corrections) == 1
        assert corrections[0]["old_value"] == "22.5"
        assert corrections[0]["new_value"] == "23.1"
        assert corrections[0]["field_name"] == "temperature"

    def test_correcting_non_existent_field_captures_null_as_old_value(
        self, batch: Batch, actor: Any
    ) -> None:
        step = _make_step(batch, StepStatus.IN_PROGRESS, {})

        event = submit_correction(
            step=step,
            actor=actor,
            corrections=[{"field_name": "new_field", "new_value": "value"}],
            reason_for_change="Adding missing field",
        )

        corrections = event.metadata["corrections"]
        assert corrections[0]["old_value"] is None
        step.refresh_from_db()
        assert step.data_json["new_field"] == "value"

    def test_multiple_field_corrections_applied_atomically(self, batch: Batch, actor: Any) -> None:
        step = _make_step(
            batch,
            StepStatus.IN_PROGRESS,
            {"temperature": "22.5", "pressure": "1.013"},
        )

        event = submit_correction(
            step=step,
            actor=actor,
            corrections=[
                {"field_name": "temperature", "new_value": "23.1"},
                {"field_name": "pressure", "new_value": "1.015"},
            ],
            reason_for_change="Transcription error on both readings",
        )

        step.refresh_from_db()
        assert step.data_json["temperature"] == "23.1"
        assert step.data_json["pressure"] == "1.015"
        assert len(event.metadata["corrections"]) == 2

    def test_audit_event_has_correct_target_fields(self, batch: Batch, actor: Any) -> None:
        step = _make_step(batch, StepStatus.IN_PROGRESS, {"temperature": "22.5"})

        event = submit_correction(
            step=step,
            actor=actor,
            corrections=[{"field_name": "temperature", "new_value": "23.1"}],
            reason_for_change="Fix",
        )

        assert event.target_type == "batch_step"
        assert event.target_id == step.pk

    def test_audit_event_metadata_contains_required_keys(self, batch: Batch, actor: Any) -> None:
        step = _make_step(batch, StepStatus.IN_PROGRESS, {"temperature": "22.5"})

        event = submit_correction(
            step=step,
            actor=actor,
            corrections=[{"field_name": "temperature", "new_value": "23.1"}],
            reason_for_change="Fix reading",
            ip_address="192.168.1.1",
        )

        assert "batch_id" in event.metadata
        assert event.metadata["batch_id"] == batch.pk
        assert "reason_for_change" in event.metadata
        assert event.metadata["reason_for_change"] == "Fix reading"
        assert "corrections" in event.metadata
        assert "ip_address" in event.metadata
        assert event.metadata["ip_address"] == "192.168.1.1"

    def test_audit_event_site_matches_batch_site(self, batch: Batch, actor: Any) -> None:
        step = _make_step(batch, StepStatus.IN_PROGRESS, {"temperature": "22.5"})

        event = submit_correction(
            step=step,
            actor=actor,
            corrections=[{"field_name": "temperature", "new_value": "23.1"}],
            reason_for_change="Fix",
        )

        assert event.site == batch.site

    def test_audit_event_actor_matches_provided_actor(self, batch: Batch, actor: Any) -> None:
        step = _make_step(batch, StepStatus.IN_PROGRESS, {"temperature": "22.5"})

        event = submit_correction(
            step=step,
            actor=actor,
            corrections=[{"field_name": "temperature", "new_value": "23.1"}],
            reason_for_change="Fix",
        )

        assert event.actor == actor

    def test_ip_address_stored_as_none_when_not_provided(self, batch: Batch, actor: Any) -> None:
        step = _make_step(batch, StepStatus.IN_PROGRESS, {"temperature": "22.5"})

        event = submit_correction(
            step=step,
            actor=actor,
            corrections=[{"field_name": "temperature", "new_value": "23.1"}],
            reason_for_change="Fix",
        )

        assert event.metadata["ip_address"] is None

    def test_stale_step_instance_does_not_overwrite_newer_db_state(
        self, batch: Batch, actor: Any
    ) -> None:
        step = _make_step(batch, StepStatus.IN_PROGRESS, {"temperature": "22.5"})
        stale_step = BatchStep.objects.get(pk=step.pk)

        BatchStep.objects.filter(pk=step.pk).update(
            data_json={"temperature": "22.5", "pressure": "1.013"}
        )

        submit_correction(
            step=stale_step,
            actor=actor,
            corrections=[{"field_name": "temperature", "new_value": "23.1"}],
            reason_for_change="Fix",
        )

        step.refresh_from_db()
        assert step.data_json == {"temperature": "23.1", "pressure": "1.013"}


@pytest.mark.django_db
class TestSubmitCorrectionValidation:
    def test_correction_on_not_started_step_raises_value_error(
        self, batch: Batch, actor: Any
    ) -> None:
        step = _make_step(batch, StepStatus.NOT_STARTED)

        with pytest.raises(ValueError, match="not correctable"):
            submit_correction(
                step=step,
                actor=actor,
                corrections=[{"field_name": "temperature", "new_value": "23.1"}],
                reason_for_change="Fix",
            )

    def test_empty_reason_for_change_raises_value_error(self, batch: Batch, actor: Any) -> None:
        step = _make_step(batch, StepStatus.IN_PROGRESS)

        with pytest.raises(ValueError, match="reason_for_change is required"):
            submit_correction(
                step=step,
                actor=actor,
                corrections=[{"field_name": "temperature", "new_value": "23.1"}],
                reason_for_change="",
            )

    def test_whitespace_only_reason_for_change_raises_value_error(
        self, batch: Batch, actor: Any
    ) -> None:
        step = _make_step(batch, StepStatus.IN_PROGRESS)

        with pytest.raises(ValueError, match="reason_for_change is required"):
            submit_correction(
                step=step,
                actor=actor,
                corrections=[{"field_name": "temperature", "new_value": "23.1"}],
                reason_for_change="   ",
            )

    def test_empty_corrections_list_raises_value_error(self, batch: Batch, actor: Any) -> None:
        step = _make_step(batch, StepStatus.IN_PROGRESS)

        with pytest.raises(ValueError, match="At least one correction"):
            submit_correction(
                step=step,
                actor=actor,
                corrections=[],
                reason_for_change="Fix",
            )

    def test_correction_entry_with_empty_field_name_raises_value_error(
        self, batch: Batch, actor: Any
    ) -> None:
        step = _make_step(batch, StepStatus.IN_PROGRESS)

        with pytest.raises(ValueError, match="non-empty field_name"):
            submit_correction(
                step=step,
                actor=actor,
                corrections=[{"field_name": "", "new_value": "23.1"}],
                reason_for_change="Fix",
            )

    def test_missing_new_value_raises_value_error(self, batch: Batch, actor: Any) -> None:
        step = _make_step(batch, StepStatus.IN_PROGRESS)

        with pytest.raises(ValueError, match="include new_value"):
            submit_correction(
                step=step,
                actor=actor,
                corrections=[{"field_name": "temperature"}],
                reason_for_change="Fix",
            )

    def test_object_new_value_raises_value_error(self, batch: Batch, actor: Any) -> None:
        step = _make_step(batch, StepStatus.IN_PROGRESS)

        with pytest.raises(ValueError, match="string, number, boolean, or null"):
            submit_correction(
                step=step,
                actor=actor,
                corrections=[{"field_name": "temperature", "new_value": {"value": "23.1"}}],
                reason_for_change="Fix",
            )

    def test_array_new_value_raises_value_error(self, batch: Batch, actor: Any) -> None:
        step = _make_step(batch, StepStatus.IN_PROGRESS)

        with pytest.raises(ValueError, match="string, number, boolean, or null"):
            submit_correction(
                step=step,
                actor=actor,
                corrections=[{"field_name": "temperature", "new_value": ["23.1"]}],
                reason_for_change="Fix",
            )

    def test_duplicate_field_name_raises_value_error(self, batch: Batch, actor: Any) -> None:
        step = _make_step(batch, StepStatus.IN_PROGRESS, {"temperature": "22.5"})

        with pytest.raises(ValueError, match="Duplicate field_name 'temperature'"):
            submit_correction(
                step=step,
                actor=actor,
                corrections=[
                    {"field_name": "temperature", "new_value": "23.1"},
                    {"field_name": "temperature", "new_value": "24.0"},
                ],
                reason_for_change="Fix",
            )


@pytest.mark.django_db
class TestSubmitCorrectionAtomicity:
    def test_transaction_atomicity_audit_failure_rolls_back_data(
        self, batch: Batch, actor: Any
    ) -> None:
        step = _make_step(batch, StepStatus.IN_PROGRESS, {"temperature": "22.5"})

        with (
            patch(
                "apps.batches.domain.corrections.record_audit_event",
                side_effect=RuntimeError("Audit write failed"),
            ),
            pytest.raises(RuntimeError, match="Audit write failed"),
        ):
            submit_correction(
                step=step,
                actor=actor,
                corrections=[{"field_name": "temperature", "new_value": "23.1"}],
                reason_for_change="Fix",
            )

        step.refresh_from_db()
        assert step.data_json["temperature"] == "22.5"
