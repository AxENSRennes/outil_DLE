from __future__ import annotations

from typing import Any

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.authz.models import SiteRole, SiteRoleAssignment
from apps.batches.models import Batch, BatchStep, BatchStepStatus, StepSignatureState
from apps.sites.models import Site

User = get_user_model()

StepTriple = tuple[BatchStep, BatchStep, BatchStep]

SNAPSHOT_JSON = {
    "schemaVersion": "v1",
    "templateCode": "CHR-PARFUM-100ML-PILOT",
    "templateName": "Chateau-Renard - Parfum 100mL pilot",
    "product": {
        "productCode": "CHR-PARF-100ML",
        "productName": "Parfum 100mL",
        "family": "Parfum",
        "formatLabel": "100mL",
    },
    "stepOrder": ["fabrication_bulk", "weighing", "packaging_execution"],
    "steps": {
        "fabrication_bulk": {
            "key": "fabrication_bulk",
            "title": "Dossier de fabrication bulk",
            "kind": "manufacturing",
            "instructions": "Saisir et vérifier les informations bulk.",
            "signaturePolicy": {"required": True, "meaning": "performed_by"},
            "fields": [
                {
                    "key": "bulk_density",
                    "type": "decimal",
                    "label": "Densite du jus",
                    "required": True,
                }
            ],
        },
        "weighing": {
            "key": "weighing",
            "title": "Fichier de pesee",
            "kind": "weighing",
            "instructions": "Renseigner la pesee.",
            "signaturePolicy": {"required": True, "meaning": "performed_by"},
            "fields": [
                {
                    "key": "density_from_bulk_record",
                    "type": "decimal",
                    "label": "Densite dossier de fabrication",
                    "required": True,
                }
            ],
        },
        "packaging_execution": {
            "key": "packaging_execution",
            "title": "Execution conditionnement",
            "kind": "packaging",
            "instructions": "Renseigner l'execution sur ligne.",
            "signaturePolicy": {"required": True, "meaning": "performed_by"},
            "fields": [],
        },
    },
}


@pytest.fixture()
def site() -> Site:
    return Site.objects.create(code="CHR", name="Chateau-Renard", is_active=True)


@pytest.fixture()
def other_site() -> Site:
    return Site.objects.create(code="LYN", name="Lyon", is_active=True)


@pytest.fixture()
def operator(site: Site) -> Any:
    user = User.objects.create_user(username="op1", password="test")
    SiteRoleAssignment.objects.create(user=user, site=site, role=SiteRole.OPERATOR, is_active=True)
    return user


@pytest.fixture()
def other_site_operator(other_site: Site) -> Any:
    user = User.objects.create_user(username="op_other", password="test")
    SiteRoleAssignment.objects.create(
        user=user, site=other_site, role=SiteRole.OPERATOR, is_active=True
    )
    return user


@pytest.fixture()
def unassigned_user() -> Any:
    return User.objects.create_user(username="nobody", password="test")


@pytest.fixture()
def batch(site: Site, operator: Any) -> Batch:
    return Batch.objects.create(
        site=site,
        batch_number="LOT-2026-001",
        status="in_progress",
        snapshot_json=SNAPSHOT_JSON,
        created_by=operator,
    )


@pytest.fixture()
def batch_steps(batch: Batch) -> StepTriple:
    step1 = BatchStep.objects.create(
        batch=batch,
        step_key="fabrication_bulk",
        title="Dossier de fabrication bulk",
        sequence_order=1,
        status=BatchStepStatus.COMPLETE,
        signature_state=StepSignatureState.SIGNED,
    )
    step2 = BatchStep.objects.create(
        batch=batch,
        step_key="weighing",
        title="Fichier de pesee",
        sequence_order=2,
        status=BatchStepStatus.IN_PROGRESS,
        signature_state=StepSignatureState.REQUIRED,
    )
    step3 = BatchStep.objects.create(
        batch=batch,
        step_key="packaging_execution",
        title="Execution conditionnement",
        sequence_order=3,
        status=BatchStepStatus.NOT_STARTED,
        signature_state=StepSignatureState.REQUIRED,
    )
    return step1, step2, step3


# ── AC1: Batch Access & Step Presentation ──


