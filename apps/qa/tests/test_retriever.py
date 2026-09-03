from unittest.mock import patch

from django.test import TestCase

from apps.documents.models import (
    Document,
    DocumentChunk,
)
from apps.qa.services.exceptions import (
    EmbeddingServiceError,
    RetrievalError,
)
from apps.qa.services.retriever import (
    retrieve_relevant_chunks,
)


def create_vector(
    first=0.0,
    second=0.0,
):
    """
    Build a 384-dimensional test vector.
    """
    return [
        float(first),
        float(second),
    ] + [
        0.0
    ] * 382


class SemanticRetrieverTests(TestCase):
    def create_document(
        self,
        title,
        status=Document.Status.INDEXED,
    ):
        return Document.objects.create(
            title=title,
            file=(
                f"documents/"
                f"{title.lower().replace(' ', '-')}.docx"
            ),
            text_content="Test document text.",
            status=status,
        )

    def create_chunk(
        self,
        document,
        chunk_index,
        content,
        embedding,
    ):
        return DocumentChunk.objects.create(
            document=document,
            chunk_index=chunk_index,
            content=content,
            start_index=chunk_index * 100,
            character_count=len(content),
            embedding=embedding,
        )

    @patch(
        "apps.qa.services.retriever.embed_query"
    )
    def test_retrieval_orders_chunks_by_similarity(
        self,
        mocked_embed_query,
    ):
        mocked_embed_query.return_value = (
            create_vector(
                first=1.0,
                second=0.0,
            )
        )

        document = self.create_document(
            "Similarity Test"
        )

        most_relevant = self.create_chunk(
            document=document,
            chunk_index=0,
            content="Most relevant chunk",
            embedding=create_vector(
                first=1.0,
                second=0.0,
            ),
        )

        second_relevant = self.create_chunk(
            document=document,
            chunk_index=1,
            content="Second relevant chunk",
            embedding=create_vector(
                first=0.8,
                second=0.6,
            ),
        )

        self.create_chunk(
            document=document,
            chunk_index=2,
            content="Unrelated chunk",
            embedding=create_vector(
                first=0.0,
                second=1.0,
            ),
        )

        results = retrieve_relevant_chunks(
            question="Test question",
            top_k=2,
            min_similarity=0.0,
        )

        self.assertEqual(
            len(results),
            2,
        )

        self.assertEqual(
            results[0].chunk_id,
            most_relevant.id,
        )

        self.assertEqual(
            results[1].chunk_id,
            second_relevant.id,
        )

        self.assertAlmostEqual(
            results[0].similarity,
            1.0,
            places=5,
        )

        self.assertAlmostEqual(
            results[1].similarity,
            0.8,
            places=5,
        )

    @patch(
        "apps.qa.services.retriever.embed_query"
    )
    def test_similarity_threshold_filters_results(
        self,
        mocked_embed_query,
    ):
        mocked_embed_query.return_value = (
            create_vector(
                first=1.0,
                second=0.0,
            )
        )

        document = self.create_document(
            "Threshold Test"
        )

        matching_chunk = self.create_chunk(
            document=document,
            chunk_index=0,
            content="Strong match",
            embedding=create_vector(
                first=1.0,
                second=0.0,
            ),
        )

        self.create_chunk(
            document=document,
            chunk_index=1,
            content="Weaker match",
            embedding=create_vector(
                first=0.8,
                second=0.6,
            ),
        )

        results = retrieve_relevant_chunks(
            question="Test question",
            top_k=5,
            min_similarity=0.90,
        )

        self.assertEqual(
            len(results),
            1,
        )

        self.assertEqual(
            results[0].chunk_id,
            matching_chunk.id,
        )

    @patch(
        "apps.qa.services.retriever.embed_query"
    )
    def test_non_indexed_documents_are_excluded(
        self,
        mocked_embed_query,
    ):
        mocked_embed_query.return_value = (
            create_vector(
                first=1.0,
                second=0.0,
            )
        )

        indexed_document = self.create_document(
            "Indexed Document",
            status=Document.Status.INDEXED,
        )

        processed_document = self.create_document(
            "Processed Document",
            status=Document.Status.PROCESSED,
        )

        indexed_chunk = self.create_chunk(
            document=indexed_document,
            chunk_index=0,
            content="Indexed content",
            embedding=create_vector(
                first=0.9,
                second=0.1,
            ),
        )

        self.create_chunk(
            document=processed_document,
            chunk_index=0,
            content="Processed content",
            embedding=create_vector(
                first=1.0,
                second=0.0,
            ),
        )

        results = retrieve_relevant_chunks(
            question="Test question",
            top_k=5,
            min_similarity=0.0,
        )

        self.assertEqual(
            len(results),
            1,
        )

        self.assertEqual(
            results[0].chunk_id,
            indexed_chunk.id,
        )

    @patch(
        "apps.qa.services.retriever.embed_query"
    )
    def test_retrieval_can_be_limited_to_documents(
        self,
        mocked_embed_query,
    ):
        mocked_embed_query.return_value = (
            create_vector(
                first=1.0,
                second=0.0,
            )
        )

        first_document = self.create_document(
            "First Document"
        )

        second_document = self.create_document(
            "Second Document"
        )

        self.create_chunk(
            document=first_document,
            chunk_index=0,
            content="First document content",
            embedding=create_vector(
                first=1.0,
                second=0.0,
            ),
        )

        second_chunk = self.create_chunk(
            document=second_document,
            chunk_index=0,
            content="Second document content",
            embedding=create_vector(
                first=0.9,
                second=0.1,
            ),
        )

        results = retrieve_relevant_chunks(
            question="Test question",
            top_k=5,
            min_similarity=0.0,
            document_ids=[
                second_document.id,
            ],
        )

        self.assertEqual(
            len(results),
            1,
        )

        self.assertEqual(
            results[0].chunk_id,
            second_chunk.id,
        )

    def test_empty_question_is_rejected(self):
        with self.assertRaises(
            RetrievalError
        ):
            retrieve_relevant_chunks(
                question="   "
            )

    def test_invalid_top_k_is_rejected(self):
        with self.assertRaises(
            RetrievalError
        ):
            retrieve_relevant_chunks(
                question="Valid question",
                top_k=0,
            )

    def test_invalid_similarity_is_rejected(self):
        with self.assertRaises(
            RetrievalError
        ):
            retrieve_relevant_chunks(
                question="Valid question",
                min_similarity=1.5,
            )

    @patch(
        "apps.qa.services.retriever.embed_query"
    )
    def test_embedding_failure_becomes_retrieval_error(
        self,
        mocked_embed_query,
    ):
        mocked_embed_query.side_effect = (
            EmbeddingServiceError(
                "Embedding failed."
            )
        )

        with self.assertRaises(
            RetrievalError
        ):
            retrieve_relevant_chunks(
                question="Valid question"
            )