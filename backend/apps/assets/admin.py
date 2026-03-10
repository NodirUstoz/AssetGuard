"""Admin configuration for assets app."""
from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import Asset, AssetAssignment, AssetCategory, AssetType


class AssetResource(resources.ModelResource):
    class Meta:
        model = Asset
        fields = [
            "asset_tag", "name", "status", "condition",
            "serial_number", "model_number", "manufacturer",
            "purchase_date", "purchase_cost", "vendor",
            "location", "building",
        ]
        export_order = fields


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "parent", "is_active", "created_at"]
    list_filter = ["is_active", "parent"]
    search_fields = ["name"]


@admin.register(AssetType)
class AssetTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "default_useful_life_months", "is_active"]
    list_filter = ["category", "is_active"]
    search_fields = ["name"]


@admin.register(Asset)
class AssetAdmin(ImportExportModelAdmin):
    resource_class = AssetResource
    list_display = [
        "asset_tag", "name", "asset_type", "status",
        "condition", "serial_number", "manufacturer",
        "location", "purchase_cost", "purchase_date",
    ]
    list_filter = [
        "status", "condition", "asset_type__category",
        "asset_type", "manufacturer",
    ]
    search_fields = [
        "asset_tag", "name", "serial_number",
        "model_number", "hostname",
    ]
    readonly_fields = ["created_at", "updated_at", "created_by"]
    fieldsets = (
        ("Identification", {
            "fields": (
                "asset_tag", "name", "description", "asset_type",
                "status", "condition", "barcode", "image",
            ),
        }),
        ("Hardware Details", {
            "fields": (
                "serial_number", "model_number", "manufacturer",
            ),
        }),
        ("Financial", {
            "fields": (
                "purchase_date", "purchase_cost",
                "purchase_order_number", "vendor", "salvage_value",
            ),
        }),
        ("Location", {
            "fields": ("location", "building", "floor", "room"),
        }),
        ("Network", {
            "fields": ("ip_address", "mac_address", "hostname"),
            "classes": ("collapse",),
        }),
        ("Additional", {
            "fields": ("notes", "custom_fields", "created_by", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(AssetAssignment)
class AssetAssignmentAdmin(admin.ModelAdmin):
    list_display = [
        "asset", "employee", "checked_out_at",
        "expected_return_date", "returned_at", "is_active",
    ]
    list_filter = ["returned_at"]
    search_fields = [
        "asset__asset_tag", "asset__name",
        "employee__first_name", "employee__last_name",
    ]
    raw_id_fields = ["asset", "employee", "checked_out_by", "checked_in_by"]
