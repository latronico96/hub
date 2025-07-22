import pytest

import recetario.utils.test_helpers as helpers
from users.utils.user_test_helpers import setup_registre_user_generate_token


@pytest.mark.django_db(transaction=True)
def tests_api_Recetas() -> None:
    client, token, user = setup_registre_user_generate_token()
    unidad1 = helpers.setup_create_gramo(user)
    unidad2 = helpers.setup_create_kilogramo(user)

    productoManzana = helpers.setup_create_manzana(user, unidad1)
    productoHarina = helpers.setup_create_harina(user, unidad2)

    # Create Recetas
    responseReceta1 = client.post(
        "/recetario/recetas/",
        {
            "nombre": "Tarta de Manzana",
            "observaciones": "Deliciosa tarta de manzana",
            "ingredientes": [
                {
                    "productoId": productoManzana.id,
                    "cantidad": 3,
                    "unidadId": productoManzana.unidad.id,
                },
                {
                    "productoId": productoHarina.id,
                    "cantidad": 500,
                    "unidadId": productoHarina.unidad.id,
                },
            ],
            "rinde": 8,
            "precio_unidad": 150.0,
            "precio": 1200.0,
        },
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert responseReceta1.status_code == 201

    # Retrieve Recetas
    response = client.get("/recetario/recetas/", HTTP_AUTHORIZATION=f"Bearer {token}")
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["nombre"] == "Tarta de Manzana"

    # Update Receta
    receta1_id = responseReceta1.data["id"]
    client.patch(
        f"/recetario/recetas/{receta1_id}/",
        {
            "id": receta1_id,
            "nombre": "Tarta de Manzana Actualizada",
            "observaciones": "Tarta de manzana con un toque especial",
            "ingredientes": [
                {
                    "id": responseReceta1.data["ingredientes"][0]["id"],
                    "receta": receta1_id,
                    "productoId": productoManzana.id,
                    "cantidad": 4,
                    "unidadId": productoManzana.unidad.id,
                }
            ],
            "rinde": 10,
            "precio_unidad": 160.0,
            "precio": 1600.0,
        },
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    responseReceta1 = client.get(
        f"/recetario/recetas/{receta1_id}/", HTTP_AUTHORIZATION=f"Bearer {token}"
    )
    assert responseReceta1.status_code == 200
    assert responseReceta1.data["nombre"] == "Tarta de Manzana Actualizada"
    assert len(responseReceta1.data["ingredientes"]) == 1
    assert responseReceta1.data["ingredientes"][0]["cantidad"] == 4

    # Delete Receta
    client.delete(
        f"/recetario/recetas/{receta1_id}/", HTTP_AUTHORIZATION=f"Bearer {token}"
    )

    response = client.get("/recetario/recetas/", HTTP_AUTHORIZATION=f"Bearer {token}")
    assert response.status_code == 200
    assert len(response.data) == 0
