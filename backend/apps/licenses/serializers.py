"""Serializers for licenses app."""
from rest_framework import serializers

from .models import LicenseAssignment, LicenseRenewal, SoftwareLicense


class SoftwareLicenseListSerializer(serializers.ModelSerializer):
    used_seats = serializers.ReadOnlyField()
    available_seats = serializers.SerializerMethodField()
    days_until_expiration = serializers.ReadOnlyField()
    utilization_percentage = serializers.ReadOnlyField()

    class Meta:
        model = SoftwareLicense
        fields = [
            "id", "name", "software_name", "version", "publisher",
            "license_type", "status", "total_seats", "used_seats",
            "available_seats", "expiration_date", "days_until_expiration",
            "utilization_percentage", "annual_cost", "created_at",
        ]

    def get_available_seats(self, obj):
        seats = obj.available_seats
        if seats == float("inf"):
            return "Unlimited"
        return seats


class SoftwareLicenseDetailSerializer(serializers.ModelSerializer):
    used_seats = serializers.ReadOnlyField()
    available_seats = serializers.SerializerMethodField()
    is_expired = serializers.ReadOnlyField()
    days_until_expiration = serializers.ReadOnlyField()
    utilization_percentage = serializers.ReadOnlyField()
    created_by_name = serializers.CharField(
        source="created_by.get_full_name", read_only=True, default=None
    )
    assignments = serializers.SerializerMethodField()
    renewals = serializers.SerializerMethodField()

    class Meta:
        model = SoftwareLicense
        fields = [
            "id", "name", "software_name", "version", "publisher",
            "license_key", "license_type", "status",
            "total_seats", "used_seats", "available_seats",
            "purchase_date", "activation_date", "expiration_date",
            "is_expired", "days_until_expiration",
            "purchase_cost", "annual_cost", "vendor",
            "purchase_order_number", "vendor_contact_name",
            "vendor_contact_email", "support_url",
            "utilization_percentage", "notes",
            "created_by", "created_by_name",
            "assignments", "renewals",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def get_available_seats(self, obj):
        seats = obj.available_seats
        if seats == float("inf"):
            return "Unlimited"
        return seats

    def get_assignments(self, obj):
        active = obj.assignments.filter(unassigned_at__isnull=True).select_related("employee", "asset")
        return LicenseAssignmentSerializer(active, many=True).data

    def get_renewals(self, obj):
        return LicenseRenewalSerializer(obj.renewals.all()[:5], many=True).data


class SoftwareLicenseCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SoftwareLicense
        fields = [
            "name", "software_name", "version", "publisher",
            "license_key", "license_type", "status",
            "total_seats", "purchase_date", "activation_date",
            "expiration_date", "purchase_cost", "annual_cost",
            "vendor", "purchase_order_number",
            "vendor_contact_name", "vendor_contact_email",
            "support_url", "notes",
        ]

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class LicenseAssignmentSerializer(serializers.ModelSerializer):
    license_name = serializers.CharField(source="license.software_name", read_only=True)
    employee_name = serializers.SerializerMethodField()
    asset_name = serializers.SerializerMethodField()
    is_active = serializers.ReadOnlyField()
    assigned_by_name = serializers.CharField(
        source="assigned_by.get_full_name", read_only=True, default=None
    )

    class Meta:
        model = LicenseAssignment
        fields = [
            "id", "license", "license_name",
            "employee", "employee_name",
            "asset", "asset_name",
            "assigned_by", "assigned_by_name",
            "assigned_at", "unassigned_at",
            "is_active", "notes",
        ]
        read_only_fields = ["id", "assigned_at", "assigned_by"]

    def get_employee_name(self, obj):
        return obj.employee.full_name if obj.employee else None

    def get_asset_name(self, obj):
        return str(obj.asset) if obj.asset else None

    def validate(self, attrs):
        license_obj = attrs.get("license")
        if license_obj and license_obj.available_seats <= 0:
            if license_obj.license_type != SoftwareLicense.LicenseType.SITE:
                from utils.exceptions import LicenseLimitExceededError
                raise LicenseLimitExceededError()

        if not attrs.get("employee") and not attrs.get("asset"):
            raise serializers.ValidationError(
                "Either an employee or an asset must be specified."
            )
        return attrs

    def create(self, validated_data):
        validated_data["assigned_by"] = self.context["request"].user
        return super().create(validated_data)


class LicenseRenewalSerializer(serializers.ModelSerializer):
    license_name = serializers.CharField(source="license.software_name", read_only=True)
    approved_by_name = serializers.CharField(
        source="approved_by.get_full_name", read_only=True, default=None
    )

    class Meta:
        model = LicenseRenewal
        fields = [
            "id", "license", "license_name",
            "renewal_date", "new_expiration_date",
            "cost", "new_seat_count", "status",
            "approved_by", "approved_by_name",
            "notes", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
