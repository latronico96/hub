from rest_framework import serializers

from ..models import Ingrediente, Producto, Unidad


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
            has_product = Producto.objects.filter(unidad_id=obj.id).exists()
        if has_ingrediente is None:
            has_ingrediente = Ingrediente.objects.filter(unidad_id=obj.id).exists()

        return not (has_product or has_ingrediente)
