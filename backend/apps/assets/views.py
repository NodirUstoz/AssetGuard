"""Views for assets app."""
import io
import logging

import qrcode
from django.http import HttpResponse
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.models import Employee
from apps.audits.models import AuditLog

from .filters import AssetAssignmentFilter, AssetFilter
from .models import Asset, AssetAssignment, AssetCategory, AssetType
from .serializers import (
    AssetAssignmentSerializer,
    AssetCategorySerializer,
    AssetCreateUpdateSerializer,
    AssetDetailSerializer,
    AssetListSerializer,
    AssetTypeSerializer,
    CheckInSerializer,
    CheckOutSerializer,
)

logger = logging.getLogger(__name__)


class IsManagerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.is_manager


class AssetCategoryViewSet(viewsets.ModelViewSet):
    queryset = AssetCategory.objects.all()
    serializer_class = AssetCategorySerializer
    permission_classes = [IsManagerOrReadOnly]
    search_fields = ["name", "description"]
    filterset_fields = ["is_active", "parent"]


class AssetTypeViewSet(viewsets.ModelViewSet):
    queryset = AssetType.objects.select_related("category").all()
    serializer_class = AssetTypeSerializer
    permission_classes = [IsManagerOrReadOnly]
    search_fields = ["name", "description"]
    filterset_fields = ["category", "is_active"]


class AssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.select_related(
        "asset_type", "asset_type__category", "created_by"
    ).all()
    permission_classes = [IsManagerOrReadOnly]
    filterset_class = AssetFilter
    search_fields = [
        "asset_tag", "name", "serial_number",
        "manufacturer", "model_number", "hostname",
    ]
    ordering_fields = [
        "asset_tag", "name", "status", "purchase_date",
        "purchase_cost", "created_at",
    ]

    def get_serializer_class(self):
        if self.action == "list":
            return AssetListSerializer
        if self.action in ["create", "update", "partial_update"]:
            return AssetCreateUpdateSerializer
        return AssetDetailSerializer

    def perform_create(self, serializer):
        asset = serializer.save()
        AuditLog.objects.create(
            action=AuditLog.Action.CREATE,
            entity_type="asset",
            entity_id=str(asset.id),
            entity_name=str(asset),
            user=self.request.user,
            details={"asset_tag": asset.asset_tag, "name": asset.name},
        )

    def perform_update(self, serializer):
        old_data = AssetDetailSerializer(self.get_object()).data
        asset = serializer.save()
        AuditLog.objects.create(
            action=AuditLog.Action.UPDATE,
            entity_type="asset",
            entity_id=str(asset.id),
            entity_name=str(asset),
            user=self.request.user,
            details={"changes": "Asset updated"},
        )

    def perform_destroy(self, instance):
        AuditLog.objects.create(
            action=AuditLog.Action.DELETE,
            entity_type="asset",
            entity_id=str(instance.id),
            entity_name=str(instance),
            user=self.request.user,
            details={"asset_tag": instance.asset_tag},
        )
        instance.delete()

    @action(detail=True, methods=["post"], url_path="check-out")
    def check_out(self, request, pk=None):
        """Check out an asset to an employee."""
        asset = self.get_object()
        serializer = CheckOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            employee = Employee.objects.get(id=serializer.validated_data["employee"])
        except Employee.DoesNotExist:
            return Response(
                {"error": "Employee not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        assignment = asset.check_out(
            employee=employee,
            checked_out_by=request.user,
            notes=serializer.validated_data.get("notes", ""),
        )

        if serializer.validated_data.get("expected_return_date"):
            assignment.expected_return_date = serializer.validated_data["expected_return_date"]
            assignment.save(update_fields=["expected_return_date"])

        AuditLog.objects.create(
            action=AuditLog.Action.CHECK_OUT,
            entity_type="asset",
            entity_id=str(asset.id),
            entity_name=str(asset),
            user=request.user,
            details={
                "employee": employee.full_name,
                "employee_id": str(employee.id),
            },
        )

        return Response(
            AssetAssignmentSerializer(assignment).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="check-in")
    def check_in(self, request, pk=None):
        """Check in an asset from its current assignment."""
        asset = self.get_object()
        serializer = CheckInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        assignment = asset.check_in(
            checked_in_by=request.user,
            condition=serializer.validated_data.get("condition"),
            notes=serializer.validated_data.get("notes", ""),
        )

        if assignment is None:
            return Response(
                {"error": "Asset is not currently checked out."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        AuditLog.objects.create(
            action=AuditLog.Action.CHECK_IN,
            entity_type="asset",
            entity_id=str(asset.id),
            entity_name=str(asset),
            user=request.user,
            details={
                "employee": assignment.employee.full_name,
                "condition": serializer.validated_data.get("condition", ""),
            },
        )

        return Response(
            AssetAssignmentSerializer(assignment).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="qr-code")
    def qr_code(self, request, pk=None):
        """Generate a QR code for the asset."""
        asset = self.get_object()

        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr_data = (
            f"AssetGuard|{asset.asset_tag}|{asset.name}|"
            f"{asset.serial_number}|{asset.status}"
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        response = HttpResponse(buffer, content_type="image/png")
        response["Content-Disposition"] = f'inline; filename="asset_{asset.asset_tag}_qr.png"'
        return response

    @action(detail=False, methods=["get"], url_path="status-summary")
    def status_summary(self, request):
        """Get a count of assets by status."""
        summary = {}
        for choice_value, choice_label in Asset.Status.choices:
            summary[choice_value] = Asset.objects.filter(status=choice_value).count()
        summary["total"] = Asset.objects.count()
        return Response(summary)


class AssetAssignmentViewSet(viewsets.ModelViewSet):
    queryset = AssetAssignment.objects.select_related(
        "asset", "employee", "checked_out_by", "checked_in_by"
    ).all()
    serializer_class = AssetAssignmentSerializer
    permission_classes = [IsManagerOrReadOnly]
    filterset_class = AssetAssignmentFilter
    search_fields = [
        "asset__asset_tag", "asset__name",
        "employee__first_name", "employee__last_name",
    ]
    ordering_fields = ["checked_out_at", "returned_at", "expected_return_date"]
    http_method_names = ["get", "head", "options"]
