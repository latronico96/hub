import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


@pytest.mark.django_db(transaction=True)
class UserModelTest(TestCase):
    def test_create_user(self):
        # Arrange
        User = get_user_model()
        user = User.objects.create_user(
            last_name="apellido",
            first_name="nombre",
            email="test@example.com",
            password="password123",
        )

        # Act & Assert
        self.assertEqual(user.first_name, "nombre")
        self.assertEqual(user.last_name, "apellido")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("password123"))

    def test_registre_user(self):
        """Testea el registro de un usuario a través de la API."""

        client = APIClient()
        responseRegister = client.post(
            "/users/register/",
            {
                "first_name": "nombre",
                "last_name": "apellido",
                "email": "test@email.com",
                "password": "testpassword",
            },
            format="json",
        )

        assert (
            responseRegister.status_code == 201
        ), f"Registration failed: {responseRegister.content}"
        assert responseRegister.data["detail"] == "User created successfully"
        assert responseRegister.data["user"]["email"] == "test@email.com"
        assert responseRegister.data["user"]["first_name"] == "nombre"
        assert responseRegister.data["user"]["last_name"] == "apellido"
        assert responseRegister.data["user"]["id"] is not None
        assert "password" not in responseRegister.data["user"]

    def test_login_user(self):
        """Testea el inicio de sesión de un usuario a través de la API."""

        client = APIClient()
        # Primero, registramos un usuario para poder iniciar sesión
        client.post(
            "/users/register/",
            {
                "first_name": "nombre",
                "last_name": "apellido",
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

        print(responseLogin)

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
            "/users/user/",
        )

        assert (
            responseUserApi.status_code == 403
        ), f"User API failed: {responseUserApi.content}"
