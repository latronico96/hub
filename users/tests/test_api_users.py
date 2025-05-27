import re

import pytest
from django.core import mail
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
        email = mail.outbox
        assert len(email) == 1, "Email not sent"
        assert (
            email[0].subject == "Bienvenido a Recetario COCOL"
        ), "Email subject mismatch"
        assert email[0].to == ["test@email.com"], "Email recipient mismatch"

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

    def test_change_password(self) -> None:
        """Testea el cambio de contraseña de un usuario a través de la API."""

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

        # Obtener el id del usuario recién creado
        from users.models import User

        user = User.objects.get(email="test@email.com")

        responseGenerateEmail = client.post(
            "/users/forgot-password/",
            {"userId": user.id},
            format="json",
        )
        assert (
            responseGenerateEmail.status_code == 200
        ), f"Generate email failed: {responseGenerateEmail.content}"
        assert (
            responseGenerateEmail.data["detail"] is not None
        ), "Detail not returned in generate email response"

        assert (
            responseGenerateEmail.data["detail"]
            == "Si el correo existe, se ha enviado un email de recuperación."
        ), "Detail not returned in generate email response"

        email = mail.outbox
        assert len(email) == 2, "Email not sent"
        assert (
            email[0].subject == "Bienvenido a Recetario COCOL"
        ), "Email subject mismatch"
        assert email[0].to == ["test@email.com"], "Email recipient mismatch"

        email_body: str = str(email[1].body)
        token = self.extraer_token_del_email(email_body)
        assert token is not None, "Token not found in email body"

        response_change_password = client.post(
            "/users/reset-password/",
            {
                "token": token,
                "password": "newpassword",
            },
            format="json",
        )
        assert (
            response_change_password.status_code == 200
        ), f"Change password failed: {response_change_password.content}"
        assert (
            response_change_password.data["detail"] is not None
        ), "Detail not returned in change password response"

        response_login = client.post(
            "/users/login/",
            {"email": "test@email.com", "password": "newpassword"},
        )

        assert (
            response_login.status_code == 200
        ), f"Login failed: {response_login.content}"
        assert (
            response_login.data["token"] is not None
        ), "Token not returned in login response"

    def extraer_token_del_email(self, cuerpo_html: str) -> str:
        match = re.search(r"token=([\w\-._~+/]+=*)", cuerpo_html)
        if match:
            return match.group(1)
        raise ValueError("Token no encontrado en el email.")

    def test_duplicate_email_registration(self) -> None:
        """Testea el registro de un usuario con un email ya existente."""

        client = APIClient()
        # Primero, registramos un usuario
        client.post(
            "/users/register/",
            {
                "name": "user name",
                "email": "test@email.com",
                "password": "testpassword",
            },
            format="json",
        )

        responseRegister = client.post(
            "/users/register/",
            {
                "name": "user name 2",
                "email": "test@email.com",
                "password": "testpassword2",
            },
            format="json",
        )

        assert (
            responseRegister.status_code == 400
        ), f"Login failed: {responseRegister.content}"
        assert (
            responseRegister.data["detail"] == "Email already exists."
        ), "Detail not returned in login response"

    def test_no_email_registration(self) -> None:
        """Testea el registro de un usuario sin email."""

        client = APIClient()
        responseRegister = client.post(
            "/users/register/",
            {
                "name": "user name",
                "password": "testpassword",
            },
            format="json",
        )

        assert (
            responseRegister.status_code == 400
        ), f"Login failed: {responseRegister.content}"
        assert (
            responseRegister.data["detail"]
            == "Username, email, and password are required."
        ), "Detail not returned in login response"

    def test_no_email_login(self) -> None:
        """Testea el registro de un usuario sin email."""

        client = APIClient()
        responseRegister = client.post(
            "/users/login/",
            {
                "password": "testpassword",
            },
            format="json",
        )

        assert (
            responseRegister.status_code == 400
        ), f"Login failed: {responseRegister.content}"
        assert (
            responseRegister.data["error"] == "Email and password are required"
        ), "Detail not returned in login response"

    def test_me_api(self) -> None:
        """Testea el acceso a la API de usuario."""

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

        responseMeApiNoAuth = client.get(
            "/users/me/",
        )
        assert (
            responseMeApiNoAuth.status_code == 403
        ), f"User API failed: {responseMeApiNoAuth.content}"

        # Luego, intentamos iniciar sesión con las mismas credenciales
        responseLogin = client.post(
            "/users/login/",
            {
                "email": "test@email.com",
                "password": "testpassword",
            },
            format="json",
        )
        assert (
            responseLogin.status_code == 200
        ), f"Login failed: {responseLogin.content}"
        assert (
            responseLogin.data["token"] is not None
        ), "Token not returned in login response"
        token = responseLogin.data["token"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        responseUserApi = client.get(
            "/users/me/",
        )
        assert (
            responseUserApi.status_code == 200
        ), f"User API failed: {responseUserApi.content}"
        assert (
            responseUserApi.data["email"] == "test@email.com"
        ), "Email not returned in user API response"

    def test_change_password_invalid_token(self) -> None:
        """Testea el cambio de contraseña con un token inválido."""

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
        # Luego, intentamos cambiar la contraseña con un token inválido
        response_change_password = client.post(
            "/users/reset-password/",
            {
                "token": "invalid_token",
                "password": "newpassword",
            },
            format="json",
        )
        assert (
            response_change_password.status_code == 400
        ), f"Change password failed: {response_change_password.content}"
        assert (
            response_change_password.data["detail"] == "Invalid token."
        ), "Detail not returned in change password response"
