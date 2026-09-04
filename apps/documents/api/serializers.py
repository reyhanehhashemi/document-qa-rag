from pathlib import Path

from rest_framework import serializers

from apps.documents.models import Document


class DocumentListSerializer(serializers.ModelSerializer):
    """
    Compact serializer used for document lists.
    """

    chunk_count = serializers.SerializerMethodField()

    class Meta:
        model = Document

        fields = (
            "id",
            "title",
            "file",
            "original_filename",
            "status",
            "processing_error",
            "chunk_count",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "original_filename",
            "status",
            "processing_error",
            "chunk_count",
            "created_at",
            "updated_at",
        )

    def get_chunk_count(
        self,
        obj,
    ) -> int:
        annotated_count = getattr(
            obj,
            "api_chunk_count",
            None,
        )

        if annotated_count is not None:
            return annotated_count

        return obj.chunks.count()


class DocumentDetailSerializer(
    DocumentListSerializer
):
    """
    Full serializer used for create, retrieve, and update.
    """

    class Meta(
        DocumentListSerializer.Meta
    ):
        fields = (
            "id",
            "title",
            "file",
            "original_filename",
            "text_content",
            "status",
            "processing_error",
            "chunk_count",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "original_filename",
            "text_content",
            "status",
            "processing_error",
            "chunk_count",
            "created_at",
            "updated_at",
        )

    def validate_file(
        self,
        value,
    ):
        """
        Accept DOCX files only.
        """
        extension = Path(
            value.name
        ).suffix.lower()

        if extension != ".docx":
            raise serializers.ValidationError(
                "Only DOCX files are supported."
            )

        return value