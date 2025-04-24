from typing import Any, Type

from django.db.models.signals import post_save
from django.dispatch import receiver

from users.models import User

from .models import Unidad


@receiver(post_save, sender=User)
def create_basic_units(
    sender: Type[User],  # pylint: disable=unused-argument
    instance: User,
    created: bool,
    **kwargs: Any,
) -> None:
    if created:
        Unidad.crear_unidades_por_defecto_para_usuario(instance)
