"""Admin configuration for maintenance app."""
from django.contrib import admin

from .models import MaintenanceLog, MaintenanceSchedule, Warranty


@admin.register(MaintenanceSchedule)
class MaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display = [
        "title", "asset", "frequency", "priority",
        "status", "scheduled_date", "completed_date",
        "estimated_cost", "actual_cost", "is_overdue",
    ]
    list_filter = ["status", "priority", "frequency"]
    search_fields = ["title", "description", "asset__asset_tag", "asset__name", "vendor"]
    ordering = ["scheduled_date"]
    raw_id_fields = ["asset", "created_by"]
    readonly_fields = ["is_overdue", "created_at", "updated_at"]
    fieldsets = (
        ("Details", {
            "fields": (
                "asset", "title", "description",
                "frequency", "priority", "status",
            ),
        }),
        ("Schedule", {
            "fields": (
                "scheduled_date", "scheduled_end_date", "completed_date",
                "is_overdue",
            ),
        }),
        ("Assignment & Cost", {
            "fields": (
                "assigned_to", "vendor",
                "estimated_cost", "actual_cost",
            ),
        }),
        ("Additional", {
            "fields": ("notes", "created_by", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(MaintenanceLog)
class MaintenanceLogAdmin(admin.ModelAdmin):
    list_display = [
        "title", "asset", "work_type",
        "performed_by", "performed_date",
        "cost", "condition_before", "condition_after",
    ]
    list_filter = ["work_type", "performed_date"]
    search_fields = [
        "title", "description", "performed_by",
        "asset__asset_tag", "asset__name",
    ]
    raw_id_fields = ["asset", "schedule", "created_by"]
    readonly_fields = ["created_at"]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Warranty)
class WarrantyAdmin(admin.ModelAdmin):
    list_display = [
        "asset", "provider", "warranty_type", "status",
        "start_date", "end_date", "is_active",
        "days_remaining", "cost",
    ]
    list_filter = ["status", "provider"]
    search_fields = ["asset__asset_tag", "asset__name", "provider", "warranty_number"]
    raw_id_fields = ["asset"]
    readonly_fields = ["is_active", "days_remaining", "created_at", "updated_at"]
