"""License models: SoftwareLicense, LicenseAssignment, LicenseRenewal."""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class SoftwareLicense(models.Model):
    """Software license tracking with seat management."""

    class LicenseType(models.TextChoices):
        PER_SEAT = "per_seat", "Per Seat"
        PER_DEVICE = "per_device", "Per Device"
        SITE = "site", "Site License"
        OPEN_SOURCE = "open_source", "Open Source"
        SUBSCRIPTION = "subscription", "Subscription"
        PERPETUAL = "perpetual", "Perpetual"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        EXPIRED = "expired", "Expired"
        PENDING_RENEWAL = "pending_renewal", "Pending Renewal"
        CANCELLED = "cancelled", "Cancelled"
        SUSPENDED = "suspended", "Suspended"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    software_name = models.CharField(max_length=255)
    version = models.CharField(max_length=50, blank=True, default="")
    publisher = models.CharField(max_length=200, blank=True, default="")
    license_key = models.TextField(blank=True, default="", help_text="Encrypted license key or serial")
    license_type = models.CharField(max_length=20, choices=LicenseType.choices, default=LicenseType.PER_SEAT)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    # Seats
    total_seats = models.PositiveIntegerField(default=1)

    # Dates
    purchase_date = models.DateField(null=True, blank=True)
    activation_date = models.DateField(null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)

    # Financial
    purchase_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    annual_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vendor = models.CharField(max_length=200, blank=True, default="")
    purchase_order_number = models.CharField(max_length=100, blank=True, default="")

    # Contact
    vendor_contact_name = models.CharField(max_length=200, blank=True, default="")
    vendor_contact_email = models.EmailField(blank=True, default="")
    support_url = models.URLField(blank=True, default="")

    notes = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_licenses",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["software_name", "name"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["expiration_date"]),
        ]

    def __str__(self):
        return f"{self.software_name} - {self.name}"

    @property
    def used_seats(self):
        return self.assignments.filter(unassigned_at__isnull=True).count()

    @property
    def available_seats(self):
        if self.license_type == self.LicenseType.SITE:
            return float("inf")
        return max(0, self.total_seats - self.used_seats)

    @property
    def is_expired(self):
        if not self.expiration_date:
            return False
        return self.expiration_date < timezone.now().date()

    @property
    def days_until_expiration(self):
        if not self.expiration_date:
            return None
        delta = self.expiration_date - timezone.now().date()
        return delta.days

    @property
    def utilization_percentage(self):
        if self.license_type == self.LicenseType.SITE or self.total_seats == 0:
            return 0
        return round((self.used_seats / self.total_seats) * 100, 1)


class LicenseAssignment(models.Model):
    """Tracks which employee or device a license seat is assigned to."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    license = models.ForeignKey(
        SoftwareLicense,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    employee = models.ForeignKey(
        "accounts.Employee",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="license_assignments",
    )
    asset = models.ForeignKey(
        "assets.Asset",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="license_assignments",
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="license_assignments_made",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    unassigned_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-assigned_at"]

    def __str__(self):
        target = self.employee or self.asset
        return f"{self.license.software_name} -> {target}"

    @property
    def is_active(self):
        return self.unassigned_at is None


class LicenseRenewal(models.Model):
    """Tracks license renewal history and upcoming renewals."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        COMPLETED = "completed", "Completed"
        DECLINED = "declined", "Declined"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    license = models.ForeignKey(
        SoftwareLicense,
        on_delete=models.CASCADE,
        related_name="renewals",
    )
    renewal_date = models.DateField()
    new_expiration_date = models.DateField()
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    new_seat_count = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_renewals",
    )
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-renewal_date"]

    def __str__(self):
        return f"Renewal: {self.license.software_name} - {self.renewal_date}"

    def apply_renewal(self):
        """Apply the renewal to the parent license."""
        if self.status != self.Status.COMPLETED:
            self.status = self.Status.COMPLETED
            self.save(update_fields=["status", "updated_at"])

        self.license.expiration_date = self.new_expiration_date
        self.license.status = SoftwareLicense.Status.ACTIVE
        if self.new_seat_count:
            self.license.total_seats = self.new_seat_count
        self.license.save()
