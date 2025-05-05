from rest_framework.routers import DefaultRouter

from .views import PermissionViewSet, UserViewSet

router = DefaultRouter()
router.register(r"", UserViewSet, basename="user")
router.register(r"permissions", PermissionViewSet, basename="permission")

urlpatterns = router.urls
