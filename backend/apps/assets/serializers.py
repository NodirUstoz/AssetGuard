"""Serializers for assets app."""
from rest_framework import serializers

from apps.accounts.serializers import EmployeeMinimalSerializer

from .models import Asset, AssetAssignment, AssetCategory, AssetType


class AssetCategorySerializer(serializers.ModelSerializer):
    subcategory_count = serializers.SerializerMethodField()
    asset_type_count = serializers.SerializerMethodField()

    class Meta:
        model = AssetCategory
        fields = [
            "id", "name", "description", "parent",
            "is_active", "subcategory_count", "asset_type_count",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_subcategory_count(self, obj):
        return obj.subcategories.count()

    def get_asset_type_count(self, obj):
        return obj.asset_types.count()


class AssetTypeSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    asset_count = serializers.SerializerMethodField()

    class Meta:
        model = AssetType
        fields = [
            "id", "name", "category", "category_name",
            "description", "default_useful_life_months",
            "is_active", "asset_count", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_asset_count(self, obj):
        return obj.assets.count()


class AssetListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""

    category_name = serializers.ReadOnlyField()
    type_name = serializers.ReadOnlyField()
    current_assignee = serializers.SerializerMethodField()

    class Meta:
        model = Asset
        fields = [
            "id", "asset_tag", "name", "status", "condition",
            "category_name", "type_name", "serial_number",
            "manufacturer", "model_number", "location",
            "purchase_date", "purchase_cost", "current_assignee",
            "created_at",
        ]

    def get_current_assignee(self, obj):
        assignment = obj.current_assignment
        if assignment:
            return {
                "employee_id": str(assignment.employee.id),
                "name": assignment.employee.full_name,
                "checked_out_at": assignment.checked_out_at,
            }
        return None


class AssetDetailSerializer(serializers.ModelSerializer):
    """Full serializer for detail views."""

    category_name = serializers.ReadOnlyField()
    type_name = serializers.ReadOnlyField()
    current_assignment = serializers.SerializerMethodField()
    assignment_history = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True, default=None)

    class Meta:
        model = Asset
        fields = [
            "id", "asset_tag", "name", "description",
            "asset_type", "category_name", "type_name",
            "status", "condition",
            "serial_number", "model_number", "manufacturer", "barcode",
            "purchase_date", "purchase_cost", "purchase_order_number",
            "vendor", "salvage_value",
            "location", "building", "floor", "room",
            "ip_address", "mac_address", "hostname",
            "image", "notes", "custom_fields",
            "current_assignment", "assignment_history",
            "created_by", "created_by_name",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def get_current_assignment(self, obj):
        assignment = obj.current_assignment
        if assignment:
            return AssetAssignmentSerializer(assignment).data
        return None

    def get_assignment_history(self, obj):
        assignments = obj.assignments.select_related("employee", "checked_out_by").all()[:10]
        return AssetAssignmentSerializer(assignments, many=True).data


class AssetCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = [
            "asset_tag", "name", "description", "asset_type",
            "status", "condition",
            "serial_number", "model_number", "manufacturer", "barcode",
            "purchase_date", "purchase_cost", "purchase_order_number",
            "vendor", "salvage_value",
            "location", "building", "floor", "room",
            "ip_address", "mac_address", "hostname",
            "image", "notes", "custom_fields",
        ]

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class AssetAssignmentSerializer(serializers.ModelSerializer):
    employee_detail = EmployeeMinimalSerializer(source="employee", read_only=True)
    asset_tag = serializers.CharField(source="asset.asset_tag", read_only=True)
    asset_name = serializers.CharField(source="asset.name", read_only=True)
    checked_out_by_name = serializers.CharField(
        source="checked_out_by.get_full_name", read_only=True, default=None
    )
    checked_in_by_name = serializers.CharField(
        source="checked_in_by.get_full_name", read_only=True, default=None
    )
    is_active = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()

    class Meta:
        model = AssetAssignment
        fields = [
            "id", "asset", "asset_tag", "asset_name",
            "employee", "employee_detail",
            "checked_out_by", "checked_out_by_name",
            "checked_out_at", "expected_return_date", "notes",
            "returned_at", "checked_in_by", "checked_in_by_name",
            "return_condition", "return_notes",
            "is_active", "is_overdue",
        ]
        read_only_fields = [
            "id", "checked_out_at", "returned_at",
            "checked_out_by", "checked_in_by",
        ]


class CheckOutSerializer(serializers.Serializer):
    """Serializer for check-out action."""

    employee = serializers.UUIDField()
    expected_return_date = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class CheckInSerializer(serializers.Serializer):
    """Serializer for check-in action."""

    condition = serializers.ChoiceField(choices=Asset.Condition.choices, required=False)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
