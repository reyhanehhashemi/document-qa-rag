from django.db.models import Count
from rest_framework import (
    parsers,
    permissions,
    viewsets,
)

from apps.documents.models import Document
from apps.documents.services.pipeline import (
    run_document_pipeline,
)

from .serializers import (
    DocumentDetailSerializer,
    DocumentListSerializer,
)


class DocumentViewSet(
    viewsets.ModelViewSet
):
    """
    CRUD API for uploaded documents.

    Creating a document automatically runs extraction,
    chunking, embedding, and indexing.

    Updating only metadata such as the title does not
    rebuild embeddings. Replacing the file does.
    """

    permission_classes = [
        permissions.AllowAny,
    ]

    parser_classes = [
        parsers.JSONParser,
        parsers.FormParser,
        parsers.MultiPartParser,
    ]

    def get_queryset(self):
        return (
            Document.objects
            .annotate(
                api_chunk_count=Count(
                    "chunks"
                )
            )
            .order_by(
                "-created_at"
            )
        )

    def get_serializer_class(self):
        if self.action == "list":
            return DocumentListSerializer

        return DocumentDetailSerializer

    def perform_create(
        self,
        serializer,
    ):
        """
        Create and automatically process a new document.
        """
        document = serializer.save()

        run_document_pipeline(
            document
        )

    def perform_update(
        self,
        serializer,
    ):
        """
        Reprocess only when the uploaded file changes.
        """
        file_was_changed = (
            "file"
            in serializer.validated_data
        )

        document = serializer.save()

        if file_was_changed:
            run_document_pipeline(
                document
            )