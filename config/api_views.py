from django.conf import settings
from django.db import connection
from drf_spectacular.utils import (
    extend_schema,
)
from rest_framework import (
    permissions,
    status,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from config.api_exceptions import (
    ServiceUnavailable,
)
from config.api_serializers import (
    APIErrorSerializer,
    HealthCheckSerializer,
)


class HealthCheckAPIView(APIView):
    """
    Lightweight API and database health check.
    """

    permission_classes = [
        permissions.AllowAny,
    ]

    @extend_schema(
        tags=["System"],
        summary="Check API health",
        description=(
            "Check whether the API is running and "
            "the PostgreSQL database is reachable."
        ),
        responses={
            200: HealthCheckSerializer,
            503: APIErrorSerializer,
        },
    )
    def get(
        self,
        request,
    ):
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT 1"
                )
                cursor.fetchone()

        except Exception as exc:
            raise ServiceUnavailable(
                detail=(
                    "Database health check failed."
                )
            ) from exc

        api_version = (
            settings.SPECTACULAR_SETTINGS.get(
                "VERSION",
                "1.0.0",
            )
        )

        return Response(
            {
                "status": "ok",
                "database": "ok",
                "version": api_version,
            },
            status=status.HTTP_200_OK,
        )