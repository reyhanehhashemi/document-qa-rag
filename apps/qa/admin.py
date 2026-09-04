from django.contrib import (
    admin,
    messages,
)
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import (
    path,
    reverse,
)

from .forms import AskQuestionAdminForm
from .models import (
    QuestionAnswer,
    QuestionAnswerSource,
)
from .services.exceptions import RAGServiceError
from .services.history import (
    answer_and_save_question,
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
    Django Admin interface for asking questions and viewing
    immutable question/answer history.
    """

    change_list_template = (
        "admin/qa/questionanswer/change_list.html"
    )

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
        """
        Prevent manual creation of history records.

        Questions are created only through the dedicated
        Ask Question workflow.
        """
        return False

    def get_urls(self):
        """
        Add a custom Django Admin URL for asking questions.
        """
        default_urls = super().get_urls()

        custom_urls = [
            path(
                "ask/",
                self.admin_site.admin_view(
                    self.ask_question_view
                ),
                name="qa_questionanswer_ask",
            ),
        ]

        return (
            custom_urls
            + default_urls
        )

    def ask_question_view(
        self,
        request,
    ):
        """
        Render and process the Admin Ask Question form.
        """
        if not request.user.has_perm(
            "qa.add_questionanswer"
        ):
            raise PermissionDenied

        if request.method == "POST":
            form = AskQuestionAdminForm(
                request.POST
            )

            if form.is_valid():
                selected_documents = (
                    form.cleaned_data[
                        "documents"
                    ]
                )

                document_ids = list(
                    selected_documents.values_list(
                        "id",
                        flat=True,
                    )
                )

                if not document_ids:
                    document_ids = None

                try:
                    history = answer_and_save_question(
                        question=(
                            form.cleaned_data[
                                "question"
                            ]
                        ),
                        top_k=(
                            form.cleaned_data[
                                "top_k"
                            ]
                        ),
                        min_similarity=(
                            form.cleaned_data[
                                "min_similarity"
                            ]
                        ),
                        document_ids=document_ids,
                    )

                except RAGServiceError as exc:
                    self.message_user(
                        request,
                        (
                            "Question answering failed: "
                            f"{exc}"
                        ),
                        level=messages.ERROR,
                    )

                else:
                    self.message_user(
                        request,
                        (
                            "Question answered and "
                            "saved successfully."
                        ),
                        level=messages.SUCCESS,
                    )

                    return redirect(
                        reverse(
                            (
                                "admin:"
                                "qa_questionanswer_change"
                            ),
                            args=[
                                history.pk,
                            ],
                        )
                    )

        else:
            form = AskQuestionAdminForm()

        context = {
            **self.admin_site.each_context(
                request
            ),
            "title": "Ask a document question",
            "opts": self.model._meta,
            "form": form,
        }

        return TemplateResponse(
            request,
            (
                "admin/qa/questionanswer/"
                "ask_question.html"
            ),
            context,
        )