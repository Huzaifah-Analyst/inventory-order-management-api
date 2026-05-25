from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from .models import Product
from .serializers import ProductSerializer


@extend_schema(tags=["Products"])
class ProductViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for products.

    - **Search**: `?search=<name_or_sku>`
    - **Ordering**: `?ordering=price` or `?ordering=-created_at`
    - **Pagination**: `?page=1&page_size=10`
    """

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "sku"]
    ordering_fields = ["name", "price", "stock_quantity", "created_at"]
    ordering = ["-created_at"]
