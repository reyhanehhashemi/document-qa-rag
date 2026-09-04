from unittest.mock import patch

from django.test import SimpleTestCase

from apps.qa.services.exceptions import (
    LLMServiceError,
    RAGServiceError,
    RetrievalError,
)
from apps.qa.services.rag import (
    NO_CONTEXT_ANSWER,
    NO_CONTEXT_ANSWER_EN,
    answer_question,
    build_context,
)
from apps.qa.services.retriever import (
    RetrievedChunk,
)


def create_retrieved_chunk(
    chunk_id=1,
    document_id=10,
    document_title="Test Document",
    chunk_index=0,
    content="Relevant document content.",
    start_index=0,
    similarity=0.85,
):
    return RetrievedChunk(
        chunk_id=chunk_id,
        document_id=document_id,
        document_title=document_title,
        chunk_index=chunk_index,
        content=content,
        start_index=start_index,
        similarity=similarity,
    )


class RAGServiceTests(SimpleTestCase):
    def test_build_context_contains_document_metadata(
        self,
    ):
        chunk = create_retrieved_chunk(
            document_title="University Rules",
            chunk_index=3,
            content="Registration happens every semester.",
            similarity=0.8123,
        )

        context = build_context(
            [chunk]
        )

        self.assertIn(
            "[Source 1]",
            context,
        )

        self.assertIn(
            "Document: University Rules",
            context,
        )

        self.assertIn(
            "Chunk index: 3",
            context,
        )

        self.assertIn(
            "Similarity: 0.8123",
            context,
        )

        self.assertIn(
            "Registration happens every semester.",
            context,
        )

    @patch(
        "apps.qa.services.rag.generate_llm_response"
    )
    @patch(
        "apps.qa.services.rag.retrieve_relevant_chunks"
    )
    def test_answer_question_uses_retrieved_context(
        self,
        mocked_retrieve,
        mocked_generate,
    ):
        chunk = create_retrieved_chunk(
            document_title="Academic Rules",
            content=(
                "ثبت نام دانشجویان در ابتدای "
                "هر ترم انجام می‌شود."
            ),
            similarity=0.91,
        )

        mocked_retrieve.return_value = [
            chunk
        ]

        mocked_generate.return_value = (
            "ثبت نام در ابتدای هر ترم انجام می‌شود."
        )

        result = answer_question(
            "ثبت نام چه زمانی انجام می‌شود؟"
        )

        self.assertEqual(
            result.answer,
            (
                "ثبت نام در ابتدای هر ترم "
                "انجام می‌شود."
            ),
        )

        self.assertEqual(
            len(result.sources),
            1,
        )

        self.assertEqual(
            result.sources[0].document_title,
            "Academic Rules",
        )

        self.assertAlmostEqual(
            result.sources[0].similarity,
            0.91,
        )

        mocked_generate.assert_called_once()

        call_kwargs = (
            mocked_generate.call_args.kwargs
        )

        self.assertIn(
            "ثبت نام چه زمانی انجام می‌شود؟",
            call_kwargs["user_prompt"],
        )

        self.assertIn(
            chunk.content,
            call_kwargs["user_prompt"],
        )

    @patch(
        "apps.qa.services.rag.generate_llm_response"
    )
    @patch(
        "apps.qa.services.rag.retrieve_relevant_chunks"
    )
    def test_no_context_does_not_call_llm(
        self,
        mocked_retrieve,
        mocked_generate,
    ):
        mocked_retrieve.return_value = []

        result = answer_question(
            "سوالی که پاسخی در اسناد ندارد"
        )

        self.assertEqual(
            result.answer,
            NO_CONTEXT_ANSWER,
        )

        self.assertEqual(
            result.sources,
            (),
        )

        mocked_generate.assert_not_called()

    @patch(
        "apps.qa.services.rag.generate_llm_response"
    )
    @patch(
        "apps.qa.services.rag.retrieve_relevant_chunks"
    )
    def test_english_no_context_answer_uses_english(
        self,
        mocked_retrieve,
        mocked_generate,
    ):
        mocked_retrieve.return_value = []

        result = answer_question(
            "Who is the university president?"
        )

        self.assertEqual(
            result.answer,
            NO_CONTEXT_ANSWER_EN,
        )

        self.assertEqual(
            result.sources,
            (),
        )

        mocked_generate.assert_not_called()

    @patch(
        "apps.qa.services.rag.retrieve_relevant_chunks"
    )
    def test_retrieval_error_is_wrapped(
        self,
        mocked_retrieve,
    ):
        mocked_retrieve.side_effect = RetrievalError(
            "Retrieval failed."
        )

        with self.assertRaises(
            RAGServiceError
        ):
            answer_question(
                "Valid question"
            )

    @patch(
        "apps.qa.services.rag.generate_llm_response"
    )
    @patch(
        "apps.qa.services.rag.retrieve_relevant_chunks"
    )
    def test_llm_error_is_wrapped(
        self,
        mocked_retrieve,
        mocked_generate,
    ):
        mocked_retrieve.return_value = [
            create_retrieved_chunk()
        ]

        mocked_generate.side_effect = (
            LLMServiceError(
                "LLM failed."
            )
        )

        with self.assertRaises(
            RAGServiceError
        ):
            answer_question(
                "Valid question"
            )

    def test_empty_question_is_rejected(self):
        with self.assertRaises(
            RAGServiceError
        ):
            answer_question(
                "   "
            )