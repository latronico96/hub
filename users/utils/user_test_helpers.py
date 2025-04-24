from rest_framework.test import APIClient

from users.models import User


def setup_registre_user_generate_token() -> tuple[APIClient, str, User]:
    user = User.objects.create_user(
        name="user name",
        password="testpassword",
        email="test@email.com",
    )

    client = APIClient()
    responseLogin = client.post(
        "/users/login/",
        {"email": "test@email.com", "password": "testpassword"},
        format="json",
    )

    assert responseLogin.status_code == 200, f"Login failed: {responseLogin.content}"
    token = responseLogin.data.get("token")
    assert token, "Token not returned in login response"

    return client, token, user
