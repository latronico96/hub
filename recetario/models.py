from typing import List, TypedDict

from django.contrib.auth.models import Permission
from django.db import models

from users.models import User


class UnidadPorDefecto(TypedDict):
    abreviacion: str
    nombre: str


class Unidad(models.Model):
    id = models.AutoField(primary_key=True)
    abreviacion = models.CharField(max_length=10)
    nombre = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="unidades")

    class Meta:
        verbose_name = "Unidad"
        verbose_name_plural = "Unidades"
        ordering = ["abreviacion"]
        permissions: list[Permission] = []

    def __str__(self) -> str:
        return str(self.nombre)

    @staticmethod
    def crear_unidades_por_defecto_para_usuario(user: User) -> None:
        unidades_por_defecto: List[UnidadPorDefecto] = [
            {"abreviacion": "kg", "nombre": "Kilogramo"},
            {"abreviacion": "g", "nombre": "Gramo"},
            {"abreviacion": "l", "nombre": "Litro"},
            {"abreviacion": "ml", "nombre": "Mililitro"},
            {"abreviacion": "unidad", "nombre": "Unidad"},
        ]

        for unidad in unidades_por_defecto:
            Unidad.objects.create(
                user=user,
                abreviacion=unidad["abreviacion"],
                nombre=unidad["nombre"],
            )

    @property
    def can_be_deleted(self) -> bool:
        return (
            not Producto.objects.filter(unidad=self).exists()
            or not Ingrediente.objects.filter(unidad=self).exists()
        )


class Producto(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    cantidad = models.FloatField()
    unidad = models.ForeignKey(
        Unidad, on_delete=models.PROTECT, related_name="productos"
    )
    precio = models.FloatField()
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="productos")

    def __str__(self) -> str:
        return str(self.nombre)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["nombre"]
        permissions: list[Permission] = []

    @property
    def can_be_deleted(self) -> bool:
        return not Ingrediente.objects.filter(producto=self).exists()


class Receta(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    observaciones = models.TextField(blank=True, null=True)
    rinde = models.FloatField()
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="recetas")
    precio_unidad = models.FloatField()
    precio = models.FloatField()

    def __str__(self) -> str:
        return str(self.nombre)

    class Meta:
        verbose_name = "Receta"
        verbose_name_plural = "Recetas"
        ordering = ["nombre"]
        permissions: list[Permission] = []


class Ingrediente(models.Model):
    id = models.AutoField(primary_key=True)
    cantidad = models.FloatField()
    unidad = models.ForeignKey(
        Unidad, on_delete=models.PROTECT, related_name="ingredientes"
    )
    producto = models.ForeignKey(
        Producto, on_delete=models.PROTECT, related_name="ingredientes"
    )
    receta = models.ForeignKey(
        Receta, on_delete=models.CASCADE, related_name="ingredientes"
    )
    user = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="ingredientes"
    )

    def __str__(self) -> str:
        return f"{self.cantidad} {self.unidad.abreviacion} de {self.producto.nombre}"

    class Meta:
        verbose_name = "Ingrediente"
        verbose_name_plural = "Ingredientes"
