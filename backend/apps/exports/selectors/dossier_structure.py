"""Read-model queries for resolved dossier structures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from apps.exports.models import (
    BatchDossierStructure,
    DossierElement,
)


@dataclass(frozen=True)
class DossierElementReadModel:
    id: int
    element_identifier: str
    element_type: str
    display_order: int
    applicability: str
    title: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class DossierStructureReadModel:
    id: int
    batch_id: int
    dossier_profile_id: int
    context_snapshot: dict[str, Any]
    is_active: bool
    resolved_at: str
    elements: tuple[DossierElementReadModel, ...]


@dataclass(frozen=True)
class DossierCompletenessItem:
    element_identifier: str
    element_type: str
    title: str
    applicability: str


def get_batch_dossier_structure(batch_id: int) -> DossierStructureReadModel | None:
    """Return the active resolved dossier structure for a batch, or None."""
    structure = (
        BatchDossierStructure.objects.filter(batch_id=batch_id, is_active=True)
        .select_related("dossier_profile")
        .prefetch_related("elements")
        .first()
    )
    if structure is None:
        return None

    return _to_read_model(structure)


def get_dossier_completeness_checklist(
    batch_id: int,
) -> tuple[DossierCompletenessItem, ...] | None:
    """Return a completeness checklist derived from the resolved structure.

    Returns None if no active structure exists for the batch.
    """
    structure = (
        BatchDossierStructure.objects.filter(batch_id=batch_id, is_active=True)
        .prefetch_related("elements")
        .first()
    )
    if structure is None:
        return None

    return tuple(
        DossierCompletenessItem(
            element_identifier=el.element_identifier,
            element_type=el.element_type,
            title=el.title,
            applicability=el.applicability,
        )
        for el in structure.elements.all()
    )


def has_resolved_dossier(batch_id: int) -> bool:
    """Check whether a batch already has an active resolved dossier structure."""
    return BatchDossierStructure.objects.filter(
        batch_id=batch_id, is_active=True
    ).exists()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _to_read_model(structure: BatchDossierStructure) -> DossierStructureReadModel:
    elements: list[DossierElement] = list(structure.elements.all())
    return DossierStructureReadModel(
        id=structure.pk,
        batch_id=structure.batch_id,
        dossier_profile_id=structure.dossier_profile_id,
        context_snapshot=structure.context_snapshot,
        is_active=structure.is_active,
        resolved_at=structure.resolved_at.isoformat(),
        elements=tuple(
            DossierElementReadModel(
                id=el.pk,
                element_identifier=el.element_identifier,
                element_type=el.element_type,
                display_order=el.display_order,
                applicability=el.applicability,
                title=el.title,
                metadata=el.metadata,
            )
            for el in elements
        ),
    )
