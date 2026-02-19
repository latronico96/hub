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
    Max,
    TextField,
    DecimalField,
)
from django.db.models.functions import Round, Coalesce, Concat, Cast
from django.forms import CharField, IntegerField
from django.http import HttpResponse
from django.template.loader import render_to_string
from openpyxl import Workbook
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
from weasyprint import HTML

from recetario.group_concat import GroupConcat
from users.service import UserService

from django.core.cache import cache
from math import ceil


from .models import (
    Ingrediente,
    MovimientoDetalle,
    Preventa,
    Producto,
    Receta,
    Unidad,
    MovimientoDeStock,
)
from .serializers import (
    PreventaSerializer,
    ProductoSerializer,
    RecetaGrillaSerializer,
    RecetaSerializer,
    UnidadSerializer,
    MovimientoDeStockSerializer,
)
from .user_totals_cache import UserTotalsCache

CACHE_TTL_PRODUCTOS = 60 * 6  # 6 minutos

def productos_cache_key(user_id: int, filtro_stock: str | None) -> str:
    return f"productos:list:u{user_id}:f{filtro_stock or 'all'}"


def invalidate_productos_cache(user_id: int) -> None:
    for f in ("all", "sin_stock", "bajo_stock", "con_stock"):
        cache.delete(f"productos:list:u{user_id}:f{f}")


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

    def list(self, request: Request, *args, **kwargs) -> Response:
        user = request.user
        filtro_stock = request.query_params.get("filtro_stock")
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 12))

        # 🔴 Admin → sin cache
        if self.user_service.is_admin_and_authenticated(request):
            qs = self._build_queryset(request)
            total = qs.count()
            start = (page - 1) * page_size
            end = start + page_size
            serializer = self.get_serializer(qs[start:end], many=True)

            return Response({
                "count": total,
                "page": page,
                "page_size": page_size,
                "results": serializer.data,
            })

        # 🟢 Usuario normal → cache
        cache_key = productos_cache_key(user.id, filtro_stock)
        productos_serializados = cache.get(cache_key)

        if productos_serializados is None:
            qs = self._build_queryset(request)
            productos_serializados = ProductoSerializer(qs, many=True).data
            cache.set(cache_key, productos_serializados, CACHE_TTL_PRODUCTOS)

        total = len(productos_serializados)
        start = (page - 1) * page_size
        end = start + page_size

        return Response({
            "count": total,
            "page": page,
            "page_size": page_size,
            "results": productos_serializados[start:end],
        })

    def _build_queryset(self, request: Request) -> QuerySet[Producto]:
        queryset = Producto.objects.order_by("nombre")

        stock_calculation = Sum(
            Case(
                When(
                    detalles_de_movimiento__movimiento__tipo='ENTRADA',
                    then=F('detalles_de_movimiento__cantidad')
                ),
                When(
                    detalles_de_movimiento__movimiento__tipo='SALIDA',
                    then=-1 * F('detalles_de_movimiento__cantidad')
                ),
                output_field=FloatField(),
            )
        )

        queryset = queryset.annotate(
            stock_actual=Coalesce(stock_calculation, Value(0.0))
        )

        queryset = queryset.filter(
            user=self.user_service.get_authenticated_user(request)
        )

        filtro_stock = request.query_params.get("filtro_stock")
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
            has_ingrediente=Exists(
                Ingrediente.objects.filter(producto=OuterRef("pk"))
            )
        )

    # 🔁 INVALIDACIONES
    def perform_create(self, serializer: BaseSerializer[Producto]) -> None:
        producto = serializer.save(user=self.request.user)
        invalidate_productos_cache(producto.user_id)

    def perform_update(self, serializer: BaseSerializer[Producto]) -> None:
        producto = serializer.save()
        invalidate_productos_cache(producto.user_id)

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        instance = self.get_object()

        if Ingrediente.objects.filter(producto=instance).exists():
            return Response(
                {"detail": "El producto está en uso y no se puede borrar."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_id = instance.user_id
        instance.delete()
        invalidate_productos_cache(user_id)

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
    queryset = MovimientoDeStock.objects.prefetch_related("detalles__producto").all()
    serializer_class = MovimientoDeStockSerializer
    user_service = UserService()
    permission_classes: list[Type[BasePermission]] = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[MovimientoDeStock]:
        qs = super().get_queryset().order_by("-fecha")
        
        if not self.user_service.is_admin_and_authenticated(self.request):
            qs = qs.filter(
                user=self.user_service.get_authenticated_user(self.request)
            )
        return qs

    def perform_create(self, serializer: BaseSerializer[MovimientoDeStock]) -> None:
        serializer.save(user=self.request.user)

    def destroy(self, request: Request, *args: object, **kwargs: object) -> Response:
        instance = self.get_object()
        instance.delete()  # esto borra también los detalles por CASCADE
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["get"],
        url_path="excel",
        permission_classes=[IsAuthenticated],
    )
    def exportar_excel(self, request: Request) -> Response:
        wb = Workbook()
        ws = wb.active
        ws.title = "Productos"

        # encabezados
        ws.append(["ID", "Nombre", "Precio", "Stock"])

        # datos
        for p in Producto.objects.all():
            ws.append([p.id, p.nombre, p.precio, p.stock_minimo])

        # preparar respuesta
        response = HttpResponse(
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            )
        )
        response["Content-Disposition"] = 'attachment; filename="productos.xlsx"'
        wb.save(response)
        return response

    @action(
        detail=False,
        methods=["get"],
        url_path="pdf",
        permission_classes=[IsAuthenticated],
    )
    def exportar_pdf(self, request: Request) -> Response:
        productos = (
            Producto.objects
            .annotate(
                ingresos=Sum(
                    Case(
                        When(
                            detalles_de_movimiento__movimiento__tipo='ENTRADA',
                            then=F('detalles_de_movimiento__cantidad')
                        ),
                        default=0,
                        output_field=FloatField()
                    )
                ),
                egresos=Sum(
                    Case(
                        When(
                            detalles_de_movimiento__movimiento__tipo='SALIDA',
                            then=F('detalles_de_movimiento__cantidad')
                        ),
                        default=0,
                        output_field=FloatField()
                    )
                ),
            )
            .annotate(
                stock_actual=F("ingresos") - F("egresos"),
                ultima_fecha=Max("detalles_de_movimiento__movimiento__fecha"),
                estado=Case(
                    When(stock_actual__lte=0, then=Value("Sin Stock")),
                    When(stock_actual__lte=F("stock_minimo"),
                        stock_actual__gt=0,
                        then=Value("Bajo Stock")),
                    default=Value("Con Stock")
                ),
                cod_Nombre=Concat(
                    Cast("id", output_field=TextField()), Value(" - "), F("nombre"),
                    output_field=TextField()
                ),
            )
        )
        html_string = render_to_string(
            "reporte_productos.html",
            {"productos": productos}
        )
        pdf = HTML(string=html_string).write_pdf()

        response = HttpResponse(pdf, content_type="application/pdf")
        iframe = self.request.query_params.get("iframe", None)
        if iframe is not None:
            response["Content-Disposition"] = 'inline; filename="productos.pdf"'
        else:
            response["Content-Disposition"] = 'attachment; filename="productos.pdf"'
        response["Cross-Origin-Opener-Policy"] = "unsafe-none"

        return response

    @action(
        detail=False,
        methods=["get"],
        url_path="pdfr",
        permission_classes=[IsAuthenticated],
    )
    def exportar_pdf2(self, request: Request) -> Response:
        id = self.request.query_params.get("id", None)

        remito = MovimientoDeStock.objects.all().get(pk=id)
        total_calculado = remito.detalles.aggregate(
            total_general=Sum(F('cantidad') * F('producto__precio'),
            output_field=DecimalField(max_digits=10, decimal_places=2))
        )
        remito.total_general = total_calculado['total_general'] or 0.00

        html_string = render_to_string(
            "remito.html",
            {"remito": remito}
        )
        pdf = HTML(string=html_string).write_pdf()

        response = HttpResponse(pdf, content_type="application/pdf")
        iframe = self.request.query_params.get("iframe", None)
        if iframe is not None:
            response["Content-Disposition"] = 'inline; filename="productos.pdf"'
        else:
            response["Content-Disposition"] = 'attachment; filename="productos.pdf"'

        response["Cross-Origin-Opener-Policy"] = "unsafe-none"

        return response
    @action(
        detail=False,
        methods=["get"],
        url_path="pdf_acumulados",
        permission_classes=[IsAuthenticated],
    )
    def exportar_pdf_productos_acumulados(self, request: Request) -> Response:  
        productos = (
            Producto.objects
            .annotate(
                entradas=Sum(
                    Case(
                        When(
                            detalles_de_movimiento__movimiento__tipo='ENTRADA',
                            then=F('detalles_de_movimiento__cantidad')
                        ),
                        default=0,
                        output_field=FloatField()
                    )
                ),
                salidas=Sum(
                    Case(
                        When(
                            detalles_de_movimiento__movimiento__tipo='SALIDA',
                            then=F('detalles_de_movimiento__cantidad')
                        ),
                        default=0,
                        output_field=FloatField()
                    )
                ),
                ultima_fecha=Max("detalles_de_movimiento__movimiento__fecha"),
            )
            .order_by("nombre")
        )

        html_string = render_to_string(
            "reporte_productos_acumulados.html",
            {"productos": productos}
        )

        pdf = HTML(string=html_string).write_pdf()

        response = HttpResponse(pdf, content_type="application/pdf")
        iframe = self.request.query_params.get("iframe", None)
        if iframe is not None:
            response["Content-Disposition"] = 'inline; filename="productos.pdf"'
        else:
            response["Content-Disposition"] = 'attachment; filename="productos.pdf"'

        response["Cross-Origin-Opener-Policy"] = "unsafe-none"

        return response


class PreventaViewSet(ModelViewSet[Preventa]):
    queryset = Preventa.objects.prefetch_related("detalles__producto").all()
    serializer_class = PreventaSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="confirmar")
    def confirmar_preventa(self, request, pk=None):
        preventa = self.get_object()

        if preventa.estado != "PENDIENTE":
            return Response(
                {"detail": "La preventa ya fue procesada."},
                status=status.HTTP_400_BAD_REQUEST
            )

        movimiento = MovimientoDeStock.objects.create(
            user=request.user,
            tipo="SALIDA",
            observaciones=f"Salida generada por preventa #{preventa.id}"
        )

        for detalle in preventa.detalles.all():
            MovimientoDetalle.objects.create(
                movimiento=movimiento,
                producto=detalle.producto,
                cantidad=detalle.cantidad
            )

        preventa.movimiento = movimiento
        preventa.estado = "CONFIRMADA"
        preventa.save()

        return Response({"detail": "Preventa confirmada y movimiento generado."})
