"""AssetGuard URL Configuration."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)

urlpatterns = [
    path("api/admin/", admin.site.urls),
    # Authentication
    path("api/auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/logout/", TokenBlacklistView.as_view(), name="token_blacklist"),
    # App URLs
    path("api/accounts/", include("apps.accounts.urls")),
    path("api/assets/", include("apps.assets.urls")),
    path("api/licenses/", include("apps.licenses.urls")),
    path("api/maintenance/", include("apps.maintenance.urls")),
    path("api/depreciation/", include("apps.depreciation.urls")),
    path("api/audits/", include("apps.audits.urls")),
    path("api/reports/", include("apps.reports.urls")),
    path("api/vendors/", include("apps.vendors.urls")),
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    try:
        import debug_toolbar
        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass

admin.site.site_header = "AssetGuard Administration"
admin.site.site_title = "AssetGuard Admin"
admin.site.index_title = "IT Asset Management"
