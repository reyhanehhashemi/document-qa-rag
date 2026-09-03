from django.test import TestCase

from apps.documents.models import (
    Document,
    DocumentChunk,
)
from apps.documents.services.chunking import (
    replace_document_chunks,
    split_document_text,
)
from apps.documents.services.exceptions import (
    DocumentChunkingError,
)


class DocumentChunkingTests(TestCase):
    def test_long_text_is_split_into_multiple_chunks(self):
        text = " ".join(
            f"word-{index}"
            for index in range(300)
        )

        chunks = split_document_text(
            text=text,
            chunk_size=200,
            chunk_overlap=40,
        )

        self.assertGreater(
            len(chunks),
            1,
        )

        for chunk in chunks:
            self.assertLessEqual(
                len(chunk.page_content),
                200,
            )

    def test_empty_text_is_rejected(self):
        with self.assertRaises(
            DocumentChunkingError
        ):
            split_document_text(
                text="   "
            )

    def test_invalid_overlap_is_rejected(self):
        with self.assertRaises(
            DocumentChunkingError
        ):
            split_document_text(
                text="Some valid document text.",
                chunk_size=100,
                chunk_overlap=100,
            )

    def test_replace_document_chunks_persists_chunks(self):
        document = Document.objects.create(
            title="Chunk Test",
            file="documents/chunk-test.docx",
            text_content=(
                "This is a long document. "
                * 100
            ),
            status=Document.Status.PROCESSED,
        )

        created_chunks = replace_document_chunks(
            document=document,
            chunk_size=250,
            chunk_overlap=50,
        )

        self.assertGreater(
            len(created_chunks),
            1,
        )

        stored_chunks = DocumentChunk.objects.filter(
            document=document
        )

        self.assertEqual(
            stored_chunks.count(),
            len(created_chunks),
        )

        for expected_index, chunk in enumerate(
            stored_chunks
        ):
            self.assertEqual(
                chunk.chunk_index,
                expected_index,
            )

            self.assertEqual(
                chunk.character_count,
                len(chunk.content),
            )

            self.assertGreaterEqual(
                chunk.start_index,
                0,
            )

    def test_reprocessing_replaces_existing_chunks(self):
        document = Document.objects.create(
            title="Reprocessing Test",
            file="documents/reprocessing-test.docx",
            text_content=(
                "First version of the document. "
                * 100
            ),
            status=Document.Status.PROCESSED,
        )

        replace_document_chunks(
            document=document,
            chunk_size=200,
            chunk_overlap=40,
        )

        original_chunk_count = (
            document.chunks.count()
        )

        self.assertGreater(
            original_chunk_count,
            1,
        )

        document.text_content = (
            "Completely new document content."
        )

        document.save(
            update_fields=[
                "text_content",
                "updated_at",
            ]
        )

        replace_document_chunks(
            document=document,
            chunk_size=200,
            chunk_overlap=40,
        )

        self.assertEqual(
            document.chunks.count(),
            1,
        )

        self.assertEqual(
            document.chunks.first().content,
            "Completely new document content.",
        )