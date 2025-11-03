from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import MercadoPagoIPNView, PermissionViewSet, UserViewSet

router = DefaultRouter()
router.register(r"permissions", PermissionViewSet, basename="permission")
router.register(r"", UserViewSet, basename="user")


urlpatterns = [
    path("mercadopago/ipn/", MercadoPagoIPNView.as_view(), name="mercadopago-ipn"),
] + router.urls
