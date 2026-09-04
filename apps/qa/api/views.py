from django.db.models import Count
from rest_framework import (
    generics,
    permissions,
    status,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.qa.models import QuestionAnswer
from apps.qa.services.exceptions import RAGServiceError
from apps.qa.services.history import (
    answer_and_save_question,
)

from .serializers import (
    AskQuestionSerializer,
    QuestionAnswerDetailSerializer,
    QuestionAnswerListSerializer,
)


class AskQuestionAPIView(APIView):
    """
    Run the complete RAG pipeline and persist its result.
    """

    permission_classes = [
        permissions.AllowAny,
    ]

    def post(
        self,
        request,
    ):
        input_serializer = AskQuestionSerializer(
            data=request.data,
        )

        input_serializer.is_valid(
            raise_exception=True
        )

        validated_data = (
            input_serializer.validated_data
        )

        try:
            history = answer_and_save_question(
                question=validated_data[
                    "question"
                ],
                top_k=validated_data[
                    "top_k"
                ],
                min_similarity=validated_data[
                    "min_similarity"
                ],
                document_ids=validated_data[
                    "document_ids"
                ],
            )

        except RAGServiceError as exc:
            return Response(
                {
                    "detail": str(
                        exc
                    ),
                },
                status=(
                    status.HTTP_503_SERVICE_UNAVAILABLE
                ),
            )

        history = (
            QuestionAnswer.objects
            .prefetch_related(
                "sources"
            )
            .get(
                pk=history.pk
            )
        )

        output_serializer = (
            QuestionAnswerDetailSerializer(
                history,
                context={
                    "request": request,
                },
            )
        )

        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class QuestionAnswerListAPIView(
    generics.ListAPIView
):
    """
    Read-only question-answer history list.
    """

    serializer_class = (
        QuestionAnswerListSerializer
    )

    permission_classes = [
        permissions.AllowAny,
    ]

    def get_queryset(self):
        return (
            QuestionAnswer.objects
            .annotate(
                api_source_count=Count(
                    "sources"
                )
            )
            .order_by(
                "-created_at"
            )
        )


class QuestionAnswerDetailAPIView(
    generics.RetrieveAPIView
):
    """
    Read-only detail view for one persisted answer.
    """

    serializer_class = (
        QuestionAnswerDetailSerializer
    )

    permission_classes = [
        permissions.AllowAny,
    ]

    def get_queryset(self):
        return (
            QuestionAnswer.objects
            .prefetch_related(
                "sources"
            )
        )