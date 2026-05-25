import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tests.factories import UserFactory, ProductFactory, CustomerFactory, OrderFactory, OrderItemFactory
from apps.orders.models import Order
from apps.products.models import Product


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
class TestOrderCreation:
    def test_create_order_success(self, auth_client):
        customer = CustomerFactory()
        product = ProductFactory(price=Decimal("20.00"), stock_quantity=50)

        payload = {
            "customer": customer.id,
            "items": [{"product": product.id, "quantity": 3}],
        }
        response = auth_client.post(reverse("order-list"), payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert float(response.data["total_amount"]) == 60.00
        assert len(response.data["items"]) == 1

    def test_create_order_total_calculated_correctly(self, auth_client):
        customer = CustomerFactory()
        p1 = ProductFactory(price=Decimal("10.00"), stock_quantity=50)
        p2 = ProductFactory(price=Decimal("25.00"), stock_quantity=50)

        payload = {
            "customer": customer.id,
            "items": [
                {"product": p1.id, "quantity": 2},
                {"product": p2.id, "quantity": 4},
            ],
        }
        response = auth_client.post(reverse("order-list"), payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        # 2*10 + 4*25 = 20 + 100 = 120
        assert float(response.data["total_amount"]) == 120.00

    def test_create_order_insufficient_stock(self, auth_client):
        customer = CustomerFactory()
        product = ProductFactory(stock_quantity=5)

        payload = {
            "customer": customer.id,
            "items": [{"product": product.id, "quantity": 10}],
        }
        response = auth_client.post(reverse("order-list"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_order_zero_stock(self, auth_client):
        customer = CustomerFactory()
        product = ProductFactory(stock_quantity=0)

        payload = {
            "customer": customer.id,
            "items": [{"product": product.id, "quantity": 1}],
        }
        response = auth_client.post(reverse("order-list"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_order_duplicate_products_rejected(self, auth_client):
        customer = CustomerFactory()
        product = ProductFactory(stock_quantity=50)

        payload = {
            "customer": customer.id,
            "items": [
                {"product": product.id, "quantity": 1},
                {"product": product.id, "quantity": 2},
            ],
        }
        response = auth_client.post(reverse("order-list"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_order_empty_items_rejected(self, auth_client):
        customer = CustomerFactory()
        payload = {"customer": customer.id, "items": []}
        response = auth_client.post(reverse("order-list"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestOrderStatusTransitions:
    def test_pending_to_processing(self, auth_client):
        order = OrderFactory(status=Order.Status.PENDING)
        url = reverse("order-update-status", kwargs={"pk": order.pk})
        response = auth_client.patch(url, {"status": "PROCESSING"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        order.refresh_from_db()
        assert order.status == Order.Status.PROCESSING

    def test_completed_deducts_stock(self, auth_client):
        product = ProductFactory(stock_quantity=20)
        order = OrderFactory(status=Order.Status.PROCESSING)
        OrderItemFactory(order=order, product=product, quantity=5, price_at_purchase=product.price)

        url = reverse("order-update-status", kwargs={"pk": order.pk})
        response = auth_client.patch(url, {"status": "COMPLETED"}, format="json")
        assert response.status_code == status.HTTP_200_OK

        product.refresh_from_db()
        assert product.stock_quantity == 15

    def test_invalid_status_transition(self, auth_client):
        order = OrderFactory(status=Order.Status.COMPLETED)
        url = reverse("order-update-status", kwargs={"pk": order.pk})
        response = auth_client.patch(url, {"status": "PENDING"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cancelled_order_no_stock_deduction(self, auth_client):
        product = ProductFactory(stock_quantity=20)
        order = OrderFactory(status=Order.Status.PENDING)
        OrderItemFactory(order=order, product=product, quantity=5, price_at_purchase=product.price)

        url = reverse("order-update-status", kwargs={"pk": order.pk})
        auth_client.patch(url, {"status": "CANCELLED"}, format="json")

        product.refresh_from_db()
        assert product.stock_quantity == 20  # unchanged


@pytest.mark.django_db
class TestOrderList:
    def test_list_orders(self, auth_client):
        OrderFactory.create_batch(3)
        response = auth_client.get(reverse("order-list"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3

    def test_filter_by_status(self, auth_client):
        OrderFactory(status=Order.Status.PENDING)
        OrderFactory(status=Order.Status.COMPLETED)
        OrderFactory(status=Order.Status.COMPLETED)

        response = auth_client.get(reverse("order-list"), {"status": "COMPLETED"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
