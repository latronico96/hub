import datetime
import logging
from typing import Any

import jwt
from django.contrib.auth import authenticate
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import (
    AllowAny,
    IsAdminUser,
    IsAuthenticated,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from hub.tasks import enviar_email_recuperacion

from .authentication import JWTAuthentication
from .models import User
from .serializers import PermissionSerializer, UserSerializer
from .service import UserService

logger = logging.getLogger(__name__)


# pylint: disable=too-many-ancestors
class UserViewSet(viewsets.ModelViewSet[User]):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    user_service = UserService()

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = self.get_object()
        force = request.query_params.get("force", "false").lower() == "true"

        if user.can_be_deleted:
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if force:
            user.delete_cascade()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {
                "detail": (
                    "Este usuario tiene:"
                    "unidades, productos, recetas o ingredientes asociados."
                    "Usá el parámetro `?force=true` para forzar el borrado en cascada."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

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
            "roles": [perm.codename for perm in user.user_permissions.all()],
            "is_admin": user.is_admin,
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
        print(name, email, password)

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
            "roles": [perm.codename for perm in user_logged.user_permissions.all()],
            "is_admin": user_logged.is_admin,
        }
        token = jwt.encode(payload, "secret", algorithm="HS256")

        return Response({"token": token})

    @action(
        detail=False,
        methods=["get"],
        url_path="me",
        permission_classes=[IsAuthenticated],
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
        user_id_raw: Any | None = request.data.get("userId")
        if not user_id_raw:
            return Response(
                {"detail": "userId is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user_id: int = int(user_id_raw)

        try:
            user: User = User.objects.get(id=user_id)
            now = datetime.datetime.now()
            exp = now + datetime.timedelta(minutes=20)

            payload = {
                "id": user.id,
                "exp": int(exp.timestamp()),
                "iat": int(now.timestamp()),
            }
            token = jwt.encode(payload, "secret", algorithm="HS256")
            enviar_email_recuperacion(user.id, token)
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

    @action(
        detail=False,
        methods=["get"],
        url_path="linkDePago",
        permission_classes=[IsAuthenticated],
    )
    def get_link_de_pago(self, request: Request) -> Response:
        plan_id_str: str | None = request.data.get("planId")

        if not plan_id_str:
            return Response(
                {"detail": "Plan id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            plan_id = int(plan_id_str)
        except ValueError:
            return Response(
                {"detail": "Plan id must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = self.user_service.get_authenticated_user(self.request)

        result = self.user_service.get_link_to_pay(user, plan_id)
        preference = result["response"]
        return JsonResponse(
            {
                "preference_id": preference["id"],
                "init_point": preference.get("init_point"),
            }
        )


class MercadoPagoIPNView(APIView):
    # 1. Permite acceso a cualquiera (Mercado Pago)
    permission_classes = [AllowAny]
    user_service = UserService()

    def post(self, request, *args, **kwargs):
        # 2. Captura los parámetros de la Query String
        # type y id son las claves esenciales que envía MP
        topic = request.query_params.get("topic")
        resource_id = request.query_params.get("id")

        if not topic or not resource_id:
            # Si no vienen los parámetros, se responde 400.
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

        sdk = self.user_service.get_mp_sdk()

        try:
            # 3. Consultar a la API de MP (Paso de seguridad)

            # El topic indica qué API consultar (payment, merchant_order, etc.)
            if topic == "payment":
                response = sdk.payment().get(resource_id)
            elif topic == "merchant_order":
                response = sdk.merchant_order().get(resource_id)
            else:
                # Si el topic es desconocido, no se procesa, pero se responde 200
                return HttpResponse(status=status.HTTP_200_OK)

            data = response["response"]

            # 4. Procesar el estado y la Referencia Externa

            # Se usa el external_reference que enviaste al crear la preferencia
            external_reference = data.get("external_reference")
            print(external_reference)
            payment_status = data.get("status")  # approved, pending, rejected, etc.

            if response["status"] != 200 or not external_reference:
                # Si MP no devuelve el recurso, se asume error o recurso no listo.
                # No se puede traquear: error lógico tuyo
                return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

            # Extraer el ID del usuario del external_reference (ej: "USER_123_PLAN_456")
            try:
                # Asume un formato como "USER_{id}_PLAN_{plan_id}"
                user_id = int(external_reference.split("_")[1])
                user = User.objects.get(id=user_id)
            except (User.DoesNotExist, IndexError, ValueError):
                # Error si el formato de external_reference es incorrecto
                # o si el ID no es un número
                return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

            # 5. Lógica de Negocio
            if payment_status == "approved":
                # Aquí ejecutas la lógica crucial:
                # - Activar la cuenta del 'user'.
                # - Actualizar el plan del 'user'.
                # - Guardar los detalles de la transacción en tu modelo de 'Payment'.
                print(f"Pago APROBADO para el usuario: {user.id}")
            elif payment_status in ["pending", "in_process"]:
                # Lógica para pagos pendientes
                print(f"Pago PENDIENTE para el usuario: {user.id}")
            else:
                # Lógica para pagos fallidos/rechazados (rejected)
                print(f"Pago RECHAZADO para el usuario: {user.id}")

            # 6. Respuesta final (fundamental para MP)
            # Siempre debes responder 200 OK para que MP
            # sepa que la notificación se recibió
            return HttpResponse(status=status.HTTP_200_OK)

        except Exception as e:
            # Manejo de errores generales (logging)
            print(f"Error procesando IPN: {e}")
            return HttpResponse(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PermissionViewSet(ReadOnlyModelViewSet[Permission]):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]
