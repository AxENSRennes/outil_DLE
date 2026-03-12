from __future__ import annotations

import pytest
from django.db import IntegrityError

from apps.sites.models import Site


@pytest.mark.django_db
def test_site_requires_unique_code() -> None:
    Site.objects.create(code="lyon-qc", name="Lyon Quality Control")

    with pytest.raises(IntegrityError):
        Site.objects.create(code="lyon-qc", name="Lyon Duplicate")
