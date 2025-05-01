from celery import shared_task
from django.core.cache import cache

from users.models import User

from .models import Producto, Receta, Unidad


@shared_task
def precargar_totales_usuarios() -> None:
    for user in User.objects.all():
        cache.set(
            f"user_totals_{user.id}",
            {
                "unidades": Unidad.objects.filter(user=user).count(),
                "productos": Producto.objects.filter(user=user).count(),
                "recetas": Receta.objects.filter(user=user).count(),
            },
            timeout=86400,
        )
