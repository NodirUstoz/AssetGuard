"""Maintenance models: MaintenanceSchedule, MaintenanceLog, Warranty."""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class MaintenanceSchedule(models.Model):
    """Scheduled maintenance events for assets."""

    class Frequency(models.TextChoices):
        ONE_TIME = "one_time", "One Time"
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"
        QUARTERLY = "quarterly", "Quarterly"
        SEMI_ANNUAL = "semi_annual", "Semi-Annual"
        ANNUAL = "annual", "Annual"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        OVERDUE = "overdue", "Overdue"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(
        "assets.Asset",
        on_delete=models.CASCADE,
        related_name="maintenance_schedules",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    frequency = models.CharField(max_length=20, choices=Frequency.choices, default=Frequency.ONE_TIME)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)

    scheduled_date = models.DateField()
    scheduled_end_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)

    assigned_to = models.CharField(max_length=200, blank=True, default="")
    vendor = models.CharField(max_length=200, blank=True, default="")
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    actual_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    notes = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_maintenance_schedules",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["scheduled_date"]
        indexes = [
            models.Index(fields=["scheduled_date", "status"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.asset.asset_tag} ({self.scheduled_date})"

    @property
    def is_overdue(self):
        if self.status in (self.Status.COMPLETED, self.Status.CANCELLED):
            return False
        return self.scheduled_date < timezone.now().date()


class MaintenanceLog(models.Model):
    """Log entries for maintenance work performed."""

    class WorkType(models.TextChoices):
        PREVENTIVE = "preventive", "Preventive"
        CORRECTIVE = "corrective", "Corrective"
        INSPECTION = "inspection", "Inspection"
        UPGRADE = "upgrade", "Upgrade"
        REPAIR = "repair", "Repair"
        REPLACEMENT = "replacement", "Replacement"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    schedule = models.ForeignKey(
        MaintenanceSchedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logs",
    )
    asset = models.ForeignKey(
        "assets.Asset",
        on_delete=models.CASCADE,
        related_name="maintenance_logs",
    )
    work_type = models.CharField(max_length=20, choices=WorkType.choices)
    title = models.CharField(max_length=255)
    description = models.TextField()
    work_performed = models.TextField(blank=True, default="")

    performed_by = models.CharField(max_length=200)
    performed_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    parts_used = models.TextField(blank=True, default="")
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Condition before/after
    condition_before = models.CharField(
        max_length=20,
        choices=[
            ("new", "New"), ("good", "Good"), ("fair", "Fair"),
            ("poor", "Poor"), ("broken", "Broken"),
        ],
        blank=True,
        default="",
    )
    condition_after = models.CharField(
        max_length=20,
        choices=[
            ("new", "New"), ("good", "Good"), ("fair", "Fair"),
            ("poor", "Poor"), ("broken", "Broken"),
        ],
        blank=True,
        default="",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_maintenance_logs",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-performed_date"]

    def __str__(self):
        return f"{self.title} - {self.asset.asset_tag} ({self.performed_date})"


class Warranty(models.Model):
    """Warranty information for assets."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        EXPIRED = "expired", "Expired"
        VOIDED = "voided", "Voided"
        CLAIMED = "claimed", "Claimed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(
        "assets.Asset",
        on_delete=models.CASCADE,
        related_name="warranties",
    )
    provider = models.CharField(max_length=200)
    warranty_number = models.CharField(max_length=100, blank=True, default="")
    warranty_type = models.CharField(max_length=100, blank=True, default="", help_text="e.g., Standard, Extended, On-Site")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    start_date = models.DateField()
    end_date = models.DateField()

    coverage_details = models.TextField(blank=True, default="")
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    contact_phone = models.CharField(max_length=20, blank=True, default="")
    contact_email = models.EmailField(blank=True, default="")
    claim_url = models.URLField(blank=True, default="")

    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-end_date"]
        verbose_name_plural = "warranties"

    def __str__(self):
        return f"Warranty: {self.asset.asset_tag} - {self.provider} (until {self.end_date})"

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE and self.end_date >= timezone.now().date()

    @property
    def days_remaining(self):
        if self.end_date < timezone.now().date():
            return 0
        return (self.end_date - timezone.now().date()).days
