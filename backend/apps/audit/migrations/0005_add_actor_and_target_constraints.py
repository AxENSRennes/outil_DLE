from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0004_add_target_check_constraint"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="auditevent",
            constraint=models.CheckConstraint(
                check=(
                    models.Q(
                        event_type__in=[
                            "identify",
                            "switch_user",
                            "lock_workstation",
                            "identify_failed",
                            "signature_reauth_succeeded",
                            "signature_reauth_failed",
                        ]
                    )
                    | models.Q(actor__isnull=False)
                ),
                name="audit_batch_event_actor_required",
            ),
        ),
        migrations.AddConstraint(
            model_name="auditevent",
            constraint=models.CheckConstraint(
                check=(
                    models.Q(target_id__isnull=True)
                    | ~models.Q(target_type__regex=r"^\s*$")
                ),
                name="audit_target_type_not_blank_when_linked",
            ),
        ),
    ]
