from typing import Any, Dict, List

from django.db import transaction
from rest_framework import serializers

from ..models import Ingrediente, Receta
from .ingrediente import IngredienteSerializer


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

    @transaction.atomic
    def create(self, validated_data: Dict[str, Any]) -> Receta:
        ingredientes_data: List[Dict[str, Any]] = validated_data.pop("ingredientes")
        receta = Receta.objects.create(**validated_data)
        user = self.context["request"].user

        ingredientes = [
            Ingrediente(receta=receta, user=user, **ingrediente_data)
            for ingrediente_data in ingredientes_data
        ]
        Ingrediente.objects.bulk_create(ingredientes)

        receta.recalcular_grilla()
        return receta

    @transaction.atomic
    def update(self, instance: Receta, validated_data: Dict[str, Any]) -> Receta:
        user = self.context["request"].user

        ingredientes_data = validated_data.pop("ingredientes", [])

        # Update simple fields
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

        # Fetch existing ingredientes once and index by id to avoid N+1 queries
        existing_ingredientes = list(instance.ingredientes.all())
        existing_by_id = {ing.id: ing for ing in existing_ingredientes}

        # Compute IDs that remain
        ingredientes_ids_nuevos = [
            ingrediente_data.get("id")
            for ingrediente_data in ingredientes_data
            if ingrediente_data.get("id")
        ]

        # Bulk delete ingredientes that were removed
        to_delete_ids = set(existing_by_id.keys()) - set(ingredientes_ids_nuevos)
        if to_delete_ids:
            instance.ingredientes.filter(id__in=to_delete_ids).delete()

        # Prepare bulk updates and creates
        to_update: List[Ingrediente] = []
        to_create: List[Ingrediente] = []

        for ingrediente_data in ingredientes_data:
            ingrediente_id = ingrediente_data.get("id")
            if ingrediente_id:
                ingrediente = existing_by_id.get(ingrediente_id)
                if ingrediente is None:
                    ingrediente = instance.ingredientes.get(id=ingrediente_id)
                ingrediente.producto = ingrediente_data.get(
                    "producto", ingrediente.producto
                )
                ingrediente.cantidad = ingrediente_data.get(
                    "cantidad", ingrediente.cantidad
                )
                ingrediente.unidad = ingrediente_data.get("unidad", ingrediente.unidad)
                ingrediente.user = user
                to_update.append(ingrediente)
            else:
                to_create.append(
                    Ingrediente(
                        receta=instance,
                        producto=ingrediente_data["producto"],
                        cantidad=ingrediente_data["cantidad"],
                        unidad=ingrediente_data["unidad"],
                        user=user,
                    )
                )

        if to_update:
            Ingrediente.objects.bulk_update(
                to_update, ["producto", "cantidad", "unidad", "user"]
            )
        if to_create:
            Ingrediente.objects.bulk_create(to_create)

        instance.recalcular_grilla()
        return instance


class RecetaGrillaSerializer(serializers.ModelSerializer[Receta]):
    ingredientes = serializers.CharField(source="ingredientes_str", read_only=True)

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
