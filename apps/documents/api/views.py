from django.db.models import Count
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
)
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


@extend_schema_view(
    list=extend_schema(
        tags=["Documents"],
        summary="List documents",
        description=(
            "Return all uploaded documents. "
            "The list response omits full extracted text."
        ),
    ),
    create=extend_schema(
        tags=["Documents"],
        summary="Upload and index a DOCX document",
        description=(
            "Upload a DOCX document. The document is automatically "
            "processed, chunked, embedded, and indexed."
        ),
    ),
    retrieve=extend_schema(
        tags=["Documents"],
        summary="Retrieve a document",
        description=(
            "Return one document including its full extracted text."
        ),
    ),
    update=extend_schema(
        tags=["Documents"],
        summary="Replace a document",
        description=(
            "Update a document. Replacing the uploaded file runs "
            "the complete processing and indexing pipeline again."
        ),
    ),
    partial_update=extend_schema(
        tags=["Documents"],
        summary="Partially update a document",
        description=(
            "Update selected document fields. A title-only update "
            "does not rebuild embeddings. Replacing the file does."
        ),
    ),
    destroy=extend_schema(
        tags=["Documents"],
        summary="Delete a document",
        description="Delete the document and its related chunks.",
    ),
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