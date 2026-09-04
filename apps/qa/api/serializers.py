from rest_framework import serializers

from apps.documents.models import Document
from apps.qa.models import (
    QuestionAnswer,
    QuestionAnswerSource,
)


class AskQuestionSerializer(serializers.Serializer):
    """
    Validate input for the document question answering API.
    """

    question = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
        help_text=(
            "Question to answer using indexed document content."
        ),
    )

    document_ids = serializers.ListField(
        child=serializers.IntegerField(
            min_value=1,
        ),
        required=False,
        allow_null=True,
        default=None,
        help_text=(
            "Optional indexed document IDs. "
            "Omit, use null, or use an empty list "
            "to search all indexed documents."
        ),
    )

    top_k = serializers.IntegerField(
        min_value=1,
        max_value=10,
        required=False,
        default=5,
        help_text=(
            "Maximum number of retrieved chunks."
        ),
    )

    min_similarity = serializers.FloatField(
        min_value=0.0,
        max_value=1.0,
        required=False,
        default=0.20,
        help_text=(
            "Minimum cosine similarity required "
            "for a retrieved chunk."
        ),
    )

    def validate_document_ids(
        self,
        value,
    ):
        """
        Selected documents must exist and already be indexed.

        An omitted, null, or empty list means:
        search all indexed documents.
        """
        if not value:
            return None

        normalized_ids = list(
            dict.fromkeys(
                value
            )
        )

        indexed_ids = set(
            Document.objects.filter(
                id__in=normalized_ids,
                status=Document.Status.INDEXED,
            ).values_list(
                "id",
                flat=True,
            )
        )

        invalid_ids = [
            document_id
            for document_id in normalized_ids
            if document_id not in indexed_ids
        ]

        if invalid_ids:
            raise serializers.ValidationError(
                (
                    "All selected documents must exist "
                    "and be indexed. Invalid document IDs: "
                    f"{invalid_ids}"
                )
            )

        return normalized_ids


class QuestionAnswerSourceSerializer(
    serializers.ModelSerializer
):
    """
    Source snapshot returned with a question answer.
    """

    chunk_id = serializers.IntegerField(
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = QuestionAnswerSource

        fields = (
            "id",
            "chunk_id",
            "document_id_snapshot",
            "document_title",
            "chunk_index",
            "similarity",
            "created_at",
        )

        read_only_fields = fields


class QuestionAnswerListSerializer(
    serializers.ModelSerializer
):
    """
    Compact serializer for question-answer history lists.
    """

    source_count = serializers.SerializerMethodField()

    class Meta:
        model = QuestionAnswer

        fields = (
            "id",
            "question",
            "answer",
            "top_k",
            "min_similarity",
            "document_ids",
            "source_count",
            "created_at",
        )

        read_only_fields = fields

    def get_source_count(
        self,
        obj,
    ) -> int:
        annotated_count = getattr(
            obj,
            "api_source_count",
            None,
        )

        if annotated_count is not None:
            return annotated_count

        return obj.sources.count()


class QuestionAnswerDetailSerializer(
    serializers.ModelSerializer
):
    """
    Complete history serializer including source snapshots.
    """

    sources = QuestionAnswerSourceSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = QuestionAnswer

        fields = (
            "id",
            "question",
            "answer",
            "top_k",
            "min_similarity",
            "document_ids",
            "sources",
            "created_at",
        )

        read_only_fields = fields


class ErrorDetailSerializer(
    serializers.Serializer
):
    """
    Standard service error response.
    """

    detail = serializers.CharField(
        read_only=True,
    )