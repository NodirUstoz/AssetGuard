"""Views for reports app."""
import logging

from django.http import HttpResponse
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audits.models import AuditLog

from .services import (
    export_assets_csv,
    generate_asset_summary_report,
    generate_assignment_report,
    generate_license_compliance_report,
    generate_maintenance_cost_report,
    generate_warranty_report,
)

logger = logging.getLogger(__name__)


class IsManagerPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_manager


class DashboardView(APIView):
    """Main dashboard endpoint aggregating key metrics."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from apps.assets.models import Asset, AssetAssignment
        from apps.licenses.models import SoftwareLicense
        from apps.maintenance.models import MaintenanceSchedule
        from django.utils import timezone

        today = timezone.now().date()

        total_assets = Asset.objects.count()
        available_assets = Asset.objects.filter(status=Asset.Status.AVAILABLE).count()
        assigned_assets = Asset.objects.filter(status=Asset.Status.ASSIGNED).count()
        in_maintenance = Asset.objects.filter(status=Asset.Status.IN_MAINTENANCE).count()

        active_assignments = AssetAssignment.objects.filter(
            returned_at__isnull=True,
        ).count()
        overdue_assignments = AssetAssignment.objects.filter(
            returned_at__isnull=True,
            expected_return_date__lt=today,
        ).count()

        active_licenses = SoftwareLicense.objects.filter(
            status=SoftwareLicense.Status.ACTIVE,
        ).count()
        expiring_licenses = SoftwareLicense.objects.filter(
            expiration_date__lte=today + timezone.timedelta(days=30),
            expiration_date__gte=today,
            status=SoftwareLicense.Status.ACTIVE,
        ).count()

        upcoming_maintenance = MaintenanceSchedule.objects.filter(
            scheduled_date__gte=today,
            scheduled_date__lte=today + timezone.timedelta(days=14),
            status=MaintenanceSchedule.Status.SCHEDULED,
        ).count()
        overdue_maintenance = MaintenanceSchedule.objects.filter(
            scheduled_date__lt=today,
            status__in=[
                MaintenanceSchedule.Status.SCHEDULED,
                MaintenanceSchedule.Status.IN_PROGRESS,
            ],
        ).count()

        return Response({
            "assets": {
                "total": total_assets,
                "available": available_assets,
                "assigned": assigned_assets,
                "in_maintenance": in_maintenance,
            },
            "assignments": {
                "active": active_assignments,
                "overdue": overdue_assignments,
            },
            "licenses": {
                "active": active_licenses,
                "expiring_soon": expiring_licenses,
            },
            "maintenance": {
                "upcoming": upcoming_maintenance,
                "overdue": overdue_maintenance,
            },
        })


class AssetSummaryReportView(APIView):
    """Full asset summary report."""

    permission_classes = [IsManagerPermission]

    def get(self, request):
        report = generate_asset_summary_report()

        AuditLog.log(
            action=AuditLog.Action.EXPORT,
            entity_type="report",
            entity_id="asset_summary",
            user=request.user,
            entity_name="Asset Summary Report",
            request=request,
        )
        return Response(report)


class AssignmentReportView(APIView):
    """Asset assignment report with date range filtering."""

    permission_classes = [IsManagerPermission]

    def get(self, request):
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        report = generate_assignment_report(date_from=date_from, date_to=date_to)
        return Response(report)


class MaintenanceCostReportView(APIView):
    """Maintenance cost report optionally filtered by year."""

    permission_classes = [IsManagerPermission]

    def get(self, request):
        year = request.query_params.get("year")
        if year:
            year = int(year)
        report = generate_maintenance_cost_report(year=year)
        return Response(report)


class LicenseComplianceReportView(APIView):
    """License compliance and utilization report."""

    permission_classes = [IsManagerPermission]

    def get(self, request):
        report = generate_license_compliance_report()
        return Response(report)


class WarrantyReportView(APIView):
    """Warranty status report across all assets."""

    permission_classes = [IsManagerPermission]

    def get(self, request):
        report = generate_warranty_report()
        return Response(report)


class AssetExportCSVView(APIView):
    """Export all assets as a downloadable CSV file."""

    permission_classes = [IsManagerPermission]

    def get(self, request):
        csv_file = export_assets_csv()

        AuditLog.log(
            action=AuditLog.Action.EXPORT,
            entity_type="asset",
            entity_id="all",
            user=request.user,
            entity_name="Asset CSV Export",
            request=request,
        )

        response = HttpResponse(csv_file.read(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="assetguard_assets_export.csv"'
        return response
