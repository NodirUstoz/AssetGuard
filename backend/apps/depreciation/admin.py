"""Admin configuration for depreciation app."""
from django.contrib import admin

from .models import DepreciationEntry, DepreciationSchedule


class DepreciationEntryInline(admin.TabularInline):
    model = DepreciationEntry
    extra = 0
    readonly_fields = [
        "period_date", "amount", "book_value_before",
        "book_value_after", "accumulated_depreciation", "created_at",
    ]
    ordering = ["-period_date"]
    can_delete = False


@admin.register(DepreciationSchedule)
class DepreciationScheduleAdmin(admin.ModelAdmin):
    list_display = [
        "asset", "method", "original_cost", "salvage_value",
        "useful_life_months", "current_book_value",
        "is_fully_depreciated", "is_active", "start_date",
    ]
    list_filter = ["method", "is_active"]
    search_fields = ["asset__asset_tag", "asset__name"]
    raw_id_fields = ["asset"]
    readonly_fields = [
        "depreciable_amount", "total_depreciated",
        "current_book_value", "remaining_life_months",
        "is_fully_depreciated", "created_at", "updated_at",
    ]
    inlines = [DepreciationEntryInline]
    fieldsets = (
        ("Asset", {
            "fields": ("asset",),
        }),
        ("Schedule Configuration", {
            "fields": (
                "method", "useful_life_months",
                "original_cost", "salvage_value",
                "depreciation_rate", "start_date", "is_active",
            ),
        }),
        ("Calculated Values", {
            "fields": (
                "depreciable_amount", "total_depreciated",
                "current_book_value", "remaining_life_months",
                "is_fully_depreciated",
            ),
        }),
        ("Additional", {
            "fields": ("notes", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(DepreciationEntry)
class DepreciationEntryAdmin(admin.ModelAdmin):
    list_display = [
        "schedule", "period_date", "amount",
        "book_value_before", "book_value_after",
        "accumulated_depreciation",
    ]
    list_filter = ["period_date"]
    search_fields = ["schedule__asset__asset_tag"]
    raw_id_fields = ["schedule"]
    readonly_fields = ["created_at"]
    ordering = ["-period_date"]
