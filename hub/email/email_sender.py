from typing import Any

from django.core.mail import EmailMultiAlternatives
from jinja2 import Environment, FileSystemLoader

from hub.settings import (
    EMAIL_HOST,
    EMAIL_HOST_PASSWORD,
    EMAIL_HOST_USER,
    EMAIL_PORT,
    STATIC_FRONTEND_URL,
)
from users.models import User


class EmailSender:
    def __init__(
        self,
        smtp_server: str = EMAIL_HOST,
        smtp_port: int = EMAIL_PORT,
        remitente: str = EMAIL_HOST_USER,
        contrasenia: str = EMAIL_HOST_PASSWORD,
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.remitente = remitente
        self.contrasenia = contrasenia

    def enviar_email_de_bienvenida(self, user: User) -> None:
        self.enviar_email_con_template(
            "email_template",
            user.email,
            {"nombre": user.name},
            "Bienvenido a Recetario COCOL",
        )

    def enviar_email_con_usuario(
        self,
        user: User,
        template_file_name: str,
        variables: dict[str, Any],
        subjet: str,
    ) -> None:
        self.enviar_email_con_template(
            template_file_name, user.email, variables, subjet
        )

    def enviar_email_con_template(
        self,
        template_file_name: str,
        email_destinatario: str,
        variables: dict[str, Any],
        subject: str,
    ) -> None:

        env = Environment(loader=FileSystemLoader("hub/email/templates"))
        template = env.get_template(template_file_name + ".html")
        html_contenido = template.render(**variables)

        # Crear y enviar el email con Django
        mensaje = EmailMultiAlternatives(
            subject=subject,
            body=html_contenido,  # fallback text, puede ir vacío si solo querés HTML
            from_email=self.remitente,
            to=[email_destinatario],
        )
        mensaje.attach_alternative(html_contenido, "text/html")
        mensaje.send()

    def enviar_email_recuperarcion_contrasenia(self, user: User, token: str) -> None:
        # Renderizar el template
        url_token_form = STATIC_FRONTEND_URL + "/updatePassword?token=" + token

        self.enviar_email_con_template(
            "email_Reset_password",
            user.email,
            {"nombre": user.name, "url": url_token_form},
            "Recuperar contraseña",
        )
