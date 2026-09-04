"""
URL configuration for the Document QA RAG project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import (
    include,
    path,
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from config.api_views import (
    HealthCheckAPIView,
)


urlpatterns = [
    path(
        "admin/",
        admin.site.urls,
    ),

    # System
    path(
        "api/health/",
        HealthCheckAPIView.as_view(),
        name="api-health",
    ),

    # API documentation
    path(
        "api/schema/",
        SpectacularAPIView.as_view(),
        name="api-schema",
    ),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(
            url_name="api-schema"
        ),
        name="api-docs",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(
            url_name="api-schema"
        ),
        name="api-redoc",
    ),

    # API v1
    path(
        "api/v1/",
        include(
            "apps.documents.api.urls"
        ),
    ),
    path(
        "api/v1/",
        include(
            "apps.qa.api.urls"
        ),
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )