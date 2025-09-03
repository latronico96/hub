import logging
import threading
from smtplib import SMTPException

from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError

from hub.email.email_sender import EmailSender
from hub.settings import is_testing
from users.models import User

logger = logging.getLogger(__name__)


def enviar_email_de_bienvenida_sincronico(user_id: int) -> None:
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
        raise

    except SMTPException as e:
        logger.error(
            "Error SMTP al enviar email a %d: %s", user_id, str(e), exc_info=True
        )
        raise

    except (ConnectionError, TimeoutError) as e:
        logger.warning(
            "Error de conexión/tiempo de espera (ID: %d): %s", user_id, str(e)
        )
        raise

    except Exception as e:
        logger.critical(
            "Error inesperado al enviar email de bienvenida: %s",
            str(e),
            exc_info=True,
            extra={"user_id": user_id},
        )
        raise


def enviar_email_recuperarcion_contrasenia_sincronico(user_id: int, token: str) -> None:
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
        raise

    except (ConnectionError, TimeoutError) as e:
        logger.warning("Error de conexión al enviar email de recuperación: %s", str(e))
        raise

    except DatabaseError as e:
        logger.error("Error de base de datos al procesar recuperación: %s", str(e))
        raise

    except Exception as e:
        logger.critical(
            "Error inesperado en recuperación (ID: %d): %s",
            user_id,
            str(e),
            exc_info=True,
            extra={"user_id": user_id, "token": token[:5] + "..."},
        )
        raise


# Funciones públicas que las otras partes de la app usarán.
def enviar_email_de_bienvenida(user_id: int) -> None:
    if is_testing:
        enviar_email_de_bienvenida_sincronico(user_id)
        return
    hilo = threading.Thread(
        target=enviar_email_de_bienvenida_sincronico, args=(user_id,)
    )
    hilo.start()


def enviar_email_recuperacion(user_id: int, token: str) -> None:
    if is_testing:
        enviar_email_recuperarcion_contrasenia_sincronico(user_id, token)
        return
    hilo = threading.Thread(
        target=enviar_email_recuperarcion_contrasenia_sincronico, args=(user_id, token)
    )
    hilo.start()
