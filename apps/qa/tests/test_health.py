from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class APIHealthCheckTests(APITestCase):
    def test_health_check_returns_ok(
        self,
    ):
        response = self.client.get(
            reverse(
                "api-health"
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["status"],
            "ok",
        )

        self.assertEqual(
            response.data["database"],
            "ok",
        )

        self.assertEqual(
            response.data["version"],
            "1.0.0",
        )

    @patch(
        "config.api_views.connection.cursor"
    )
    def test_health_check_returns_503_when_database_fails(
        self,
        mocked_cursor,
    ):
        mocked_cursor.side_effect = RuntimeError(
            "Database unavailable."
        )

        response = self.client.get(
            reverse(
                "api-health"
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )

        self.assertEqual(
            response.data["error"]["code"],
            "service_unavailable",
        )

        self.assertEqual(
            response.data["error"]["message"],
            "Database health check failed.",
        )