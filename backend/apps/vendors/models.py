"""Vendor models: Vendor, VendorContact, PurchaseOrder."""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Vendor(models.Model):
    """Vendor/supplier from whom assets and licenses are procured."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        BLACKLISTED = "blacklisted", "Blacklisted"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=30, unique=True, help_text="Short vendor code, e.g. DELL, MSFT")
    website = models.URLField(blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    description = models.TextField(blank=True, default="")

    # Address
    address_line_1 = models.CharField(max_length=255, blank=True, default="")
    address_line_2 = models.CharField(max_length=255, blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    state = models.CharField(max_length=100, blank=True, default="")
    postal_code = models.CharField(max_length=20, blank=True, default="")
    country = models.CharField(max_length=100, blank=True, default="")

    # Primary contact
    primary_contact_name = models.CharField(max_length=200, blank=True, default="")
    primary_contact_email = models.EmailField(blank=True, default="")
    primary_contact_phone = models.CharField(max_length=30, blank=True, default="")

    # Financial
    payment_terms = models.CharField(max_length=100, blank=True, default="", help_text="e.g. Net 30, Net 60")
    tax_id = models.CharField(max_length=50, blank=True, default="")
    account_number = models.CharField(max_length=100, blank=True, default="")

    notes = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_vendors",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def total_purchase_orders(self):
        return self.purchase_orders.count()

    @property
    def total_spent(self):
        total = self.purchase_orders.filter(
            status=PurchaseOrder.Status.RECEIVED,
        ).aggregate(total=models.Sum("total_amount"))["total"]
        return total or 0


class VendorContact(models.Model):
    """Additional contacts for a vendor."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name="contacts",
    )
    name = models.CharField(max_length=200)
    title = models.CharField(max_length=150, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    is_primary = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_primary", "name"]

    def __str__(self):
        return f"{self.name} ({self.vendor.code})"


class PurchaseOrder(models.Model):
    """Purchase orders placed with vendors."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        APPROVED = "approved", "Approved"
        ORDERED = "ordered", "Ordered"
        PARTIALLY_RECEIVED = "partially_received", "Partially Received"
        RECEIVED = "received", "Received"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    po_number = models.CharField(max_length=100, unique=True)
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.PROTECT,
        related_name="purchase_orders",
    )
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.DRAFT)
    description = models.TextField(blank=True, default="")

    order_date = models.DateField(null=True, blank=True)
    expected_delivery_date = models.DateField(null=True, blank=True)
    received_date = models.DateField(null=True, blank=True)

    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    notes = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_purchase_orders",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_purchase_orders",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["po_number"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"PO-{self.po_number} ({self.vendor.code})"

    def calculate_total(self):
        """Recalculate total from line items."""
        line_total = self.line_items.aggregate(
            total=models.Sum("line_total"),
        )["total"] or 0
        self.subtotal = line_total
        self.total_amount = self.subtotal + self.tax_amount + self.shipping_cost
        self.save(update_fields=["subtotal", "total_amount", "updated_at"])


class PurchaseOrderLineItem(models.Model):
    """Individual line items within a purchase order."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name="line_items",
    )
    description = models.CharField(max_length=500)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    received_quantity = models.PositiveIntegerField(default=0)
    asset = models.ForeignKey(
        "assets.Asset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="purchase_line_items",
        help_text="Link to asset created from this line item",
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.description} x{self.quantity}"

    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)
