from rest_framework.routers import DefaultRouter

from .views import UnidadViewSet

router = DefaultRouter()
router.register(r"unidades", UnidadViewSet, basename="unidades")


urlpatterns = router.urls
