"""Report generation services for AssetGuard."""
import csv
import io
import logging
from datetime import timedelta
from decimal import Decimal

from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone

from apps.assets.models import Asset, AssetAssignment, AssetCategory
from apps.licenses.models import SoftwareLicense
from apps.maintenance.models import MaintenanceLog, MaintenanceSchedule, Warranty

logger = logging.getLogger(__name__)


def generate_asset_summary_report():
    """Generate a high-level summary of all assets in the system."""
    total_assets = Asset.objects.count()

    status_breakdown = {}
    for status_value, status_label in Asset.Status.choices:
        status_breakdown[status_value] = Asset.objects.filter(status=status_value).count()

    condition_breakdown = {}
    for condition_value, condition_label in Asset.Condition.choices:
        condition_breakdown[condition_value] = Asset.objects.filter(condition=condition_value).count()

    financials = Asset.objects.aggregate(
        total_purchase_cost=Sum("purchase_cost"),
        avg_purchase_cost=Avg("purchase_cost"),
        total_salvage_value=Sum("salvage_value"),
    )

    category_breakdown = []
    for category in AssetCategory.objects.filter(parent__isnull=True, is_active=True):
        count = Asset.objects.filter(asset_type__category=category).count()
        cost = Asset.objects.filter(asset_type__category=category).aggregate(
            total=Sum("purchase_cost"),
        )["total"] or Decimal("0.00")
        category_breakdown.append({
            "category": category.name,
            "count": count,
            "total_cost": str(cost),
        })

    return {
        "generated_at": timezone.now().isoformat(),
        "total_assets": total_assets,
        "status_breakdown": status_breakdown,
        "condition_breakdown": condition_breakdown,
        "financials": {
            "total_purchase_cost": str(financials["total_purchase_cost"] or 0),
            "average_purchase_cost": str(round(financials["avg_purchase_cost"] or 0, 2)),
            "total_salvage_value": str(financials["total_salvage_value"] or 0),
        },
        "by_category": category_breakdown,
    }


def generate_assignment_report(date_from=None, date_to=None):
    """Generate a report on asset assignments within a date range."""
    queryset = AssetAssignment.objects.select_related("asset", "employee")

    if date_from:
        queryset = queryset.filter(checked_out_at__date__gte=date_from)
    if date_to:
        queryset = queryset.filter(checked_out_at__date__lte=date_to)

    total_assignments = queryset.count()
    active_assignments = queryset.filter(returned_at__isnull=True).count()
    returned_assignments = queryset.filter(returned_at__isnull=False).count()
    overdue_assignments = queryset.filter(
        returned_at__isnull=True,
        expected_return_date__lt=timezone.now().date(),
    ).count()

    top_employees = list(
        queryset.values("employee__first_name", "employee__last_name")
        .annotate(assignment_count=Count("id"))
        .order_by("-assignment_count")[:10]
    )

    return {
        "generated_at": timezone.now().isoformat(),
        "date_range": {
            "from": str(date_from) if date_from else None,
            "to": str(date_to) if date_to else None,
        },
        "total_assignments": total_assignments,
        "active_assignments": active_assignments,
        "returned_assignments": returned_assignments,
        "overdue_assignments": overdue_assignments,
        "top_employees": top_employees,
    }


def generate_maintenance_cost_report(year=None):
    """Generate a report on maintenance costs, optionally filtered by year."""
    queryset = MaintenanceLog.objects.all()
    if year:
        queryset = queryset.filter(performed_date__year=year)

    totals = queryset.aggregate(
        total_cost=Sum("cost"),
        total_entries=Count("id"),
        avg_cost=Avg("cost"),
    )

    by_work_type = list(
        queryset.values("work_type")
        .annotate(total_cost=Sum("cost"), count=Count("id"))
        .order_by("-total_cost")
    )

    monthly_costs = list(
        queryset.extra(select={"month": "EXTRACT(MONTH FROM performed_date)"})
        .values("month")
        .annotate(total_cost=Sum("cost"), count=Count("id"))
        .order_by("month")
    )

    top_assets = list(
        queryset.values("asset__asset_tag", "asset__name")
        .annotate(total_cost=Sum("cost"), maintenance_count=Count("id"))
        .order_by("-total_cost")[:10]
    )

    return {
        "generated_at": timezone.now().isoformat(),
        "year": year,
        "total_cost": str(totals["total_cost"] or 0),
        "total_entries": totals["total_entries"],
        "average_cost": str(round(totals["avg_cost"] or 0, 2)),
        "by_work_type": by_work_type,
        "monthly_costs": monthly_costs,
        "top_cost_assets": top_assets,
    }


