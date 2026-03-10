"""URL configuration for assets app."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AssetAssignmentViewSet,
    AssetCategoryViewSet,
    AssetTypeViewSet,
    AssetViewSet,
)

router = DefaultRouter()
router.register(r"categories", AssetCategoryViewSet, basename="asset-category")
router.register(r"types", AssetTypeViewSet, basename="asset-type")
router.register(r"assignments", AssetAssignmentViewSet, basename="asset-assignment")
router.register(r"", AssetViewSet, basename="asset")

urlpatterns = [
    path("", include(router.urls)),
]
