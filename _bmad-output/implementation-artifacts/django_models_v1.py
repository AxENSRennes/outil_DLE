from django.conf import settings
from django.db import models


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Organization(TimestampedModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Site(TimestampedModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="sites",
    )
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100)
    timezone = models.CharField(max_length=64, default="Europe/Paris")
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code"],
                name="uniq_site_code_per_organization",
            )
        ]

    def __str__(self):
        return f"{self.organization.code} / {self.code}"


class Product(TimestampedModel):
    site = models.ForeignKey(
        Site,
        on_delete=models.PROTECT,
        related_name="products",
    )
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100)
    family = models.CharField(max_length=255, blank=True)
    format_label = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["site", "code"],
                name="uniq_product_code_per_site",
            )
        ]

    def __str__(self):
        return self.name


class MMR(TimestampedModel):
    site = models.ForeignKey(
        Site,
        on_delete=models.PROTECT,
        related_name="mmrs",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="mmrs",
    )
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["site", "code"],
                name="uniq_mmr_code_per_site",
            )
        ]

    def __str__(self):
        return self.name


class MMRVersionStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    RETIRED = "retired", "Retired"


class MMRVersion(TimestampedModel):
    mmr = models.ForeignKey(
        MMR,
        on_delete=models.PROTECT,
        related_name="versions",
    )
    version_number = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20,
        choices=MMRVersionStatus.choices,
        default=MMRVersionStatus.DRAFT,
    )
    schema_json = models.JSONField()
    change_summary = models.TextField(blank=True)
    activated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="activated_mmr_versions",
        null=True,
        blank=True,
    )
    activated_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_mmr_versions",
    )

    class Meta:
        ordering = ["-version_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["mmr", "version_number"],
                name="uniq_mmr_version_number",
            )
        ]

    def __str__(self):
        return f"{self.mmr.code} v{self.version_number}"


class BatchStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    READY = "ready", "Ready"
    IN_EXECUTION = "in_execution", "In execution"
    REVIEW_REQUIRED = "review_required", "Review required"
    UNDER_REVIEW = "under_review", "Under review"
    RELEASED = "released", "Released"
    REJECTED = "rejected", "Rejected"
    ARCHIVED = "archived", "Archived"


class ReviewState(models.TextChoices):
    NONE = "none", "None"
    REQUIRED = "required", "Required"
    IN_REVIEW = "in_review", "In review"
    REVIEWED = "reviewed", "Reviewed"
    CHANGED_SINCE_REVIEW = "changed_since_review", "Changed since review"


class SignatureState(models.TextChoices):
    NONE = "none", "None"
    REQUIRED = "required", "Required"
    PARTIALLY_SIGNED = "partially_signed", "Partially signed"
    SIGNED = "signed", "Signed"
    CHANGED_SINCE_SIGNATURE = "changed_since_signature", "Changed since signature"


class Batch(TimestampedModel):
    site = models.ForeignKey(
        Site,
        on_delete=models.PROTECT,
        related_name="batches",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="batches",
    )
    mmr_version = models.ForeignKey(
        MMRVersion,
        on_delete=models.PROTECT,
        related_name="batches",
    )
    batch_number = models.CharField(max_length=100, unique=True)
    status = models.CharField(
        max_length=32,
        choices=BatchStatus.choices,
        default=BatchStatus.DRAFT,
    )
    review_state = models.CharField(
        max_length=32,
        choices=ReviewState.choices,
        default=ReviewState.NONE,
    )
    signature_state = models.CharField(
        max_length=32,
        choices=SignatureState.choices,
        default=SignatureState.NONE,
    )
    lot_size_target = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    lot_size_actual = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    review_started_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_batches",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assigned_batches",
        null=True,
        blank=True,
    )
    batch_context_json = models.JSONField(default=dict, blank=True)
    snapshot_json = models.JSONField()

    def __str__(self):
        return self.batch_number


