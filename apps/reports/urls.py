from django.urls import path

from .views import TopProductsView

urlpatterns = [
    path("top-products/", TopProductsView.as_view(), name="report-top-products"),
]
