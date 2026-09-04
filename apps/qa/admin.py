from django.contrib import admin

from .models import (
    QuestionAnswer,
    QuestionAnswerSource,
)


class QuestionAnswerSourceInline(
    admin.TabularInline
):
    """
    Read-only source snapshots displayed below QA history.
    """

    model = QuestionAnswerSource

    extra = 0

    can_delete = False

    fields = (
        "document_title",
        "chunk_index",
        "similarity",
        "chunk_state",
    )

    readonly_fields = (
        "document_title",
        "chunk_index",
        "similarity",
        "chunk_state",
    )

    @admin.display(
        description="Original chunk",
    )
    def chunk_state(self, obj):
        if obj.chunk_id is None:
            return "Deleted"

        return f"Chunk #{obj.chunk_id}"

    def has_add_permission(
        self,
        request,
        obj=None,
    ):
        return False


@admin.register(QuestionAnswer)
class QuestionAnswerAdmin(admin.ModelAdmin):
    """
    Read-only Django Admin view for question/answer history.

    New questions will be added through a dedicated Admin workflow
    in the next stage.
    """

    list_display = (
        "question_preview",
        "answer_preview",
        "source_count",
        "created_at",
    )

    search_fields = (
        "question",
        "answer",
        "sources__document_title",
    )

    ordering = (
        "-created_at",
    )

    date_hierarchy = "created_at"

    fields = (
        "question",
        "answer",
        "top_k",
        "min_similarity",
        "document_ids",
        "created_at",
    )

    readonly_fields = (
        "question",
        "answer",
        "top_k",
        "min_similarity",
        "document_ids",
        "created_at",
    )

    inlines = (
        QuestionAnswerSourceInline,
    )

    @admin.display(
        description="Question",
    )
    def question_preview(self, obj):
        if len(obj.question) <= 80:
            return obj.question

        return (
            f"{obj.question[:77]}..."
        )

    @admin.display(
        description="Answer",
    )
    def answer_preview(self, obj):
        if len(obj.answer) <= 100:
            return obj.answer

        return (
            f"{obj.answer[:97]}..."
        )

    @admin.display(
        description="Sources",
    )
    def source_count(self, obj):
        return obj.sources.count()

    def has_add_permission(
        self,
        request,
    ):
        return False