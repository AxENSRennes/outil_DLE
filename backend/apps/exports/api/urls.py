from __future__ import annotations

from django.urls import path

from apps.exports.api.views import BatchDossierStructureView, ResolveBatchDossierView

app_name = "exports-api"

urlpatterns = [
    path(
        "batches/<int:batch_id>/dossier-structure/",
        BatchDossierStructureView.as_view(),
        name="batch-dossier-structure",
    ),
    path(
        "batches/<int:batch_id>/resolve-dossier/",
        ResolveBatchDossierView.as_view(),
        name="resolve-batch-dossier",
    ),
]
