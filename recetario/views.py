from typing import Type

from django.db.models import QuerySet
from rest_framework.decorators import action
from rest_framework.permissions import (
    BasePermission,
    DjangoModelPermissions,
    IsAuthenticated,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from users.service import UserService

from .models import Producto, Receta, Unidad
from .serializers import (
    ProductoSerializer,
    RecetaGrillaSerializer,
    RecetaSerializer,
    UnidadSerializer,
)
from .user_totals_cache import UserTotalsCache


# pylint: disable=too-many-ancestors
class UnidadViewSet(ModelViewSet[Unidad]):
    queryset = Unidad.objects.all()
    serializer_class = UnidadSerializer
    user_service = UserService()
    permission_classes: list[Type[BasePermission]] = [DjangoModelPermissions]

    def get_queryset(self) -> QuerySet[Unidad]:
        if self.user_service.is_admin_and_authenticated(self.request):
            return Unidad.objects.all()
        return Unidad.objects.filter(
            user=self.user_service.get_authenticated_user(self.request)
        )

    def perform_create(self, serializer: BaseSerializer[Unidad]) -> None:
        serializer.save(user=self.request.user)


# pylint: disable=too-many-ancestors
class ProductoViewSet(ModelViewSet[Producto]):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    user_service = UserService()
    permission_classes: list[Type[BasePermission]] = [DjangoModelPermissions]

    def get_queryset(self) -> QuerySet[Producto]:
        if self.user_service.is_admin_and_authenticated(self.request):
            return Producto.objects.all()
        return Producto.objects.filter(
            user=self.user_service.get_authenticated_user(self.request)
        )

    def perform_create(self, serializer: BaseSerializer[Producto]) -> None:
        serializer.save(user=self.request.user)


# pylint: disable=too-many-ancestors
class RecetaViewSet(ModelViewSet[Receta]):
    queryset = Receta.objects.all()
    serializer_class = RecetaSerializer
    user_service = UserService()
    permission_classes: list[Type[BasePermission]] = [DjangoModelPermissions]

    def get_queryset(self) -> QuerySet[Receta]:
        if self.user_service.is_admin_and_authenticated(self.request):
            return Receta.objects.all()
        return Receta.objects.filter(
            user=self.user_service.get_authenticated_user(self.request)
        )

    def perform_create(self, serializer: BaseSerializer[Receta]) -> None:
        serializer.save(user=self.request.user)

    @action(
        detail=False,
        methods=["get"],
        url_path="grilla",
        permission_classes=[IsAuthenticated, DjangoModelPermissions],
    )
    def grilla_recetas(self, request: Request) -> Response:
        if self.user_service.is_admin_and_authenticated(self.request):
            recetas = Receta.objects.all()
        else:
            recetas = Receta.objects.filter(
                user=self.user_service.get_authenticated_user(self.request)
            )
        serializer = RecetaGrillaSerializer(recetas, many=True)
        return Response(serializer.data)


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        user_id = request.user.id
        totals = UserTotalsCache().get(user_id)
        return Response(totals)
