from typing import Type

from django.core.cache import cache
from django.db.models import Exists, OuterRef, QuerySet
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission, DjangoModelPermissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.viewsets import ModelViewSet

from users.service import UserService

from ..models import Ingrediente, Producto, Unidad
from ..serializers import UnidadSerializer
from .cache_utils import (
    CACHE_TTL_UNIDADES,
    invalidate_productos_cache,
    invalidate_unidades_cache,
    unidades_cache_key,
)


# pylint: disable=too-many-ancestors
class UnidadViewSet(ModelViewSet[Unidad]):
    queryset = Unidad.objects.all()
    serializer_class = UnidadSerializer
    user_service = UserService()
    permission_classes: list[Type[BasePermission]] = [DjangoModelPermissions]
    pagination_class = PageNumberPagination

    def get_queryset(self) -> QuerySet[Unidad]:
        user = self.request.user
        if self.user_service.is_admin_and_authenticated(self.request):
            return (
                Unidad.objects.all()
                .order_by("nombre")
                .annotate(
                    has_product=Exists(Producto.objects.filter(unidad=OuterRef("pk"))),
                    has_ingrediente=Exists(
                        Ingrediente.objects.filter(unidad=OuterRef("pk"))
                    ),
                )
            )

        return (
            Unidad.objects.filter(user=user)
            .order_by("nombre")
            .annotate(
                has_product=Exists(Producto.objects.filter(unidad=OuterRef("pk"))),
                has_ingrediente=Exists(
                    Ingrediente.objects.filter(unidad=OuterRef("pk"))
                ),
            )
        )

    # type: ignore[override]
    def list(self, request: Request, *args, **kwargs) -> Response:
        cache_key = unidades_cache_key(request.user.id)
        data = cache.get(cache_key)
        if data is None:
            qs = self.get_queryset()
            data = UnidadSerializer(qs, many=True).data
            cache.set(cache_key, data, CACHE_TTL_UNIDADES)
        return Response(data)

    def perform_create(self, serializer: BaseSerializer[Unidad]) -> None:
        unidad = serializer.save(user=self.request.user)
        invalidate_unidades_cache(unidad.user_id)
        invalidate_productos_cache(unidad.user_id)

    def perform_update(self, serializer: BaseSerializer[Unidad]) -> None:
        unidad = serializer.save()
        invalidate_unidades_cache(unidad.user_id)
        invalidate_productos_cache(unidad.user_id)

    # type: ignore[override]
    def destroy(self, request: Request, *args, **kwargs) -> Response:
        instance = self.get_object()
        if (
            Producto.objects.filter(unidad=instance).exists()
            or Ingrediente.objects.filter(unidad=instance).exists()
        ):
            return Response(
                {"detail": "La unidad está en uso y no se puede borrar."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user_id = instance.user_id
        instance.delete()
        invalidate_unidades_cache(user_id)
        invalidate_productos_cache(user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
