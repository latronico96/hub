from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ..user_totals_cache import UserTotalsCache


# pylint: disable=too-many-ancestors
class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:  # type: ignore[override]
        user_id = request.user.id
        if user_id is None:
            raise ValueError("Authenticated user must have an ID")
        totals = UserTotalsCache().get(user_id)
        return Response(totals)
