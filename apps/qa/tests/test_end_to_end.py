import tempfile
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core.files.uploadedfile import (
    SimpleUploadedFile,
)
from django.test import (
    override_settings,
)
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.documents.models import Document
from apps.qa.models import QuestionAnswer
from apps.qa.services.retriever import (
    RetrievedChunk,
)


class DocumentQAEndToEndTests(
    APITestCase
):
    def setUp(self):
        self.media_directory = (
            tempfile.TemporaryDirectory()
        )

        self.media_override = (
            override_settings(
                MEDIA_ROOT=(
                    self.media_directory.name
                )
            )
        )

        self.media_override.enable()

    def tearDown(self):
        self.media_override.disable()

        self.media_directory.cleanup()

    def fake_index_document(
        self,
        document,
    ):
        """
        Replace only the expensive embedding/indexing boundary.

        DOCX extraction and chunking still run normally.
        """
        document.status = (
            Document.Status.INDEXED
        )

        document.processing_error = ""

        document.save(
            update_fields=[
                "status",
                "processing_error",
                "updated_at",
            ]
        )

    @patch(
        (
            "apps.qa.services.rag."
            "generate_llm_response"
        )
    )
    @patch(
        (
            "apps.qa.services.rag."
            "retrieve_relevant_chunks"
        )
    )
    @patch(
        (
            "apps.documents.services.pipeline."
            "index_document"
        )
    )
    def test_document_upload_to_answer_history_flow(
        self,
        mocked_index_document,
        mocked_retrieve,
        mocked_generate,
    ):
        mocked_index_document.side_effect = (
            self.fake_index_document
        )

        sample_path = (
            Path(
                settings.BASE_DIR
            )
            / "sample_data"
            / "northbridge_student_guide.docx"
        )

        with sample_path.open(
            "rb"
        ) as sample_file:
            uploaded_file = (
                SimpleUploadedFile(
                    sample_path.name,
                    sample_file.read(),
                    content_type=(
                        "application/vnd."
                        "openxmlformats-officedocument."
                        "wordprocessingml.document"
                    ),
                )
            )

        upload_response = (
            self.client.post(
                reverse(
                    "document-list"
                ),
                data={
                    "title": (
                        "End-to-End "
                        "University Guide"
                    ),
                    "file": uploaded_file,
                },
                format="multipart",
            )
        )

        self.assertEqual(
            upload_response.status_code,
            status.HTTP_201_CREATED,
        )

        document = (
            Document.objects.get(
                pk=upload_response.data["id"]
            )
        )

        self.assertEqual(
            document.status,
            Document.Status.INDEXED,
        )

        self.assertIn(
            "Course registration opens",
            document.text_content,
        )

        self.assertGreater(
            document.chunks.count(),
            0,
        )

        relevant_chunk = (
            document.chunks.filter(
                content__icontains=(
                    "late payment fee"
                )
            ).first()
        )

        self.assertIsNotNone(
            relevant_chunk
        )

        retrieved_chunk = (
            RetrievedChunk(
                chunk_id=relevant_chunk.id,
                document_id=document.id,
                document_title=document.title,
                chunk_index=(
                    relevant_chunk.chunk_index
                ),
                content=(
                    relevant_chunk.content
                ),
                start_index=(
                    relevant_chunk.start_index
                ),
                similarity=0.91,
            )
        )

        mocked_retrieve.return_value = [
            retrieved_chunk
        ]

        mocked_generate.return_value = (
            "The late tuition payment fee "
            "is 25 US dollars."
        )

        ask_response = (
            self.client.post(
                reverse(
                    "question-ask"
                ),
                data={
                    "question": (
                        "How much is the late "
                        "tuition payment fee?"
                    ),
                    "document_ids": [
                        document.id,
                    ],
                    "top_k": 3,
                    "min_similarity": 0.20,
                },
                format="json",
            )
        )

        self.assertEqual(
            ask_response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            ask_response.data["answer"],
            (
                "The late tuition payment fee "
                "is 25 US dollars."
            ),
        )

        self.assertEqual(
            ask_response.data[
                "document_ids"
            ],
            [
                document.id,
            ],
        )

        self.assertEqual(
            len(
                ask_response.data[
                    "sources"
                ]
            ),
            1,
        )

        self.assertEqual(
            ask_response.data[
                "sources"
            ][0]["document_title"],
            document.title,
        )

        history = (
            QuestionAnswer.objects.get(
                pk=ask_response.data["id"]
            )
        )

        self.assertEqual(
            history.sources.count(),
            1,
        )

        history_list_response = (
            self.client.get(
                reverse(
                    "question-list"
                )
            )
        )

        self.assertEqual(
            history_list_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            history_list_response.data[
                "count"
            ],
            1,
        )

        history_detail_response = (
            self.client.get(
                reverse(
                    "question-detail",
                    args=[
                        history.id,
                    ],
                )
            )
        )

        self.assertEqual(
            history_detail_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(
                history_detail_response.data[
                    "sources"
                ]
            ),
            1,
        )

        delete_response = (
            self.client.delete(
                reverse(
                    "document-detail",
                    args=[
                        document.id,
                    ],
                )
            )
        )

        self.assertEqual(
            delete_response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        history.refresh_from_db()

        source = (
            history.sources.get()
        )

        self.assertIsNone(
            source.chunk_id
        )

        self.assertEqual(
            source.document_title,
            (
                "End-to-End "
                "University Guide"
            ),
        )

        final_history_response = (
            self.client.get(
                reverse(
                    "question-detail",
                    args=[
                        history.id,
                    ],
                )
            )
        )

        self.assertEqual(
            final_history_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIsNone(
            final_history_response.data[
                "sources"
            ][0]["chunk_id"]
        )