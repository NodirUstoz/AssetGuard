"""Views for vendors app."""
import logging

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.audits.models import AuditLog

from .models import PurchaseOrder, PurchaseOrderLineItem, Vendor, VendorContact
from .serializers import (
    PurchaseOrderCreateUpdateSerializer,
    PurchaseOrderDetailSerializer,
    PurchaseOrderLineItemSerializer,
    PurchaseOrderListSerializer,
    VendorContactSerializer,
    VendorCreateUpdateSerializer,
    VendorDetailSerializer,
    VendorListSerializer,
)

logger = logging.getLogger(__name__)


class IsManagerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.is_manager


class VendorViewSet(viewsets.ModelViewSet):
    """CRUD operations for vendors."""

    queryset = Vendor.objects.all()
    permission_classes = [IsManagerOrReadOnly]
    search_fields = ["name", "code", "primary_contact_name", "primary_contact_email"]
    ordering_fields = ["name", "code", "created_at"]
    filterset_fields = ["status"]

    def get_serializer_class(self):
        if self.action == "list":
            return VendorListSerializer
        if self.action in ["create", "update", "partial_update"]:
            return VendorCreateUpdateSerializer
        return VendorDetailSerializer

    def perform_create(self, serializer):
        vendor = serializer.save()
        AuditLog.log(
            action=AuditLog.Action.CREATE,
            entity_type="vendor",
            entity_id=vendor.id,
            user=self.request.user,
            entity_name=str(vendor),
            request=self.request,
        )

    @action(detail=True, methods=["get"], url_path="purchase-history")
    def purchase_history(self, request, pk=None):
        """Get all purchase orders for a specific vendor."""
        vendor = self.get_object()
        orders = vendor.purchase_orders.all().order_by("-created_at")
        serializer = PurchaseOrderListSerializer(orders, many=True)
        return Response(serializer.data)


class VendorContactViewSet(viewsets.ModelViewSet):
    """CRUD operations for vendor contacts."""

    queryset = VendorContact.objects.select_related("vendor").all()
    serializer_class = VendorContactSerializer
    permission_classes = [IsManagerOrReadOnly]
    filterset_fields = ["vendor", "is_primary"]
    search_fields = ["name", "email", "title"]


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    """CRUD operations for purchase orders."""

    queryset = PurchaseOrder.objects.select_related(
        "vendor", "created_by", "approved_by",
    ).all()
    permission_classes = [IsManagerOrReadOnly]
    search_fields = ["po_number", "description", "vendor__name"]
    ordering_fields = ["po_number", "order_date", "total_amount", "created_at"]
    filterset_fields = ["vendor", "status"]

    def get_serializer_class(self):
        if self.action == "list":
            return PurchaseOrderListSerializer
        if self.action in ["create", "update", "partial_update"]:
            return PurchaseOrderCreateUpdateSerializer
        return PurchaseOrderDetailSerializer

    def perform_create(self, serializer):
        po = serializer.save()
        AuditLog.log(
            action=AuditLog.Action.CREATE,
            entity_type="purchase_order",
            entity_id=po.id,
            user=self.request.user,
            entity_name=str(po),
            request=self.request,
        )

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        """Approve a purchase order."""
        po = self.get_object()
        if po.status != PurchaseOrder.Status.SUBMITTED:
            return Response(
                {"error": "Only submitted purchase orders can be approved."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        po.status = PurchaseOrder.Status.APPROVED
        po.approved_by = request.user
        po.save(update_fields=["status", "approved_by", "updated_at"])

        AuditLog.log(
            action=AuditLog.Action.UPDATE,
            entity_type="purchase_order",
            entity_id=po.id,
            user=request.user,
            entity_name=str(po),
            details={"action": "approved"},
            request=request,
        )
        return Response(PurchaseOrderDetailSerializer(po).data)

    @action(detail=True, methods=["post"], url_path="mark-received")
    def mark_received(self, request, pk=None):
        """Mark a purchase order as received."""
        from django.utils import timezone

        po = self.get_object()
        if po.status not in (PurchaseOrder.Status.ORDERED, PurchaseOrder.Status.PARTIALLY_RECEIVED):
            return Response(
                {"error": "Only ordered or partially received POs can be marked as received."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        po.status = PurchaseOrder.Status.RECEIVED
        po.received_date = timezone.now().date()
        po.save(update_fields=["status", "received_date", "updated_at"])

        AuditLog.log(
            action=AuditLog.Action.UPDATE,
            entity_type="purchase_order",
            entity_id=po.id,
            user=request.user,
            entity_name=str(po),
            details={"action": "received"},
            request=request,
        )
        return Response(PurchaseOrderDetailSerializer(po).data)


class PurchaseOrderLineItemViewSet(viewsets.ModelViewSet):
    """CRUD operations for purchase order line items."""

    queryset = PurchaseOrderLineItem.objects.select_related(
        "purchase_order", "asset",
    ).all()
    serializer_class = PurchaseOrderLineItemSerializer
    permission_classes = [IsManagerOrReadOnly]
    filterset_fields = ["purchase_order"]

    def perform_create(self, serializer):
        line_item = serializer.save()
        line_item.purchase_order.calculate_total()

    def perform_update(self, serializer):
        line_item = serializer.save()
        line_item.purchase_order.calculate_total()

    def perform_destroy(self, instance):
        po = instance.purchase_order
        instance.delete()
        po.calculate_total()
