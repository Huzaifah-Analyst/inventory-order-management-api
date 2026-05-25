import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tests.factories import UserFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(api_client):
    user = UserFactory()
    response = api_client.post(
        reverse("auth-login"),
        {"username": user.username, "password": "TestPass123!"},
        format="json",
    )
    token = response.data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@pytest.mark.django_db
class TestRegistration:
    def test_register_success(self, api_client):
        payload = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        }
        response = api_client.post(reverse("auth-register"), payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True
        assert "user" in response.data

    def test_register_password_mismatch(self, api_client):
        payload = {
            "username": "user2",
            "email": "user2@example.com",
            "password": "SecurePass123!",
            "password_confirm": "WrongPass!",
        }
        response = api_client.post(reverse("auth-register"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_duplicate_email(self, api_client):
        UserFactory(email="taken@example.com")
        payload = {
            "username": "anotheruser",
            "email": "taken@example.com",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        }
        response = api_client.post(reverse("auth-register"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLogin:
    def test_login_success(self, api_client):
        user = UserFactory()
        response = api_client.post(
            reverse("auth-login"),
            {"username": user.username, "password": "TestPass123!"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert "user" in response.data

    def test_login_invalid_credentials(self, api_client):
        response = api_client.post(
            reverse("auth-login"),
            {"username": "nobody", "password": "wrong"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_protected_endpoint_without_token(self, api_client):
        response = api_client.get(reverse("product-list"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
