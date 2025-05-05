from django.db.models import QuerySet
from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.views import APIView

from users.service import UserService

from .models import Producto, Receta, Unidad
from .serializers import ProductoSerializer, RecetaSerializer, UnidadSerializer
from .user_totals_cache import UserTotalsCache


# pylint: disable=too-many-ancestors
class UnidadViewSet(viewsets.ModelViewSet[Unidad]):
    queryset = Unidad.objects.all()
    serializer_class = UnidadSerializer
    user_service = UserService()
    permission_classes: list = [DjangoModelPermissions]

    def get_queryset(self) -> QuerySet[Unidad]:
        if self.user_service.is_admin_and_authenticated(self.request):
            return Unidad.objects.all()
        return Unidad.objects.filter(
            user=self.user_service.get_authenticated_user(self.request)
        )

    def perform_create(self, serializer: BaseSerializer[Unidad]) -> None:
        serializer.save(user=self.request.user)


# pylint: disable=too-many-ancestors
class ProductoViewSet(viewsets.ModelViewSet[Producto]):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    user_service = UserService()
    permission_classes: list = [DjangoModelPermissions]

    def get_queryset(self) -> QuerySet[Producto]:
        if self.user_service.is_admin_and_authenticated(self.request):
            return Producto.objects.all()
        return Producto.objects.filter(
            user=self.user_service.get_authenticated_user(self.request)
        )

    def perform_create(self, serializer: BaseSerializer[Producto]) -> None:
        serializer.save(user=self.request.user)


# pylint: disable=too-many-ancestors
class RecetaViewSet(viewsets.ModelViewSet[Receta]):
    queryset = Receta.objects.all()
    serializer_class = RecetaSerializer
    user_service = UserService()
    permission_classes: list = [DjangoModelPermissions]

    def get_queryset(self) -> QuerySet[Receta]:
        if self.user_service.is_admin_and_authenticated(self.request):
            return Receta.objects.all()
        return Receta.objects.filter(
            user=self.user_service.get_authenticated_user(self.request)
        )

    def perform_create(self, serializer: BaseSerializer[Receta]) -> None:
        serializer.save(user=self.request.user)


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        user_id = request.user.id
        totals = UserTotalsCache().get(user_id)
        return Response(totals)
