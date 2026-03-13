from __future__ import annotations

from typing import ClassVar

from django.db import models


class Site(models.Model):
    code = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("code",)

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class Product(models.Model):
    site = models.ForeignKey(Site, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100)
    family = models.CharField(max_length=255, blank=True)
    format_label = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(fields=["site", "code"], name="uniq_product_code_per_site"),
        ]
        ordering = ("code",)

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"
