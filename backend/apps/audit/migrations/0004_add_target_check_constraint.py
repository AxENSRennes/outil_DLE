# Additive migration for code review fix (Story 4.1)
# Adds CHECK constraint enforcing target_type/target_id consistency.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0003_add_batch_event_types_and_target_linkage"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="auditevent",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(target_type="", target_id__isnull=True)
                    | (~models.Q(target_type="") & models.Q(target_id__isnull=False))
                ),
                name="audit_target_type_id_consistent",
            ),
        ),
    ]
