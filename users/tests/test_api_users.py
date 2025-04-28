import pytest
from django.test import TestCase
from rest_framework.test import APIClient


@pytest.mark.django_db(transaction=True)
class UserModelTest(TestCase):
    def test_registre_user(self) -> None:
        """Testea el registro de un usuario a través de la API."""

        client = APIClient()
        responseRegister = client.post(
            "/users/register/",
            {
                "name": "user name",
                "email": "test@email.com",
                "password": "testpassword",
            },
            format="json",
        )

        assert (
            responseRegister.status_code == 200
        ), f"Login failed: {responseRegister.content}"
        assert (
            responseRegister.data["token"] is not None
        ), "Token not returned in login response"

    def test_login_user(self) -> None:
        """Testea el inicio de sesión de un usuario a través de la API."""

        client = APIClient()
        # Primero, registramos un usuario para poder iniciar sesión
        client.post(
            "/users/register/",
            {
                "name": "user name",
                "email": "test@email.com",
                "password": "testpassword",
            },
            format="json",
        )
        # Luego, intentamos iniciar sesión con las mismas credenciales
        responseLogin = client.post(
            "/users/login/",
            {"email": "test@email.com", "password": "fakePassword"},
        )

        assert (
            responseLogin.status_code == 403
        ), f"Login should fail with wrong password: {responseLogin.content}"
        assert responseLogin.data["detail"] == "Invalid credentials"

        responseLogin = client.post(
            "/users/login/",
            {"email": "test@email.com", "password": "testpassword"},
        )

        assert (
            responseLogin.status_code == 200
        ), f"Login failed: {responseLogin.content}"
        assert (
            responseLogin.data["token"] is not None
        ), "Token not returned in login response"

        responseUserApi = client.get(
            "/users/",
        )

        assert (
            responseUserApi.status_code == 403
        ), f"User API failed: {responseUserApi.content}"
