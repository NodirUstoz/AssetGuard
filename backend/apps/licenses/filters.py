"""Filters for license queries."""
import django_filters
from django.utils import timezone

from .models import LicenseAssignment, SoftwareLicense


class SoftwareLicenseFilter(django_filters.FilterSet):
    """Advanced filtering for software licenses."""

    software_name = django_filters.CharFilter(lookup_expr="icontains")
    publisher = django_filters.CharFilter(lookup_expr="icontains")
    vendor = django_filters.CharFilter(lookup_expr="icontains")
    is_expired = django_filters.BooleanFilter(method="filter_expired")
    expiring_within_days = django_filters.NumberFilter(method="filter_expiring")
    cost_min = django_filters.NumberFilter(field_name="annual_cost", lookup_expr="gte")
    cost_max = django_filters.NumberFilter(field_name="annual_cost", lookup_expr="lte")
    has_available_seats = django_filters.BooleanFilter(method="filter_available_seats")

    class Meta:
        model = SoftwareLicense
        fields = [
            "status", "license_type", "publisher",
            "software_name", "vendor",
            "is_expired", "expiring_within_days",
            "cost_min", "cost_max", "has_available_seats",
        ]

    def filter_expired(self, queryset, name, value):
        today = timezone.now().date()
        if value:
            return queryset.filter(expiration_date__lt=today)
        return queryset.filter(
            models_Q_expiration_date__gte=today,
        ).exclude(expiration_date__isnull=True) | queryset.filter(expiration_date__isnull=True)

    def filter_expiring(self, queryset, name, value):
        today = timezone.now().date()
        cutoff = today + timezone.timedelta(days=int(value))
        return queryset.filter(
            expiration_date__gte=today,
            expiration_date__lte=cutoff,
            status=SoftwareLicense.Status.ACTIVE,
        )

    def filter_available_seats(self, queryset, name, value):
        """Filter licenses that have (or don't have) available seats.
        This is a post-query filter since available_seats is a property."""
        # For simplicity, use a basic annotation approach
        ids = []
        for lic in queryset:
            has_seats = lic.available_seats > 0 if isinstance(lic.available_seats, (int, float)) else True
            if (value and has_seats) or (not value and not has_seats):
                ids.append(lic.id)
        return queryset.filter(id__in=ids)


class LicenseAssignmentFilter(django_filters.FilterSet):
    """Filtering for license assignments."""

    is_active = django_filters.BooleanFilter(method="filter_active")
    assigned_from = django_filters.DateTimeFilter(field_name="assigned_at", lookup_expr="gte")
    assigned_to = django_filters.DateTimeFilter(field_name="assigned_at", lookup_expr="lte")

    class Meta:
        model = LicenseAssignment
        fields = ["license", "employee", "asset", "is_active"]

    def filter_active(self, queryset, name, value):
        if value:
            return queryset.filter(unassigned_at__isnull=True)
        return queryset.filter(unassigned_at__isnull=False)
