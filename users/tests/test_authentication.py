from unittest import TestCase
from unittest.mock import MagicMock, patch

import jwt
from rest_framework.exceptions import AuthenticationFailed

from users.authentication import JWTAuthentication
from users.models import User


class TestJWTAuthentication(TestCase):
    def setUp(self) -> None:
        self.auth = JWTAuthentication()
        self.valid_token = jwt.encode({"id": 1}, "secret", algorithm="HS256")
        self.expired_token = jwt.encode(
            {"id": 1, "exp": 0}, "secret", algorithm="HS256"
        )
        self.invalid_token = "invalid.token.value"

    def test_authenticate_missing_authorization_header(self) -> None:
        request = MagicMock()
        request.headers = {}
        self.assertIsNone(self.auth.authenticate(request))

    def test_authenticate_invalid_token_format(self) -> None:
        request = MagicMock()
        request.headers = {"Authorization": "InvalidHeader"}
        self.assertIsNone(self.auth.authenticate(request))

    def test_authenticate_expired_token(self) -> None:
        request = MagicMock()
        request.headers = {"Authorization": f"Bearer {self.expired_token}"}
        with self.assertRaises(AuthenticationFailed) as context:
            self.auth.authenticate(request)
        self.assertEqual(str(context.exception), "Token expired")

    def test_authenticate_invalid_token(self) -> None:
        request = MagicMock()
        request.headers = {"Authorization": f"Bearer {self.invalid_token}"}
        with self.assertRaises(AuthenticationFailed) as context:
            self.auth.authenticate(request)
        self.assertEqual(str(context.exception), "Invalid token")

    @patch("users.models.User.objects.get")
    def test_authenticate_user_not_found(self, mock_get: MagicMock) -> None:
        mock_get.side_effect = User.DoesNotExist
        request = MagicMock()
        request.headers = {"Authorization": f"Bearer {self.valid_token}"}
        with self.assertRaises(AuthenticationFailed) as context:
            self.auth.authenticate(request)
        self.assertEqual(str(context.exception), "User not found")

    @patch("users.models.User.objects.get")
    def test_authenticate_success(self, mock_get: MagicMock) -> None:
        mock_user = MagicMock()
        mock_get.return_value = mock_user
        request = MagicMock()
        request.headers = {"Authorization": f"Bearer {self.valid_token}"}
        auth_result = self.auth.authenticate(request)
        assert auth_result is not None
        user, _ = auth_result
        self.assertEqual(user, mock_user)

    def test_authenticate_expired_token_exception(self) -> None:
        request = MagicMock()
        request.headers = {"Authorization": f"Bearer {self.expired_token}"}
        with self.assertRaises(AuthenticationFailed) as context:
            self.auth.authenticate(request)
        self.assertEqual(str(context.exception), "Token expired")

    def test_authenticate_invalid_token_exception(self) -> None:
        request = MagicMock()
        request.headers = {"Authorization": f"Bearer {self.invalid_token}"}
        with self.assertRaises(AuthenticationFailed) as context:
            self.auth.authenticate(request)
        self.assertEqual(str(context.exception), "Invalid token")

    @patch("users.models.User.objects.get")
    def test_authenticate_user_not_found_exception(self, mock_get: MagicMock) -> None:
        mock_get.side_effect = User.DoesNotExist
        request = MagicMock()
        request.headers = {"Authorization": f"Bearer {self.valid_token}"}
        with self.assertRaises(AuthenticationFailed) as context:
            self.auth.authenticate(request)
        self.assertEqual(str(context.exception), "User not found")