@pytest.mark.django_db
def test_authorized_operator_can_access_batch_execution(
    operator: Any, batch: Batch, batch_steps: StepTriple
) -> None:
    """AC1: Authorized operator can access batch execution view."""
    client = APIClient()
    client.force_login(operator)
    response = client.get(f"/api/v1/batches/{batch.id}/execution/")
    assert response.status_code == 200
    data = response.json()
    assert data["batch_number"] == "LOT-2026-001"
    assert data["status"] == "in_progress"
    assert data["product_name"] == "Parfum 100mL"
    assert data["product_code"] == "CHR-PARF-100ML"
    assert data["template_name"] == "Chateau-Renard - Parfum 100mL pilot"
    assert data["template_code"] == "CHR-PARFUM-100ML-PILOT"
    assert data["site"]["code"] == "CHR"
    assert data["site"]["name"] == "Chateau-Renard"
    assert len(data["steps"]) == 3


@pytest.mark.django_db
def test_steps_ordered_by_sequence_order(
    operator: Any, batch: Batch, batch_steps: StepTriple
) -> None:
    """AC1: Steps come from batch record ordered by sequence_order."""
    client = APIClient()
    client.force_login(operator)
    response = client.get(f"/api/v1/batches/{batch.id}/execution/")
    steps = response.json()["steps"]
    assert steps[0]["sequence_order"] == 1
    assert steps[1]["sequence_order"] == 2
    assert steps[2]["sequence_order"] == 3
    assert steps[0]["step_key"] == "fabrication_bulk"
    assert steps[1]["step_key"] == "weighing"
    assert steps[2]["step_key"] == "packaging_execution"


# ── AC2: Execution Status Visibility ──


@pytest.mark.django_db
def test_each_step_shows_visible_status(
    operator: Any, batch: Batch, batch_steps: StepTriple
) -> None:
    """AC2: Each step includes visible status in response."""
    client = APIClient()
    client.force_login(operator)
    response = client.get(f"/api/v1/batches/{batch.id}/execution/")
    steps = response.json()["steps"]
    assert steps[0]["status"] == "complete"
    assert steps[1]["status"] == "in_progress"
    assert steps[2]["status"] == "not_started"


@pytest.mark.django_db
def test_current_step_id_points_to_first_non_completed_applicable_step(
    operator: Any, batch: Batch, batch_steps: StepTriple
) -> None:
    """AC2: current_step_id identifies first non-completed applicable step."""
    client = APIClient()
    client.force_login(operator)
    response = client.get(f"/api/v1/batches/{batch.id}/execution/")
    data = response.json()
    # Step 1 is complete, step 2 is in_progress → current is step 2
    assert data["current_step_id"] == batch_steps[1].id


@pytest.mark.django_db
def test_progress_summary(operator: Any, batch: Batch, batch_steps: StepTriple) -> None:
    """AC2: Progress shows total, completed, and applicable counts."""
    client = APIClient()
    client.force_login(operator)
    response = client.get(f"/api/v1/batches/{batch.id}/execution/")
    progress = response.json()["progress"]
    assert progress["total"] == 3
    assert progress["completed"] == 1  # Only fabrication_bulk is complete
    assert progress["applicable"] == 3  # All steps are applicable


# ── AC3: Step Navigation & Context Loading ──


@pytest.mark.django_db
def test_step_detail_returns_frozen_definition_from_snapshot(
    operator: Any, batch: Batch, batch_steps: StepTriple
) -> None:
    """AC3: Step detail loads definition from batch snapshot JSONB."""
    client = APIClient()
    client.force_login(operator)
    step = batch_steps[1]  # weighing
    response = client.get(f"/api/v1/batches/steps/{step.id}/")
    assert response.status_code == 200
    data = response.json()
    assert data["step_key"] == "weighing"
    assert data["kind"] == "weighing"
    assert data["instructions"] == "Renseigner la pesee."
    assert data["batch_id"] == batch.id
    assert len(data["fields"]) == 1
    assert data["fields"][0]["key"] == "density_from_bulk_record"
    assert data["signature_policy"]["required"] is True
    assert data["signature_policy"]["meaning"] == "performed_by"


@pytest.mark.django_db
def test_step_detail_returns_blocking_policy(
    operator: Any, batch: Batch, batch_steps: StepTriple
) -> None:
    """AC3: Step detail includes blocking policy from model fields."""
    client = APIClient()
    client.force_login(operator)
    step = batch_steps[0]  # fabrication_bulk
    response = client.get(f"/api/v1/batches/steps/{step.id}/")
    data = response.json()
    bp = data["blocking_policy"]
    assert bp["blocks_execution_progress"] is False
    assert bp["blocks_step_completion"] is True
    assert bp["blocks_signature"] is False
    assert bp["blocks_pre_qa_handoff"] is True


