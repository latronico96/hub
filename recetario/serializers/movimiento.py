from typing import Any, Dict, List

from django.db import transaction
from rest_framework import serializers

from ..models import MovimientoDeStock, MovimientoDetalle


class MovimientoDetalleSerializer(serializers.ModelSerializer):
    # Usamos el campo producto_id directo para evitar consultas durante la validación
    # y la serialización (lee el FK sin join). El nombre del producto se resuelve con
    # prefetch en la vista (detalles__producto).
    productoId = serializers.IntegerField(source="producto_id")
    nombre_producto = serializers.CharField(
        source="producto.nombre",
        read_only=True,
    )

    class Meta:
        model = MovimientoDetalle
        fields = [
            "id",
            "productoId",
            "nombre_producto",
            "cantidad",
            "precio_unitario",
        ]
        read_only_fields = [
            "id",
            "nombre_producto",
        ]


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
            "localidad",
        ]
        read_only_fields = ["id", "fecha", "user"]

    @transaction.atomic
    def create(self, validated_data: Dict[str, Any]) -> MovimientoDeStock:
        detalles_data: List[Dict[str, Any]] = validated_data.pop("detalles")
        movimiento = MovimientoDeStock.objects.create(**validated_data)

        detalles = [
            MovimientoDetalle(
                movimiento=movimiento,
                **detalle_data,
            )
            for detalle_data in detalles_data
        ]
        MovimientoDetalle.objects.bulk_create(detalles)

        return movimiento

    @transaction.atomic
    def update(
        self,
        instance: MovimientoDeStock,
        validated_data: Dict[str, Any],
    ) -> MovimientoDeStock:
        detalles_data = validated_data.pop("detalles", None)
        instance.tipo = validated_data.get("tipo", instance.tipo)
        instance.nombre = validated_data.get("nombre", instance.nombre)
        instance.calle = validated_data.get("calle", instance.calle)
        instance.localidad = validated_data.get("localidad", instance.localidad)
        instance.observaciones = validated_data.get(
            "observaciones",
            instance.observaciones,
        )
        instance.save()

        if detalles_data is not None:
            instance.detalles.all().delete()
            detalles = [
                MovimientoDetalle(
                    movimiento=instance,
                    **detalle_data,
                )
                for detalle_data in detalles_data
            ]
            MovimientoDetalle.objects.bulk_create(detalles)

        return instance
