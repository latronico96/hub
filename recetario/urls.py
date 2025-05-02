from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ProductoViewSet, RecetaViewSet, UnidadViewSet, DashboardView

router = DefaultRouter()
router.register(r"unidades", UnidadViewSet, basename="unidades")
router.register(r"productos", ProductoViewSet, basename="productos")
router.register(r"recetas", RecetaViewSet, basename="recetas")

urlpatterns = [
    path('dashboard/totales/', DashboardView.as_view(), name='dashboard-totales'),
] + router.urls
