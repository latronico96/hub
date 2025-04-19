from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'created_at', 'is_active', 'is_admin']
        def to_representation(self, instance):
            representation = super().to_representation(instance)
            representation.pop('password', None)  # Elimina 'password' si existe
            return representation