def generate_license_compliance_report():
    """Generate a license compliance and utilization report."""
    licenses = SoftwareLicense.objects.all()
    total = licenses.count()
    active = licenses.filter(status=SoftwareLicense.Status.ACTIVE).count()
    expired = licenses.filter(status=SoftwareLicense.Status.EXPIRED).count()

    total_annual_cost = licenses.aggregate(total=Sum("annual_cost"))["total"] or Decimal("0.00")
    total_purchase_cost = licenses.aggregate(total=Sum("purchase_cost"))["total"] or Decimal("0.00")

    over_utilized = []
    under_utilized = []
    for lic in licenses.filter(status=SoftwareLicense.Status.ACTIVE):
        utilization = lic.utilization_percentage
        entry = {
            "id": str(lic.id),
            "software_name": lic.software_name,
            "total_seats": lic.total_seats,
            "used_seats": lic.used_seats,
            "utilization": utilization,
        }
        if lic.license_type != SoftwareLicense.LicenseType.SITE:
            if lic.used_seats > lic.total_seats:
                over_utilized.append(entry)
            elif utilization < 25 and lic.total_seats > 1:
                under_utilized.append(entry)

    expiring_30 = licenses.filter(
        expiration_date__lte=timezone.now().date() + timedelta(days=30),
        expiration_date__gte=timezone.now().date(),
        status=SoftwareLicense.Status.ACTIVE,
    ).count()

    return {
        "generated_at": timezone.now().isoformat(),
        "total_licenses": total,
        "active": active,
        "expired": expired,
        "compliance_rate": round((active / total * 100), 1) if total > 0 else 100,
        "total_annual_cost": str(total_annual_cost),
        "total_purchase_cost": str(total_purchase_cost),
        "over_utilized_licenses": over_utilized,
        "under_utilized_licenses": under_utilized,
        "expiring_within_30_days": expiring_30,
    }


def generate_warranty_report():
    """Generate a report on warranty status across all assets."""
    warranties = Warranty.objects.select_related("asset").all()
    total = warranties.count()
    active = warranties.filter(
        status=Warranty.Status.ACTIVE,
        end_date__gte=timezone.now().date(),
    ).count()
    expired = warranties.filter(end_date__lt=timezone.now().date()).count()

    total_cost = warranties.aggregate(total=Sum("cost"))["total"] or Decimal("0.00")

    expiring_soon = list(
        warranties.filter(
            end_date__lte=timezone.now().date() + timedelta(days=60),
            end_date__gte=timezone.now().date(),
            status=Warranty.Status.ACTIVE,
        ).values(
            "asset__asset_tag", "asset__name",
            "provider", "end_date",
        ).order_by("end_date")[:20]
    )

    return {
        "generated_at": timezone.now().isoformat(),
        "total_warranties": total,
        "active_warranties": active,
        "expired_warranties": expired,
        "total_warranty_cost": str(total_cost),
        "expiring_within_60_days": expiring_soon,
    }


def export_assets_csv():
    """Export all assets as a CSV file in-memory."""
    output = io.StringIO()
    writer = csv.writer(output)

    headers = [
        "Asset Tag", "Name", "Category", "Type", "Status", "Condition",
        "Serial Number", "Model Number", "Manufacturer",
        "Purchase Date", "Purchase Cost", "Vendor",
        "Location", "Building", "Floor", "Room",
        "IP Address", "Hostname",
        "Created At",
    ]
    writer.writerow(headers)

    assets = Asset.objects.select_related("asset_type", "asset_type__category").all()
    for asset in assets:
        writer.writerow([
            asset.asset_tag,
            asset.name,
            asset.category_name or "",
            asset.type_name or "",
            asset.get_status_display(),
            asset.get_condition_display(),
            asset.serial_number,
            asset.model_number,
            asset.manufacturer,
            asset.purchase_date.isoformat() if asset.purchase_date else "",
            str(asset.purchase_cost),
            asset.vendor,
            asset.location,
            asset.building,
            asset.floor,
            asset.room,
            asset.ip_address or "",
            asset.hostname,
            asset.created_at.isoformat(),
        ])

    output.seek(0)
    return output
