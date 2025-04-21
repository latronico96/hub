from rest_framework import serializers

from .models import Unidad


class UnidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unidad
        fields = "__all__"