@pytest.mark.django_db
def test_step_kind_from_snapshot(operator: Any, batch: Batch, batch_steps: StepTriple) -> None:
    """AC3: Step kind comes from the snapshot, not the model."""
    client = APIClient()
    client.force_login(operator)
    response = client.get(f"/api/v1/batches/{batch.id}/execution/")
    steps = response.json()["steps"]
    assert steps[0]["kind"] == "manufacturing"
    assert steps[1]["kind"] == "weighing"
    assert steps[2]["kind"] == "packaging"


@pytest.mark.django_db
def test_step_requires_signature_from_snapshot(
    operator: Any, batch: Batch, batch_steps: StepTriple
) -> None:
    """AC3: requires_signature comes from snapshot signaturePolicy."""
    client = APIClient()
    client.force_login(operator)
    response = client.get(f"/api/v1/batches/{batch.id}/execution/")
    steps = response.json()["steps"]
    for step in steps:
        assert step["requires_signature"] is True


# ── Security: Authorization & Access Control ──


@pytest.mark.django_db
def test_unauthorized_user_wrong_site_receives_403(
    other_site_operator: Any, batch: Batch, batch_steps: StepTriple
) -> None:
    """Security: User with role on different site gets 403."""
    client = APIClient()
    client.force_login(other_site_operator)
    response = client.get(f"/api/v1/batches/{batch.id}/execution/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_unauthorized_user_no_role_receives_403(
    unassigned_user: Any, batch: Batch, batch_steps: StepTriple
) -> None:
    """Security: User with no role on any site gets 403."""
    client = APIClient()
    client.force_login(unassigned_user)
    response = client.get(f"/api/v1/batches/{batch.id}/execution/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_unauthenticated_user_receives_403(batch: Batch, batch_steps: StepTriple) -> None:
    """Security: Unauthenticated user gets 403."""
    client = APIClient()
    response = client.get(f"/api/v1/batches/{batch.id}/execution/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_nonexistent_batch_returns_404(operator: Any) -> None:
    """Security: Nonexistent batch returns 404."""
    client = APIClient()
    client.force_login(operator)
    response = client.get("/api/v1/batches/99999/execution/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_batch_from_different_site_not_accessible(
    other_site_operator: Any, other_site: Site, batch: Batch, batch_steps: StepTriple
) -> None:
    """Security: Operator cannot access batch from another site."""
    client = APIClient()
    client.force_login(other_site_operator)
    response = client.get(f"/api/v1/batches/{batch.id}/execution/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_step_detail_wrong_site_returns_403(
    other_site_operator: Any, batch: Batch, batch_steps: StepTriple
) -> None:
    """Security: Step detail endpoint also enforces site-scoping."""
    client = APIClient()
    client.force_login(other_site_operator)
    step = batch_steps[0]
    response = client.get(f"/api/v1/batches/steps/{step.id}/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_nonexistent_step_returns_404(operator: Any) -> None:
    """Security: Nonexistent step returns 404."""
    client = APIClient()
    client.force_login(operator)
    response = client.get("/api/v1/batches/steps/99999/")
    assert response.status_code == 404


# ── Edge cases ──


@pytest.mark.django_db
def test_current_step_id_null_when_all_complete(operator: Any, batch: Batch) -> None:
    """Edge: current_step_id is null when all steps are complete."""
    BatchStep.objects.create(
        batch=batch,
        step_key="fabrication_bulk",
        title="Fabrication",
        sequence_order=1,
        status=BatchStepStatus.COMPLETE,
    )
    BatchStep.objects.create(
        batch=batch,
        step_key="weighing",
        title="Pesee",
        sequence_order=2,
        status=BatchStepStatus.SIGNED,
    )
    client = APIClient()
    client.force_login(operator)
    response = client.get(f"/api/v1/batches/{batch.id}/execution/")
    assert response.json()["current_step_id"] is None


@pytest.mark.django_db
def test_non_applicable_step_excluded_from_current_step(operator: Any, batch: Batch) -> None:
    """Edge: Non-applicable step is skipped when computing current_step_id."""
    BatchStep.objects.create(
        batch=batch,
        step_key="fabrication_bulk",
        title="Fabrication",
        sequence_order=1,
        status=BatchStepStatus.NOT_STARTED,
        is_applicable=False,
    )
    step2 = BatchStep.objects.create(
        batch=batch,
        step_key="weighing",
        title="Pesee",
        sequence_order=2,
        status=BatchStepStatus.NOT_STARTED,
        is_applicable=True,
    )
    client = APIClient()
    client.force_login(operator)
    response = client.get(f"/api/v1/batches/{batch.id}/execution/")
    data = response.json()
    assert data["current_step_id"] == step2.id
    # Non-applicable step still appears in list
    assert len(data["steps"]) == 2
    assert data["steps"][0]["is_applicable"] is False
