from celery import shared_task

from hub.email.email_sender import EmailSender
from users.models import User


@shared_task
def enviar_email_de_bienvenida_task(user_id: int) -> None:
    user = User.objects.get(pk=user_id)
    email_sender = EmailSender()
    email_sender.enviar_email_de_bienvenida(user)


@shared_task
def enviar_email_recuperarcion_contrasenia_task(user_id: int, token: str) -> None:
    user = User.objects.get(pk=user_id)
    email_sender = EmailSender()
    email_sender.enviar_email_recuperarcion_contrasenia(user, token)
