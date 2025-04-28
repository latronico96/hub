import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from jinja2 import Environment, FileSystemLoader

from hub.settings import EMAIL_HOST, EMAIL_HOST_PASSWORD, EMAIL_HOST_USER, EMAIL_PORT
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
        subjet: str,
    ) -> None:
        # Renderizar el template
        env = Environment(loader=FileSystemLoader("recetario/email/templates"))
        template = env.get_template(template_file_name + ".html")
        html_contenido = template.render(**variables)

        # Crear email
        mensaje = MIMEMultipart("alternative")
        mensaje["Subject"] = subjet
        mensaje["From"] = self.remitente
        mensaje["To"] = email_destinatario

        parte_html = MIMEText(html_contenido, "html")
        mensaje.attach(parte_html)

        # Enviar el email
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.remitente, self.contrasenia)
            server.send_message(mensaje)
