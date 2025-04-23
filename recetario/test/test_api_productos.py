import pytest

from recetario.utils.test_helpers import setup_create_gramo, setup_create_kilogramo
from users.utils.user_test_helpers import setup_registre_user_generate_token


@pytest.mark.django_db(transaction=True)
def tests_api_productos():
    client, token, user = setup_registre_user_generate_token()
    # Create Unidades
    unidad1 = setup_create_gramo(user)
    unidad2 = setup_create_kilogramo(user)

    # Create Productos
    responseProducto1 = client.post(
        "/recetario/productos/",
        {
            "nombre": "Azúcar",
            "cantidad": 500,
            "unidad": unidad1.id,
        },
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    responseProducto2 = client.post(
        "/recetario/productos/",
        {
            "nombre": "Harina",
            "cantidad": 1000,
            "unidad": unidad2.id,
        },
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert responseProducto1.status_code == 201
    assert responseProducto2.status_code == 201

    # Retrieve Productos
    response = client.get("/recetario/productos/", HTTP_AUTHORIZATION=f"Bearer {token}")
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]["nombre"] == "Azúcar"
    assert response.data[1]["nombre"] == "Harina"

    # Update Producto
    producto1_id = responseProducto1.data["id"]
    client.patch(
        f"/recetario/productos/{producto1_id}/",
        {
            "nombre": "Azúcar Refinada",
            "cantidad": 750,
        },
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    responseProducto1 = client.get(
        f"/recetario/productos/{producto1_id}/", HTTP_AUTHORIZATION=f"Bearer {token}"
    )
    assert responseProducto1.status_code == 200
    assert responseProducto1.data["nombre"] == "Azúcar Refinada"
    assert responseProducto1.data["cantidad"] == 750

    # Delete Producto
    producto2_id = responseProducto2.data["id"]
    client.delete(
        f"/recetario/productos/{producto2_id}/", HTTP_AUTHORIZATION=f"Bearer {token}"
    )

    response = client.get("/recetario/productos/", HTTP_AUTHORIZATION=f"Bearer {token}")
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["nombre"] == "Azúcar Refinada"
