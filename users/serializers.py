from typing import Any

from rest_framework import serializers

from .models import User


# pylint: disable=too-few-public-methods
class UserSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = [
            "id",
            "name",
            "email",
            "created_at",
            "is_active",
            "is_admin",
        ]

    def to_representation(self, instance: User) -> dict[str, Any]:
        representation = super().to_representation(instance)
        representation.pop("password", None)
        return representation
