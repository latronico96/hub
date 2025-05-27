import logging
from smtplib import SMTPException
from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest
from celery.exceptions import Retry
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError

from hub.tasks import (
    enviar_email_de_bienvenida_task,
    enviar_email_recuperarcion_contrasenia_task,
)
from users.models import User


@pytest.fixture
def mock_user() -> User:
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_email_sender() -> Generator[Any, None, None]:
    with patch("hub.tasks.EmailSender") as mock:
        instance = mock.return_value
        yield instance


class TestEnviarEmailDeBienvenidaTask:
    def test_envio_exitoso(self, mock_user: User, mock_email_sender: Any) -> None:
        """Test que el email se envía correctamente"""
        with patch("hub.tasks.User.objects.get", return_value=mock_user):
            result = enviar_email_de_bienvenida_task(1)

            mock_email_sender.enviar_email_de_bienvenida.assert_called_once_with(
                mock_user
            )
            assert result is None

    def test_usuario_no_existe(self, mock_email_sender: Any) -> None:
        """Test cuando el usuario no existe"""
        with patch("hub.tasks.User.objects.get", side_effect=ObjectDoesNotExist):
            with pytest.raises(ObjectDoesNotExist):
                enviar_email_de_bienvenida_task(999)

        mock_email_sender.enviar_email_de_bienvenida.assert_not_called()

    def test_error_smtp_y_reintento(
        self, mock_user: User, mock_email_sender: Any
    ) -> None:
        """Test para errores SMTP que deben reintentarse"""
        mock_email_sender.enviar_email_de_bienvenida.side_effect = SMTPException(
            "Error SMTP"
        )

        with patch("hub.tasks.User.objects.get", return_value=mock_user):
            task = enviar_email_de_bienvenida_task.s(1)
            with pytest.raises(Retry):
                task.apply()

        mock_email_sender.enviar_email_de_bienvenida.assert_called_once_with(mock_user)

    def test_error_conexion_y_reintento(
        self, mock_user: User, mock_email_sender: Any
    ) -> None:
        """Test para errores de conexión que deben reintentarse"""
        mock_email_sender.enviar_email_de_bienvenida.side_effect = ConnectionError(
            "Error conexión"
        )

        with patch("hub.tasks.User.objects.get", return_value=mock_user):
            task = enviar_email_de_bienvenida_task.s(1)
            with pytest.raises(Retry):
                task.apply()

        mock_email_sender.enviar_email_de_bienvenida.assert_called_once_with(mock_user)

    def test_error_timeout_y_reintento(
        self, mock_user: User, mock_email_sender: Any
    ) -> None:
        """Test para timeouts que deben reintentarse"""
        mock_email_sender.enviar_email_de_bienvenida.side_effect = TimeoutError(
            "Timeout"
        )

        with patch("hub.tasks.User.objects.get", return_value=mock_user):
            task = enviar_email_de_bienvenida_task.s(1)
            with pytest.raises(Retry):
                task.apply()

        mock_email_sender.enviar_email_de_bienvenida.assert_called_once_with(mock_user)

    def test_error_inesperado(
        self, mock_user: User, mock_email_sender: Any, caplog: Any
    ) -> None:
        """Test para errores inesperados"""
        mock_email_sender.enviar_email_de_bienvenida.side_effect = Exception(
            "Error inesperado"
        )

        with patch("hub.tasks.User.objects.get", return_value=mock_user):
            with pytest.raises(Exception):
                enviar_email_de_bienvenida_task(1)

        assert "Error inesperado" in caplog.text
        mock_email_sender.enviar_email_de_bienvenida.assert_called_once_with(mock_user)

    def test_logging_exitoso(
        self, mock_user: User, mock_email_sender: Any, caplog: Any
    ) -> None:
        """Test que verifica el logging en caso exitoso"""
        import hub.tasks

        hub.tasks.logger.setLevel(logging.INFO)  # <--- Asegura nivel INFO
        caplog.clear()
        with caplog.at_level(logging.INFO, logger="hub.tasks"):
            with patch("hub.tasks.User.objects.get", return_value=mock_user):
                enviar_email_de_bienvenida_task(1)
        assert "Email de bienvenida enviado exitosamente" in caplog.text
        assert str(mock_user.email) in caplog.text
        assert str(mock_user.id) in caplog.text


