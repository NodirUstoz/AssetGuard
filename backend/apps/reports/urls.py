"""URL configuration for reports app."""
from django.urls import path

from .views import (
    AssetExportCSVView,
    AssetSummaryReportView,
    AssignmentReportView,
    DashboardView,
    LicenseComplianceReportView,
    MaintenanceCostReportView,
    WarrantyReportView,
)

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("asset-summary/", AssetSummaryReportView.as_view(), name="report-asset-summary"),
    path("assignments/", AssignmentReportView.as_view(), name="report-assignments"),
    path("maintenance-costs/", MaintenanceCostReportView.as_view(), name="report-maintenance-costs"),
    path("license-compliance/", LicenseComplianceReportView.as_view(), name="report-license-compliance"),
    path("warranties/", WarrantyReportView.as_view(), name="report-warranties"),
    path("export/assets-csv/", AssetExportCSVView.as_view(), name="export-assets-csv"),
]
