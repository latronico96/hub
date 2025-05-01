from django.contrib.auth import get_user_model
from django.core.cache import cache

from recetario.models import Producto, Receta, Unidad

User = get_user_model()


class AllUserTotalsCache:
    def __init__(self, timeout: int = 86400):
        self.cache_key = "all_user_totals"
        self.timeout = timeout

    def get(self, user_id: int) -> dict:
        all_totals = cache.get(self.cache_key)
        if all_totals is None:
            all_totals = self._compute_all_totals()
            cache.set(self.cache_key, all_totals, self.timeout)
        return all_totals.get(user_id, {"unidades": 0, "productos": 0, "recetas": 0})

    def invalidate(self) -> None:
        cache.delete(self.cache_key)

    def _compute_all_totals(self) -> dict[int, dict[str, int]]:
        result = {}
        for user in User.objects.all():
            result[user.id] = {
                "unidades": Unidad.objects.filter(user=user).count(),
                "productos": Producto.objects.filter(user=user).count(),
                "recetas": Receta.objects.filter(user=user).count(),
            }
        return result
