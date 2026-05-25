from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path("admin/", admin.site.urls),

    # API schema & docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # App routes
    path("api/auth/", include("apps.accounts.urls")),
    path("api/products/", include("apps.products.urls")),
    path("api/customers/", include("apps.customers.urls")),
    path("api/orders/", include("apps.orders.urls")),
    path("api/reports/", include("apps.reports.urls")),

    # Health check
    path("api/health/", include("core.urls")),
]
