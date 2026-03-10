"""Tests for the assets app -- models, views, and business logic."""
import uuid
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.accounts.models import Department, Employee, User
from apps.assets.models import Asset, AssetAssignment, AssetCategory, AssetType


class AssetCategoryModelTest(TestCase):
    """Unit tests for AssetCategory model."""

    def test_create_category(self):
        category = AssetCategory.objects.create(name="Hardware")
        self.assertEqual(str(category), "Hardware")
        self.assertTrue(category.is_active)

    def test_subcategory_display(self):
        parent = AssetCategory.objects.create(name="Hardware")
        child = AssetCategory.objects.create(name="Laptops", parent=parent)
        self.assertEqual(str(child), "Hardware > Laptops")

    def test_category_uuid_primary_key(self):
        category = AssetCategory.objects.create(name="Software")
        self.assertIsInstance(category.id, uuid.UUID)


class AssetTypeModelTest(TestCase):
    """Unit tests for AssetType model."""

    def setUp(self):
        self.category = AssetCategory.objects.create(name="Hardware")

    def test_create_asset_type(self):
        asset_type = AssetType.objects.create(
            name="Laptop",
            category=self.category,
            default_useful_life_months=48,
        )
        self.assertEqual(str(asset_type), "Hardware - Laptop")
        self.assertEqual(asset_type.default_useful_life_months, 48)

    def test_unique_together_constraint(self):
        AssetType.objects.create(name="Laptop", category=self.category)
        with self.assertRaises(Exception):
            AssetType.objects.create(name="Laptop", category=self.category)


class AssetModelTest(TestCase):
    """Unit tests for Asset model."""

    def setUp(self):
        self.category = AssetCategory.objects.create(name="Hardware")
        self.asset_type = AssetType.objects.create(name="Laptop", category=self.category)
        self.user = User.objects.create_user(
            username="testadmin",
            email="admin@test.com",
            password="testpass1234",
            role=User.Role.ADMIN,
        )
        self.department = Department.objects.create(name="Engineering", code="ENG")
        self.employee = Employee.objects.create(
            employee_id="EMP-001",
            first_name="John",
            last_name="Doe",
            email="john@test.com",
            department=self.department,
        )

    def test_create_asset(self):
        asset = Asset.objects.create(
            asset_tag="AST-0001",
            name="Dell Latitude 7420",
            asset_type=self.asset_type,
            purchase_cost=Decimal("1200.00"),
            created_by=self.user,
        )
        self.assertEqual(str(asset), "AST-0001 - Dell Latitude 7420")
        self.assertEqual(asset.status, Asset.Status.AVAILABLE)
        self.assertTrue(asset.is_available)

    def test_asset_unique_tag(self):
        Asset.objects.create(
            asset_tag="AST-0001",
            name="Laptop 1",
            asset_type=self.asset_type,
        )
        with self.assertRaises(Exception):
            Asset.objects.create(
                asset_tag="AST-0001",
                name="Laptop 2",
                asset_type=self.asset_type,
            )

    def test_check_out(self):
        asset = Asset.objects.create(
            asset_tag="AST-0002",
            name="Test Laptop",
            asset_type=self.asset_type,
        )
        assignment = asset.check_out(
            employee=self.employee,
            checked_out_by=self.user,
            notes="Test assignment",
        )
        asset.refresh_from_db()
        self.assertEqual(asset.status, Asset.Status.ASSIGNED)
        self.assertFalse(asset.is_available)
        self.assertIsNotNone(assignment)
        self.assertEqual(assignment.employee, self.employee)
        self.assertTrue(assignment.is_active)

    def test_check_out_unavailable_raises(self):
        asset = Asset.objects.create(
            asset_tag="AST-0003",
            name="Test Laptop",
            asset_type=self.asset_type,
            status=Asset.Status.ASSIGNED,
        )
        from utils.exceptions import AssetNotAvailableError
        with self.assertRaises(AssetNotAvailableError):
            asset.check_out(employee=self.employee, checked_out_by=self.user)

    def test_check_in(self):
        asset = Asset.objects.create(
            asset_tag="AST-0004",
            name="Test Laptop",
            asset_type=self.asset_type,
        )
        asset.check_out(employee=self.employee, checked_out_by=self.user)
        assignment = asset.check_in(
            checked_in_by=self.user,
            condition=Asset.Condition.GOOD,
            notes="Returned in good condition",
        )
        asset.refresh_from_db()
        self.assertEqual(asset.status, Asset.Status.AVAILABLE)
        self.assertEqual(asset.condition, Asset.Condition.GOOD)
        self.assertIsNotNone(assignment.returned_at)
        self.assertFalse(assignment.is_active)

    def test_category_and_type_names(self):
        asset = Asset.objects.create(
            asset_tag="AST-0005",
            name="Test",
            asset_type=self.asset_type,
        )
        self.assertEqual(asset.category_name, "Hardware")
        self.assertEqual(asset.type_name, "Laptop")

    def test_current_assignment_none_when_available(self):
        asset = Asset.objects.create(
            asset_tag="AST-0006",
            name="Test",
            asset_type=self.asset_type,
        )
        self.assertIsNone(asset.current_assignment)


