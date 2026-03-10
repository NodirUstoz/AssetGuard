"""Admin configuration for accounts app."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Department, Employee, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        "email", "username", "first_name", "last_name",
        "role", "department", "is_active", "last_login",
    ]
    list_filter = ["role", "is_active", "department", "is_staff"]
    search_fields = ["email", "username", "first_name", "last_name"]
    ordering = ["email"]

    fieldsets = BaseUserAdmin.fieldsets + (
        ("AssetGuard Profile", {
            "fields": ("role", "phone", "avatar", "department", "receive_notifications"),
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("AssetGuard Profile", {
            "fields": ("email", "first_name", "last_name", "role", "department"),
        }),
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "manager_name", "cost_center", "is_active", "employee_count"]
    list_filter = ["is_active"]
    search_fields = ["name", "code", "manager_name"]
    ordering = ["name"]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = [
        "employee_id", "full_name", "email", "department",
        "job_title", "status", "is_active", "assigned_assets_count",
    ]
    list_filter = ["status", "is_active", "department"]
    search_fields = ["employee_id", "first_name", "last_name", "email"]
    ordering = ["last_name", "first_name"]
    raw_id_fields = ["user"]
