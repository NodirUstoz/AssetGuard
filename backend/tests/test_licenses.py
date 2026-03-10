"""Tests for the licenses app -- models, views, and business logic."""
import uuid
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.accounts.models import Department, Employee, User
from apps.assets.models import Asset, AssetCategory, AssetType
from apps.licenses.models import LicenseAssignment, LicenseRenewal, SoftwareLicense


class SoftwareLicenseModelTest(TestCase):
    """Unit tests for SoftwareLicense model."""

    def test_create_license(self):
        license_obj = SoftwareLicense.objects.create(
            name="Enterprise License",
            software_name="Microsoft Office 365",
            publisher="Microsoft",
            license_type=SoftwareLicense.LicenseType.PER_SEAT,
            total_seats=50,
            purchase_cost=Decimal("5000.00"),
            annual_cost=Decimal("2500.00"),
        )
        self.assertEqual(str(license_obj), "Microsoft Office 365 - Enterprise License")
        self.assertEqual(license_obj.status, SoftwareLicense.Status.ACTIVE)
        self.assertEqual(license_obj.used_seats, 0)
        self.assertEqual(license_obj.available_seats, 50)

    def test_utilization_percentage(self):
        license_obj = SoftwareLicense.objects.create(
            name="Team License",
            software_name="Slack",
            total_seats=10,
        )
        self.assertEqual(license_obj.utilization_percentage, 0)

    def test_site_license_unlimited_seats(self):
        license_obj = SoftwareLicense.objects.create(
            name="Site License",
            software_name="Internal Tool",
            license_type=SoftwareLicense.LicenseType.SITE,
            total_seats=1,
        )
        self.assertEqual(license_obj.available_seats, float("inf"))

    def test_is_expired(self):
        expired = SoftwareLicense.objects.create(
            name="Old License",
            software_name="Expired Software",
            expiration_date=timezone.now().date() - timedelta(days=30),
        )
        self.assertTrue(expired.is_expired)

        active = SoftwareLicense.objects.create(
            name="Current License",
            software_name="Current Software",
            expiration_date=timezone.now().date() + timedelta(days=30),
        )
        self.assertFalse(active.is_expired)

    def test_days_until_expiration(self):
        license_obj = SoftwareLicense.objects.create(
            name="Soon License",
            software_name="Test",
            expiration_date=timezone.now().date() + timedelta(days=15),
        )
        self.assertEqual(license_obj.days_until_expiration, 15)

    def test_no_expiration_date(self):
        perpetual = SoftwareLicense.objects.create(
            name="Perpetual",
            software_name="Tool",
            license_type=SoftwareLicense.LicenseType.PERPETUAL,
        )
        self.assertFalse(perpetual.is_expired)
        self.assertIsNone(perpetual.days_until_expiration)


class LicenseAssignmentModelTest(TestCase):
    """Unit tests for LicenseAssignment model."""

    def setUp(self):
        self.license = SoftwareLicense.objects.create(
            name="Test License",
            software_name="Test App",
            total_seats=5,
        )
        self.department = Department.objects.create(name="Dev", code="DEV")
        self.employee = Employee.objects.create(
            employee_id="EMP-L01",
            first_name="Test",
            last_name="User",
            email="test@test.com",
            department=self.department,
        )
        self.user = User.objects.create_user(
            username="licmgr",
            email="licmgr@test.com",
            password="testpass1234",
        )

    def test_assign_license(self):
        assignment = LicenseAssignment.objects.create(
            license=self.license,
            employee=self.employee,
            assigned_by=self.user,
        )
        self.assertTrue(assignment.is_active)
        self.assertEqual(self.license.used_seats, 1)
        self.assertEqual(self.license.available_seats, 4)

    def test_unassign_license(self):
        assignment = LicenseAssignment.objects.create(
            license=self.license,
            employee=self.employee,
            assigned_by=self.user,
        )
        assignment.unassigned_at = timezone.now()
        assignment.save()
        self.assertFalse(assignment.is_active)
        self.assertEqual(self.license.used_seats, 0)
        self.assertEqual(self.license.available_seats, 5)


class LicenseRenewalModelTest(TestCase):
    """Unit tests for LicenseRenewal model."""

    def test_apply_renewal(self):
        license_obj = SoftwareLicense.objects.create(
            name="Renew Test",
            software_name="Test",
            total_seats=10,
            expiration_date=timezone.now().date() - timedelta(days=5),
            status=SoftwareLicense.Status.EXPIRED,
        )
        new_expiry = timezone.now().date() + timedelta(days=365)
        renewal = LicenseRenewal.objects.create(
            license=license_obj,
            renewal_date=timezone.now().date(),
            new_expiration_date=new_expiry,
            cost=Decimal("3000.00"),
            new_seat_count=20,
            status=LicenseRenewal.Status.APPROVED,
        )

        renewal.apply_renewal()
        license_obj.refresh_from_db()

        self.assertEqual(license_obj.expiration_date, new_expiry)
        self.assertEqual(license_obj.total_seats, 20)
        self.assertEqual(license_obj.status, SoftwareLicense.Status.ACTIVE)
        self.assertEqual(renewal.status, LicenseRenewal.Status.COMPLETED)


class LicenseAPITest(APITestCase):
    """Integration tests for License API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="licadmin",
            email="licadmin@test.com",
            password="testpass1234",
            role=User.Role.ADMIN,
            first_name="Lic",
            last_name="Admin",
        )
        self.client.force_authenticate(user=self.admin)

    def test_list_licenses(self):
        SoftwareLicense.objects.create(name="L1", software_name="App1")
        SoftwareLicense.objects.create(name="L2", software_name="App2")

        response = self.client.get("/api/licenses/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_create_license(self):
        data = {
            "name": "New License",
            "software_name": "New App",
            "license_type": "per_seat",
            "total_seats": 25,
            "purchase_cost": "1000.00",
            "annual_cost": "500.00",
        }
        response = self.client.post("/api/licenses/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_compliance_summary(self):
        SoftwareLicense.objects.create(name="A", software_name="A", status=SoftwareLicense.Status.ACTIVE)
        SoftwareLicense.objects.create(name="B", software_name="B", status=SoftwareLicense.Status.EXPIRED)

        response = self.client.get("/api/licenses/compliance-summary/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 2)
        self.assertEqual(response.data["active"], 1)
        self.assertEqual(response.data["expired"], 1)

    def test_expiring_soon(self):
        SoftwareLicense.objects.create(
            name="Expiring",
            software_name="Exp",
            expiration_date=timezone.now().date() + timedelta(days=10),
            status=SoftwareLicense.Status.ACTIVE,
        )
        SoftwareLicense.objects.create(
            name="Not Expiring",
            software_name="NotExp",
            expiration_date=timezone.now().date() + timedelta(days=90),
            status=SoftwareLicense.Status.ACTIVE,
        )

        response = self.client.get("/api/licenses/expiring-soon/", {"days": 30})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
