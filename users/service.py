from typing import Optional

import mercadopago
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest

from hub.settings import MERCADOPAGO

from .models import Plan, User


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

    def get_mp_sdk(self):
        return mercadopago.SDK(MERCADOPAGO["access_token"])

    def get_link_to_pay(self, user: User, plan_id: int):
        sdk = self.get_mp_sdk()

        external_reference = f"USER_{user.id}_PLAN_{plan_id}"

        plan_a_pagar = Plan.objects.get(id=plan_id)

        payload = {
            "items": [
                {
                    "title": plan_a_pagar.nombre,
                    "quantity": 1,
                    "unit_price": plan_a_pagar.precio,
                    "currency_id": "ARS",
                }
            ],
            "back_urls": {
                "success": MERCADOPAGO["success_url"],
                "failure": MERCADOPAGO["failure_url"],
                "pending": MERCADOPAGO["failure_url"],
            },
            "auto_return": "approved",
            "notification_url": MERCADOPAGO["notification_url"],
            "external_reference": external_reference,
        }

        return sdk.preference().create(payload)
