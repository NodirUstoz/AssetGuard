"""Serializers for vendors app."""
from rest_framework import serializers

from .models import PurchaseOrder, PurchaseOrderLineItem, Vendor, VendorContact


class VendorContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorContact
        fields = [
            "id", "vendor", "name", "title",
            "email", "phone", "is_primary",
            "notes", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class VendorListSerializer(serializers.ModelSerializer):
    total_purchase_orders = serializers.ReadOnlyField()

    class Meta:
        model = Vendor
        fields = [
            "id", "name", "code", "website", "status",
            "primary_contact_name", "primary_contact_email",
            "primary_contact_phone", "total_purchase_orders",
            "created_at",
        ]


class VendorDetailSerializer(serializers.ModelSerializer):
    total_purchase_orders = serializers.ReadOnlyField()
    total_spent = serializers.ReadOnlyField()
    contacts = VendorContactSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(
        source="created_by.get_full_name", read_only=True, default=None,
    )

    class Meta:
        model = Vendor
        fields = [
            "id", "name", "code", "website", "status", "description",
            "address_line_1", "address_line_2", "city", "state",
            "postal_code", "country",
            "primary_contact_name", "primary_contact_email",
            "primary_contact_phone",
            "payment_terms", "tax_id", "account_number",
            "total_purchase_orders", "total_spent",
            "contacts", "notes",
            "created_by", "created_by_name",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


class VendorCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = [
            "name", "code", "website", "status", "description",
            "address_line_1", "address_line_2", "city", "state",
            "postal_code", "country",
            "primary_contact_name", "primary_contact_email",
            "primary_contact_phone",
            "payment_terms", "tax_id", "account_number",
            "notes",
        ]

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class PurchaseOrderLineItemSerializer(serializers.ModelSerializer):
    asset_tag = serializers.CharField(source="asset.asset_tag", read_only=True, default=None)

    class Meta:
        model = PurchaseOrderLineItem
        fields = [
            "id", "purchase_order", "description",
            "quantity", "unit_price", "line_total",
            "received_quantity", "asset", "asset_tag",
        ]
        read_only_fields = ["id", "line_total"]


class PurchaseOrderListSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source="vendor.name", read_only=True)
    vendor_code = serializers.CharField(source="vendor.code", read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrder
        fields = [
            "id", "po_number", "vendor", "vendor_name", "vendor_code",
            "status", "order_date", "expected_delivery_date",
            "total_amount", "item_count", "created_at",
        ]

    def get_item_count(self, obj):
        return obj.line_items.count()


class PurchaseOrderDetailSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source="vendor.name", read_only=True)
    line_items = PurchaseOrderLineItemSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(
        source="created_by.get_full_name", read_only=True, default=None,
    )
    approved_by_name = serializers.CharField(
        source="approved_by.get_full_name", read_only=True, default=None,
    )

    class Meta:
        model = PurchaseOrder
        fields = [
            "id", "po_number", "vendor", "vendor_name",
            "status", "description",
            "order_date", "expected_delivery_date", "received_date",
            "subtotal", "tax_amount", "shipping_cost", "total_amount",
            "line_items", "notes",
            "created_by", "created_by_name",
            "approved_by", "approved_by_name",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_by", "approved_by", "created_at", "updated_at"]


class PurchaseOrderCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrder
        fields = [
            "po_number", "vendor", "status", "description",
            "order_date", "expected_delivery_date", "received_date",
            "tax_amount", "shipping_cost", "notes",
        ]

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)
