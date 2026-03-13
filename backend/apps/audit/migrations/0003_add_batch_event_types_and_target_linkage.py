# Generated manually — additive migration for Story 4.1
# Adds batch-domain event types to AuditEventType choices,
# target_type/target_id fields, and composite indexes.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0002_alter_auditevent_actor_alter_auditevent_site"),
    ]

    operations = [
        # Expand event_type choices (no DB-level change for CharField)
        migrations.AlterField(
            model_name="auditevent",
            name="event_type",
            field=models.CharField(
                choices=[
                    ("identify", "Identify"),
                    ("switch_user", "Switch User"),
                    ("lock_workstation", "Lock Workstation"),
                    ("identify_failed", "Identify Failed"),
                    ("signature_reauth_succeeded", "Signature Reauth Succeeded"),
                    ("signature_reauth_failed", "Signature Reauth Failed"),
                    ("batch_created", "Batch Created"),
                    ("step_draft_saved", "Step Draft Saved"),
                    ("step_completed", "Step Completed"),
                    ("step_signed", "Step Signed"),
                    (
                        "batch_submitted_for_pre_qa",
                        "Batch Submitted for Pre-QA",
                    ),
                    ("pre_qa_review_confirmed", "Pre-QA Review Confirmed"),
                    ("quality_review_started", "Quality Review Started"),
                    ("batch_released", "Batch Released"),
                    ("batch_rejected", "Batch Rejected"),
                    (
                        "batch_returned_for_correction",
                        "Batch Returned for Correction",
                    ),
                    ("correction_submitted", "Correction Submitted"),
                    ("change_reviewed", "Change Reviewed"),
                ],
                max_length=64,
            ),
        ),
        # Add target linkage fields
        migrations.AddField(
            model_name="auditevent",
            name="target_type",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="auditevent",
            name="target_id",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        # Composite index for batch-scoped queries
        migrations.AddIndex(
            model_name="auditevent",
            index=models.Index(
                fields=["target_type", "target_id"],
                name="audit_target_type_id_idx",
            ),
        ),
        # Actor history index
        migrations.AddIndex(
            model_name="auditevent",
            index=models.Index(
                fields=["actor", "occurred_at"],
                name="audit_actor_occurred_idx",
            ),
        ),
    ]
