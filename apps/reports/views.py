from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from drf_spectacular.utils import extend_schema

from apps.orders.models import Order, OrderItem


class TopProductSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    product_sku = serializers.CharField()
    total_quantity_sold = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)


@extend_schema(
    tags=["Reports"],
    summary="Top 5 best-selling products",
    description=(
        "Returns the top 5 products by total quantity sold across all **COMPLETED** orders, "
        "along with total revenue generated per product."
    ),
    responses={200: TopProductSerializer(many=True)},
)
class TopProductsView(APIView):
    """GET /api/reports/top-products/"""

    def get(self, request):
        top_products = (
            OrderItem.objects.filter(order__status=Order.Status.COMPLETED)
            .values(
                product_id=F("product__id"),
                product_name=F("product__name"),
                product_sku=F("product__sku"),
            )
            .annotate(
                total_quantity_sold=Sum("quantity"),
                total_revenue=Sum(
                    ExpressionWrapper(
                        F("quantity") * F("price_at_purchase"),
                        output_field=DecimalField(max_digits=14, decimal_places=2),
                    )
                ),
            )
            .order_by("-total_quantity_sold")[:5]
        )

        serializer = TopProductSerializer(top_products, many=True)
        return Response(
            {
                "count": len(serializer.data),
                "results": serializer.data,
            }
        )
