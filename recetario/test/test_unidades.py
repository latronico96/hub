import pytest

from recetario.models import Unidad
from users.utils.user_test_helpers import setup_registre_user_generate_token


@pytest.mark.django_db(transaction=True)
def test_unidades():
    _, _, user = setup_registre_user_generate_token()

    unidadesDefault = Unidad.objects.count()

    data = [
        {"nombre": "Gramos", "abreviacion": "g"},
        {"nombre": "Kilogramos", "abreviacion": "kg"},
        {"nombre": "Mililitros", "abreviacion": "ml"},
    ]

    unidadesCreadas = []

    for d in data:
        unidad = Unidad.objects.create(user=user, **d)
        unidadesCreadas.append(unidad)

    unidades = Unidad.objects.filter(id__in=[u.id for u in unidadesCreadas]).order_by(
        "id"
    )

    assert unidades.count() == len(data)

    for i, unidad in enumerate(unidades):
        expected = data[i]
        assert unidad.nombre == expected["nombre"]
        assert unidad.abreviacion == expected["abreviacion"]
        assert str(unidad) == expected["nombre"]
        assert unidad.user == user
