"""URL configuration for depreciation app."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DepreciationEntryViewSet, DepreciationScheduleViewSet

router = DefaultRouter()
router.register(r"entries", DepreciationEntryViewSet, basename="depreciation-entry")
router.register(r"", DepreciationScheduleViewSet, basename="depreciation-schedule")

urlpatterns = [
    path("", include(router.urls)),
]
