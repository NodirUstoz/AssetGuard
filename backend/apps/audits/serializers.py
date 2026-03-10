"""Serializers for audits app."""
from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    """Read-only serializer for audit log entries."""

    user_display = serializers.SerializerMethodField()
    action_display = serializers.CharField(source="get_action_display", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id", "action", "action_display",
            "entity_type", "entity_id", "entity_name",
            "user", "user_display", "user_email",
            "ip_address", "user_agent",
            "details", "timestamp",
        ]
        read_only_fields = fields

    def get_user_display(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.email
        return obj.user_email or "System"


class AuditLogSummarySerializer(serializers.Serializer):
    """Serializer for audit log summary/statistics."""

    action = serializers.CharField()
    count = serializers.IntegerField()


class EntityAuditSerializer(serializers.Serializer):
    """Serializer for querying audit logs for a specific entity."""

    entity_type = serializers.CharField(required=True)
    entity_id = serializers.CharField(required=True)
