"""Serializers for maintenance app."""
from rest_framework import serializers

from .models import MaintenanceLog, MaintenanceSchedule, Warranty


class MaintenanceScheduleSerializer(serializers.ModelSerializer):
    asset_tag = serializers.CharField(source="asset.asset_tag", read_only=True)
    asset_name = serializers.CharField(source="asset.name", read_only=True)
    is_overdue = serializers.ReadOnlyField()
    created_by_name = serializers.CharField(
        source="created_by.get_full_name", read_only=True, default=None
    )

    class Meta:
        model = MaintenanceSchedule
        fields = [
            "id", "asset", "asset_tag", "asset_name",
            "title", "description", "frequency", "priority", "status",
            "scheduled_date", "scheduled_end_date", "completed_date",
            "assigned_to", "vendor",
            "estimated_cost", "actual_cost",
            "is_overdue", "notes",
            "created_by", "created_by_name",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class MaintenanceLogSerializer(serializers.ModelSerializer):
    asset_tag = serializers.CharField(source="asset.asset_tag", read_only=True)
    asset_name = serializers.CharField(source="asset.name", read_only=True)
    schedule_title = serializers.CharField(source="schedule.title", read_only=True, default=None)
    created_by_name = serializers.CharField(
        source="created_by.get_full_name", read_only=True, default=None
    )

    class Meta:
        model = MaintenanceLog
        fields = [
            "id", "schedule", "schedule_title",
            "asset", "asset_tag", "asset_name",
            "work_type", "title", "description", "work_performed",
            "performed_by", "performed_date",
            "start_time", "end_time",
            "parts_used", "cost",
            "condition_before", "condition_after",
            "created_by", "created_by_name", "created_at",
        ]
        read_only_fields = ["id", "created_by", "created_at"]

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class WarrantySerializer(serializers.ModelSerializer):
    asset_tag = serializers.CharField(source="asset.asset_tag", read_only=True)
    asset_name = serializers.CharField(source="asset.name", read_only=True)
    is_active = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()

    class Meta:
        model = Warranty
        fields = [
            "id", "asset", "asset_tag", "asset_name",
            "provider", "warranty_number", "warranty_type", "status",
            "start_date", "end_date",
            "coverage_details", "cost",
            "contact_phone", "contact_email", "claim_url",
            "is_active", "days_remaining",
            "notes", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
