"""Admin configuration for vendors app."""
from django.contrib import admin

from .models import PurchaseOrder, PurchaseOrderLineItem, Vendor, VendorContact


class VendorContactInline(admin.TabularInline):
    model = VendorContact
    extra = 0
    fields = ["name", "title", "email", "phone", "is_primary"]


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = [
        "code", "name", "status",
        "primary_contact_name", "primary_contact_email",
        "total_purchase_orders", "created_at",
    ]
    list_filter = ["status", "country"]
    search_fields = ["name", "code", "primary_contact_name", "primary_contact_email"]
    ordering = ["name"]
    inlines = [VendorContactInline]
    readonly_fields = ["created_at", "updated_at", "created_by"]
    fieldsets = (
        ("General", {
            "fields": ("name", "code", "website", "status", "description"),
        }),
        ("Address", {
            "fields": (
                "address_line_1", "address_line_2",
                "city", "state", "postal_code", "country",
            ),
        }),
        ("Primary Contact", {
            "fields": (
                "primary_contact_name",
                "primary_contact_email",
                "primary_contact_phone",
            ),
        }),
        ("Financial", {
            "fields": ("payment_terms", "tax_id", "account_number"),
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


class PurchaseOrderLineItemInline(admin.TabularInline):
    model = PurchaseOrderLineItem
    extra = 1
    fields = ["description", "quantity", "unit_price", "line_total", "received_quantity", "asset"]
    readonly_fields = ["line_total"]


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = [
        "po_number", "vendor", "status",
        "order_date", "total_amount", "created_at",
    ]
    list_filter = ["status", "vendor"]
    search_fields = ["po_number", "description", "vendor__name"]
    ordering = ["-created_at"]
    inlines = [PurchaseOrderLineItemInline]
    readonly_fields = ["created_at", "updated_at", "subtotal", "total_amount"]
    raw_id_fields = ["vendor", "created_by", "approved_by"]
