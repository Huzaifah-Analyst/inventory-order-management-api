import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tests.factories import UserFactory, ProductFactory, CustomerFactory, OrderFactory, OrderItemFactory
from apps.orders.models import Order


@pytest.fixture
def auth_client():
    client = APIClient()
    user = UserFactory()
    resp = client.post(
        reverse("auth-login"),
        {"username": user.username, "password": "TestPass123!"},
        format="json",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
    return client


@pytest.mark.django_db
class TestTopProductsReport:
    def test_returns_top_5_products(self, auth_client):
        # Create 7 products with varying sales volumes
        products = [ProductFactory(price=Decimal("10.00"), stock_quantity=200) for _ in range(7)]
        order = OrderFactory(status=Order.Status.COMPLETED)

        for i, product in enumerate(products):
            OrderItemFactory(
                order=order,
                product=product,
                quantity=(i + 1) * 10,  # 10, 20, 30, ..., 70
                price_at_purchase=product.price,
            )

        response = auth_client.get(reverse("report-top-products"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 5
        results = response.data["results"]
        assert len(results) == 5

        # Verify descending order by quantity
        quantities = [r["total_quantity_sold"] for r in results]
        assert quantities == sorted(quantities, reverse=True)

    def test_only_counts_completed_orders(self, auth_client):
        product = ProductFactory(price=Decimal("10.00"), stock_quantity=100)

        # Pending order — should NOT be counted
        pending_order = OrderFactory(status=Order.Status.PENDING)
        OrderItemFactory(order=pending_order, product=product, quantity=50, price_at_purchase=product.price)

        # Completed order — SHOULD be counted
        completed_order = OrderFactory(status=Order.Status.COMPLETED)
        OrderItemFactory(order=completed_order, product=product, quantity=30, price_at_purchase=product.price)

        response = auth_client.get(reverse("report-top-products"))
        assert response.status_code == status.HTTP_200_OK
        result = response.data["results"][0]
        assert result["total_quantity_sold"] == 30  # only completed counts

    def test_revenue_calculation(self, auth_client):
        product = ProductFactory(price=Decimal("15.00"), stock_quantity=100)
        order = OrderFactory(status=Order.Status.COMPLETED)
        OrderItemFactory(order=order, product=product, quantity=4, price_at_purchase=Decimal("15.00"))

        response = auth_client.get(reverse("report-top-products"))
        assert response.status_code == status.HTTP_200_OK
        result = response.data["results"][0]
        assert float(result["total_revenue"]) == 60.00  # 4 * 15.00

    def test_empty_report_when_no_completed_orders(self, auth_client):
        product = ProductFactory(stock_quantity=50)
        order = OrderFactory(status=Order.Status.PENDING)
        OrderItemFactory(order=order, product=product, quantity=10, price_at_purchase=product.price)

        response = auth_client.get(reverse("report-top-products"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0
        assert response.data["results"] == []
