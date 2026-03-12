from rest_framework import serializers

from ..models import Ingrediente, Producto, Unidad


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
