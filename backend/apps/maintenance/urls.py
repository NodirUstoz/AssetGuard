"""URL configuration for maintenance app."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    MaintenanceLogViewSet,
    MaintenanceScheduleViewSet,
    WarrantyViewSet,
)

router = DefaultRouter()
router.register(r"schedules", MaintenanceScheduleViewSet, basename="maintenance-schedule")
router.register(r"logs", MaintenanceLogViewSet, basename="maintenance-log")
router.register(r"warranties", WarrantyViewSet, basename="warranty")

urlpatterns = [
    path("", include(router.urls)),
]
