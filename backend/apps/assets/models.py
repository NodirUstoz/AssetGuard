"""Asset models: Asset, AssetCategory, AssetType, AssetStatus tracking, AssetAssignment."""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class AssetCategory(models.Model):
    """Top-level asset category (e.g., Hardware, Software, Furniture)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True, default="")
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subcategories",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "asset categories"

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name


class AssetType(models.Model):
    """Specific asset type within a category (e.g., Laptop, Desktop, Server)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    category = models.ForeignKey(
        AssetCategory,
        on_delete=models.CASCADE,
        related_name="asset_types",
    )
    description = models.TextField(blank=True, default="")
    default_useful_life_months = models.PositiveIntegerField(
        default=36,
        help_text="Default useful life in months for depreciation",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["category__name", "name"]
        unique_together = ["name", "category"]

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class Asset(models.Model):
    """Core asset record representing a single trackable item."""

    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        ASSIGNED = "assigned", "Assigned"
        IN_MAINTENANCE = "in_maintenance", "In Maintenance"
        RETIRED = "retired", "Retired"
        DISPOSED = "disposed", "Disposed"
        LOST = "lost", "Lost"
        DAMAGED = "damaged", "Damaged"

    class Condition(models.TextChoices):
        NEW = "new", "New"
        GOOD = "good", "Good"
        FAIR = "fair", "Fair"
        POOR = "poor", "Poor"
        BROKEN = "broken", "Broken"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset_tag = models.CharField(max_length=50, unique=True, help_text="Unique asset identifier tag")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    asset_type = models.ForeignKey(
        AssetType,
        on_delete=models.PROTECT,
        related_name="assets",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    condition = models.CharField(max_length=20, choices=Condition.choices, default=Condition.NEW)

    # Identification
    serial_number = models.CharField(max_length=200, blank=True, default="")
    model_number = models.CharField(max_length=200, blank=True, default="")
    manufacturer = models.CharField(max_length=200, blank=True, default="")
    barcode = models.CharField(max_length=200, blank=True, default="")

    # Financial
    purchase_date = models.DateField(null=True, blank=True)
    purchase_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    purchase_order_number = models.CharField(max_length=100, blank=True, default="")
    vendor = models.CharField(max_length=200, blank=True, default="")
    salvage_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Location
    location = models.CharField(max_length=300, blank=True, default="")
    building = models.CharField(max_length=100, blank=True, default="")
    floor = models.CharField(max_length=20, blank=True, default="")
    room = models.CharField(max_length=50, blank=True, default="")

    # Network (for IT equipment)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    mac_address = models.CharField(max_length=17, blank=True, default="")
    hostname = models.CharField(max_length=200, blank=True, default="")

    # Metadata
    image = models.ImageField(upload_to="assets/", blank=True, null=True)
    notes = models.TextField(blank=True, default="")
    custom_fields = models.JSONField(default=dict, blank=True)

    # Tracking
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_assets",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["asset_tag"]),
            models.Index(fields=["serial_number"]),
            models.Index(fields=["status"]),
            models.Index(fields=["asset_type"]),
        ]

    def __str__(self):
        return f"{self.asset_tag} - {self.name}"

    @property
    def is_available(self):
        return self.status == self.Status.AVAILABLE

    @property
    def current_assignment(self):
        return self.assignments.filter(returned_at__isnull=True).first()

    @property
    def category_name(self):
        return self.asset_type.category.name if self.asset_type else None

    @property
    def type_name(self):
        return self.asset_type.name if self.asset_type else None

    def check_out(self, employee, checked_out_by, notes=""):
        """Assign the asset to an employee."""
        from utils.exceptions import AssetNotAvailableError

        if not self.is_available:
            raise AssetNotAvailableError()

        assignment = AssetAssignment.objects.create(
            asset=self,
            employee=employee,
            checked_out_by=checked_out_by,
            notes=notes,
        )
        self.status = self.Status.ASSIGNED
        self.save(update_fields=["status", "updated_at"])
        return assignment

    def check_in(self, checked_in_by, condition=None, notes=""):
        """Return the asset from its current assignment."""
        assignment = self.current_assignment
        if assignment:
            assignment.returned_at = timezone.now()
            assignment.checked_in_by = checked_in_by
            assignment.return_notes = notes
            if condition:
                assignment.return_condition = condition
            assignment.save()

        self.status = self.Status.AVAILABLE
        if condition:
            self.condition = condition
        self.save(update_fields=["status", "condition", "updated_at"])
        return assignment


class AssetAssignment(models.Model):
    """Records the check-out and check-in of assets to employees."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    employee = models.ForeignKey(
        "accounts.Employee",
        on_delete=models.CASCADE,
        related_name="asset_assignments",
    )
    checked_out_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="checkouts_performed",
    )
    checked_out_at = models.DateTimeField(auto_now_add=True)
    expected_return_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    # Return info
    returned_at = models.DateTimeField(null=True, blank=True)
    checked_in_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="checkins_performed",
    )
    return_condition = models.CharField(
        max_length=20,
        choices=Asset.Condition.choices,
        blank=True,
        default="",
    )
    return_notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-checked_out_at"]
        indexes = [
            models.Index(fields=["asset", "returned_at"]),
        ]

    def __str__(self):
        status_str = "Active" if self.returned_at is None else "Returned"
        return f"{self.asset.asset_tag} -> {self.employee.full_name} ({status_str})"

    @property
    def is_active(self):
        return self.returned_at is None

    @property
    def is_overdue(self):
        if self.returned_at or not self.expected_return_date:
            return False
        return timezone.now().date() > self.expected_return_date
