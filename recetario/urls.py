from django.urls import path
from rest_framework.routers import DefaultRouter
from .views.unidad import UnidadViewSet
from .views.producto import ProductoViewSet
from .views.receta import RecetaViewSet
from .views.movimiento_stock import MovimientoStockViewSet
from .views.dashboard import DashboardView

router = DefaultRouter()
router.register(r"unidades", UnidadViewSet, basename="unidades")
router.register(r"productos", ProductoViewSet, basename="productos")
router.register(r"recetas", RecetaViewSet, basename="recetas")
router.register(r"movimientos", MovimientoStockViewSet, basename="movimientos")

urlpatterns = [
    path("dashboard/totales/", DashboardView.as_view(), name="dashboard-totales"),
] + router.urls
