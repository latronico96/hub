from rest_framework import viewsets

from .models import Producto, Receta, Unidad
from .serializers import ProductoSerializer, RecetaSerializer, UnidadSerializer


class UnidadViewSet(viewsets.ModelViewSet):
    queryset = Unidad.objects.all()
    serializer_class = UnidadSerializer

    def get_queryset(self):
        if self.request.user.is_admin:
            return Unidad.objects.all()
        return Unidad.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer

    def get_queryset(self):
        if self.request.user.is_admin:
            return Producto.objects.all()
        return Producto.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RecetaViewSet(viewsets.ModelViewSet):
    queryset = Receta.objects.all()
    serializer_class = RecetaSerializer

    def get_queryset(self):
        if self.request.user.is_admin:
            return Receta.objects.all()
        return Receta.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
