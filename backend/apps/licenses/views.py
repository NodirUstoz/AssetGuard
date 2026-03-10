"""Views for licenses app."""
import logging

from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.audits.models import AuditLog

from .models import LicenseAssignment, LicenseRenewal, SoftwareLicense
from .serializers import (
    LicenseAssignmentSerializer,
    LicenseRenewalSerializer,
    SoftwareLicenseCreateUpdateSerializer,
    SoftwareLicenseDetailSerializer,
    SoftwareLicenseListSerializer,
)

logger = logging.getLogger(__name__)


class IsManagerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.is_manager


class SoftwareLicenseViewSet(viewsets.ModelViewSet):
    queryset = SoftwareLicense.objects.all()
    permission_classes = [IsManagerOrReadOnly]
    search_fields = ["name", "software_name", "publisher", "vendor", "license_key"]
    ordering_fields = ["software_name", "expiration_date", "purchase_cost", "created_at"]
    filterset_fields = ["status", "license_type", "publisher"]

    def get_serializer_class(self):
        if self.action == "list":
            return SoftwareLicenseListSerializer
        if self.action in ["create", "update", "partial_update"]:
            return SoftwareLicenseCreateUpdateSerializer
        return SoftwareLicenseDetailSerializer

    def perform_create(self, serializer):
        license_obj = serializer.save()
        AuditLog.objects.create(
            action=AuditLog.Action.CREATE,
            entity_type="license",
            entity_id=str(license_obj.id),
            entity_name=str(license_obj),
            user=self.request.user,
            details={"software": license_obj.software_name},
        )

    @action(detail=False, methods=["get"], url_path="expiring-soon")
    def expiring_soon(self, request):
        """Get licenses expiring within the next 30 days."""
        days = int(request.query_params.get("days", 30))
        cutoff = timezone.now().date() + timezone.timedelta(days=days)
        licenses = SoftwareLicense.objects.filter(
            expiration_date__lte=cutoff,
            expiration_date__gte=timezone.now().date(),
            status=SoftwareLicense.Status.ACTIVE,
        ).order_by("expiration_date")
        serializer = SoftwareLicenseListSerializer(licenses, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="compliance-summary")
    def compliance_summary(self, request):
        """Get license compliance summary."""
        total = SoftwareLicense.objects.count()
        active = SoftwareLicense.objects.filter(status=SoftwareLicense.Status.ACTIVE).count()
        expired = SoftwareLicense.objects.filter(status=SoftwareLicense.Status.EXPIRED).count()
        pending = SoftwareLicense.objects.filter(status=SoftwareLicense.Status.PENDING_RENEWAL).count()

        # Over-utilized licenses
        over_utilized = 0
        for lic in SoftwareLicense.objects.filter(status=SoftwareLicense.Status.ACTIVE):
            if lic.license_type != SoftwareLicense.LicenseType.SITE and lic.used_seats > lic.total_seats:
                over_utilized += 1

        return Response({
            "total": total,
            "active": active,
            "expired": expired,
            "pending_renewal": pending,
            "over_utilized": over_utilized,
            "compliance_rate": round((active / total * 100), 1) if total > 0 else 100,
        })


class LicenseAssignmentViewSet(viewsets.ModelViewSet):
    queryset = LicenseAssignment.objects.select_related(
        "license", "employee", "asset", "assigned_by"
    ).all()
    serializer_class = LicenseAssignmentSerializer
    permission_classes = [IsManagerOrReadOnly]
    filterset_fields = ["license", "employee", "asset"]
    search_fields = [
        "license__software_name",
        "employee__first_name", "employee__last_name",
    ]

    @action(detail=True, methods=["post"])
    def unassign(self, request, pk=None):
        """Unassign a license from an employee/asset."""
        assignment = self.get_object()
        if assignment.unassigned_at:
            return Response(
                {"error": "This assignment is already unassigned."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        assignment.unassigned_at = timezone.now()
        assignment.save(update_fields=["unassigned_at"])

        AuditLog.objects.create(
            action=AuditLog.Action.UPDATE,
            entity_type="license_assignment",
            entity_id=str(assignment.id),
            entity_name=str(assignment),
            user=request.user,
            details={"action": "unassigned"},
        )
        return Response(LicenseAssignmentSerializer(assignment).data)


class LicenseRenewalViewSet(viewsets.ModelViewSet):
    queryset = LicenseRenewal.objects.select_related("license", "approved_by").all()
    serializer_class = LicenseRenewalSerializer
    permission_classes = [IsManagerOrReadOnly]
    filterset_fields = ["license", "status"]
    ordering_fields = ["renewal_date", "created_at"]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        """Approve a pending license renewal."""
        renewal = self.get_object()
        if renewal.status != LicenseRenewal.Status.PENDING:
            return Response(
                {"error": "Only pending renewals can be approved."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        renewal.status = LicenseRenewal.Status.APPROVED
        renewal.approved_by = request.user
        renewal.save(update_fields=["status", "approved_by", "updated_at"])
        return Response(LicenseRenewalSerializer(renewal).data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Complete a renewal and apply changes to the license."""
        renewal = self.get_object()
        if renewal.status not in (LicenseRenewal.Status.PENDING, LicenseRenewal.Status.APPROVED):
            return Response(
                {"error": "This renewal cannot be completed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        renewal.apply_renewal()
        return Response(LicenseRenewalSerializer(renewal).data)
