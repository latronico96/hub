import datetime
import logging

import jwt
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from hub.email.email_sender import EmailSender

from .authentication import JWTAuthentication
from .models import User
from .serializers import UserSerializer

logger = logging.getLogger(__name__)


# pylint: disable=too-many-ancestors
class UserViewSet(viewsets.ModelViewSet[User]):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(
        detail=False, methods=["post"], url_path="login", permission_classes=[AllowAny]
    )
    def login(self, request: Request) -> Response:
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"error": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=email, password=password)

        if not user:
            raise AuthenticationFailed("Invalid credentials")

        payload = {
            "id": user.id,
            "exp": datetime.datetime.now() + datetime.timedelta(hours=24),
            "iat": datetime.datetime.now(),
        }
        token = jwt.encode(payload, "secret", algorithm="HS256")

        return Response({"token": token})

    @action(
        detail=False,
        methods=["post"],
        url_path="register",
        permission_classes=[AllowAny],
    )
    def register(self, request: Request) -> Response:
        name = request.data.get("name")
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password or not name:
            return Response(
                {"detail": "Username, email, and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {"detail": "Email already exists."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            User.objects.create_user(
                email=email,
                password=password,
                name=name,
            )
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        user_logged = authenticate(request, username=email, password=password)

        if not user_logged:
            raise AuthenticationFailed("Invalid credentials")

        payload = {
            "id": user_logged.id,
            "exp": datetime.datetime.now() + datetime.timedelta(hours=24),
            "iat": datetime.datetime.now(),
        }
        token = jwt.encode(payload, "secret", algorithm="HS256")

        return Response({"token": token})

    @action(
        detail=False,
        methods=["get"],
        url_path="me",
    )
    def me(self, request: Request) -> Response:
        """
        Endpoint to get the current user's information.
        """
        user = self.request.user
        if not user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["post"],
        url_path="forgot-password",
        permission_classes=[AllowAny],
    )
    def forgot_password(self, request: Request) -> Response:
        """
        Endpoint to handle password reset requests.
        """
        email = request.data.get("email")
        if not email:
            return Response(
                {"detail": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
            now = datetime.datetime.now()
            exp = now + datetime.timedelta(minutes=20)

            payload = {
                "id": user.id,
                "exp": int(exp.timestamp()),
                "iat": int(now.timestamp()),
            }
            token = jwt.encode(payload, "secret", algorithm="HS256")
            email_sender: EmailSender = EmailSender()
            email_sender.enviar_email_recuperarcion_contrasenia(user, token)
        except User.DoesNotExist as e:
            logger.error("Ocurrió un error: %s", str(e), exc_info=True)
            return Response(
                {"detail": "User with this email does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {"detail": "Si el correo existe, se ha enviado un email de recuperación."},
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["post"],
        url_path="reset-password",
        permission_classes=[AllowAny],
    )
    def update_password(self, request: Request) -> Response:
        """
        Endpoint to update the user's password.
        """

        token: str | None = request.data.get("token")
        new_password = request.data.get("password")
        if not new_password:
            return Response(
                {"detail": "New password is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not token:
            return Response(
                {"detail": "Token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user: User = JWTAuthentication.get_user(token)
        except User.DoesNotExist as e:
            logger.error("Ocurrió un error: %s", str(e), exc_info=True)
            return Response(
                {"detail": "User with this email does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except (
            AuthenticationFailed,
            jwt.ExpiredSignatureError,
            jwt.InvalidTokenError,
        ) as e:
            logger.error("Ocurrió un error: %s", str(e), exc_info=True)
            return Response(
                {"detail": "Invalid token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()

        return Response({"detail": "Password updated successfully."})
