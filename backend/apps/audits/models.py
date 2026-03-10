"""Audit models: AuditLog for tracking all system changes."""
import uuid

from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Immutable audit trail for every significant action in the system."""

    class Action(models.TextChoices):
        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"
        CHECK_OUT = "check_out", "Check Out"
        CHECK_IN = "check_in", "Check In"
        ASSIGN = "assign", "Assign"
        UNASSIGN = "unassign", "Unassign"
        LOGIN = "login", "Login"
        EXPORT = "export", "Export"
        IMPORT = "import", "Import"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.CharField(max_length=20, choices=Action.choices)
    entity_type = models.CharField(
        max_length=50,
        help_text="The type of object affected, e.g. asset, license, employee",
    )
    entity_id = models.CharField(max_length=50, help_text="Primary key of the affected object")
    entity_name = models.CharField(max_length=300, blank=True, default="")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    user_email = models.EmailField(blank=True, default="")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True, default="")
    details = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["action"]),
            models.Index(fields=["user", "timestamp"]),
        ]
        verbose_name = "audit log"
        verbose_name_plural = "audit logs"

    def __str__(self):
        user_display = self.user.email if self.user else self.user_email or "System"
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {user_display} {self.action} {self.entity_type} {self.entity_name}"

    def save(self, *args, **kwargs):
        # Auto-populate user_email for persistence even if user is deleted
        if self.user and not self.user_email:
            self.user_email = self.user.email
        super().save(*args, **kwargs)

    @classmethod
    def log(cls, action, entity_type, entity_id, user=None, entity_name="",
            details=None, request=None):
        """Convenience factory method to create an audit log entry."""
        ip_address = None
        user_agent = ""
        if request:
            ip_address = (
                request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
                or request.META.get("REMOTE_ADDR")
            )
            user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]

        return cls.objects.create(
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            entity_name=str(entity_name)[:300],
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
        )
