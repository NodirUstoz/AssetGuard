"""Serializers for accounts app."""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Department, Employee

User = get_user_model()


class DepartmentSerializer(serializers.ModelSerializer):
    employee_count = serializers.ReadOnlyField()
    asset_count = serializers.ReadOnlyField()

    class Meta:
        model = Department
        fields = [
            "id", "name", "code", "description",
            "manager_name", "manager_email", "cost_center",
            "is_active", "employee_count", "asset_count",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class UserSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True, default=None)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "full_name", "role", "phone", "avatar", "department",
            "department_name", "receive_notifications", "is_active",
            "last_login", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "last_login", "created_at", "updated_at"]
        extra_kwargs = {
            "password": {"write_only": True, "required": False},
        }

    def get_full_name(self, obj):
        return obj.get_full_name()


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=10)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "password", "password_confirm", "role", "phone",
            "department", "receive_notifications",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "first_name", "last_name", "phone", "role",
            "department", "receive_notifications", "is_active",
        ]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=10)
    new_password_confirm = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})
        return attrs

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value


class EmployeeSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    assigned_assets_count = serializers.ReadOnlyField()
    department_name = serializers.CharField(source="department.name", read_only=True, default=None)

    class Meta:
        model = Employee
        fields = [
            "id", "user", "employee_id", "first_name", "last_name",
            "full_name", "email", "phone", "job_title", "department",
            "department_name", "location", "hire_date", "status",
            "is_active", "assigned_assets_count", "notes",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class EmployeeMinimalSerializer(serializers.ModelSerializer):
    """Minimal employee serializer for use in nested representations."""

    full_name = serializers.ReadOnlyField()

    class Meta:
        model = Employee
        fields = ["id", "employee_id", "full_name", "email", "department"]
