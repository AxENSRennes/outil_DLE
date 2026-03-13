from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.authz.models import SiteRole, SiteRoleAssignment
from apps.batches.models import Batch, BatchStep, BatchStepStatus, StepSignatureState
from apps.sites.models import Site

User = get_user_model()


class Command(BaseCommand):
    help = "Create a realistic demo batch with steps for development and testing."

    def handle(self, *args: Any, **options: Any) -> None:
        site, _ = Site.objects.get_or_create(
            code="CHR", defaults={"name": "Chateau-Renard", "is_active": True}
        )

        operator, created = User.objects.get_or_create(
            username="operator1",
            defaults={"first_name": "Marie", "last_name": "Dupont"},
        )
        if created:
            operator.set_password("demo1234")
            operator.set_workstation_pin("1234")
            operator.save()

        SiteRoleAssignment.objects.get_or_create(
            user=operator,
            site=site,
            role=SiteRole.OPERATOR,
            defaults={"is_active": True},
        )

        reviewer, created = User.objects.get_or_create(
            username="reviewer1",
            defaults={"first_name": "Jean", "last_name": "Martin"},
        )
        if created:
            reviewer.set_password("demo1234")
            reviewer.set_workstation_pin("5678")
            reviewer.save()

        SiteRoleAssignment.objects.get_or_create(
            user=reviewer,
            site=site,
            role=SiteRole.PRODUCTION_REVIEWER,
            defaults={"is_active": True},
        )

        snapshot_path = (
            Path(__file__).resolve().parents[5]
            / "_bmad-output"
            / "implementation-artifacts"
            / "mmr-version-example.json"
        )

        if snapshot_path.exists():
            snapshot_json = json.loads(snapshot_path.read_text())
            self.stdout.write(f"  Loaded snapshot from {snapshot_path}")
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"  mmr-version-example.json not found at {snapshot_path}, using inline."
                )
            )
            snapshot_json = _fallback_snapshot()

        batch, batch_created = Batch.objects.get_or_create(
            batch_number="LOT-2026-001",
            defaults={
                "site": site,
                "status": "in_progress",
                "snapshot_json": snapshot_json,
                "created_by": operator,
                "lot_size_target": 500,
                "batch_context_json": {
                    "line": "PMS",
                    "machine": "PMS",
                    "format": "100mL",
                    "glitter": "without_glitter",
                },
            },
        )

        if not batch_created:
            self.stdout.write(self.style.WARNING("  Batch LOT-2026-001 already exists, skipping."))
            return

        steps_config = snapshot_json.get("steps", {})
        step_order = snapshot_json.get("stepOrder", [])

        ns = BatchStepStatus.NOT_STARTED
        nr = StepSignatureState.NOT_REQUIRED
        statuses = {
            "fabrication_bulk": (BatchStepStatus.COMPLETE, StepSignatureState.SIGNED),
            "weighing": (BatchStepStatus.IN_PROGRESS, StepSignatureState.REQUIRED),
            "line_cleaning_previous_run": (ns, nr),
            "packaging_execution": (ns, StepSignatureState.REQUIRED),
            "finished_product_control": (ns, StepSignatureState.REQUIRED),
            "gencod_control_uni2_uni3": (ns, nr),
            "intermediate_leakage_pms_glitter": (ns, nr),
            "dossier_checklist_pre_qa": (ns, nr),
            "pre_qa_review": (ns, StepSignatureState.REQUIRED),
        }

        not_applicable_keys = {"gencod_control_uni2_uni3"}

        for seq, step_key in enumerate(step_order, start=1):
            step_def = steps_config.get(step_key, {})
            step_status, sig_state = statuses.get(
                step_key, (BatchStepStatus.NOT_STARTED, StepSignatureState.NOT_REQUIRED)
            )
            sig_policy = step_def.get("signaturePolicy", {})
            blocking = step_def.get("blockingPolicy", {})

            if sig_state == StepSignatureState.NOT_REQUIRED and sig_policy.get("required"):
                sig_state = StepSignatureState.REQUIRED

            BatchStep.objects.create(
                batch=batch,
                step_key=step_key,
                title=step_def.get("title", step_key),
                sequence_order=seq,
                status=step_status,
                signature_state=sig_state,
                is_applicable=step_key not in not_applicable_keys,
                blocks_execution_progress=blocking.get("blocksExecutionProgress", False),
                blocks_step_completion=blocking.get("blocksStepCompletion", True),
                blocks_signature=blocking.get("blocksSignature", False),
                blocks_pre_qa_handoff=blocking.get("blocksPreQaHandoff", True),
            )

        step_count = batch.steps.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Created batch LOT-2026-001 with {step_count} steps on site CHR.\n"
                f"  Operator: operator1 (PIN: 1234)\n"
                f"  Reviewer: reviewer1 (PIN: 5678)"
            )
        )


def _fallback_snapshot() -> dict[str, Any]:
    return {
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
                "kind": "manufacturing",
                "instructions": "Saisir les informations bulk.",
                "signaturePolicy": {"required": True, "meaning": "performed_by"},
                "blockingPolicy": {
                    "blocksExecutionProgress": False,
                    "blocksStepCompletion": True,
                    "blocksSignature": True,
                    "blocksPreQaHandoff": True,
                },
                "fields": [],
            },
            "weighing": {
                "key": "weighing",
                "title": "Fichier de pesee",
                "kind": "weighing",
                "instructions": "Renseigner la pesee.",
                "signaturePolicy": {"required": True, "meaning": "performed_by"},
                "blockingPolicy": {
                    "blocksExecutionProgress": False,
                    "blocksStepCompletion": True,
                    "blocksSignature": True,
                    "blocksPreQaHandoff": True,
                },
                "fields": [],
            },
        },
    }
