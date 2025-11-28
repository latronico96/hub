from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    DashboardView,
    ProductoViewSet,
    RecetaViewSet,
    UnidadViewSet,
    MovimientoStockViewSet,
    PreventaViewSet,
    CostoLaboralViewSet,
    ConfiguracionNegocioViewSet,
)

router = DefaultRouter()
router.register(r"unidades", UnidadViewSet, basename="unidades")
router.register(r"productos", ProductoViewSet, basename="productos")
router.register(r"recetas", RecetaViewSet, basename="recetas")
router.register(r"movimientos", MovimientoStockViewSet, basename="movimientos")
router.register(r"costos-laborales", CostoLaboralViewSet, basename="costos-laborales")
router.register(r"preventas", PreventaViewSet, basename="preventas")
router.register(
    r"configuracion-negocio",
    ConfiguracionNegocioViewSet,
    basename="configuracion-negocio"
)

urlpatterns = [
    path("dashboard/totales/", DashboardView.as_view(), name="dashboard-totales"),
] + router.urls
