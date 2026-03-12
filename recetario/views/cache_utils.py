from django.core.cache import cache

# ───── CACHE TTL ─────
CACHE_TTL_PRODUCTOS = 60 * 10  # 10 min
CACHE_TTL_RECETAS = 60 * 5     # 5 min
CACHE_TTL_UNIDADES = 60 * 60 * 2  # 2 horas


# ───── CACHE KEYS ─────
def productos_cache_key(user_id: int) -> str:
    return f"productos:list:u{user_id}"


def recetas_cache_key(user_id: int) -> str:
    return f"recetas:list:u{user_id}"


def unidades_cache_key(user_id: int) -> str:
    return f"unidades:list:u{user_id}"


# ───── CACHE INVALIDATIONS ─────
def invalidate_productos_cache(user_id: int) -> None:
    cache.delete(f"productos:list:u{user_id}")
    invalidate_recetas_cache(user_id)


def invalidate_recetas_cache(user_id: int) -> None:
    cache.delete(f"recetas:list:u{user_id}")


def invalidate_unidades_cache(user_id: int) -> None:
    cache.delete(f"unidades:list:u{user_id}")
