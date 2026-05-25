from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Order
from .serializers import OrderCreateSerializer, OrderReadSerializer, OrderStatusUpdateSerializer


@extend_schema(tags=["Orders"])
class OrderViewSet(viewsets.ModelViewSet):
    """
    Order lifecycle management.

    - **Create** an order with items — stock is validated at creation time.
    - **Update status** via PATCH — stock is deducted when status reaches COMPLETED.
    - Status transitions: PENDING → PROCESSING → COMPLETED | CANCELLED
    """

    queryset = Order.objects.select_related("customer").prefetch_related("items__product").all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "customer"]
    ordering_fields = ["created_at", "total_amount", "status"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        if self.action in ("update", "partial_update"):
            return OrderStatusUpdateSerializer
        return OrderReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        read_serializer = OrderReadSerializer(order, context={"request": request})
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True  # Always patch — only status is updatable
        return super().update(request, *args, **kwargs)

    # Convenience endpoint: PATCH /orders/{id}/status/
    @extend_schema(request=OrderStatusUpdateSerializer, responses=OrderReadSerializer)
    @action(detail=True, methods=["patch"], url_path="status")
    def update_status(self, request, pk=None):
        """Shortcut endpoint to update order status only."""
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        return Response(OrderReadSerializer(updated).data)
