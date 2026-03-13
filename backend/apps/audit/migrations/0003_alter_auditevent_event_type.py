from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0002_alter_auditevent_actor_alter_auditevent_site"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auditevent",
            name="event_type",
            field=models.CharField(
                choices=[
                    ("identify", "Identify"),
                    ("switch_user", "Switch User"),
                    ("lock_workstation", "Lock Workstation"),
                    ("lock_failed", "Lock Failed"),
                    ("identify_failed", "Identify Failed"),
                    ("signature_reauth_succeeded", "Signature Reauth Succeeded"),
                    ("signature_reauth_failed", "Signature Reauth Failed"),
                ],
                max_length=64,
            ),
        ),
    ]
