"""Views for accounts app."""
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Department, Employee
from .serializers import (
    ChangePasswordSerializer,
    DepartmentSerializer,
    EmployeeSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)

User = get_user_model()


class IsAdminOrManager(permissions.BasePermission):
    """Allow access to admin and manager roles only."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_manager


class DepartmentViewSet(viewsets.ModelViewSet):
    """CRUD operations for departments."""

    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    search_fields = ["name", "code", "description"]
    ordering_fields = ["name", "code", "created_at"]
    filterset_fields = ["is_active"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.IsAuthenticated()]
        return [IsAdminOrManager()]


class UserViewSet(viewsets.ModelViewSet):
    """CRUD operations for users."""

    queryset = User.objects.select_related("department").all()
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering_fields = ["username", "email", "created_at", "last_login"]
    filterset_fields = ["role", "is_active", "department"]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ["me", "change_password"]:
            return [permissions.IsAuthenticated()]
        return [IsAdminOrManager()]

    @action(detail=False, methods=["get", "patch"])
    def me(self, request):
        """Get or update the current user's profile."""
        if request.method == "GET":
            serializer = UserSerializer(request.user)
            return Response(serializer.data)

        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)

    @action(detail=False, methods=["post"])
    def change_password(self, request):
        """Change the current user's password."""
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response({"detail": "Password changed successfully."}, status=status.HTTP_200_OK)


class EmployeeViewSet(viewsets.ModelViewSet):
    """CRUD operations for employees."""

    queryset = Employee.objects.select_related("department", "user").all()
    serializer_class = EmployeeSerializer
    search_fields = ["employee_id", "first_name", "last_name", "email", "job_title"]
    ordering_fields = ["last_name", "employee_id", "hire_date", "created_at"]
    filterset_fields = ["department", "status", "is_active", "location"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.IsAuthenticated()]
        return [IsAdminOrManager()]
