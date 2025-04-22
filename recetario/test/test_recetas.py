import pytest

from recetario.models import Ingrediente, Producto, Receta, Unidad
from users.utils.user_test_helpers import setup_registre_user_generate_token


@pytest.mark.django_db(transaction=True)
def test_recetas():
    _, _, user = setup_registre_user_generate_token()

    # Create Unidad and Producto
    unidad = Unidad.objects.create(nombre="Gramos", abreviacion="g", user=user)
    producto = Producto.objects.create(
        nombre="Azúcar", cantidad=500, unidad=unidad, user=user
    )

    # Create Receta with Ingredientes
    receta = Receta.objects.create(nombre="Torta", user=user)
    ingrediente = Ingrediente.objects.create(
        cantidad=200, unidad=unidad, producto=producto, receta=receta, user=user
    )

    # Assertions for Receta
    assert receta.nombre == "Torta"
    assert receta.user == user
    assert receta.ingredientes.count() == 1

    # Assertions for Ingrediente
    assert ingrediente.cantidad == 200
    assert ingrediente.unidad == unidad
    assert ingrediente.producto == producto
    assert ingrediente.receta == receta
    assert ingrediente.user == user


@pytest.mark.django_db(transaction=True)
def test_recetas_with_ingredientes():
    _, _, user = setup_registre_user_generate_token()

    unidad = Unidad.objects.create(nombre="Gramos", abreviacion="g", user=user)
    receta = Receta.objects.create(nombre="Torta", user=user)

    ingredientes_data = [
        {
            "producto": Producto.objects.create(
                nombre="Azúcar", cantidad=500, unidad=unidad, user=user
            ),
            "cantidad": 200,
        },
        {
            "producto": Producto.objects.create(
                nombre="Harina", cantidad=1000, unidad=unidad, user=user
            ),
            "cantidad": 300,
        },
    ]

    for data in ingredientes_data:
        Ingrediente.objects.create(receta=receta, user=user, unidad=unidad, **data)

    ingredientes = Ingrediente.objects.filter(receta=receta).order_by("id")
    assert ingredientes.count() == len(ingredientes_data)

    for i, ingrediente in enumerate(ingredientes):
        expected = ingredientes_data[i]
        assert ingrediente.producto == expected["producto"]
        assert ingrediente.cantidad == expected["cantidad"]
        assert ingrediente.unidad == unidad
        assert ingrediente.receta == receta
        assert ingrediente.user == user
