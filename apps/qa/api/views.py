from django.db.models import Count
from drf_spectacular.utils import (
    OpenApiExample,
    extend_schema,
    extend_schema_view,
)
from rest_framework import (
    generics,
    permissions,
    status,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.qa.models import QuestionAnswer
from apps.qa.services.exceptions import (
    RAGServiceError,
)
from apps.qa.services.history import (
    answer_and_save_question,
)
from config.api_exceptions import (
    ServiceUnavailable,
)
from config.api_serializers import (
    APIErrorSerializer,
)

from .pagination import (
    QuestionHistoryPagination,
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

    @extend_schema(
        tags=["Question Answering"],
        summary="Ask a document-grounded question",
        description=(
            "Retrieve relevant chunks from indexed documents, "
            "generate a grounded answer, persist the result, "
            "and return the answer with its source snapshots."
        ),
        request=AskQuestionSerializer,
        responses={
            201: QuestionAnswerDetailSerializer,
            400: APIErrorSerializer,
            503: APIErrorSerializer,
        },
        examples=[
            OpenApiExample(
                "Question using selected documents",
                request_only=True,
                value={
                    "question": (
                        "When does course registration open?"
                    ),
                    "document_ids": [
                        1,
                    ],
                    "top_k": 3,
                    "min_similarity": 0.2,
                },
            ),
        ],
    )
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
            raise ServiceUnavailable(
                detail=str(
                    exc
                )
            ) from exc

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


@extend_schema_view(
    get=extend_schema(
        tags=["Question History"],
        summary="List question-answer history",
        description=(
            "Return paginated saved question-answer history "
            "in reverse chronological order."
        ),
    ),
)
class QuestionAnswerListAPIView(
    generics.ListAPIView
):
    """
    Read-only paginated question-answer history list.
    """

    serializer_class = (
        QuestionAnswerListSerializer
    )

    pagination_class = (
        QuestionHistoryPagination
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


@extend_schema_view(
    get=extend_schema(
        tags=["Question History"],
        summary="Retrieve a saved answer",
        description=(
            "Return one persisted question-answer item "
            "including its source snapshots."
        ),
        responses={
            200: QuestionAnswerDetailSerializer,
            404: APIErrorSerializer,
        },
    ),
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