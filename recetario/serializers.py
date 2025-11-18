from typing import Any, Dict, List

from rest_framework import serializers

from django.db.models import Sum, Case, When, FloatField, F

from .models import (
    Ingrediente,
    MovimientoDetalle,
    Preventa,
    PreventaDetalle,
    Producto,
    Receta,
    Unidad,
    MovimientoDeStock,
)


class UnidadSerializer(serializers.ModelSerializer[Unidad]):
    can_be_deleted = serializers.SerializerMethodField()

    class Meta:
        model = Unidad
        fields = ["id", "nombre", "abreviacion", "can_be_deleted"]
        read_only_fields = ["id"]

    def get_can_be_deleted(self, obj: Unidad) -> bool:
        has_product = getattr(obj, "has_product", None)
        has_ingrediente = getattr(obj, "has_ingrediente", None)

        if has_product is None:
            has_product = Producto.objects.filter(unidad=obj).exists()
        if has_ingrediente is None:
            has_ingrediente = Ingrediente.objects.filter(unidad=obj).exists()

        return not (has_product or has_ingrediente)


class ProductoSerializer(serializers.ModelSerializer[Producto]):
    unidadId = serializers.PrimaryKeyRelatedField(
        queryset=Unidad.objects.all(),
        source="unidad",
    )
    can_be_deleted = serializers.SerializerMethodField()
    stock = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = [
            "id",
            "nombre",
            "cantidad",
            "unidadId",
            "precio",
            "can_be_deleted",
            "stock",
            "stock_minimo",
            "peso",
            "codigo",
        ]
        read_only_fields = ["id"]

    def get_can_be_deleted(self, obj: Producto) -> bool:
        has_ingrediente = getattr(obj, "has_ingrediente", None)
        if has_ingrediente is None:
            has_ingrediente = Ingrediente.objects.filter(producto=obj).exists()
        return not has_ingrediente

    def get_stock(self, obj: Producto) -> float:
        result = (
            MovimientoDetalle.objects
            .filter(producto=obj)
            .aggregate(
                total_stock=Sum(
                    Case(
                        When(movimiento__tipo='ENTRADA', then='cantidad'),
                        When(movimiento__tipo='SALIDA', then=-1 * F('cantidad')),
                        output_field=FloatField(),
                    )
                )
            )
        )
        return result['total_stock'] or 0.0


class IngredienteSerializer(serializers.ModelSerializer[Ingrediente]):
    productoId = serializers.PrimaryKeyRelatedField(
        queryset=Producto.objects.all(),
        source="producto",
    )
    unidadId = serializers.PrimaryKeyRelatedField(
        queryset=Unidad.objects.all(),
        source="unidad",
    )

    class Meta:
        model = Ingrediente
        fields = ["id", "productoId", "cantidad", "unidadId"]
        read_only_fields = ["id"]


class RecetaSerializer(serializers.ModelSerializer[Receta]):
    ingredientes = IngredienteSerializer(many=True)

    class Meta:
        model = Receta
        fields = [
            "id",
            "nombre",
            "observaciones",
            "ingredientes",
            "rinde",
            "precio_unidad",
            "precio",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data: Dict[str, Any]) -> Receta:
        ingredientes_data: List[Dict[str, Any]] = validated_data.pop("ingredientes")
        receta = Receta.objects.create(**validated_data)
        user = self.context["request"].user

        for ingrediente_data in ingredientes_data:
            ingrediente_data["user"] = user
            Ingrediente.objects.create(receta=receta, **ingrediente_data)

        return receta

    def update(self, instance: Receta, validated_data: Dict[str, Any]) -> Receta:
        user = self.context["request"].user

        ingredientes_data = validated_data.pop("ingredientes", [])

        instance.nombre = validated_data.get("nombre", instance.nombre)
        instance.rinde = validated_data.get("rinde", instance.rinde)
        instance.observaciones = validated_data.get(
            "observaciones", instance.observaciones
        )
        instance.precio_unidad = validated_data.get(
            "precio_unidad", instance.precio_unidad
        )
        instance.precio = validated_data.get("precio", instance.precio)
        instance.save()

        ingredientes_ids_nuevos = [
            ingrediente_data.get("id")
            for ingrediente_data in ingredientes_data
            if ingrediente_data.get("id")
        ]

        for ingrediente in instance.ingredientes.all():
            if ingrediente.id not in ingredientes_ids_nuevos:
                ingrediente.delete()

        for ingrediente_data in ingredientes_data:
            ingrediente_id = ingrediente_data.get("id")
            if ingrediente_id:
                ingrediente = instance.ingredientes.get(id=ingrediente_id)
                ingrediente.producto = ingrediente_data.get(
                    "producto", ingrediente.producto
                )
                ingrediente.cantidad = ingrediente_data.get(
                    "cantidad", ingrediente.cantidad
                )
                ingrediente.unidad = ingrediente_data.get("unidad", ingrediente.unidad)
                ingrediente.user = user
                ingrediente.save()
            else:
                Ingrediente.objects.create(
                    receta=instance,
                    producto=ingrediente_data["producto"],
                    cantidad=ingrediente_data["cantidad"],
                    unidad=ingrediente_data["unidad"],
                    user=user,
                )

        return instance


