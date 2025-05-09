from __future__ import annotations

from typing import Any

from django.apps import apps
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    Permission,
    PermissionsMixin,
)
from django.db import models


class UserManager(BaseUserManager["User"]):
    def create_user(
        self, email: str, password: str | None = None, **extra_fields: Any
    ) -> "User":
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, email: str, password: str | None = None, **extra_fields: Any
    ) -> "User":
        extra_fields.setdefault("is_admin", True)

        return self.create_user(email, password, name=email)


class User(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    user_permissions = models.ManyToManyField(Permission, blank=True)

    objects: UserManager = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    def __str__(self) -> str:
        return f"{self.name}"

    @property
    def is_staff(self) -> bool:
        return self.is_admin

    @property
    def can_be_deleted(self) -> bool:
        unidad_model = apps.get_model("recetario", "Unidad")
        producto_model = apps.get_model("recetario", "Producto")
        receta_model = apps.get_model("recetario", "Receta")
        ingrediente_model = apps.get_model("recetario", "Ingrediente")

        tiene_unidades = unidad_model.objects.filter(user=self).exists()
        tiene_productos = producto_model.objects.filter(user=self).exists()
        tiene_recetas = receta_model.objects.filter(user=self).exists()
        tiene_ingredientes = ingrediente_model.objects.filter(user=self).exists()

        return not any(
            [tiene_unidades, tiene_productos, tiene_recetas, tiene_ingredientes]
        )

    def delete_cascade(self) -> None:
        unidad_model = apps.get_model("recetario", "Unidad")
        producto_model = apps.get_model("recetario", "Producto")
        receta_model = apps.get_model("recetario", "Receta")
        ingrediente_model = apps.get_model("recetario", "Ingrediente")

        ingrediente_model.objects.filter(user=self).delete()
        producto_model.objects.filter(user=self).delete()
        unidad_model.objects.filter(user=self).delete()
        receta_model.objects.filter(user=self).delete()

        self.delete()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-created_at"]
