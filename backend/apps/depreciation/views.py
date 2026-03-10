"""Views for depreciation app."""
import logging

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import DepreciationEntry, DepreciationSchedule
from .serializers import (
    DepreciationEntrySerializer,
    DepreciationScheduleCreateSerializer,
    DepreciationScheduleDetailSerializer,
    DepreciationScheduleListSerializer,
)
from .services import generate_full_depreciation_schedule

logger = logging.getLogger(__name__)


class IsManagerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.is_manager


class DepreciationScheduleViewSet(viewsets.ModelViewSet):
    """CRUD operations for depreciation schedules."""

    queryset = DepreciationSchedule.objects.select_related("asset").all()
    permission_classes = [IsManagerOrReadOnly]
    search_fields = ["asset__asset_tag", "asset__name"]
    ordering_fields = ["start_date", "original_cost", "created_at"]
    filterset_fields = ["method", "is_active", "asset"]

    def get_serializer_class(self):
        if self.action == "list":
            return DepreciationScheduleListSerializer
        if self.action in ["create", "update", "partial_update"]:
            return DepreciationScheduleCreateSerializer
        return DepreciationScheduleDetailSerializer

    @action(detail=True, methods=["get"])
    def preview(self, request, pk=None):
        """
        Preview the full projected depreciation schedule
        without persisting entries to the database.
        """
        schedule = self.get_object()
        projected = generate_full_depreciation_schedule(schedule)
        return Response({
            "asset_tag": schedule.asset.asset_tag,
            "method": schedule.get_method_display(),
            "original_cost": str(schedule.original_cost),
            "salvage_value": str(schedule.salvage_value),
            "useful_life_months": schedule.useful_life_months,
            "projected_entries": projected,
        })

    @action(detail=False, methods=["get"], url_path="fully-depreciated")
    def fully_depreciated(self, request):
        """List all assets that have been fully depreciated."""
        schedules = DepreciationSchedule.objects.select_related("asset").filter(
            is_active=True,
        )
        fully_dep = [s for s in schedules if s.is_fully_depreciated]
        serializer = DepreciationScheduleListSerializer(fully_dep, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Get depreciation summary across all active schedules."""
        from django.db.models import Sum

        schedules = DepreciationSchedule.objects.filter(is_active=True)
        total_original = schedules.aggregate(t=Sum("original_cost"))["t"] or 0
        total_salvage = schedules.aggregate(t=Sum("salvage_value"))["t"] or 0

        total_depreciated = sum(s.total_depreciated for s in schedules)
        total_book_value = sum(s.current_book_value for s in schedules)
        fully_depreciated = sum(1 for s in schedules if s.is_fully_depreciated)

        return Response({
            "total_schedules": schedules.count(),
            "total_original_cost": str(total_original),
            "total_salvage_value": str(total_salvage),
            "total_depreciated": str(total_depreciated),
            "total_current_book_value": str(total_book_value),
            "fully_depreciated_count": fully_depreciated,
        })


class DepreciationEntryViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for depreciation entries."""

    queryset = DepreciationEntry.objects.select_related(
        "schedule", "schedule__asset",
    ).all()
    serializer_class = DepreciationEntrySerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["schedule"]
    ordering_fields = ["period_date", "amount", "created_at"]
    search_fields = ["schedule__asset__asset_tag"]
