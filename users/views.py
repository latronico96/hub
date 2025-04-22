import datetime

import jwt
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import User
from .serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(
        detail=False, methods=["post"], url_path="login", permission_classes=[AllowAny]
    )
    def login(self, request):
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
    def register(self, request):
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
            user = User.objects.create_user(
                email=email,
                password=password,  # This will be hashed by create_user
                name=name,
            )
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "detail": "User created successfully",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                },
            },
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="me",
    )
    def me(self):
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
