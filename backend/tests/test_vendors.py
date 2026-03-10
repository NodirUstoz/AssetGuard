"""Tests for the vendors app -- models, views, and purchase order workflow."""
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.accounts.models import User
from apps.vendors.models import PurchaseOrder, PurchaseOrderLineItem, Vendor, VendorContact


class VendorModelTest(TestCase):
    """Unit tests for Vendor model."""

    def test_create_vendor(self):
        vendor = Vendor.objects.create(
            name="Dell Technologies",
            code="DELL",
            website="https://dell.com",
            primary_contact_name="Sales Team",
            primary_contact_email="sales@dell.com",
        )
        self.assertEqual(str(vendor), "DELL - Dell Technologies")
        self.assertEqual(vendor.status, Vendor.Status.ACTIVE)
        self.assertEqual(vendor.total_purchase_orders, 0)

    def test_unique_code(self):
        Vendor.objects.create(name="Vendor A", code="VENA")
        with self.assertRaises(Exception):
            Vendor.objects.create(name="Vendor B", code="VENA")


class VendorContactModelTest(TestCase):
    """Unit tests for VendorContact model."""

    def setUp(self):
        self.vendor = Vendor.objects.create(name="Microsoft", code="MSFT")

    def test_create_contact(self):
        contact = VendorContact.objects.create(
            vendor=self.vendor,
            name="Account Manager",
            email="am@microsoft.com",
            is_primary=True,
        )
        self.assertEqual(str(contact), "Account Manager (MSFT)")
        self.assertTrue(contact.is_primary)


class PurchaseOrderModelTest(TestCase):
    """Unit tests for PurchaseOrder model."""

    def setUp(self):
        self.vendor = Vendor.objects.create(name="HP Inc", code="HP")
        self.user = User.objects.create_user(
            username="pomgr",
            email="po@test.com",
            password="testpass1234",
            role=User.Role.MANAGER,
        )

    def test_create_purchase_order(self):
        po = PurchaseOrder.objects.create(
            po_number="PO-2024-001",
            vendor=self.vendor,
            created_by=self.user,
            order_date=timezone.now().date(),
        )
        self.assertEqual(str(po), "PO-PO-2024-001 (HP)")
        self.assertEqual(po.status, PurchaseOrder.Status.DRAFT)

    def test_line_items_and_total(self):
        po = PurchaseOrder.objects.create(
            po_number="PO-2024-002",
            vendor=self.vendor,
            created_by=self.user,
        )
        PurchaseOrderLineItem.objects.create(
            purchase_order=po,
            description="Laptop Model X",
            quantity=5,
            unit_price=Decimal("1200.00"),
        )
        PurchaseOrderLineItem.objects.create(
            purchase_order=po,
            description="Monitor 27 inch",
            quantity=5,
            unit_price=Decimal("400.00"),
        )
        po.calculate_total()
        po.refresh_from_db()

        self.assertEqual(po.subtotal, Decimal("8000.00"))
        self.assertEqual(po.total_amount, Decimal("8000.00"))

    def test_line_item_auto_total(self):
        po = PurchaseOrder.objects.create(
            po_number="PO-2024-003",
            vendor=self.vendor,
            created_by=self.user,
        )
        item = PurchaseOrderLineItem.objects.create(
            purchase_order=po,
            description="Keyboard",
            quantity=10,
            unit_price=Decimal("75.00"),
        )
        self.assertEqual(item.line_total, Decimal("750.00"))


class VendorAPITest(APITestCase):
    """Integration tests for Vendor API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="vendoradmin",
            email="vendoradmin@test.com",
            password="testpass1234",
            role=User.Role.ADMIN,
            first_name="Vendor",
            last_name="Admin",
        )
        self.client.force_authenticate(user=self.admin)

    def test_list_vendors(self):
        Vendor.objects.create(name="V1", code="V1")
        Vendor.objects.create(name="V2", code="V2")

        response = self.client.get("/api/vendors/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_create_vendor(self):
        data = {
            "name": "Lenovo",
            "code": "LEN",
            "website": "https://lenovo.com",
            "primary_contact_email": "sales@lenovo.com",
        }
        response = self.client.post("/api/vendors/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Vendor.objects.count(), 1)

    def test_create_purchase_order(self):
        vendor = Vendor.objects.create(name="Cisco", code="CSCO")
        data = {
            "po_number": "PO-TEST-001",
            "vendor": str(vendor.id),
            "description": "Network equipment order",
        }
        response = self.client.post("/api/vendors/purchase-orders/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_approve_purchase_order(self):
        vendor = Vendor.objects.create(name="Dell", code="DELLT")
        po = PurchaseOrder.objects.create(
            po_number="PO-APR-001",
            vendor=vendor,
            status=PurchaseOrder.Status.SUBMITTED,
            created_by=self.admin,
        )
        response = self.client.post(f"/api/vendors/purchase-orders/{po.id}/approve/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        po.refresh_from_db()
        self.assertEqual(po.status, PurchaseOrder.Status.APPROVED)
        self.assertEqual(po.approved_by, self.admin)
