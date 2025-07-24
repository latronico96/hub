from unittest import TestCase
from unittest.mock import MagicMock, patch

import jwt
import pytest
from rest_framework.exceptions import AuthenticationFailed

from users.authentication import JWTAuthentication
from users.models import User


@pytest.mark.django_db
class TestJWTAuthentication(TestCase):
    def setUp(self) -> None:
        self.auth = JWTAuthentication()
        self.valid_token = jwt.encode({"id": 1}, "secret", algorithm="HS256")
        self.expired_token = jwt.encode(
            {"id": 1, "exp": 0}, "secret", algorithm="HS256"
        )
        self.invalid_token = "invalid.token.value"

    def make_request(self, headers=None, cookies=None) -> MagicMock:
        request = MagicMock()
        request.headers = headers or {}
        request.COOKIES = cookies or {}
        return request

    def test_missing_authorization_header(self):
        request = self.make_request()
        self.assertIsNone(self.auth.authenticate(request))

    def test_invalid_token_format(self):
        request = self.make_request(headers={"Authorization": "InvalidHeader"})
        self.assertIsNone(self.auth.authenticate(request))

    @patch("users.models.User.objects.get")
    def test_valid_authorization_header(self, mock_get: MagicMock):
        mock_user = MagicMock()
        mock_get.return_value = mock_user
        request = self.make_request(
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )
        result = self.auth.authenticate(request)
        self.assertEqual(result[0], mock_user)

    @patch("users.models.User.objects.get")
    def test_valid_cookie_token(self, mock_get: MagicMock):
        mock_user = MagicMock()
        mock_get.return_value = mock_user
        request = self.make_request(cookies={"jwt_token": self.valid_token})
        result = self.auth.authenticate(request)
        self.assertEqual(result[0], mock_user)

    def test_invalid_token_in_cookie(self):
        request = self.make_request(cookies={"jwt_token": "not.a.valid.token"})
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    def test_no_token_anywhere(self):
        request = self.make_request()
        self.assertIsNone(self.auth.authenticate(request))

    def test_expired_token(self):
        request = self.make_request(
            headers={"Authorization": f"Bearer {self.expired_token}"}
        )
        with self.assertRaises(AuthenticationFailed) as context:
            self.auth.authenticate(request)
        self.assertEqual(str(context.exception), "Token expired")

    def test_invalid_token(self):
        request = self.make_request(
            headers={"Authorization": f"Bearer {self.invalid_token}"}
        )
        with self.assertRaises(AuthenticationFailed) as context:
            self.auth.authenticate(request)
        self.assertEqual(str(context.exception), "Invalid token")

    @patch("users.models.User.objects.get")
    def test_user_not_found(self, mock_get: MagicMock):
        mock_get.side_effect = User.DoesNotExist
        request = self.make_request(
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )
        with self.assertRaises(AuthenticationFailed) as context:
            self.auth.authenticate(request)
        self.assertEqual(str(context.exception), "User not found")
