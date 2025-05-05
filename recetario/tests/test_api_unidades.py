import pytest

from users.utils.user_test_helpers import setup_registre_user_generate_token


@pytest.mark.django_db()
def test_api_unidades() -> None:
    client, token, _ = setup_registre_user_generate_token()

    responseUnidad1 = client.post(
        "/recetario/unidades/",
        {
            "nombre": "Gramos",
            "abreviacion": "g",
        },
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert responseUnidad1.status_code == 201

    responseUnidad2 = client.post(
        "/recetario/unidades/",
        {
            "nombre": "Kilogramos",
            "abreviacion": "kg",
        },
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert responseUnidad2.status_code == 201

    responseUnidad3 = client.post(
        "/recetario/unidades/",
        {
            "nombre": "Mililitros",
            "abreviacion": "ml",
        },
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert responseUnidad3.status_code == 201

    response = client.get("/recetario/unidades/", HTTP_AUTHORIZATION=f"Bearer {token}")

    assert response.status_code == 200
    assert len(response.data) == 8  # 5 por defecto + 3 creadas en el test

    unidad1_id = responseUnidad1.data["id"]
    unidad3_id = responseUnidad3.data["id"]

    responseDelete = client.delete(
        "/recetario/unidades/" + str(unidad3_id) + "/",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert responseDelete.status_code == 204

    response = client.get("/recetario/unidades/", HTTP_AUTHORIZATION=f"Bearer {token}")

    assert response.status_code == 200
    assert len(response.data) == 7

    responsePathUnidad1 = client.patch(
        f"/recetario/unidades/{unidad1_id}/",
        {
            "nombre": "Gramos 2",
            "abreviacion": "G",
        },
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert responsePathUnidad1.status_code == 200

    responseUnidad1 = client.get(
        "/recetario/unidades/" + str(unidad1_id) + "/",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert responseUnidad1.status_code == 200
    assert responseUnidad1.data["nombre"] == "Gramos 2"
    assert responseUnidad1.data["abreviacion"] == "G"
    assert responseUnidad1.data["id"] == unidad1_id
