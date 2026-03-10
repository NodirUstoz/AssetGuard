"""Admin configuration for licenses app."""
from django.contrib import admin

from .models import LicenseAssignment, LicenseRenewal, SoftwareLicense


@admin.register(SoftwareLicense)
class SoftwareLicenseAdmin(admin.ModelAdmin):
    list_display = [
        "software_name", "name", "license_type", "status",
        "total_seats", "used_seats", "available_seats",
        "expiration_date", "annual_cost",
    ]
    list_filter = ["status", "license_type", "publisher"]
    search_fields = ["name", "software_name", "publisher", "license_key", "vendor"]
    ordering = ["software_name", "name"]
    readonly_fields = [
        "used_seats", "available_seats", "is_expired",
        "days_until_expiration", "utilization_percentage",
        "created_at", "updated_at", "created_by",
    ]
    fieldsets = (
        ("Software Info", {
            "fields": (
                "name", "software_name", "version", "publisher",
                "license_key", "license_type", "status",
            ),
        }),
        ("Seats", {
            "fields": (
                "total_seats", "used_seats", "available_seats",
                "utilization_percentage",
            ),
        }),
        ("Dates", {
            "fields": (
                "purchase_date", "activation_date", "expiration_date",
                "is_expired", "days_until_expiration",
            ),
        }),
        ("Financial", {
            "fields": (
                "purchase_cost", "annual_cost", "vendor",
                "purchase_order_number",
            ),
        }),
        ("Vendor Contact", {
            "fields": (
                "vendor_contact_name", "vendor_contact_email", "support_url",
            ),
            "classes": ("collapse",),
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


@admin.register(LicenseAssignment)
class LicenseAssignmentAdmin(admin.ModelAdmin):
    list_display = [
        "license", "employee", "asset",
        "assigned_at", "unassigned_at", "is_active",
    ]
    list_filter = ["unassigned_at", "license__software_name"]
    search_fields = [
        "license__software_name",
        "employee__first_name", "employee__last_name",
        "asset__asset_tag",
    ]
    raw_id_fields = ["license", "employee", "asset", "assigned_by"]


@admin.register(LicenseRenewal)
class LicenseRenewalAdmin(admin.ModelAdmin):
    list_display = [
        "license", "renewal_date", "new_expiration_date",
        "cost", "new_seat_count", "status",
    ]
    list_filter = ["status"]
    search_fields = ["license__software_name"]
    raw_id_fields = ["license", "approved_by"]
    readonly_fields = ["created_at", "updated_at"]
