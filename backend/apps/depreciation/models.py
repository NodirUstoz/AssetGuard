"""Depreciation models: DepreciationSchedule, DepreciationEntry."""
import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone


class DepreciationSchedule(models.Model):
    """Depreciation schedule for an asset."""

    class Method(models.TextChoices):
        STRAIGHT_LINE = "straight_line", "Straight Line"
        DECLINING_BALANCE = "declining_balance", "Declining Balance"
        DOUBLE_DECLINING = "double_declining", "Double Declining Balance"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.OneToOneField(
        "assets.Asset",
        on_delete=models.CASCADE,
        related_name="depreciation_schedule",
    )
    method = models.CharField(
        max_length=20,
        choices=Method.choices,
        default=Method.STRAIGHT_LINE,
    )
    useful_life_months = models.PositiveIntegerField(
        help_text="Useful life of the asset in months",
    )
    original_cost = models.DecimalField(max_digits=12, decimal_places=2)
    salvage_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    depreciation_rate = models.DecimalField(
        max_digits=6, decimal_places=4, default=0,
        help_text="Annual rate for declining balance method (e.g., 0.2000 for 20%)",
    )
    start_date = models.DateField()
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Depreciation: {self.asset.asset_tag} ({self.get_method_display()})"

    @property
    def depreciable_amount(self):
        """Total amount that can be depreciated."""
        return self.original_cost - self.salvage_value

    @property
    def total_depreciated(self):
        """Sum of all depreciation entries."""
        total = self.entries.aggregate(
            total=models.Sum("amount")
        )["total"]
        return total or Decimal("0.00")

    @property
    def current_book_value(self):
        """Current book value of the asset."""
        return max(self.original_cost - self.total_depreciated, self.salvage_value)

    @property
    def remaining_life_months(self):
        """Months remaining in the useful life."""
        elapsed = (timezone.now().date() - self.start_date).days / 30.44
        remaining = self.useful_life_months - elapsed
        return max(0, round(remaining))

    @property
    def is_fully_depreciated(self):
        """Whether the asset has been fully depreciated."""
        return self.current_book_value <= self.salvage_value


class DepreciationEntry(models.Model):
    """Individual monthly depreciation entry."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    schedule = models.ForeignKey(
        DepreciationSchedule,
        on_delete=models.CASCADE,
        related_name="entries",
    )
    period_date = models.DateField(help_text="First day of the depreciation period month")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    book_value_before = models.DecimalField(max_digits=12, decimal_places=2)
    book_value_after = models.DecimalField(max_digits=12, decimal_places=2)
    accumulated_depreciation = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["period_date"]
        unique_together = ["schedule", "period_date"]

    def __str__(self):
        return (
            f"{self.schedule.asset.asset_tag} - "
            f"{self.period_date.strftime('%Y-%m')}: ${self.amount}"
        )
