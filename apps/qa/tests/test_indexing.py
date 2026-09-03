from unittest.mock import patch

from django.test import TestCase

from apps.documents.models import (
    Document,
    DocumentChunk,
)
from apps.qa.services.exceptions import (
    DocumentIndexingError,
)
from apps.qa.services.indexing import (
    index_document,
)


class DocumentIndexingTests(TestCase):
    @patch(
        "apps.qa.services.indexing.embed_texts"
    )
    def test_index_document_stores_embeddings(
        self,
        mocked_embed_texts,
    ):
        document = Document.objects.create(
            title="Indexing Test",
            file="documents/indexing-test.docx",
            text_content="Full document text.",
            status=Document.Status.PROCESSED,
        )

        DocumentChunk.objects.create(
            document=document,
            chunk_index=0,
            content="First chunk",
            start_index=0,
            character_count=11,
        )

        DocumentChunk.objects.create(
            document=document,
            chunk_index=1,
            content="Second chunk",
            start_index=12,
            character_count=12,
        )

        mocked_embed_texts.return_value = [
            [1.0] + [0.0] * 383,
            [0.0, 1.0] + [0.0] * 382,
        ]

        index_document(
            document
        )

        document.refresh_from_db()

        self.assertEqual(
            document.status,
            Document.Status.INDEXED,
        )

        self.assertEqual(
            document.processing_error,
            "",
        )

        chunks = list(
            document.chunks.order_by(
                "chunk_index"
            )
        )

        self.assertEqual(
            len(chunks),
            2,
        )

        for chunk in chunks:
            self.assertIsNotNone(
                chunk.embedding
            )

            self.assertEqual(
                len(chunk.embedding),
                384,
            )

    def test_document_without_chunks_fails_indexing(
        self,
    ):
        document = Document.objects.create(
            title="No Chunks",
            file="documents/no-chunks.docx",
            text_content="Some text.",
            status=Document.Status.PROCESSED,
        )

        with self.assertRaises(
            DocumentIndexingError
        ):
            index_document(
                document
            )

        document.refresh_from_db()

        self.assertEqual(
            document.status,
            Document.Status.FAILED,
        )

        self.assertNotEqual(
            document.processing_error,
            "",
        )