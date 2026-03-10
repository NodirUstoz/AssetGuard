"""Tests for the depreciation app -- calculation services and models."""
from datetime import date
from decimal import Decimal

from django.test import TestCase

from apps.assets.models import Asset, AssetCategory, AssetType
from apps.depreciation.models import DepreciationEntry, DepreciationSchedule
from apps.depreciation.services import (
    calculate_declining_balance_monthly,
    calculate_double_declining_monthly,
    calculate_straight_line_monthly,
    generate_depreciation_entry,
    generate_full_depreciation_schedule,
)


class DepreciationCalculationTest(TestCase):
    """Unit tests for depreciation calculation functions."""

    def setUp(self):
        category = AssetCategory.objects.create(name="Equipment")
        asset_type = AssetType.objects.create(name="Server", category=category)
        self.asset = Asset.objects.create(
            asset_tag="DEP-001",
            name="Test Server",
            asset_type=asset_type,
            purchase_cost=Decimal("12000.00"),
        )
        self.schedule = DepreciationSchedule.objects.create(
            asset=self.asset,
            method=DepreciationSchedule.Method.STRAIGHT_LINE,
            useful_life_months=60,
            original_cost=Decimal("12000.00"),
            salvage_value=Decimal("2000.00"),
            start_date=date(2024, 1, 1),
        )

    def test_straight_line_monthly(self):
        monthly = calculate_straight_line_monthly(self.schedule)
        # (12000 - 2000) / 60 = 166.67
        self.assertEqual(monthly, Decimal("166.67"))

    def test_declining_balance_monthly(self):
        schedule = DepreciationSchedule(
            asset=self.asset,
            method=DepreciationSchedule.Method.DECLINING_BALANCE,
            useful_life_months=60,
            original_cost=Decimal("12000.00"),
            salvage_value=Decimal("2000.00"),
            depreciation_rate=Decimal("0.2000"),
        )
        monthly = calculate_declining_balance_monthly(
            schedule, Decimal("12000.00"),
        )
        # 12000 * 0.20 / 12 = 200.00
        self.assertEqual(monthly, Decimal("200.00"))

    def test_double_declining_monthly(self):
        schedule = DepreciationSchedule(
            asset=self.asset,
            method=DepreciationSchedule.Method.DOUBLE_DECLINING,
            useful_life_months=60,
            original_cost=Decimal("12000.00"),
            salvage_value=Decimal("2000.00"),
        )
        monthly = calculate_double_declining_monthly(
            schedule, Decimal("12000.00"),
        )
        # Annual rate = 2 / (60/12) = 0.4 ; 12000 * 0.4 / 12 = 400.00
        self.assertEqual(monthly, Decimal("400.00"))

    def test_straight_line_zero_life(self):
        schedule = DepreciationSchedule(
            asset=self.asset,
            method=DepreciationSchedule.Method.STRAIGHT_LINE,
            useful_life_months=0,
            original_cost=Decimal("1000.00"),
            salvage_value=Decimal("0.00"),
        )
        monthly = calculate_straight_line_monthly(schedule)
        self.assertEqual(monthly, Decimal("0.00"))

    def test_does_not_depreciate_below_salvage(self):
        schedule = DepreciationSchedule(
            asset=self.asset,
            method=DepreciationSchedule.Method.DECLINING_BALANCE,
            useful_life_months=60,
            original_cost=Decimal("12000.00"),
            salvage_value=Decimal("2000.00"),
            depreciation_rate=Decimal("0.5000"),
        )
        # With book value very close to salvage
        monthly = calculate_declining_balance_monthly(
            schedule, Decimal("2100.00"),
        )
        # Should cap at 2100 - 2000 = 100
        self.assertEqual(monthly, Decimal("100.00"))


class DepreciationEntryGenerationTest(TestCase):
    """Tests for generating depreciation entries."""

    def setUp(self):
        category = AssetCategory.objects.create(name="Equipment")
        asset_type = AssetType.objects.create(name="Switch", category=category)
        self.asset = Asset.objects.create(
            asset_tag="DEP-002",
            name="Network Switch",
            asset_type=asset_type,
            purchase_cost=Decimal("3600.00"),
        )
        self.schedule = DepreciationSchedule.objects.create(
            asset=self.asset,
            method=DepreciationSchedule.Method.STRAIGHT_LINE,
            useful_life_months=36,
            original_cost=Decimal("3600.00"),
            salvage_value=Decimal("0.00"),
            start_date=date(2024, 1, 1),
        )

    def test_generate_entry(self):
        entry = generate_depreciation_entry(self.schedule, date(2024, 1, 1))
        self.assertIsNotNone(entry)
        self.assertEqual(entry.amount, Decimal("100.00"))
        self.assertEqual(entry.book_value_before, Decimal("3600.00"))
        self.assertEqual(entry.book_value_after, Decimal("3500.00"))

    def test_duplicate_entry_returns_none(self):
        generate_depreciation_entry(self.schedule, date(2024, 1, 1))
        duplicate = generate_depreciation_entry(self.schedule, date(2024, 1, 1))
        self.assertIsNone(duplicate)

    def test_entry_before_start_date(self):
        entry = generate_depreciation_entry(self.schedule, date(2023, 12, 1))
        self.assertIsNone(entry)

    def test_generate_full_schedule(self):
        projected = generate_full_depreciation_schedule(self.schedule)
        self.assertEqual(len(projected), 36)
        # First entry
        self.assertEqual(projected[0]["amount"], "100.00")
        self.assertEqual(projected[0]["book_value_after"], "3500.00")
        # Last entry
        self.assertEqual(projected[-1]["book_value_after"], "0.00")


class DepreciationScheduleModelTest(TestCase):
    """Unit tests for DepreciationSchedule model properties."""

    def setUp(self):
        category = AssetCategory.objects.create(name="Infra")
        asset_type = AssetType.objects.create(name="Router", category=category)
        self.asset = Asset.objects.create(
            asset_tag="DEP-003",
            name="Core Router",
            asset_type=asset_type,
        )

    def test_depreciable_amount(self):
        schedule = DepreciationSchedule.objects.create(
            asset=self.asset,
            method=DepreciationSchedule.Method.STRAIGHT_LINE,
            useful_life_months=48,
            original_cost=Decimal("10000.00"),
            salvage_value=Decimal("1000.00"),
            start_date=date(2024, 1, 1),
        )
        self.assertEqual(schedule.depreciable_amount, Decimal("9000.00"))

    def test_fully_depreciated(self):
        schedule = DepreciationSchedule.objects.create(
            asset=self.asset,
            method=DepreciationSchedule.Method.STRAIGHT_LINE,
            useful_life_months=2,
            original_cost=Decimal("200.00"),
            salvage_value=Decimal("0.00"),
            start_date=date(2024, 1, 1),
        )
        generate_depreciation_entry(schedule, date(2024, 1, 1))
        generate_depreciation_entry(schedule, date(2024, 2, 1))
        schedule.refresh_from_db()
        self.assertTrue(schedule.is_fully_depreciated)
        self.assertEqual(schedule.current_book_value, Decimal("0.00"))
