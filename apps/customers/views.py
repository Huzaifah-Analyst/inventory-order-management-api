from drf_spectacular.utils import extend_schema
from rest_framework import filters, viewsets

from .models import Customer
from .serializers import CustomerSerializer


@extend_schema(tags=["Customers"])
class CustomerViewSet(viewsets.ModelViewSet):
    """Full CRUD for customers. Search by name or email."""

    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["full_name", "email", "phone_number"]
    ordering_fields = ["full_name", "email", "created_at"]
    ordering = ["-created_at"]
