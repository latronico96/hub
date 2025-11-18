from decimal import Decimal
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
    stock_minimo = models.FloatField(default=0)
    peso = models.DecimalField(max_digits=4, decimal_places=3, default=0)
    codigo = models.CharField(max_length=10, unique=True, default="")

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


class MovimientoDeStock(models.Model):
    id = models.AutoField(primary_key=True)
    fecha = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="movimientos_de_stock"
    )
    TIPO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SALIDA', 'Salida'),
    ]
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)

    nombre = models.TextField(blank=True, null=True)
    calle = models.TextField(blank=True, null=True)
    localidad = models.TextField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.fecha:%d/%m/%Y}"

    class Meta:
        verbose_name = "Movimiento de Stock"
        verbose_name_plural = "Movimientos de Stock"
        ordering = ["-fecha"]


class MovimientoDetalle(models.Model):
    movimiento = models.ForeignKey(
        MovimientoDeStock,
        on_delete=models.CASCADE,
        related_name="detalles"
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name="detalles_de_movimiento"
    )
    cantidad = models.FloatField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"

    @property
    def unidad(self):
        return self.producto.unidad
    
    @property
    def total(self) -> float:
        return (Decimal(self.cantidad) * Decimal(self.producto.precio)).quantize(Decimal("0.00"))


class Preventa(models.Model):
    id = models.AutoField(primary_key=True)
    fecha = models.DateTimeField(auto_now_add=True)
    nombre = models.TextField(blank=True, null=True)
    calle = models.TextField(blank=True, null=True)
    localidad = models.TextField(blank=True, null=True)
    user = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="preventas"
    )
    observaciones = models.TextField(blank=True, null=True)
    movimiento = models.OneToOneField(
        MovimientoDeStock,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="preventa_origen"
    )
    estado = models.CharField(
        max_length=20,
        choices=[
            ("PENDIENTE", "Pendiente"),
            ("CONFIRMADA", "Confirmada"),
            ("CANCELADA", "Cancelada"),
        ],
        default="PENDIENTE"
    )

    def __str__(self):
        return f"Preventa #{self.id} - {self.nombre} ({self.estado})"

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Preventa"
        verbose_name_plural = "Preventas"


class PreventaDetalle(models.Model):
    preventa = models.ForeignKey(
        Preventa,
        on_delete=models.CASCADE,
        related_name="detalles"
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name="detalles_preventa"
    )
    cantidad = models.FloatField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"

