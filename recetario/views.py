from rest_framework import viewsets

from .models import Unidad
from .serializers import UnidadSerializer


class UnidadViewSet(viewsets.ModelViewSet):
    queryset = Unidad.objects.all()
    serializer_class = UnidadSerializer
