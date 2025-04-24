import jwt
from django.http import HttpRequest
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from users.models import User  # o donde tengas tu modelo


class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request: HttpRequest) -> tuple[User, None] | None:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, "secret", algorithms=["HS256"])
        except jwt.ExpiredSignatureError as exc:
            raise AuthenticationFailed("Token expired") from exc
        except jwt.InvalidTokenError as exc:
            raise AuthenticationFailed("Invalid token") from exc

        try:
            user = User.objects.get(id=payload["id"])
        except User.DoesNotExist as exc:
            raise AuthenticationFailed("User not found") from exc

        return (user, None)
