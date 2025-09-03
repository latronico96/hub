from typing import Type

from django.db.models import Exists, F, OuterRef, QuerySet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
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

from recetario.group_concat import GroupConcat
from users.service import UserService

from .models import Ingrediente, Producto, Receta, Unidad
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
        all_unidades = Unidad.objects.all().order_by("nombre")

        if not self.user_service.is_admin_and_authenticated(self.request):
            all_unidades = all_unidades.filter(
                user=self.user_service.get_authenticated_user(self.request)
            )

        return all_unidades.annotate(
            has_product=Exists(Producto.objects.filter(unidad=OuterRef("pk"))),
            has_ingrediente=Exists(Ingrediente.objects.filter(unidad=OuterRef("pk"))),
        )

    def perform_create(self, serializer: BaseSerializer[Unidad]) -> None:
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if (
            Producto.objects.filter(unidad=instance).exists()
            or Ingrediente.objects.filter(unidad=instance).exists()
        ):
            return Response(
                {"detail": "La unidad está en uso y no se puede borrar."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# pylint: disable=too-many-ancestors
class ProductoViewSet(ModelViewSet[Producto]):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    user_service = UserService()
    permission_classes: list[Type[BasePermission]] = [DjangoModelPermissions]

    def get_queryset(self) -> QuerySet[Producto]:
        all_productos = Producto.objects.all().order_by("nombre")
        if self.user_service.is_admin_and_authenticated(self.request):
            all_productos = all_productos.filter(
                user=self.user_service.get_authenticated_user(self.request)
            ).order_by("nombre")
        return all_productos.annotate(
            has_ingrediente=Exists(Ingrediente.objects.filter(unidad=OuterRef("pk"))),
        )

    def perform_create(self, serializer: BaseSerializer[Producto]) -> None:
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if Ingrediente.objects.filter(producto=instance).exists():
            return Response(
                {"detail": "El producto está en uso y no se puede borrar."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# pylint: disable=too-many-ancestors
class RecetaViewSet(ModelViewSet[Receta]):
    pagination_class = PageNumberPagination
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
        ingredientes_agg = GroupConcat(
            F("ingredientes__producto__nombre"), separator=", "
        )

        if self.user_service.is_admin_and_authenticated(self.request):
            recetas = Receta.objects.annotate(
                ingredientes_str=ingredientes_agg
            ).order_by("nombre")
        else:
            recetas = (
                Receta.objects.filter(
                    user=self.user_service.get_authenticated_user(self.request)
                )
                .annotate(ingredientes_str=ingredientes_agg)
                .order_by("nombre")
            )

        serializer = RecetaGrillaSerializer(recetas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        user_id = request.user.id
        if user_id is None:
            raise ValueError("Authenticated user must have an ID")
        totals = UserTotalsCache().get(int(user_id))
        return Response(totals)
