import logging
from smtplib import SMTPException
from typing import Any

from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError

from hub.email.email_sender import EmailSender
from users.models import User

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(SMTPException, ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_jitter=True,
)
def enviar_email_de_bienvenida_task(self: Any, user_id: int) -> None:
    try:
        user = User.objects.get(pk=user_id)
        email_sender = EmailSender()
        email_sender.enviar_email_de_bienvenida(user)
        logger.info(
            "Email de bienvenida enviado exitosamente a %s (ID: %d)",
            user.email,
            user_id,
        )

    except ObjectDoesNotExist as e:
        logger.error(
            "Usuario no encontrado (ID: %d): %s", user_id, str(e), exc_info=True
        )
        # No reintentar para este error
        raise

    except SMTPException as e:
        logger.error(
            "Error SMTP al enviar email a %d: %s", user_id, str(e), exc_info=True
        )
        raise self.retry(exc=e)

    except (ConnectionError, TimeoutError) as e:
        logger.warning(
            "Error de conexión/tiempo de espera (ID: %d): %s", user_id, str(e)
        )
        raise self.retry(exc=e)

    except Exception as e:
        logger.critical(
            "Error inesperado al enviar email de bienvenida: %s",
            str(e),
            exc_info=True,
            extra={"user_id": user_id},
        )
        raise


@shared_task(
    bind=True,
    max_retries=5,  # Más reintentos para recuperación
    default_retry_delay=30,
    autoretry_for=(SMTPException, ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_jitter=True,
)
def enviar_email_recuperarcion_contrasenia_task(
    self: Any, user_id: int, token: str
) -> None:
    try:
        user = User.objects.get(pk=user_id)
        email_sender = EmailSender()
        email_sender.enviar_email_recuperarcion_contrasenia(user, token)
        logger.info("Email de recuperación enviado a %s (ID: %d)", user.email, user_id)

    except ObjectDoesNotExist as e:
        logger.error(
            "Usuario no encontrado para recuperación (ID: %d): %s", user_id, str(e)
        )
        # No reintentar para este error
        raise

    except SMTPException as e:
        logger.error(
            "Error SMTP al enviar email de recuperación a %d: %s", user_id, str(e)
        )
        raise self.retry(exc=e)

    except (ConnectionError, TimeoutError) as e:
        logger.warning("Error de conexión al enviar email de recuperación: %s", str(e))
        raise self.retry(exc=e)

    except DatabaseError as e:
        logger.error("Error de base de datos al procesar recuperación: %s", str(e))
        raise self.retry(exc=e, countdown=120)  # Esperar más para DB

    except Exception as e:
        logger.critical(
            "Error inesperado en recuperación (ID: %d): %s",
            user_id,
            str(e),
            exc_info=True,
            extra={"user_id": user_id, "token": token[:5] + "..."},
        )
        raise
