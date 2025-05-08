import pytest

from recetario.models import Producto, Unidad
from users.utils.user_test_helpers import setup_registre_user_generate_token


@pytest.mark.django_db(transaction=True)
def test_productos() -> None:
    _, _, user = setup_registre_user_generate_token()

    unidad = Unidad.objects.create(nombre="Gramos", abreviacion="g", user=user)

    data = [
        {"nombre": "Azúcar", "cantidad": 500, "precio": 1.5},
        {"nombre": "Harina", "cantidad": 1000, "precio": 0.8},
    ]

    for d in data:
        Producto.objects.create(user=user, unidad=unidad, **d)

    productos = Producto.objects.order_by("id")
    assert productos.count() == len(data)

    for i, producto in enumerate(productos):
        expected = data[i]
        assert producto.nombre == expected["nombre"]
        assert producto.cantidad == expected["cantidad"]
        assert producto.unidad == unidad
        assert producto.user == user
        assert str(producto) == expected["nombre"]
        assert producto.precio == expected["precio"]
        assert producto.unidad.nombre == "Gramos"
