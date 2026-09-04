from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class DeploymentConfigurationTests(
    SimpleTestCase
):
    def test_whitenoise_middleware_is_enabled(
        self,
    ):
        middleware = (
            "whitenoise.middleware."
            "WhiteNoiseMiddleware"
        )

        self.assertIn(
            middleware,
            settings.MIDDLEWARE,
        )

        security_index = (
            settings.MIDDLEWARE.index(
                "django.middleware.security."
                "SecurityMiddleware"
            )
        )

        whitenoise_index = (
            settings.MIDDLEWARE.index(
                middleware
            )
        )

        self.assertEqual(
            whitenoise_index,
            security_index + 1,
        )

    def test_whitenoise_static_storage_is_configured(
        self,
    ):
        backend = (
            settings.STORAGES[
                "staticfiles"
            ][
                "BACKEND"
            ]
        )

        self.assertEqual(
            backend,
            (
                "whitenoise.storage."
                "CompressedStaticFilesStorage"
            ),
        )

    def test_static_root_is_configured(
        self,
    ):
        self.assertIsInstance(
            settings.STATIC_ROOT,
            Path,
        )

        self.assertTrue(
            str(
                settings.STATIC_ROOT
            )
        )