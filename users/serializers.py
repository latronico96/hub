from typing import Any

from django.contrib.auth.models import Permission
from rest_framework.serializers import ModelSerializer

from .models import User


# pylint: disable=too-few-public-methods
class UserSerializer(ModelSerializer[User]):
    class Meta:
        model = User
        fields = [
            "id",
            "name",
            "email",
            "created_at",
            "updated_at",
            "is_active",
            "is_admin",
            "user_permissions",
            "can_be_deleted",
            "plan",
        ]

    def to_representation(self, instance: User) -> dict[str, Any]:
        representation = super().to_representation(instance)
        representation.pop("password", None)
        return representation


class PermissionSerializer(ModelSerializer[Permission]):
    class Meta:
        model = Permission
        fields = ["id", "name", "codename"]
