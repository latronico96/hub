from typing import Any, Dict, List

from rest_framework import serializers

from .models import Ingrediente, Producto, Receta, Unidad


class UnidadSerializer(serializers.ModelSerializer[Unidad]):
    can_be_deleted = serializers.SerializerMethodField()

    class Meta:
        model = Unidad
        fields = ["id", "nombre", "abreviacion", "can_be_deleted"]
        read_only_fields = ["id"]

    def get_can_be_deleted(self, obj: Unidad) -> bool:
        return obj.can_be_deleted


class ProductoSerializer(serializers.ModelSerializer[Producto]):
    unidadId = serializers.PrimaryKeyRelatedField(
        queryset=Unidad.objects.all(),
        source="unidad",
    )
    can_be_deleted = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = ["id", "nombre", "cantidad", "unidadId", "precio", "can_be_deleted"]
        read_only_fields = ["id"]

    def get_can_be_deleted(self, obj: Producto) -> bool:
        return obj.can_be_deleted


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
    ingredientes = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = ["id", "nombre", "ingredientes"]

    def get_ingredientes(self, obj: Receta) -> str:
        ingredientes = obj.ingredientes.all()
        ingredientes_str = [
            f"{ingrediente.producto.nombre}"
            + f" ({ingrediente.cantidad} {ingrediente.unidad.abreviacion})"
            for ingrediente in ingredientes
        ]
        return ", ".join(ingredientes_str)
