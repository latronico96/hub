from __future__ import annotations

from typing import Any

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
        # Importación diferida para evitar dependencias circulares
        from recetario.models import Unidad, Producto, Receta, Ingrediente

        tiene_unidades = Unidad.objects.filter(user=self).exists()
        tiene_productos = Producto.objects.filter(user=self).exists()
        tiene_recetas = Receta.objects.filter(user=self).exists()
        tiene_ingredientes = Ingrediente.objects.filter(user=self).exists()

        return not any([tiene_unidades, tiene_productos, tiene_recetas, tiene_ingredientes])

    def delete_cascade(self):
        from recetario.models import Unidad, Producto, Receta, Ingrediente

        Ingrediente.objects.filter(user=self).delete()
        Producto.objects.filter(user=self).delete()
        Unidad.objects.filter(user=self).delete()
        Receta.objects.filter(user=self).delete()

        self.delete()
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-created_at"]
