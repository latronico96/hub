import jwt
from django.http import HttpRequest
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from users.models import User


class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request: HttpRequest) -> tuple[User, None] | None:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        token = auth_header.split(" ")[1]
        user = self.get_user(token)
        return (user, None)

    @staticmethod
    def get_user(token: str) -> User:
        if not token or not token.strip():
            raise AuthenticationFailed("Token is missing or empty")

        try:
            payload = jwt.decode(token, "secret", algorithms=["HS256"])
            user = User.objects.get(id=payload["id"])
            return user
        except User.DoesNotExist as exc:
            raise AuthenticationFailed("User not found") from exc
        except jwt.ExpiredSignatureError as exc:
            raise AuthenticationFailed("Token expired") from exc
        except jwt.InvalidTokenError as exc:
            raise AuthenticationFailed("Invalid token") from exc
