from typing import Any, Type
import os

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from hub.email.email_sender import EmailSender
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


def send_email_welcome(instance: User) -> None:
    if settings.EMAIL_BACKEND == "django.core.mail.backends.locmem.EmailBackend":
        print("Skipping email sending in test environment")  # Debugging log
        return
    email_sender: EmailSender = EmailSender()
    email_sender.enviar_email_de_bienvenida(instance)


@receiver(post_save, sender=User)
def handle_user_creation(
    sender: Type[User],  # pylint: disable=unused-argument
    instance: User,
    created: bool,
    **kwargs: Any,
) -> None:
    if created:
        send_email_welcome(instance)
