"""Filters for asset queries."""
import django_filters

from .models import Asset, AssetAssignment


class AssetFilter(django_filters.FilterSet):
    """Advanced filtering for assets."""

    asset_tag = django_filters.CharFilter(lookup_expr="icontains")
    name = django_filters.CharFilter(lookup_expr="icontains")
    serial_number = django_filters.CharFilter(lookup_expr="icontains")
    manufacturer = django_filters.CharFilter(lookup_expr="icontains")
    vendor = django_filters.CharFilter(lookup_expr="icontains")
    category = django_filters.UUIDFilter(field_name="asset_type__category__id")
    purchase_date_from = django_filters.DateFilter(field_name="purchase_date", lookup_expr="gte")
    purchase_date_to = django_filters.DateFilter(field_name="purchase_date", lookup_expr="lte")
    cost_min = django_filters.NumberFilter(field_name="purchase_cost", lookup_expr="gte")
    cost_max = django_filters.NumberFilter(field_name="purchase_cost", lookup_expr="lte")
    location = django_filters.CharFilter(lookup_expr="icontains")
    building = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Asset
        fields = [
            "status", "condition", "asset_type",
            "asset_tag", "name", "serial_number",
            "manufacturer", "vendor", "category",
            "purchase_date_from", "purchase_date_to",
            "cost_min", "cost_max", "location", "building",
        ]


class AssetAssignmentFilter(django_filters.FilterSet):
    """Filtering for asset assignments."""

    is_active = django_filters.BooleanFilter(method="filter_active")
    is_overdue = django_filters.BooleanFilter(method="filter_overdue")
    checked_out_from = django_filters.DateTimeFilter(field_name="checked_out_at", lookup_expr="gte")
    checked_out_to = django_filters.DateTimeFilter(field_name="checked_out_at", lookup_expr="lte")

    class Meta:
        model = AssetAssignment
        fields = ["asset", "employee", "is_active", "is_overdue"]

    def filter_active(self, queryset, name, value):
        if value:
            return queryset.filter(returned_at__isnull=True)
        return queryset.filter(returned_at__isnull=False)

    def filter_overdue(self, queryset, name, value):
        from django.utils import timezone

        if value:
            return queryset.filter(
                returned_at__isnull=True,
                expected_return_date__lt=timezone.now().date(),
            )
        return queryset
