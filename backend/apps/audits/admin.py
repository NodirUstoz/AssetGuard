"""Admin configuration for audits app."""
from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Read-only admin for audit logs -- entries should never be modified."""

    list_display = [
        "timestamp", "action", "entity_type",
        "entity_name", "user_email", "ip_address",
    ]
    list_filter = ["action", "entity_type", "timestamp"]
    search_fields = ["entity_name", "entity_id", "user_email", "ip_address"]
    ordering = ["-timestamp"]
    readonly_fields = [
        "id", "action", "entity_type", "entity_id", "entity_name",
        "user", "user_email", "ip_address", "user_agent",
        "details", "timestamp",
    ]
    date_hierarchy = "timestamp"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
