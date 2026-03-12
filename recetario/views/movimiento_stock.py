from typing import Type

from django.db.models import (
    Case,
    DecimalField,
    F,
    FloatField,
    Max,
    QuerySet,
    Sum,
    When,
    Value,
    TextField,
)
from django.db.models.functions import Concat, Cast
from django.http import HttpResponse
from django.template.loader import render_to_string
from openpyxl import Workbook
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.viewsets import ModelViewSet
from weasyprint import HTML

from users.service import UserService

from ..models import MovimientoDeStock, Producto
from ..serializers import MovimientoDeStockSerializer


# pylint: disable=too-many-ancestors
class MovimientoStockViewSet(ModelViewSet[MovimientoDeStock]):
    queryset = MovimientoDeStock.objects.prefetch_related("detalles__producto").all()
    serializer_class = MovimientoDeStockSerializer
    user_service = UserService()
    permission_classes: list[Type[BasePermission]] = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[MovimientoDeStock]:  # type: ignore[override]
        qs = super().get_queryset().order_by("-fecha")
        if not self.user_service.is_admin_and_authenticated(self.request):
            qs = qs.filter(user=self.user_service.get_authenticated_user(self.request))
        return qs

    def perform_create(self, serializer: BaseSerializer[MovimientoDeStock]) -> None:
        serializer.save(user=self.request.user)

    # type: ignore[override]
    def destroy(self, request: Request, *args, **kwargs) -> Response:
        instance = self.get_object()
        instance.delete()
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
                    When(stock_actual__lte=F("stock_minimo"), stock_actual__gt=0,
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
            total_general=Sum(
                F('cantidad') * F('producto__precio'),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
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
