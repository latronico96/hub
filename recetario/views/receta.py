from typing import Type

from django.core.cache import cache
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (
    BasePermission,
    DjangoModelPermissions,
    IsAuthenticated
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.viewsets import ModelViewSet

from users.service import UserService

from ..models import Receta
from ..serializers import RecetaGrillaSerializer, RecetaSerializer
from .cache_utils import (
    CACHE_TTL_RECETAS,
    recetas_cache_key,
    invalidate_recetas_cache,
)


# pylint: disable=too-many-ancestors
class RecetaViewSet(ModelViewSet[Receta]):
    pagination_class = PageNumberPagination
    queryset = Receta.objects.all()
    serializer_class = RecetaSerializer
    user_service = UserService()
    permission_classes: list[Type[BasePermission]] = [DjangoModelPermissions]

    def get_queryset(self):
        request = self.request
        if self.user_service.is_admin_and_authenticated(request):
            return (
                Receta.objects
                .order_by("nombre")
                .prefetch_related("ingredientes__producto__unidad")
            )
        user = request.user
        return (
            Receta.objects
            .filter(user=user)
            .order_by("nombre")
            .prefetch_related("ingredientes__producto__unidad")
        )

    # type: ignore[override]
    def list(self, request: Request, *args, **kwargs) -> Response:
        user = request.user
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 12))
        search = request.query_params.get("search", "").strip().lower()

        # admin → sin cache
        if self.user_service.is_admin_and_authenticated(request):
            qs = (
                Receta.objects
                .order_by("nombre")
                .prefetch_related("ingredientes__producto__unidad")
            )
            if search:
                qs = qs.filter(nombre__icontains=search)
            total = qs.count()
            start = (page-1)*page_size
            end = start+page_size
            serializer = self.get_serializer(qs[start:end], many=True)
            return Response({
                "count": total,
                "page": page,
                "page_size": page_size,
                "results": serializer.data
            })

        # usuario normal → cache (BUGFIX: cachear toda la lista sin búsqueda)
        cache_key = recetas_cache_key(user.id)
        recetas_en_cache = cache.get(cache_key)

        if recetas_en_cache is None:
            qs = (
                Receta.objects.filter(user=user)
                .order_by("nombre")
                .prefetch_related("ingredientes__producto__unidad")
            )
            recetas_en_cache = RecetaSerializer(qs, many=True).data
            cache.set(cache_key, recetas_en_cache, CACHE_TTL_RECETAS)

        # aplicar búsqueda sobre cache (solo si hay búsqueda)
        resultados = recetas_en_cache
        if search:
            resultados = (
                [r for r in recetas_en_cache if search in r["nombre"].lower()]
            )

        # paginación sobre resultados filtrados
        total = len(resultados)
        start = (page-1)*page_size
        end = start+page_size
        return Response({
            "count": total,
            "page": page,
            "page_size": page_size,
            "results": resultados[start:end]
        })

    def perform_create(self, serializer: BaseSerializer[Receta]) -> None:
        receta = serializer.save(user=self.request.user)
        invalidate_recetas_cache(receta.user_id)

    def perform_update(self, serializer: BaseSerializer[Receta]) -> None:
        receta = serializer.save()
        invalidate_recetas_cache(receta.user_id)

    # type: ignore[override]
    def destroy(self, request: Request, *args, **kwargs) -> Response:
        receta = self.get_object()
        user_id = receta.user_id
        receta.delete()
        invalidate_recetas_cache(user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["get"],
        url_path="grilla",
        permission_classes=[IsAuthenticated, DjangoModelPermissions]
    )
    def grilla_recetas(self, request: Request) -> Response:
        user = request.user
        search = request.query_params.get("search", "").strip().lower()

        # admin → sin cache
        if self.user_service.is_admin_and_authenticated(request):
            base_qs = Receta.objects.only(
                "id",
                "nombre",
                "ingredientes_str",
                "costo",
                "costo_unidad",
                "precio",
                "precio_unidad",
                "rinde",
            ).order_by("nombre")
            if search:
                base_qs = base_qs.filter(nombre__icontains=search)
            serializer = RecetaGrillaSerializer(base_qs, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # usuario normal → cache (BUGFIX: cachea la lista completa SIN búsqueda)
        cache_key = recetas_cache_key(user.id)
        recetas_en_cache = cache.get(cache_key)

        if recetas_en_cache is None:
            base_qs = Receta.objects.filter(user=user).only(
                "id",
                "nombre",
                "ingredientes_str",
                "costo",
                "costo_unidad",
                "precio",
                "precio_unidad",
                "rinde",
            ).order_by("nombre")
            recetas_en_cache = RecetaGrillaSerializer(base_qs, many=True).data
            cache.set(cache_key, recetas_en_cache, CACHE_TTL_RECETAS)

        # aplicar búsqueda sobre cache (solo si hay búsqueda)
        resultados = recetas_en_cache
        if search:
            resultados = (
                [r for r in recetas_en_cache if search in r["nombre"].lower()]
            )
        return Response({
            "count": len(resultados),
            "results": resultados
        })
