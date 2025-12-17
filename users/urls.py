from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    MercadoPagoIPNView,
    PermissionViewSet,
    UserViewSet,
    ImportDatabaseView,
    ExportDatabaseView,
)

router = DefaultRouter()
router.register(r"permissions", PermissionViewSet, basename="permission")
router.register(r"", UserViewSet, basename="user")

urlpatterns = [
    path("mercadopago/ipn/", MercadoPagoIPNView.as_view(), name="mercadopago-ipn"),
    path("import-db/", ImportDatabaseView.as_view(), name="import-database"),
    path("export-db/", ExportDatabaseView.as_view(), name="export-database"),
] + router.urls
