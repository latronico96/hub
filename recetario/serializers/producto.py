from rest_framework import serializers

from ..models import Ingrediente, Producto, Unidad


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
        ]
        read_only_fields = ["id"]

    def get_can_be_deleted(self, obj: Producto) -> bool:
        has_ingrediente = getattr(obj, "has_ingrediente", None)
        if has_ingrediente is None:
            has_ingrediente = Ingrediente.objects.filter(producto=obj).exists()
        return not has_ingrediente

    def get_stock(self, obj: Producto) -> float:
        # Nota: calcular stock aquí puede generar N+1 queries.
        # Mantener 0.0 por desempeño  y calcular stock en endpoints/reportes
        # específicos con anotaciones cuando sea necesario.
        return 0.0
