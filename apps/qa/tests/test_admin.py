from django.contrib import admin
from django.contrib.auth import (
    get_user_model,
)
from django.test import (
    RequestFactory,
    TestCase,
)
from django.urls import reverse

from apps.qa.models import (
    QuestionAnswer,
    QuestionAnswerSource,
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