class TestEnviarEmailRecuperacionContraseniaTask:
    def test_envio_exitoso(self, mock_user: User, mock_email_sender: Any) -> None:
        """Test que el email de recuperación se envía correctamente"""
        test_token = "test_token123"
        method = mock_email_sender.enviar_email_recuperarcion_contrasenia

        with patch("hub.tasks.User.objects.get", return_value=mock_user):
            result = enviar_email_recuperarcion_contrasenia_task(1, test_token)

            method.assert_called_once_with(mock_user, test_token)
            assert result is None

    def test_usuario_no_existe(self, mock_email_sender: Any) -> None:
        """Test cuando el usuario no existe para recuperación"""
        method = mock_email_sender.enviar_email_recuperarcion_contrasenia

        with patch("hub.tasks.User.objects.get", side_effect=ObjectDoesNotExist):
            with pytest.raises(ObjectDoesNotExist):
                enviar_email_recuperarcion_contrasenia_task(999, "token")

        method.assert_not_called()

    def test_error_smtp_y_reintento(
        self, mock_user: User, mock_email_sender: Any
    ) -> None:
        """Test para errores SMTP en recuperación que deben reintentarse"""
        test_token = "test_token123"
        method = mock_email_sender.enviar_email_recuperarcion_contrasenia
        method.side_effect = SMTPException("Error SMTP")

        with patch("hub.tasks.User.objects.get", return_value=mock_user):
            task = enviar_email_recuperarcion_contrasenia_task.s(1, test_token)
            with pytest.raises(Retry):
                task.apply()

        method.assert_called_once_with(mock_user, test_token)

    def test_error_conexion_y_reintento(
        self, mock_user: User, mock_email_sender: Any
    ) -> None:
        """Test para errores de conexión en recuperación"""
        test_token = "test_token123"
        method = mock_email_sender.enviar_email_recuperarcion_contrasenia
        method.side_effect = ConnectionError("Error conexión")

        with patch("hub.tasks.User.objects.get", return_value=mock_user):
            task = enviar_email_recuperarcion_contrasenia_task.s(1, test_token)
            with pytest.raises(Retry):
                task.apply()

        method.assert_called_once_with(mock_user, test_token)

    def test_error_timeout_y_reintento(
        self, mock_user: User, mock_email_sender: Any
    ) -> None:
        """Test para timeouts en recuperación"""
        test_token = "test_token123"
        method = mock_email_sender.enviar_email_recuperarcion_contrasenia
        method.side_effect = TimeoutError("Timeout")

        with patch("hub.tasks.User.objects.get", return_value=mock_user):
            task = enviar_email_recuperarcion_contrasenia_task.s(1, test_token)
            with pytest.raises(Retry):
                task.apply()

        method.assert_called_once_with(mock_user, test_token)

    def test_error_db_y_reintento(
        self, mock_user: User, mock_email_sender: Any
    ) -> None:
        """Test para errores de base de datos en recuperación"""
        test_token = "test_token123"
        method = mock_email_sender.enviar_email_recuperarcion_contrasenia
        method.side_effect = DatabaseError("Error DB")

        with patch("hub.tasks.User.objects.get", return_value=mock_user):
            task = enviar_email_recuperarcion_contrasenia_task.s(1, test_token)
            with pytest.raises(Retry):
                task.apply()

        method.assert_called_once_with(mock_user, test_token)

    def test_error_inesperado_recuperacion(
        self, mock_user: User, mock_email_sender: Any, caplog: Any
    ) -> None:
        """Test para errores inesperados en recuperación"""
        test_token = "test_token123"
        method = mock_email_sender.enviar_email_recuperarcion_contrasenia
        method.side_effect = Exception("Error inesperado")

        with patch("hub.tasks.User.objects.get", return_value=mock_user):
            with pytest.raises(Exception):
                enviar_email_recuperarcion_contrasenia_task(1, test_token)

        assert "Error inesperado" in caplog.text
        assert "token" in caplog.text
        method.assert_called_once_with(mock_user, test_token)

    def test_logging_exitoso_recuperacion(
        self, mock_user: User, mock_email_sender: Any, caplog: Any
    ) -> None:
        """Test que verifica el logging en caso exitoso de recuperación"""
        import hub.tasks

        test_token = "test_token123"
        method = mock_email_sender.enviar_email_recuperarcion_contrasenia

        hub.tasks.logger.setLevel(logging.INFO)
        caplog.clear()
        with caplog.at_level(logging.INFO, logger="hub.tasks"):
            with patch("hub.tasks.User.objects.get", return_value=mock_user):
                enviar_email_recuperarcion_contrasenia_task(1, test_token)

        assert "Email de recuperación enviado" in caplog.text
        assert str(mock_user.email) in caplog.text
        assert str(mock_user.id) in caplog.text
        method.assert_called_once_with(mock_user, test_token)
