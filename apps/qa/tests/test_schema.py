import json

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class APIDocumentationTests(APITestCase):
    def test_openapi_schema_is_available(
        self,
    ):
        response = self.client.get(
            reverse(
                "api-schema"
            ),
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        schema = json.loads(
            response.content
        )

        self.assertTrue(
            schema["openapi"].startswith(
                "3."
            )
        )

        self.assertEqual(
            schema["info"]["title"],
            "Document QA RAG API",
        )

        expected_paths = (
            "/api/v1/documents/",
            "/api/v1/questions/",
            "/api/v1/questions/ask/",
        )

        for path in expected_paths:
            self.assertIn(
                path,
                schema["paths"],
            )

    def test_swagger_ui_is_available(
        self,
    ):
        response = self.client.get(
            reverse(
                "api-docs"
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertContains(
            response,
            "swagger",
            status_code=status.HTTP_200_OK,
        )

    def test_redoc_ui_is_available(
        self,
    ):
        response = self.client.get(
            reverse(
                "api-redoc"
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertContains(
            response,
            "redoc",
            status_code=status.HTTP_200_OK,
        )