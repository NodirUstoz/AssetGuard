"""Views for maintenance app."""
import logging

from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import MaintenanceLog, MaintenanceSchedule, Warranty
from .serializers import (
    MaintenanceLogSerializer,
    MaintenanceScheduleSerializer,
    WarrantySerializer,
)

logger = logging.getLogger(__name__)


class IsManagerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.is_manager


class MaintenanceScheduleViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceSchedule.objects.select_related("asset", "created_by").all()
    serializer_class = MaintenanceScheduleSerializer
    permission_classes = [IsManagerOrReadOnly]
    search_fields = ["title", "description", "asset__asset_tag", "asset__name", "vendor"]
    ordering_fields = ["scheduled_date", "priority", "status", "created_at"]
    filterset_fields = ["asset", "status", "priority", "frequency"]

    @action(detail=False, methods=["get"])
    def upcoming(self, request):
        """Get upcoming maintenance within the next N days."""
        days = int(request.query_params.get("days", 30))
        cutoff = timezone.now().date() + timezone.timedelta(days=days)
        schedules = MaintenanceSchedule.objects.filter(
            scheduled_date__lte=cutoff,
            scheduled_date__gte=timezone.now().date(),
            status__in=[
                MaintenanceSchedule.Status.SCHEDULED,
                MaintenanceSchedule.Status.IN_PROGRESS,
            ],
        ).select_related("asset").order_by("scheduled_date")
        serializer = self.get_serializer(schedules, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def overdue(self, request):
        """Get overdue maintenance schedules."""
        schedules = MaintenanceSchedule.objects.filter(
            scheduled_date__lt=timezone.now().date(),
            status__in=[
                MaintenanceSchedule.Status.SCHEDULED,
                MaintenanceSchedule.Status.IN_PROGRESS,
            ],
        ).select_related("asset").order_by("scheduled_date")
        serializer = self.get_serializer(schedules, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="calendar")
    def calendar_view(self, request):
        """Get maintenance events for calendar display within a date range."""
        start = request.query_params.get("start")
        end = request.query_params.get("end")

        queryset = MaintenanceSchedule.objects.select_related("asset").all()
        if start:
            queryset = queryset.filter(scheduled_date__gte=start)
        if end:
            queryset = queryset.filter(scheduled_date__lte=end)

        events = []
        for schedule in queryset:
            events.append({
                "id": str(schedule.id),
                "title": f"{schedule.asset.asset_tag}: {schedule.title}",
                "start": schedule.scheduled_date.isoformat(),
                "end": (schedule.scheduled_end_date or schedule.scheduled_date).isoformat(),
                "priority": schedule.priority,
                "status": schedule.status,
                "asset_id": str(schedule.asset.id),
            })
        return Response(events)


class MaintenanceLogViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceLog.objects.select_related(
        "asset", "schedule", "created_by"
    ).all()
    serializer_class = MaintenanceLogSerializer
    permission_classes = [IsManagerOrReadOnly]
    search_fields = [
        "title", "description", "performed_by",
        "asset__asset_tag", "asset__name",
    ]
    ordering_fields = ["performed_date", "cost", "created_at"]
    filterset_fields = ["asset", "work_type", "schedule"]

    @action(detail=False, methods=["get"], url_path="cost-summary")
    def cost_summary(self, request):
        """Get maintenance cost summary."""
        from django.db.models import Sum, Count, Avg

        logs = MaintenanceLog.objects.all()

        asset_id = request.query_params.get("asset")
        if asset_id:
            logs = logs.filter(asset_id=asset_id)

        year = request.query_params.get("year")
        if year:
            logs = logs.filter(performed_date__year=int(year))

        summary = logs.aggregate(
            total_cost=Sum("cost"),
            total_entries=Count("id"),
            avg_cost=Avg("cost"),
        )

        by_type = (
            logs.values("work_type")
            .annotate(total=Sum("cost"), count=Count("id"))
            .order_by("-total")
        )

        return Response({
            "total_cost": summary["total_cost"] or 0,
            "total_entries": summary["total_entries"],
            "average_cost": round(summary["avg_cost"] or 0, 2),
            "by_type": list(by_type),
        })


class WarrantyViewSet(viewsets.ModelViewSet):
    queryset = Warranty.objects.select_related("asset").all()
    serializer_class = WarrantySerializer
    permission_classes = [IsManagerOrReadOnly]
    search_fields = ["provider", "warranty_number", "asset__asset_tag", "asset__name"]
    ordering_fields = ["end_date", "start_date", "created_at"]
    filterset_fields = ["asset", "status", "provider"]

    @action(detail=False, methods=["get"], url_path="expiring-soon")
    def expiring_soon(self, request):
        """Get warranties expiring within the next N days."""
        days = int(request.query_params.get("days", 30))
        cutoff = timezone.now().date() + timezone.timedelta(days=days)
        warranties = Warranty.objects.filter(
            end_date__lte=cutoff,
            end_date__gte=timezone.now().date(),
            status=Warranty.Status.ACTIVE,
        ).select_related("asset").order_by("end_date")
        serializer = self.get_serializer(warranties, many=True)
        return Response(serializer.data)
