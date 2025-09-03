from typing import Any, Type

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from hub.tasks import enviar_email_de_bienvenida
from users.models import User

from .models import Producto, Receta, Unidad
from .permission_manager import PermissionManager
from .user_totals_cache import UserTotalsCache


@receiver(post_save, sender=User)
def create_basic_units(
    sender: Type[User],  # pylint: disable=unused-argument
    instance: User,
    created: bool,
    **kwargs: Any,
) -> None:
    if created:
        Unidad.crear_unidades_por_defecto_para_usuario(instance)


@receiver(post_save, sender=User)
def handle_user_creation(
    sender: Type[User],  # pylint: disable=unused-argument
    instance: User,
    created: bool,
    **kwargs: Any,
) -> None:
    if created:
        PermissionManager.assign_permissions_to_user(
            instance, PermissionManager.USER_ROLE
        )
        enviar_email_de_bienvenida(instance.id)


@receiver(post_save, sender=Unidad)
def handle_unidad_creation(
    sender: Type[Unidad],  # pylint: disable=unused-argument
    instance: Unidad,
    created: bool,
    **kwargs: Any,
) -> None:
    if created:
        UserTotalsCache().invalidate(instance.user.id)


@receiver(post_delete, sender=Unidad)
def handle_unidad_deletion(
    sender: Type[Unidad],  # pylint: disable=unused-argument
    instance: Unidad,
    **kwargs: Any,
) -> None:
    UserTotalsCache().invalidate(instance.user.id)


@receiver(post_save, sender=Producto)
def handle_producto_creation(
    sender: Type[Producto],  # pylint: disable=unused-argument
    instance: Producto,
    created: bool,
    **kwargs: Any,
) -> None:
    if created:
        UserTotalsCache().invalidate(instance.user.id)


@receiver(post_delete, sender=Producto)
def handle_producto_deletion(
    sender: Type[Producto],  # pylint: disable=unused-argument
    instance: Producto,
    **kwargs: Any,
) -> None:
    UserTotalsCache().invalidate(instance.user.id)


@receiver(post_save, sender=Receta)
def handle_receta_creation(
    sender: Type[Receta],  # pylint: disable=unused-argument
    instance: Receta,
    created: bool,
    **kwargs: Any,
) -> None:
    if created:
        UserTotalsCache().invalidate(instance.user.id)


@receiver(post_delete, sender=Receta)
def handle_receta_deletion(
    sender: Type[Receta],  # pylint: disable=unused-argument
    instance: Receta,
    **kwargs: Any,
) -> None:
    UserTotalsCache().invalidate(instance.user.id)
