import datetime
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from .models import Unidad, Producto, Receta
from .serializers import UnidadSerializer, ProductoSerializer, RecetaSerializer

CACHE_TTL = 60 * 15  # 15 minutes

class UnidadViewSet(ModelViewSet):
    queryset = Unidad.objects.all()
    serializer_class = UnidadSerializer

    def get_queryset(self):
        return self.queryset  # Returning the actual queryset

class ProductoViewSet(ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer

    @method_decorator(cache_page(CACHE_TTL))
    def list(self, request, *args, **kwargs):
        user_products = self.queryset.filter(user=request.user)
        return Response(ProductoSerializer(user_products, many=True).data)

class RecetaViewSet(ModelViewSet):
    queryset = Receta.objects.all()
    serializer_class = RecetaSerializer

    @method_decorator(cache_page(CACHE_TTL))
    def list(self, request, *args, **kwargs):
        cache_key = f'recetas_grilla_user_{request.user.id}'
        # Add logic to handle caching
        return Response(self.serializer_class(self.queryset, many=True).data)

class MovimientoStockViewSet(ModelViewSet):
    # Implementation for MovimientoStock
    pass

class PreventaViewSet(ModelViewSet):
    # Implementation for Preventa
    pass

class DashboardView(ModelViewSet):
    # Implementation for Dashboard
    pass
