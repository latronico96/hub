import pytest

from users.utils.user_test_helpers import setup_registre_user_generate_token


@pytest.mark.django_db(transaction=True)
def test_api_unidades():
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

    client.post(
        "/recetario/unidades/",
        {
            "nombre": "Kilogramos",
            "abreviacion": "kg",
        },
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    responseUnidad3 = client.post(
        "/recetario/unidades/",
        {
            "nombre": "Mililitros",
            "abreviacion": "ml",
        },
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    response = client.get("/recetario/unidades/", HTTP_AUTHORIZATION=f"Bearer {token}")

    assert response.status_code == 200
    assert len(response.data) == 3
    assert response.data[0]["nombre"] == "Gramos"

    unidad1_id = responseUnidad1.data["id"]
    unidad3_id = responseUnidad3.data["id"]

    client.delete(
        "/recetario/unidades/" + str(unidad3_id) + "/",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    response = client.get("/recetario/unidades/", HTTP_AUTHORIZATION=f"Bearer {token}")

    assert response.status_code == 200
    assert len(response.data) == 2

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
