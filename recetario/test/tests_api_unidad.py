import pytest
from rest_framework.test import APIClient

from recetario.models import Unidad
from users.models import User


@pytest.mark.django_db(transaction=True)
def test_list_unidades():
    user = User.objects.create_user(
        last_name="testuser",
        password="testpassword",
        email="test@email.com",
        first_name="Test",
    )

    Unidad.objects.create(nombre="Gramos", abreviacion="g", user=user)
    Unidad.objects.create(nombre="Kilogramos", abreviacion="kg", user=user)
    Unidad.objects.create(nombre="Mililitros", abreviacion="ml", user=user)

    client = APIClient()
    responseLogin = client.post(
        "/users/login/",
        {"email": "test@email.com", "password": "testpassword"},
        format="json",
    )

    assert responseLogin.status_code == 200, f"Login failed: {responseLogin.content}"
    token = responseLogin.data.get("token")
    assert token, "Token not returned in login response"

    response = client.get("/recetario/unidades/", HTTP_AUTHORIZATION=f"Bearer {token}")

    assert response.status_code == 200
    assert len(response.data) == 3
    assert response.data[0]["nombre"] == "Gramos"
