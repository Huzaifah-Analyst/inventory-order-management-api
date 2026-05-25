import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tests.factories import UserFactory, ProductFactory


@pytest.fixture
def api_client():
    return APIClient()


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
class TestProductCRUD:
    def test_list_products(self, auth_client):
        ProductFactory.create_batch(5)
        response = auth_client.get(reverse("product-list"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 5

    def test_create_product(self, auth_client):
        payload = {
            "name": "Test Widget",
            "sku": "TW-001",
            "description": "A test widget",
            "price": "49.99",
            "stock_quantity": 100,
        }
        response = auth_client.post(reverse("product-list"), payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["sku"] == "TW-001"
        assert float(response.data["price"]) == 49.99

    def test_create_duplicate_sku(self, auth_client):
        ProductFactory(sku="DUP-001")
        payload = {"name": "Dup", "sku": "DUP-001", "price": "10.00", "stock_quantity": 5}
        response = auth_client.post(reverse("product-list"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_product(self, auth_client):
        product = ProductFactory(price="10.00")
        url = reverse("product-detail", kwargs={"pk": product.pk})
        response = auth_client.patch(url, {"price": "25.00"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert float(response.data["price"]) == 25.00

    def test_delete_product(self, auth_client):
        product = ProductFactory()
        url = reverse("product-detail", kwargs={"pk": product.pk})
        response = auth_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_retrieve_product(self, auth_client):
        product = ProductFactory()
        url = reverse("product-detail", kwargs={"pk": product.pk})
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == product.id


@pytest.mark.django_db
class TestProductValidation:
    def test_negative_price_rejected(self, auth_client):
        payload = {"name": "Bad", "sku": "BAD-001", "price": "-5.00", "stock_quantity": 10}
        response = auth_client.post(reverse("product-list"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_negative_stock_rejected(self, auth_client):
        payload = {"name": "Bad", "sku": "BAD-002", "price": "5.00", "stock_quantity": -1}
        response = auth_client.post(reverse("product-list"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestProductSearch:
    def test_search_by_name(self, auth_client):
        ProductFactory(name="Alpha Widget")
        ProductFactory(name="Beta Gadget")
        response = auth_client.get(reverse("product-list"), {"search": "Alpha"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["name"] == "Alpha Widget"

    def test_search_by_sku(self, auth_client):
        ProductFactory(sku="FIND-ME-001")
        ProductFactory(sku="OTHER-002")
        response = auth_client.get(reverse("product-list"), {"search": "FIND-ME"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_pagination(self, auth_client):
        ProductFactory.create_batch(15)
        response = auth_client.get(reverse("product-list"), {"page_size": 5})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 5
        assert response.data["total_pages"] == 3