class BatchStepStatus(models.TextChoices):
    NOT_STARTED = "not_started", "Not started"
    IN_PROGRESS = "in_progress", "In progress"
    COMPLETED = "completed", "Completed"
    SIGNED = "signed", "Signed"
    FLAGGED = "flagged", "Flagged"
    UNDER_REVIEW = "under_review", "Under review"
    APPROVED = "approved", "Approved"


class StepReviewState(models.TextChoices):
    NONE = "none", "None"
    REQUIRED = "required", "Required"
    IN_REVIEW = "in_review", "In review"
    APPROVED = "approved", "Approved"
    CHANGED = "changed", "Changed"


class StepSignatureState(models.TextChoices):
    NOT_REQUIRED = "not_required", "Not required"
    REQUIRED = "required", "Required"
    SIGNED = "signed", "Signed"
    CHANGED = "changed", "Changed"


class BatchStep(TimestampedModel):
    batch = models.ForeignKey(
        Batch,
        on_delete=models.CASCADE,
        related_name="steps",
    )
    step_key = models.CharField(max_length=100)
    occurrence_key = models.CharField(max_length=100, default="default")
    occurrence_index = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=255)
    sequence_order = models.PositiveIntegerField()
    source_document_code = models.CharField(max_length=100, blank=True)
    is_applicable = models.BooleanField(default=True)
    applicability_basis_json = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=32,
        choices=BatchStepStatus.choices,
        default=BatchStepStatus.NOT_STARTED,
    )
    review_state = models.CharField(
        max_length=32,
        choices=StepReviewState.choices,
        default=StepReviewState.NONE,
    )
    signature_state = models.CharField(
        max_length=32,
        choices=StepSignatureState.choices,
        default=StepSignatureState.NOT_REQUIRED,
    )
    blocks_execution_progress = models.BooleanField(default=False)
    blocks_step_completion = models.BooleanField(default=True)
    blocks_signature = models.BooleanField(default=False)
    blocks_pre_qa_handoff = models.BooleanField(default=True)
    data_json = models.JSONField(default=dict)
    meta_json = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    last_edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="edited_batch_steps",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["sequence_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["batch", "step_key", "occurrence_key"],
                name="uniq_batch_step_occurrence",
            )
        ]

    def __str__(self):
        return f"{self.batch.batch_number} / {self.step_key} / {self.occurrence_key}"


class BatchDocumentStatus(models.TextChoices):
    EXPECTED = "expected", "Expected"
    PRESENT = "present", "Present"
    MISSING = "missing", "Missing"


class BatchDocumentRepeatMode(models.TextChoices):
    SINGLE = "single", "Single"
    PER_SHIFT = "per_shift", "Per shift"
    PER_TEAM = "per_team", "Per team"
    PER_BOX = "per_box", "Per box"
    PER_EVENT = "per_event", "Per event"


class BatchDocumentRequirement(TimestampedModel):
    batch = models.ForeignKey(
        Batch,
        on_delete=models.CASCADE,
        related_name="document_requirements",
    )
    document_code = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    source_step_key = models.CharField(max_length=100, blank=True)
    is_required = models.BooleanField(default=True)
    is_applicable = models.BooleanField(default=True)
    repeat_mode = models.CharField(
        max_length=32,
        choices=BatchDocumentRepeatMode.choices,
        default=BatchDocumentRepeatMode.SINGLE,
    )
    expected_count = models.PositiveIntegerField(default=1)
    actual_count = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=32,
        choices=BatchDocumentStatus.choices,
        default=BatchDocumentStatus.EXPECTED,
    )
    applicability_basis_json = models.JSONField(default=dict, blank=True)
    meta_json = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["batch", "document_code"],
                name="uniq_batch_document_requirement",
            )
        ]

    def __str__(self):
        return f"{self.batch.batch_number} / {self.document_code}"


class SignatureMeaning(models.TextChoices):
    PERFORMED_BY = "performed_by", "Performed by"
    REVIEWED_BY = "reviewed_by", "Reviewed by"
    APPROVED_BY = "approved_by", "Approved by"
    RELEASED_BY = "released_by", "Released by"


