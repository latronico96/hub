from .user_totals_cache import UserTotalsCache


def precargar_totales_usuarios() -> None:
    user_totals_cache = UserTotalsCache()
    user_totals_cache.warm_up_cache()
