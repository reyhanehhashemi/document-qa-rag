from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.documents.models import (
    Document,
    DocumentChunk,
)
from apps.qa.models import (
    QuestionAnswer,
    QuestionAnswerSource,
)
from apps.qa.services.exceptions import (
    RAGServiceError,
)


class QuestionAnswerAPITests(APITestCase):
    def create_document(
        self,
        title="Indexed Document",
        status_value=Document.Status.INDEXED,
    ):
        return Document.objects.create(
            title=title,
            file="documents/test.docx",
            text_content="Test document content.",
            status=status_value,
        )

    def create_history(
        self,
        question="When does registration open?",
        answer=(
            "Registration opens fourteen days "
            "before the semester."
        ),
        document_ids=None,
    ):
        return QuestionAnswer.objects.create(
            question=question,
            answer=answer,
            top_k=5,
            min_similarity=0.20,
            document_ids=document_ids,
        )

    @patch(
        "apps.qa.api.views.answer_and_save_question"
    )
    def test_ask_question_without_document_filter(
        self,
        mocked_answer,
    ):
        history = self.create_history()

        mocked_answer.return_value = history

        response = self.client.post(
            reverse(
                "question-ask"
            ),
            data={
                "question": (
                    "When does registration open?"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        mocked_answer.assert_called_once_with(
            question=(
                "When does registration open?"
            ),
            top_k=5,
            min_similarity=0.20,
            document_ids=None,
        )

        self.assertEqual(
            response.data["id"],
            history.id,
        )

    @patch(
        "apps.qa.api.views.answer_and_save_question"
    )
    def test_ask_question_with_selected_documents(
        self,
        mocked_answer,
    ):
        document = self.create_document()

        history = self.create_history(
            document_ids=[
                document.id,
            ]
        )

        mocked_answer.return_value = history

        response = self.client.post(
            reverse(
                "question-ask"
            ),
            data={
                "question": (
                    "What does the document say?"
                ),
                "document_ids": [
                    document.id,
                ],
                "top_k": 3,
                "min_similarity": 0.30,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        mocked_answer.assert_called_once_with(
            question=(
                "What does the document say?"
            ),
            top_k=3,
            min_similarity=0.30,
            document_ids=[
                document.id,
            ],
        )

    @patch(
        "apps.qa.api.views.answer_and_save_question"
    )
    def test_empty_document_list_means_all_documents(
        self,
        mocked_answer,
    ):
        history = self.create_history()

        mocked_answer.return_value = history

        response = self.client.post(
            reverse(
                "question-ask"
            ),
            data={
                "question": "Test question",
                "document_ids": [],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        mocked_answer.assert_called_once_with(
            question="Test question",
            top_k=5,
            min_similarity=0.20,
            document_ids=None,
        )

    @patch(
        "apps.qa.api.views.answer_and_save_question"
    )
    def test_nonexistent_document_is_rejected(
        self,
        mocked_answer,
    ):
        response = self.client.post(
            reverse(
                "question-ask"
            ),
            data={
                "question": "Test question",
                "document_ids": [
                    999999,
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            response.data["error"]["code"],
            "validation_error",
        )

        self.assertIn(
            "document_ids",
            response.data[
                "error"
            ][
                "details"
            ],
        )

        mocked_answer.assert_not_called()

    @patch(
        "apps.qa.api.views.answer_and_save_question"
    )
    def test_unindexed_document_is_rejected(
        self,
        mocked_answer,
    ):
        document = self.create_document(
            status_value=(
                Document.Status.PROCESSED
            )
        )

        response = self.client.post(
            reverse(
                "question-ask"
            ),
            data={
                "question": "Test question",
                "document_ids": [
                    document.id,
                ],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            response.data["error"]["code"],
            "validation_error",
        )

        self.assertIn(
            "document_ids",
            response.data[
                "error"
            ][
                "details"
            ],
        )

        mocked_answer.assert_not_called()

    @patch(
        "apps.qa.api.views.answer_and_save_question"
    )
    def test_rag_failure_returns_service_unavailable(
        self,
        mocked_answer,
    ):
        mocked_answer.side_effect = RAGServiceError(
            "Unable to generate the document-based answer."
        )

        response = self.client.post(
            reverse(
                "question-ask"
            ),
            data={
                "question": "Test question",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )

        self.assertEqual(
            response.data["error"]["code"],
            "service_unavailable",
        )

        self.assertEqual(
            response.data["error"]["message"],
            (
                "Unable to generate the "
                "document-based answer."
            ),
        )

    def test_history_list_returns_saved_answers(
        self,
    ):
        history = self.create_history()

        response = self.client.get(
            reverse(
                "question-list"
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        self.assertEqual(
            len(
                response.data["results"]
            ),
            1,
        )

        self.assertEqual(
            response.data[
                "results"
            ][0]["id"],
            history.id,
        )

        self.assertEqual(
            response.data[
                "results"
            ][0]["source_count"],
            0,
        )

    def test_history_detail_contains_sources(
        self,
    ):
        document = self.create_document()

        content = (
            "Registration opens fourteen "
            "days before the semester."
        )

        chunk = DocumentChunk.objects.create(
            document=document,
            chunk_index=0,
            content=content,
            start_index=0,
            character_count=len(
                content
            ),
        )

        history = self.create_history(
            document_ids=[
                document.id,
            ]
        )

        QuestionAnswerSource.objects.create(
            question_answer=history,
            chunk=chunk,
            document_id_snapshot=document.id,
            document_title=document.title,
            chunk_index=chunk.chunk_index,
            similarity=0.87,
        )

        response = self.client.get(
            reverse(
                "question-detail",
                args=[
                    history.id,
                ],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(
                response.data["sources"]
            ),
            1,
        )

        source = response.data[
            "sources"
        ][0]

        self.assertEqual(
            source["document_title"],
            document.title,
        )

        self.assertEqual(
            source["chunk_index"],
            0,
        )

        self.assertAlmostEqual(
            source["similarity"],
            0.87,
        )

    def test_history_list_is_read_only(
        self,
    ):
        response = self.client.post(
            reverse(
                "question-list"
            ),
            data={
                "question": "Manual history entry",
                "answer": "Should not be created.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

        self.assertEqual(
            response.data["error"]["code"],
            "method_not_allowed",
        )

        self.assertEqual(
            QuestionAnswer.objects.count(),
            0,
        )

    @patch(
        "apps.qa.api.views.answer_and_save_question"
    )
    def test_blank_question_returns_standardized_validation_error(
        self,
        mocked_answer,
    ):
        response = self.client.post(
            reverse(
                "question-ask"
            ),
            data={
                "question": "",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            response.data["error"]["code"],
            "validation_error",
        )

        self.assertIn(
            "question",
            response.data[
                "error"
            ][
                "details"
            ],
        )

        mocked_answer.assert_not_called()

    def test_history_list_is_paginated(
        self,
    ):
        for index in range(
            21
        ):
            self.create_history(
                question=(
                    f"Question {index}"
                )
            )

        response = self.client.get(
            reverse(
                "question-list"
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            21,
        )

        self.assertEqual(
            len(
                response.data["results"]
            ),
            20,
        )

        self.assertIsNotNone(
            response.data["next"]
        )

        self.assertIsNone(
            response.data["previous"]
        )

    def test_missing_history_returns_standardized_404(
        self,
    ):
        response = self.client.get(
            reverse(
                "question-detail",
                args=[
                    999999,
                ],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertEqual(
            response.data["error"]["code"],
            "not_found",
        )

        self.assertIn(
            "message",
            response.data["error"],
        )