class RecetaGrillaSerializer(serializers.ModelSerializer[Receta]):
    ingredientes = serializers.CharField(source="ingredientes_str", read_only=True)
    costo_unidad = serializers.FloatField(read_only=True)
    costo = serializers.FloatField(read_only=True)

    class Meta:
        model = Receta
        fields = [
            "id",
            "nombre",
            "ingredientes",
            "precio",
            "precio_unidad",
            "rinde",
            "costo_unidad",
            "costo"
        ]


class MovimientoDetalleSerializer(serializers.ModelSerializer):
    productoId = serializers.PrimaryKeyRelatedField(
        queryset=Producto.objects.all(),
        source="producto"
    )
    nombre_producto = serializers.CharField(source="producto.nombre", read_only=True)

    class Meta:
        model = MovimientoDetalle
        fields = ["id", "productoId", "nombre_producto", "cantidad", "precio_unitario"]
        read_only_fields = ["id", "nombre_producto"]


class MovimientoDeStockSerializer(serializers.ModelSerializer):
    detalles = MovimientoDetalleSerializer(many=True)
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = MovimientoDeStock
        fields = [
            "id",
            "tipo",
            "fecha",
            "user",
            "observaciones",
            "detalles",
            "nombre",
            "calle",
            "localidad"
        ]
        read_only_fields = ["id", "fecha", "user"]

    def create(self, validated_data):
        detalles_data = validated_data.pop("detalles")
        movimiento = MovimientoDeStock.objects.create(**validated_data)

        for detalle_data in detalles_data:
            MovimientoDetalle.objects.create(movimiento=movimiento, **detalle_data)

        return movimiento

    def update(self, instance, validated_data):
        detalles_data = validated_data.pop("detalles", None)
        instance.tipo = validated_data.get("tipo", instance.tipo)
        instance.nombre = validated_data.get("nombre", instance.nombre)
        instance.calle = validated_data.get("calle", instance.calle)
        instance.localidad = validated_data.get("localidad", instance.localidad)
        instance.observaciones = validated_data.get(
            "observaciones",
            instance.observaciones
        )
        instance.save()

        if detalles_data is not None:
            instance.detalles.all().delete()
            for detalle_data in detalles_data:
                MovimientoDetalle.objects.create(movimiento=instance, **detalle_data)

        return instance


class PreventaDetalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreventaDetalle
        fields = ["id", "producto", "cantidad", "precio_unitario", "subtotal"]
        read_only_fields = ["id", "subtotal"]


class PreventaSerializer(serializers.ModelSerializer):
    detalles = PreventaDetalleSerializer(many=True)

    class Meta:
        model = Preventa
        fields = [
            "id",
            "fecha",
            "nombre",
            "calle",
            "localidad",
            "user",
            "observaciones",
            "estado",
            "detalles",
            "movimiento",
        ]
        read_only_fields = ["id", "fecha", "movimiento"]

    def create(self, validated_data):
        detalles_data = validated_data.pop("detalles")
        preventa = Preventa.objects.create(**validated_data)
        for detalle_data in detalles_data:
            PreventaDetalle.objects.create(preventa=preventa, **detalle_data)
        return preventa
