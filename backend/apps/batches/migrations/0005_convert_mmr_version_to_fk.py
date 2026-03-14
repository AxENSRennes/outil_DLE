"""Convert Batch.mmr_version_id (PositiveIntegerField placeholder) to a proper
ForeignKey to mmr.MMRVersion.

The DB column name stays ``mmr_version_id`` in both cases, so this is a
non-destructive schema change: RenameField is a state-only rename (the column
name doesn't change), and AlterField adds the FK constraint.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("batches", "0004_add_uniq_batch_sequence_order"),
        ("mmr", "0001_initial_mmr_models"),
    ]

    operations = [
        # Step 1: Rename the Django field from "mmr_version_id" to
        # "mmr_version".  Because ForeignKey fields store their DB column as
        # <field_name>_id, the DB column stays "mmr_version_id" — no actual
        # column rename happens.
        migrations.RenameField(
            model_name="batch",
            old_name="mmr_version_id",
            new_name="mmr_version",
        ),
        # Step 2: Alter the field type from PositiveIntegerField to ForeignKey.
        # This adds the FK constraint on the existing column.
        migrations.AlterField(
            model_name="batch",
            name="mmr_version",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="batches",
                to="mmr.mmrversion",
            ),
        ),
    ]
