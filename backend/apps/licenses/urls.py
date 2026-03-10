"""URL configuration for licenses app."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    LicenseAssignmentViewSet,
    LicenseRenewalViewSet,
    SoftwareLicenseViewSet,
)

router = DefaultRouter()
router.register(r"assignments", LicenseAssignmentViewSet, basename="license-assignment")
router.register(r"renewals", LicenseRenewalViewSet, basename="license-renewal")
router.register(r"", SoftwareLicenseViewSet, basename="license")

urlpatterns = [
    path("", include(router.urls)),
]
