from recetario.models import Producto, Unidad
from users.models import User


def setup_create_gramo(user: User) -> Unidad:
    return Unidad.objects.create(
        nombre="Gramos",
        abreviacion="g",
        user=user,
    )


def setup_create_kilogramo(user: User) -> Unidad:
    return Unidad.objects.create(
        nombre="Kilogramos",
        abreviacion="kg",
        user=user,
    )


def setup_create_mililitro(user: User) -> Unidad:
    return Unidad.objects.create(
        nombre="Mililitros",
        abreviacion="ml",
        user=user,
    )


def setup_create_manzana(user: User, unidad: Unidad) -> Producto:
    return Producto.objects.create(
        nombre="Manzana",
        cantidad=1000,
        unidad=unidad,
        precio=1000.0,
        user=user,
    )


def setup_create_harina(user: User, unidad: Unidad) -> Producto:
    return Producto.objects.create(
        nombre="Harina",
        cantidad=1,
        unidad=unidad,
        precio=1600.0,
        user=user,
    )
