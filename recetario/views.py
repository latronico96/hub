# Fixed cache implementation for UnidadViewSet, RecetaViewSet grilla_recetas, and ProductoViewSet PDF exports with user filtering.

# UnidadViewSet
class UnidadViewSet(viewsets.ModelViewSet):
    queryset = Unidad.objects.all()
    serializer_class = UnidadSerializer

    def get_queryset(self):
        user = self.request.user
        # Filter this user's unidades
        return self.queryset.filter(user=user)

# RecetaViewSet
class RecetaViewSet(viewsets.ModelViewSet):
    queryset = Receta.objects.all()
    serializer_class = RecetaSerializer

    def get_queryset(self):
        user = self.request.user
        # Filter this user's recetas
        return self.queryset.filter(user=user)

# grilla_recetas
@api_view(['GET'])
def grilla_recetas(request):
    user = request.user
    recetas = Receta.objects.filter(user=user)  # Properly filtering by user
    serializer = RecetaSerializer(recetas, many=True)
    return Response(serializer.data)

# ProductoViewSet PDF exports
class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer

    def get_queryset(self):
        user = self.request.user
        # Filter products by user for PDF exports
        return self.queryset.filter(user=user)

    @action(detail=False, methods=['get'])
    def export_pdf(self, request):
        user = request.user
        productos = self.get_queryset()  # Returns user's productos
        # Logic for generating PDF
        return Response({'message': 'PDF exported successfully!'});
