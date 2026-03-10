"""Views for audits app."""
import logging
from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import AuditLog
from .serializers import AuditLogSerializer

logger = logging.getLogger(__name__)


class IsAdminOrManager(permissions.BasePermission):
    """Audit logs are only visible to admins and managers."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_manager


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for audit logs.
    Supports filtering by entity_type, entity_id, action, user, and date range.
    """

    queryset = AuditLog.objects.select_related("user").all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminOrManager]
    search_fields = ["entity_name", "user_email", "entity_id"]
    ordering_fields = ["timestamp", "action", "entity_type"]
    filterset_fields = ["action", "entity_type", "user"]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by entity
        entity_type = self.request.query_params.get("entity_type")
        entity_id = self.request.query_params.get("entity_id")
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)
        if entity_id:
            queryset = queryset.filter(entity_id=entity_id)

        # Filter by date range
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from:
            queryset = queryset.filter(timestamp__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__date__lte=date_to)

        return queryset

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """
        Get a summary of audit log activity.
        Accepts optional 'days' query param (default 30).
        """
        days = int(request.query_params.get("days", 30))
        since = timezone.now() - timedelta(days=days)

        logs = AuditLog.objects.filter(timestamp__gte=since)

        by_action = list(
            logs.values("action")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        by_entity = list(
            logs.values("entity_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        by_user = list(
            logs.values("user_email")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        daily_activity = list(
            logs.extra(select={"day": "DATE(timestamp)"})
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )

        return Response({
            "period_days": days,
            "total_events": logs.count(),
            "by_action": by_action,
            "by_entity_type": by_entity,
            "top_users": by_user,
            "daily_activity": daily_activity,
        })

    @action(detail=False, methods=["get"], url_path="entity-history")
    def entity_history(self, request):
        """Get full audit history for a specific entity."""
        entity_type = request.query_params.get("entity_type")
        entity_id = request.query_params.get("entity_id")

        if not entity_type or not entity_id:
            return Response(
                {"error": "Both entity_type and entity_id are required."},
                status=400,
            )

        logs = AuditLog.objects.filter(
            entity_type=entity_type,
            entity_id=entity_id,
        ).select_related("user").order_by("-timestamp")

        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)
