from typing import TypedDict

from django.core.cache import cache

from recetario.models import Producto, Receta, Unidad
from users.models import User


class UserTotals(TypedDict):
    unidades: int
    productos: int
    recetas: int


class UserTotalsCache:
    def __init__(self, timeout: int = 86400):
        self.cache_prefix = "user_totals_"
        self.all_users_key = "all_users_with_totals"
        self.timeout = timeout

    def get(self, user_id: int) -> UserTotals:
        user_key = f"{self.cache_prefix}{user_id}"
        cached_data: UserTotals = cache.get(user_key)
        if cached_data is not None:
            return cached_data
        user_data = self._compute_user_totals(user_id)
        cache.set(user_key, user_data, self.timeout)
        self._update_users_list(user_id)
        return user_data

    def invalidate(self, user_id: int | None = None) -> None:
        if user_id is None:
            user_ids = cache.get(self.all_users_key, [])
            for uid in user_ids:
                cache.delete(f"{self.cache_prefix}{uid}")
            cache.delete(self.all_users_key)
        else:
            cache.delete(f"{self.cache_prefix}{user_id}")
            self._remove_from_users_list(user_id)

    def _compute_user_totals(self, user_id: int) -> UserTotals:
        try:
            user = User.objects.get(pk=user_id)
            return {
                "unidades": Unidad.objects.filter(user=user).count(),
                "productos": Producto.objects.filter(user=user).count(),
                "recetas": Receta.objects.filter(user=user).count(),
            }
        except User.DoesNotExist:
            return {"unidades": 0, "productos": 0, "recetas": 0}

    def _update_users_list(self, user_id: int) -> None:
        user_ids = cache.get(self.all_users_key, set())
        user_ids.add(user_id)
        cache.set(self.all_users_key, user_ids, self.timeout)

    def _remove_from_users_list(self, user_id: int) -> None:
        user_ids = cache.get(self.all_users_key, set())
        if user_id in user_ids:
            user_ids.remove(user_id)
            cache.set(self.all_users_key, user_ids, self.timeout)

    def warm_up_cache(self, user_ids: list[int] | None = None) -> None:
        if user_ids is None:
            user_ids = list(User.objects.values_list("id", flat=True))
        for user_id in user_ids:
            self.get(user_id)
