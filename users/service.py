from typing import Optional

from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest

from .models import User


class UserService:
    def get_authenticated_user(self, request: HttpRequest) -> Optional[User]:
        user = request.user
        if isinstance(user, AnonymousUser):
            return None
        return user

    def is_admin_and_authenticated(self, request: HttpRequest) -> bool:
        user = self.get_authenticated_user(request)
        if user is None:
            return False
        return user.is_admin
