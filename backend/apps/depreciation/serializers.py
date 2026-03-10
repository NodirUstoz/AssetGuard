"""Serializers for depreciation app."""
from rest_framework import serializers

from .models import DepreciationEntry, DepreciationSchedule


class DepreciationScheduleListSerializer(serializers.ModelSerializer):
    asset_tag = serializers.CharField(source="asset.asset_tag", read_only=True)
    asset_name = serializers.CharField(source="asset.name", read_only=True)
    total_depreciated = serializers.ReadOnlyField()
    current_book_value = serializers.ReadOnlyField()
    remaining_life_months = serializers.ReadOnlyField()
    is_fully_depreciated = serializers.ReadOnlyField()

    class Meta:
        model = DepreciationSchedule
        fields = [
            "id", "asset", "asset_tag", "asset_name",
            "method", "useful_life_months",
            "original_cost", "salvage_value",
            "total_depreciated", "current_book_value",
            "remaining_life_months", "is_fully_depreciated",
            "start_date", "is_active", "created_at",
        ]


class DepreciationScheduleDetailSerializer(serializers.ModelSerializer):
    asset_tag = serializers.CharField(source="asset.asset_tag", read_only=True)
    asset_name = serializers.CharField(source="asset.name", read_only=True)
    depreciable_amount = serializers.ReadOnlyField()
    total_depreciated = serializers.ReadOnlyField()
    current_book_value = serializers.ReadOnlyField()
    remaining_life_months = serializers.ReadOnlyField()
    is_fully_depreciated = serializers.ReadOnlyField()
    entries = serializers.SerializerMethodField()

    class Meta:
        model = DepreciationSchedule
        fields = [
            "id", "asset", "asset_tag", "asset_name",
            "method", "useful_life_months",
            "original_cost", "salvage_value", "depreciation_rate",
            "depreciable_amount", "total_depreciated",
            "current_book_value", "remaining_life_months",
            "is_fully_depreciated", "start_date",
            "is_active", "notes", "entries",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_entries(self, obj):
        entries = obj.entries.all().order_by("-period_date")[:24]
        return DepreciationEntrySerializer(entries, many=True).data


class DepreciationScheduleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepreciationSchedule
        fields = [
            "asset", "method", "useful_life_months",
            "original_cost", "salvage_value", "depreciation_rate",
            "start_date", "notes",
        ]

    def validate(self, attrs):
        if attrs.get("salvage_value", 0) >= attrs.get("original_cost", 0):
            raise serializers.ValidationError({
                "salvage_value": "Salvage value must be less than original cost."
            })

        method = attrs.get("method")
        if method == DepreciationSchedule.Method.DECLINING_BALANCE:
            if not attrs.get("depreciation_rate") or attrs["depreciation_rate"] <= 0:
                raise serializers.ValidationError({
                    "depreciation_rate": "Depreciation rate is required for declining balance method."
                })
        return attrs


class DepreciationEntrySerializer(serializers.ModelSerializer):
    asset_tag = serializers.CharField(
        source="schedule.asset.asset_tag", read_only=True
    )

    class Meta:
        model = DepreciationEntry
        fields = [
            "id", "schedule", "asset_tag",
            "period_date", "amount",
            "book_value_before", "book_value_after",
            "accumulated_depreciation",
            "notes", "created_at",
        ]
        read_only_fields = ["id", "created_at"]
