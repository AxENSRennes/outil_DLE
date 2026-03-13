from __future__ import annotations

import factory
from django.contrib.auth import get_user_model

from apps.batches.models import Batch, BatchStatus, BatchStep, StepStatus
from apps.sites.models import Site

_UserModel = get_user_model()


class SiteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Site

    code = factory.Sequence(lambda n: f"site-{n:03d}")
    name = factory.LazyAttribute(lambda obj: f"Site {obj.code}")


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = _UserModel

    username = factory.Sequence(lambda n: f"user-{n:04d}")
    password = factory.django.Password("test-pass-123")


class BatchFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Batch

    reference = factory.Sequence(lambda n: f"LOT-{n:06d}")
    status = BatchStatus.IN_PROGRESS
    site = factory.SubFactory(SiteFactory)


class BatchStepFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BatchStep

    batch = factory.SubFactory(BatchFactory)
    order = factory.Sequence(lambda n: n + 1)
    reference = factory.LazyAttribute(lambda obj: f"Step {obj.order}")
    status = StepStatus.IN_PROGRESS
