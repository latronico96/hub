from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from ..models import MovimientoDeStock, MovimientoDetalle, Preventa
from ..serializers import PreventaSerializer


class PreventaViewSet(ModelViewSet[Preventa]):
    queryset = Preventa.objects.prefetch_related("detalles__producto").all()
    serializer_class = PreventaSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):  # type: ignore[override]
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="confirmar")
    def confirmar_preventa(self, request: Request, pk=None):  # type: ignore[override]
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
