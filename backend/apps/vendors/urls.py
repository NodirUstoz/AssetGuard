"""URL configuration for vendors app."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    PurchaseOrderLineItemViewSet,
    PurchaseOrderViewSet,
    VendorContactViewSet,
    VendorViewSet,
)

router = DefaultRouter()
router.register(r"contacts", VendorContactViewSet, basename="vendor-contact")
router.register(r"purchase-orders/line-items", PurchaseOrderLineItemViewSet, basename="po-line-item")
router.register(r"purchase-orders", PurchaseOrderViewSet, basename="purchase-order")
router.register(r"", VendorViewSet, basename="vendor")

urlpatterns = [
    path("", include(router.urls)),
]