class Signature(TimestampedModel):
    batch = models.ForeignKey(
        Batch,
        on_delete=models.CASCADE,
        related_name="signatures",
    )
    batch_step = models.ForeignKey(
        BatchStep,
        on_delete=models.CASCADE,
        related_name="signatures",
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="batch_signatures",
    )
    meaning = models.CharField(max_length=32, choices=SignatureMeaning.choices)
    signed_data_hash = models.CharField(max_length=128)
    signed_snapshot_json = models.JSONField()
    reason = models.TextField(blank=True)
    signed_at = models.DateTimeField()


class ExceptionSeverity(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    CRITICAL = "critical", "Critical"


class ExceptionStatus(models.TextChoices):
    OPEN = "open", "Open"
    INVESTIGATING = "investigating", "Investigating"
    RESOLVED = "resolved", "Resolved"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"


class Exception(TimestampedModel):
    batch = models.ForeignKey(
        Batch,
        on_delete=models.CASCADE,
        related_name="exceptions",
    )
    batch_step = models.ForeignKey(
        BatchStep,
        on_delete=models.CASCADE,
        related_name="exceptions",
        null=True,
        blank=True,
    )
    code = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=100)
    severity = models.CharField(max_length=16, choices=ExceptionSeverity.choices)
    status = models.CharField(
        max_length=16,
        choices=ExceptionStatus.choices,
        default=ExceptionStatus.OPEN,
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    resolution_notes = models.TextField(blank=True)
    raised_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="raised_exceptions",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assigned_exceptions",
        null=True,
        blank=True,
    )
    raised_at = models.DateTimeField()
    resolved_at = models.DateTimeField(null=True, blank=True)


class ReviewAction(models.TextChoices):
    REQUESTED = "requested", "Requested"
    STARTED = "started", "Started"
    APPROVED = "approved", "Approved"
    SENT_BACK = "sent_back", "Sent back"
    COMMENTED = "commented", "Commented"


class ReviewStage(models.TextChoices):
    PRE_QA = "pre_qa", "Pre-QA"
    QA = "qa", "QA"


class ReviewEvent(TimestampedModel):
    batch = models.ForeignKey(
        Batch,
        on_delete=models.CASCADE,
        related_name="review_events",
    )
    batch_step = models.ForeignKey(
        BatchStep,
        on_delete=models.CASCADE,
        related_name="review_events",
        null=True,
        blank=True,
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="review_events",
    )
    stage = models.CharField(max_length=16, choices=ReviewStage.choices)
    action = models.CharField(max_length=32, choices=ReviewAction.choices)
    comment = models.TextField(blank=True)


class ReleaseDecision(models.TextChoices):
    RELEASED = "released", "Released"
    REJECTED = "rejected", "Rejected"


class ReleaseEvent(TimestampedModel):
    batch = models.ForeignKey(
        Batch,
        on_delete=models.CASCADE,
        related_name="release_events",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="release_events",
    )
    decision = models.CharField(max_length=16, choices=ReleaseDecision.choices)
    comment = models.TextField(blank=True)


class AttachmentKind(models.TextChoices):
    PHOTO = "photo", "Photo"
    PDF = "pdf", "PDF"
    EVIDENCE = "evidence", "Evidence"
    OTHER = "other", "Other"


class Attachment(TimestampedModel):
    batch = models.ForeignKey(
        Batch,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    batch_step = models.ForeignKey(
        BatchStep,
        on_delete=models.CASCADE,
        related_name="attachments",
        null=True,
        blank=True,
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploaded_attachments",
    )
    kind = models.CharField(max_length=16, choices=AttachmentKind.choices)
    file = models.FileField(upload_to="batch_attachments/%Y/%m/%d")
    filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100)


class AuditEvent(TimestampedModel):
    entity_type = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=100)
    action = models.CharField(max_length=100)
    actor_id = models.CharField(max_length=100, blank=True)
    actor_name = models.CharField(max_length=255, blank=True)
    context_json = models.JSONField(default=dict, blank=True)
    old_data = models.JSONField(null=True, blank=True)
    new_data = models.JSONField(null=True, blank=True)
    reason = models.TextField(blank=True)
