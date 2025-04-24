from __future__ import annotations

from typing import Any

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
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
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser):
    name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects: UserManager = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def __str__(self) -> str:
        return f"{self.name}"

    def has_perm(self, _: str, __: Any = None) -> bool:
        return True

    def has_module_perms(self, _: str) -> bool:
        return True

    @property
    def is_staff(self) -> bool:
        return self.is_admin
