from typing import Any, Dict, List

from django.db import transaction
from rest_framework import serializers

from ..models import Preventa, PreventaDetalle


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

    @transaction.atomic
    def create(self, validated_data: Dict[str, Any]) -> Preventa:
        detalles_data: List[Dict[str, Any]] = validated_data.pop("detalles")
        preventa = Preventa.objects.create(**validated_data)
        detalles = [
            PreventaDetalle(preventa=preventa, **detalle_data)
            for detalle_data in detalles_data
        ]
        PreventaDetalle.objects.bulk_create(detalles)
        return preventa
