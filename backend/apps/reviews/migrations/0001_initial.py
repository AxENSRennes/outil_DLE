from __future__ import annotations

from typing import ClassVar

from django.db import migrations


class Migration(migrations.Migration):

    initial = True

    dependencies: ClassVar[list[tuple[str, str]]] = []

    operations: ClassVar[list[migrations.operations.base.Operation]] = []
