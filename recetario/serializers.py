from typing import Any, Dict, List

from rest_framework import serializers

from .models import Ingrediente, Producto, Receta, Unidad


class UnidadSerializer(serializers.ModelSerializer[Unidad]):
    class Meta:
        model = Unidad
        fields = ["id", "nombre", "abreviacion"]
        read_only_fields = ["id"]


class ProductoSerializer(serializers.ModelSerializer[Producto]):
    unidad = serializers.PrimaryKeyRelatedField(queryset=Unidad.objects.all())

    class Meta:
        model = Producto
        fields = ["id", "nombre", "cantidad", "unidad"]
        read_only_fields = ["id"]


class IngredienteSerializer(serializers.ModelSerializer[Ingrediente]):
    producto = serializers.PrimaryKeyRelatedField(queryset=Producto.objects.all())
    unidad = serializers.PrimaryKeyRelatedField(queryset=Unidad.objects.all())

    class Meta:
        model = Ingrediente
        fields = ["id", "producto", "cantidad", "unidad"]
        read_only_fields = ["id"]


class RecetaSerializer(serializers.ModelSerializer[Receta]):
    ingredientes = IngredienteSerializer(many=True)

    class Meta:
        model = Receta
        fields = ["id", "nombre", "descripcion", "ingredientes"]
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
        instance.descripcion = validated_data.get("descripcion", instance.descripcion)
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
