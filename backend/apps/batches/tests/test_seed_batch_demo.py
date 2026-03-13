from __future__ import annotations

from typing import Any

import pytest
from django.core.management import call_command

from apps.batches.management.commands import seed_batch_demo
from apps.batches.models import Batch, BatchStep

DEMO_SNAPSHOT = {
    "schemaVersion": "v1",
    "templateCode": "CHR-PARFUM-100ML-PILOT",
    "templateName": "Chateau-Renard - Parfum 100mL pilot",
    "product": {
        "productCode": "CHR-PARF-100ML",
        "productName": "Parfum 100mL",
        "family": "Parfum",
        "formatLabel": "100mL",
    },
    "stepOrder": ["fabrication_bulk", "weighing"],
    "steps": {
        "fabrication_bulk": {
            "key": "fabrication_bulk",
            "title": "Dossier de fabrication bulk",
            "signaturePolicy": {"required": True, "meaning": "performed_by"},
            "blockingPolicy": {
                "blocksExecutionProgress": False,
                "blocksStepCompletion": True,
                "blocksSignature": True,
                "blocksPreQaHandoff": True,
            },
        },
        "weighing": {
            "key": "weighing",
            "title": "Fichier de pesee",
            "signaturePolicy": {"required": True, "meaning": "performed_by"},
            "blockingPolicy": {
                "blocksExecutionProgress": False,
                "blocksStepCompletion": True,
                "blocksSignature": True,
                "blocksPreQaHandoff": True,
            },
        },
    },
}


@pytest.mark.django_db
def test_seed_batch_demo_rolls_back_partial_batch_when_step_creation_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(seed_batch_demo.Path, "exists", lambda self: False)
    monkeypatch.setattr(seed_batch_demo, "_fallback_snapshot", lambda: DEMO_SNAPSHOT)

    original_create = BatchStep.objects.create
    create_calls = 0

    def flaky_create(*args: Any, **kwargs: Any) -> BatchStep:
        nonlocal create_calls
        create_calls += 1
        if create_calls == 1:
            raise RuntimeError("simulated step creation failure")
        return original_create(*args, **kwargs)

    monkeypatch.setattr(BatchStep.objects, "create", flaky_create)

    with pytest.raises(RuntimeError, match="simulated step creation failure"):
        call_command("seed_batch_demo")

    assert not Batch.objects.filter(batch_number="LOT-2026-001").exists()
    assert BatchStep.objects.count() == 0

    monkeypatch.setattr(BatchStep.objects, "create", original_create)

    call_command("seed_batch_demo")

    batch = Batch.objects.get(batch_number="LOT-2026-001")
    assert batch.steps.count() == len(DEMO_SNAPSHOT["stepOrder"])
