from django.db import models

from users.models import User


class Unidad(models.Model):
    id = models.AutoField(primary_key=True)
    abreviacion = models.CharField(max_length=10)
    nombre = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="unidades")

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    cantidad = models.FloatField()
    unidad = models.ForeignKey(
        Unidad, on_delete=models.PROTECT, related_name="productos"
    )
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="productos")

    def __str__(self):
        return self.nombre


class Receta(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="recetas")

    def __str__(self):
        return self.nombre


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

    def __str__(self):
        return self.nombre
