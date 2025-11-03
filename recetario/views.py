from typing import Type

from django.db.models import (
    Case,
    Exists,
    F,
    FloatField,
    OuterRef,
    QuerySet,
    Sum,
    When,
    Value,
)
from django.db.models.functions import Round, Coalesce
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


from .models import Ingrediente, Producto, Receta, Unidad, MovimientoDeStock
from .serializers import (
    ProductoSerializer,
    RecetaGrillaSerializer,
    RecetaSerializer,
    UnidadSerializer,
    MovimientoDeStockSerializer,
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

    def destroy(self, request: Request, *args: object, **kwargs: object) -> Response:
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
        queryset = super().get_queryset().order_by("nombre")

        stock_calculation = Sum(
            Case(
                When(
                    movimientos_de_stock__tipo='ENTRADA',
                    then='movimientos_de_stock__cantidad'
                ),
                When(
                    movimientos_de_stock__tipo='SALIDA',
                    then=-1 * F('movimientos_de_stock__cantidad')
                ),
                output_field=FloatField(),
            )
        )

        queryset = queryset.annotate(
            stock_actual=Coalesce(
                stock_calculation, Value(0.0), output_field=FloatField()
            )
        )

        if self.user_service.is_admin_and_authenticated(self.request):
            queryset = queryset.filter(
                user=self.user_service.get_authenticated_user(self.request)
            )

        filtro_stock = self.request.query_params.get("filtro_stock")

        if filtro_stock == "sin_stock":
            queryset = queryset.filter(stock_actual__lte=0)
        elif filtro_stock == "bajo_stock":
            queryset = queryset.filter(
                stock_actual__lte=F("stock_minimo"),
                stock_actual__gt=0
            )
        elif filtro_stock == "con_stock":
            queryset = queryset.filter(stock_actual__gt=0)

        return queryset.annotate(
            has_ingrediente=Exists(Ingrediente.objects.filter(unidad=OuterRef("pk"))),
        )

    def perform_create(self, serializer: BaseSerializer[Producto]) -> None:
        serializer.save(user=self.request.user)

    def destroy(self, request: Request, *args: object, **kwargs: object) -> Response:
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

        costo_total = Round(Sum(
            F('ingredientes__producto__precio') *
            F('ingredientes__cantidad') /
            F('ingredientes__producto__cantidad')
        ), 2)

        base_queryset = Receta.objects.annotate(
            ingredientes_str=ingredientes_agg,
            costo=costo_total,
            costo_unidad=Round(costo_total / F('rinde'), 2)
        ).order_by("nombre")

        if self.user_service.is_admin_and_authenticated(self.request):
            recetas = base_queryset
        else:
            recetas = base_queryset.filter(
                user=self.user_service.get_authenticated_user(self.request)
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


class MovimientoStockViewSet(ModelViewSet[MovimientoDeStock]):
    queryset = MovimientoDeStock.objects.all()
    serializer_class = MovimientoDeStockSerializer
    user_service = UserService()
    permission_classes: list[Type[BasePermission]] = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Unidad]:
        all_movimientos = MovimientoDeStock.objects.all().order_by("fecha")

        if not self.user_service.is_admin_and_authenticated(self.request):
            all_movimientos = all_movimientos.filter(
                user=self.user_service.get_authenticated_user(self.request)
            )

        return all_movimientos.annotate(
            has_product=Exists(Producto.objects.filter(unidad=OuterRef("pk"))),
            has_ingrediente=Exists(Ingrediente.objects.filter(unidad=OuterRef("pk"))),
        )

    def perform_create(self, serializer: BaseSerializer[Unidad]) -> None:
        serializer.save(user=self.request.user)

    def destroy(self, request: Request, *args: object, **kwargs: object) -> Response:
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
