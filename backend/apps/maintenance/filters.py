"""Filters for maintenance queries."""
import django_filters
from django.utils import timezone

from .models import MaintenanceLog, MaintenanceSchedule, Warranty


class MaintenanceScheduleFilter(django_filters.FilterSet):
    """Advanced filtering for maintenance schedules."""

    is_overdue = django_filters.BooleanFilter(method="filter_overdue")
    scheduled_from = django_filters.DateFilter(field_name="scheduled_date", lookup_expr="gte")
    scheduled_to = django_filters.DateFilter(field_name="scheduled_date", lookup_expr="lte")
    cost_min = django_filters.NumberFilter(field_name="estimated_cost", lookup_expr="gte")
    cost_max = django_filters.NumberFilter(field_name="estimated_cost", lookup_expr="lte")

    class Meta:
        model = MaintenanceSchedule
        fields = [
            "asset", "status", "priority", "frequency",
            "is_overdue", "scheduled_from", "scheduled_to",
            "cost_min", "cost_max",
        ]

    def filter_overdue(self, queryset, name, value):
        if value:
            return queryset.filter(
                scheduled_date__lt=timezone.now().date(),
                status__in=[
                    MaintenanceSchedule.Status.SCHEDULED,
                    MaintenanceSchedule.Status.IN_PROGRESS,
                ],
            )
        return queryset


class MaintenanceLogFilter(django_filters.FilterSet):
    """Advanced filtering for maintenance logs."""

    performed_from = django_filters.DateFilter(field_name="performed_date", lookup_expr="gte")
    performed_to = django_filters.DateFilter(field_name="performed_date", lookup_expr="lte")
    cost_min = django_filters.NumberFilter(field_name="cost", lookup_expr="gte")
    cost_max = django_filters.NumberFilter(field_name="cost", lookup_expr="lte")

    class Meta:
        model = MaintenanceLog
        fields = [
            "asset", "work_type", "schedule",
            "performed_from", "performed_to",
            "cost_min", "cost_max",
        ]


class WarrantyFilter(django_filters.FilterSet):
    """Advanced filtering for warranties."""

    is_active = django_filters.BooleanFilter(method="filter_active")
    expiring_within_days = django_filters.NumberFilter(method="filter_expiring")
    cost_min = django_filters.NumberFilter(field_name="cost", lookup_expr="gte")
    cost_max = django_filters.NumberFilter(field_name="cost", lookup_expr="lte")

    class Meta:
        model = Warranty
        fields = ["asset", "status", "provider", "is_active", "expiring_within_days"]

    def filter_active(self, queryset, name, value):
        today = timezone.now().date()
        if value:
            return queryset.filter(
                status=Warranty.Status.ACTIVE,
                end_date__gte=today,
            )
        return queryset.exclude(
            status=Warranty.Status.ACTIVE,
            end_date__gte=today,
        )

    def filter_expiring(self, queryset, name, value):
        today = timezone.now().date()
        cutoff = today + timezone.timedelta(days=int(value))
        return queryset.filter(
            end_date__gte=today,
            end_date__lte=cutoff,
            status=Warranty.Status.ACTIVE,
        )
