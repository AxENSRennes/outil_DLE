from __future__ import annotations

import factory
from django.contrib.auth import get_user_model

from apps.batches.models import Batch, BatchStatus, BatchStep, StepStatus
from apps.mmr.models import MMR, MMRVersion
from apps.sites.models import Product, Site

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


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    site = factory.SubFactory(SiteFactory)
    code = factory.Sequence(lambda n: f"PROD-{n:03d}")
    name = factory.LazyAttribute(lambda obj: f"Product {obj.code}")


class MMRFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MMR

    site = factory.SubFactory(SiteFactory)
    product = factory.SubFactory(ProductFactory, site=factory.SelfAttribute("..site"))
    name = factory.Sequence(lambda n: f"MMR-{n:03d}")
    code = factory.Sequence(lambda n: f"MMR-{n:03d}")


class MMRVersionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MMRVersion

    mmr = factory.SubFactory(MMRFactory)
    version_number = factory.Sequence(lambda n: n + 1)
    created_by = factory.SubFactory(UserFactory)


class BatchFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Batch

    batch_number = factory.Sequence(lambda n: f"LOT-{n:06d}")
    status = BatchStatus.IN_PROGRESS
    site = factory.SubFactory(SiteFactory)
    mmr_version = factory.SubFactory(MMRVersionFactory, mmr__site=factory.SelfAttribute("...site"))
    created_by = factory.SubFactory(UserFactory)


class BatchStepFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BatchStep

    batch = factory.SubFactory(BatchFactory)
    order = factory.Sequence(lambda n: n + 1)
    reference = factory.LazyAttribute(lambda obj: f"Step {obj.order}")
    status = StepStatus.IN_PROGRESS
