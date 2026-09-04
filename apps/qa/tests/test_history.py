from unittest.mock import patch

from django.test import TestCase

from apps.documents.models import (
    Document,
    DocumentChunk,
)
from apps.qa.models import QuestionAnswer
from apps.qa.services.exceptions import RAGServiceError
from apps.qa.services.history import (
    answer_and_save_question,
)
from apps.qa.services.rag import (
    NO_CONTEXT_ANSWER,
    RAGAnswer,
    RAGSource,
)


class QuestionAnswerHistoryTests(TestCase):
    def create_document(self):
        return Document.objects.create(
            title="Academic Rules",
            file="documents/academic-rules.docx",
            text_content=(
                "ثبت نام دانشجویان در ابتدای "
                "هر ترم انجام می‌شود."
            ),
            status=Document.Status.INDEXED,
        )

    def create_chunk(
        self,
        document,
    ):
        content = (
            "ثبت نام دانشجویان در ابتدای "
            "هر ترم انجام می‌شود."
        )

        return DocumentChunk.objects.create(
            document=document,
            chunk_index=0,
            content=content,
            start_index=0,
            character_count=len(content),
        )

    @patch(
        "apps.qa.services.history.answer_question"
    )
    def test_answer_and_sources_are_saved(
        self,
        mocked_answer_question,
    ):
        document = self.create_document()

        chunk = self.create_chunk(
            document
        )

        mocked_answer_question.return_value = RAGAnswer(
            question=(
                "ثبت نام چه زمانی انجام می‌شود؟"
            ),
            answer=(
                "ثبت نام در ابتدای هر ترم "
                "انجام می‌شود."
            ),
            sources=(
                RAGSource(
                    chunk_id=chunk.id,
                    document_id=document.id,
                    document_title=document.title,
                    chunk_index=chunk.chunk_index,
                    similarity=0.91,
                ),
            ),
        )

        history = answer_and_save_question(
            question=(
                "ثبت نام چه زمانی انجام می‌شود؟"
            ),
            top_k=3,
            min_similarity=0.40,
            document_ids=[
                document.id,
            ],
        )

        self.assertEqual(
            QuestionAnswer.objects.count(),
            1,
        )

        self.assertEqual(
            history.question,
            "ثبت نام چه زمانی انجام می‌شود؟",
        )

        self.assertEqual(
            history.answer,
            (
                "ثبت نام در ابتدای هر ترم "
                "انجام می‌شود."
            ),
        )

        self.assertEqual(
            history.top_k,
            3,
        )

        self.assertEqual(
            history.min_similarity,
            0.40,
        )

        self.assertEqual(
            history.document_ids,
            [
                document.id,
            ],
        )

        self.assertEqual(
            history.sources.count(),
            1,
        )

        source = history.sources.get()

        self.assertEqual(
            source.chunk_id,
            chunk.id,
        )

        self.assertEqual(
            source.document_id_snapshot,
            document.id,
        )

        self.assertEqual(
            source.document_title,
            document.title,
        )

        self.assertEqual(
            source.chunk_index,
            0,
        )

        self.assertAlmostEqual(
            source.similarity,
            0.91,
        )

        mocked_answer_question.assert_called_once_with(
            question=(
                "ثبت نام چه زمانی انجام می‌شود؟"
            ),
            top_k=3,
            min_similarity=0.40,
            document_ids=[
                document.id,
            ],
        )

    @patch(
        "apps.qa.services.history.answer_question"
    )
    def test_no_context_answer_is_saved_without_sources(
        self,
        mocked_answer_question,
    ):
        mocked_answer_question.return_value = RAGAnswer(
            question="سوال بدون پاسخ",
            answer=NO_CONTEXT_ANSWER,
            sources=(),
        )

        history = answer_and_save_question(
            question="سوال بدون پاسخ"
        )

        self.assertEqual(
            history.answer,
            NO_CONTEXT_ANSWER,
        )

        self.assertEqual(
            history.sources.count(),
            0,
        )

        self.assertIsNone(
            history.document_ids
        )

    @patch(
        "apps.qa.services.history.answer_question"
    )
    def test_source_history_survives_document_deletion(
        self,
        mocked_answer_question,
    ):
        document = self.create_document()

        chunk = self.create_chunk(
            document
        )

        document_id = document.id
        document_title = document.title

        mocked_answer_question.return_value = RAGAnswer(
            question="ثبت نام چه زمانی است؟",
            answer="در ابتدای هر ترم.",
            sources=(
                RAGSource(
                    chunk_id=chunk.id,
                    document_id=document.id,
                    document_title=document.title,
                    chunk_index=chunk.chunk_index,
                    similarity=0.88,
                ),
            ),
        )

        history = answer_and_save_question(
            question="ثبت نام چه زمانی است؟"
        )

        source = history.sources.get()

        document.delete()

        source.refresh_from_db()

        self.assertIsNone(
            source.chunk_id
        )

        self.assertEqual(
            source.document_id_snapshot,
            document_id,
        )

        self.assertEqual(
            source.document_title,
            document_title,
        )

        self.assertEqual(
            QuestionAnswer.objects.count(),
            1,
        )

    @patch(
        "apps.qa.services.history.answer_question"
    )
    def test_rag_failure_does_not_create_history(
        self,
        mocked_answer_question,
    ):
        mocked_answer_question.side_effect = (
            RAGServiceError(
                "RAG failed."
            )
        )

        with self.assertRaises(
            RAGServiceError
        ):
            answer_and_save_question(
                question="Valid question"
            )

        self.assertEqual(
            QuestionAnswer.objects.count(),
            0,
        )