class AssetAssignmentModelTest(TestCase):
    """Unit tests for AssetAssignment model."""

    def setUp(self):
        category = AssetCategory.objects.create(name="Hardware")
        asset_type = AssetType.objects.create(name="Laptop", category=category)
        self.asset = Asset.objects.create(
            asset_tag="AST-A001",
            name="Test Laptop",
            asset_type=asset_type,
        )
        self.department = Department.objects.create(name="IT", code="IT")
        self.employee = Employee.objects.create(
            employee_id="EMP-A01",
            first_name="Jane",
            last_name="Smith",
            email="jane@test.com",
            department=self.department,
        )
        self.user = User.objects.create_user(
            username="mgr",
            email="mgr@test.com",
            password="testpass1234",
        )

    def test_is_overdue(self):
        assignment = AssetAssignment.objects.create(
            asset=self.asset,
            employee=self.employee,
            checked_out_by=self.user,
            expected_return_date=timezone.now().date() - timezone.timedelta(days=5),
        )
        self.assertTrue(assignment.is_overdue)

    def test_not_overdue_when_returned(self):
        assignment = AssetAssignment.objects.create(
            asset=self.asset,
            employee=self.employee,
            checked_out_by=self.user,
            expected_return_date=timezone.now().date() - timezone.timedelta(days=5),
            returned_at=timezone.now(),
        )
        self.assertFalse(assignment.is_overdue)

    def test_not_overdue_without_return_date(self):
        assignment = AssetAssignment.objects.create(
            asset=self.asset,
            employee=self.employee,
            checked_out_by=self.user,
        )
        self.assertFalse(assignment.is_overdue)


class AssetAPITest(APITestCase):
    """Integration tests for Asset API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username="apiadmin",
            email="apiadmin@test.com",
            password="testpass1234",
            role=User.Role.ADMIN,
            first_name="API",
            last_name="Admin",
        )
        self.client.force_authenticate(user=self.admin_user)

        self.category = AssetCategory.objects.create(name="Hardware")
        self.asset_type = AssetType.objects.create(name="Laptop", category=self.category)

    def test_list_assets(self):
        Asset.objects.create(asset_tag="A001", name="Laptop 1", asset_type=self.asset_type)
        Asset.objects.create(asset_tag="A002", name="Laptop 2", asset_type=self.asset_type)

        response = self.client.get("/api/assets/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_create_asset(self):
        data = {
            "asset_tag": "NEW-001",
            "name": "New Laptop",
            "asset_type": str(self.asset_type.id),
            "purchase_cost": "1500.00",
            "manufacturer": "Dell",
        }
        response = self.client.post("/api/assets/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Asset.objects.count(), 1)
        self.assertEqual(Asset.objects.first().created_by, self.admin_user)

    def test_retrieve_asset_detail(self):
        asset = Asset.objects.create(
            asset_tag="DET-001",
            name="Detail Laptop",
            asset_type=self.asset_type,
            serial_number="SN123456",
        )
        response = self.client.get(f"/api/assets/{asset.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["asset_tag"], "DET-001")
        self.assertEqual(response.data["serial_number"], "SN123456")

    def test_status_summary(self):
        Asset.objects.create(asset_tag="S1", name="A", asset_type=self.asset_type, status=Asset.Status.AVAILABLE)
        Asset.objects.create(asset_tag="S2", name="B", asset_type=self.asset_type, status=Asset.Status.ASSIGNED)
        Asset.objects.create(asset_tag="S3", name="C", asset_type=self.asset_type, status=Asset.Status.AVAILABLE)

        response = self.client.get("/api/assets/status-summary/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 3)
        self.assertEqual(response.data["available"], 2)
        self.assertEqual(response.data["assigned"], 1)

    def test_unauthenticated_access_denied(self):
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/assets/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
