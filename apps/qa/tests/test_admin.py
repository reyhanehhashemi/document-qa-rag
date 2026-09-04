from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import (
    get_user_model,
)
from django.test import (
    RequestFactory,
    TestCase,
)
from django.urls import reverse

from apps.documents.models import Document
from apps.qa.models import (
    QuestionAnswer,
    QuestionAnswerSource,
)
from apps.qa.services.exceptions import (
    RAGServiceError,
)


class QuestionAnswerAdminTests(TestCase):
    def setUp(self):
        user_model = get_user_model()

        self.admin_user = (
            user_model.objects.create_superuser(
                username="admin",
                email="admin@example.com",
                password="test-password",
            )
        )

        self.client.force_login(
            self.admin_user
        )

        self.model_admin = (
            admin.site._registry[
                QuestionAnswer
            ]
        )

        self.ask_url = reverse(
            "admin:qa_questionanswer_ask"
        )

    def create_document(
        self,
        title,
        status=Document.Status.INDEXED,
    ):
        return Document.objects.create(
            title=title,
            file=(
                "documents/"
                f"{title.lower().replace(' ', '-')}.docx"
            ),
            text_content="Test content.",
            status=status,
        )

    def test_question_history_cannot_be_added_manually(
        self,
    ):
        request = (
            RequestFactory().get(
                "/admin/qa/questionanswer/add/"
            )
        )

        request.user = self.admin_user

        self.assertFalse(
            self.model_admin.has_add_permission(
                request
            )
        )

    def test_history_change_page_displays_source_snapshot(
        self,
    ):
        history = QuestionAnswer.objects.create(
            question=(
                "ثبت نام چه زمانی انجام می‌شود؟"
            ),
            answer=(
                "ثبت نام در ابتدای هر ترم "
                "انجام می‌شود."
            ),
            top_k=3,
            min_similarity=0.20,
        )

        QuestionAnswerSource.objects.create(
            question_answer=history,
            chunk=None,
            document_id_snapshot=123,
            document_title="Academic Rules",
            chunk_index=2,
            similarity=0.88,
        )

        response = self.client.get(
            reverse(
                "admin:qa_questionanswer_change",
                args=[
                    history.pk,
                ],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Academic Rules",
        )

        self.assertContains(
            response,
            "0.88",
        )

    def test_changelist_displays_ask_question_link(
        self,
    ):
        response = self.client.get(
            reverse(
                "admin:qa_questionanswer_changelist"
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Ask question",
        )

        self.assertContains(
            response,
            self.ask_url,
        )

    def test_ask_form_displays_only_indexed_documents(
        self,
    ):
        indexed_document = self.create_document(
            "Indexed Document",
            status=Document.Status.INDEXED,
        )

        processed_document = self.create_document(
            "Processed Document",
            status=Document.Status.PROCESSED,
        )

        response = self.client.get(
            self.ask_url
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            indexed_document.title,
        )

        self.assertNotContains(
            response,
            processed_document.title,
        )

    @patch(
        "apps.qa.admin.answer_and_save_question"
    )
    def test_empty_document_selection_searches_all_documents(
        self,
        mocked_answer_and_save,
    ):
        history = QuestionAnswer.objects.create(
            question="Saved question",
            answer="Saved answer",
        )

        mocked_answer_and_save.return_value = (
            history
        )

        response = self.client.post(
            self.ask_url,
            data={
                "question": (
                    "موضوع اسناد چیست؟"
                ),
                "top_k": "5",
                "min_similarity": "0.20",
            },
        )

        mocked_answer_and_save.assert_called_once_with(
            question="موضوع اسناد چیست؟",
            top_k=5,
            min_similarity=0.20,
            document_ids=None,
        )

        self.assertRedirects(
            response,
            reverse(
                "admin:qa_questionanswer_change",
                args=[
                    history.pk,
                ],
            ),
        )

    @patch(
        "apps.qa.admin.answer_and_save_question"
    )
    def test_selected_documents_are_passed_to_rag(
        self,
        mocked_answer_and_save,
    ):
        document = self.create_document(
            "Selected Document"
        )

        history = QuestionAnswer.objects.create(
            question="Saved question",
            answer="Saved answer",
        )

        mocked_answer_and_save.return_value = (
            history
        )

        response = self.client.post(
            self.ask_url,
            data={
                "question": (
                    "این سند درباره چیست؟"
                ),
                "documents": [
                    str(document.id),
                ],
                "top_k": "3",
                "min_similarity": "0.40",
            },
        )

        mocked_answer_and_save.assert_called_once_with(
            question="این سند درباره چیست؟",
            top_k=3,
            min_similarity=0.40,
            document_ids=[
                document.id,
            ],
        )

        self.assertRedirects(
            response,
            reverse(
                "admin:qa_questionanswer_change",
                args=[
                    history.pk,
                ],
            ),
        )

    @patch(
        "apps.qa.admin.answer_and_save_question"
    )
    def test_rag_error_is_displayed_on_ask_page(
        self,
        mocked_answer_and_save,
    ):
        mocked_answer_and_save.side_effect = (
            RAGServiceError(
                "RAG failed."
            )
        )

        response = self.client.post(
            self.ask_url,
            data={
                "question": "Valid question",
                "top_k": "5",
                "min_similarity": "0.20",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "RAG failed.",
        )