from typing import Type

from django.core.cache import cache
from django.db.models import QuerySet
from rest_framework import status
from rest_framework.permissions import BasePermission, DjangoModelPermissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.viewsets import ModelViewSet

from users.service import UserService

from ..models import Ingrediente, Producto
from ..serializers import ProductoSerializer
from .cache_utils import (
    CACHE_TTL_PRODUCTOS,
    invalidate_productos_cache,
    productos_cache_key,
)


# pylint: disable=too-many-ancestors
class ProductoViewSet(ModelViewSet[Producto]):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    user_service = UserService()
    permission_classes: list[Type[BasePermission]] = [DjangoModelPermissions]

    def _build_queryset(self, request: Request) -> QuerySet[Producto]:
        return (
            Producto.objects
            .filter(
                user=self.user_service.get_authenticated_user(request)
            )
            .select_related('unidad')
            .order_by("nombre")
        )

    # type: ignore[override]
    def list(self, request: Request, *args, **kwargs) -> Response:
        user = request.user
        search = (request.query_params.get("search") or "").strip().lower()

        page_param = request.query_params.get("page")
        page_size_param = request.query_params.get("page_size")
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 12))

        if self.user_service.is_admin_and_authenticated(request):
            qs = (
                Producto.objects
                .select_related('unidad')
                .order_by("nombre")
            )
            if search:
                qs = qs.filter(nombre__icontains=search)
            if page_param is None:
                serializer = self.get_serializer(qs, many=True)
                return Response(serializer.data)

            # 🔹 CON paginación
            page = int(page_param)
            page_size = int(page_size_param or 12)

            total = qs.count()
            start = (page - 1) * page_size
            end = start + page_size

            serializer = self.get_serializer(qs[start:end], many=True)
            return Response({
                "count": total,
                "page": page,
                "page_size": page_size,
                "results": serializer.data
            })

        cache_key = productos_cache_key(user.id)
        productos = cache.get(cache_key)

        if productos is None:
            qs = self._build_queryset(request)
            productos = ProductoSerializer(qs, many=True).data
            cache.set(cache_key, productos, CACHE_TTL_PRODUCTOS)

        resultados = productos

        if search:
            resultados = [
                p for p in resultados
                if search in p["nombre"].lower()
            ]
        if page_param is None:
            return Response({
                "count": len(resultados),
                "page": 1,
                "page_size": len(resultados),
                "results": resultados
            })

        # 🔹 CON paginación
        page = int(page_param)
        page_size = int(page_size_param or 12)

        total = len(resultados)
        start = (page - 1) * page_size
        end = start + page_size

        return Response({
            "count": total,
            "page": page,
            "page_size": page_size,
            "results": resultados[start:end]
        })

    def perform_create(self, serializer: BaseSerializer[Producto]) -> None:
        producto = serializer.save(user=self.request.user)
        invalidate_productos_cache(producto.user_id)

    def perform_update(self, serializer: BaseSerializer[Producto]) -> None:
        producto = serializer.save()
        invalidate_productos_cache(producto.user_id)

    # type: ignore[override]
    def destroy(self, request: Request, *args, **kwargs) -> Response:
        instance = self.get_object()
        if Ingrediente.objects.filter(producto=instance).exists():
            return Response(
                {"detail": "El producto está en uso y no se puede borrar."},
                status=status.HTTP_400_BAD_REQUEST
            )
        user_id = instance.user_id
        instance.delete()
        invalidate_productos_cache(user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
