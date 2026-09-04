import tempfile
from unittest.mock import patch

from django.core.files.uploadedfile import (
    SimpleUploadedFile,
)
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.documents.models import Document


class DocumentAPITests(APITestCase):
    def setUp(self):
        self.media_directory = (
            tempfile.TemporaryDirectory()
        )

        self.media_override = override_settings(
            MEDIA_ROOT=self.media_directory.name
        )

        self.media_override.enable()

    def tearDown(self):
        self.media_override.disable()

        self.media_directory.cleanup()

    def create_document(
        self,
        title="Existing Document",
    ):
        return Document.objects.create(
            title=title,
            file="documents/existing.docx",
            text_content="Existing extracted text.",
            status=Document.Status.INDEXED,
        )

    def test_document_list_returns_documents(
        self,
    ):
        document = self.create_document()

        response = self.client.get(
            reverse(
                "document-list"
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]["id"],
            document.id,
        )

        self.assertNotIn(
            "text_content",
            response.data[0],
        )

    def test_document_detail_contains_text_content(
        self,
    ):
        document = self.create_document()

        response = self.client.get(
            reverse(
                "document-detail",
                args=[
                    document.id,
                ],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["text_content"],
            "Existing extracted text.",
        )

    @patch(
        "apps.documents.api.views.run_document_pipeline"
    )
    def test_create_document_runs_pipeline(
        self,
        mocked_pipeline,
    ):
        uploaded_file = SimpleUploadedFile(
            "student-guide.docx",
            b"fake docx content",
            content_type=(
                "application/vnd.openxmlformats-"
                "officedocument.wordprocessingml.document"
            ),
        )

        response = self.client.post(
            reverse(
                "document-list"
            ),
            data={
                "title": "Student Guide",
                "file": uploaded_file,
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        document = Document.objects.get(
            title="Student Guide"
        )

        mocked_pipeline.assert_called_once_with(
            document
        )

    @patch(
        "apps.documents.api.views.run_document_pipeline"
    )
    def test_title_only_patch_does_not_run_pipeline(
        self,
        mocked_pipeline,
    ):
        document = self.create_document()

        response = self.client.patch(
            reverse(
                "document-detail",
                args=[
                    document.id,
                ],
            ),
            data={
                "title": "Updated Title",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        document.refresh_from_db()

        self.assertEqual(
            document.title,
            "Updated Title",
        )

        mocked_pipeline.assert_not_called()

    @patch(
        "apps.documents.api.views.run_document_pipeline"
    )
    def test_file_patch_runs_pipeline(
        self,
        mocked_pipeline,
    ):
        document = self.create_document()

        replacement_file = SimpleUploadedFile(
            "replacement.docx",
            b"replacement docx content",
            content_type=(
                "application/vnd.openxmlformats-"
                "officedocument.wordprocessingml.document"
            ),
        )

        response = self.client.patch(
            reverse(
                "document-detail",
                args=[
                    document.id,
                ],
            ),
            data={
                "file": replacement_file,
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        document.refresh_from_db()

        mocked_pipeline.assert_called_once_with(
            document
        )

    def test_delete_document(
        self,
    ):
        document = self.create_document()

        response = self.client.delete(
            reverse(
                "document-detail",
                args=[
                    document.id,
                ],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Document.objects.filter(
                id=document.id
            ).exists()
        )

    def test_non_docx_file_is_rejected(
        self,
    ):
        uploaded_file = SimpleUploadedFile(
            "invalid.txt",
            b"not a docx file",
            content_type="text/plain",
        )

        response = self.client.post(
            reverse(
                "document-list"
            ),
            data={
                "title": "Invalid Document",
                "file": uploaded_file,
            },
            format="multipart",
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
            "file",
            response.data[
                "error"
            ][
                "details"
            ],
        )

        self.assertEqual(
            Document.objects.count(),
            0,
        )

    def test_missing_document_returns_standardized_404(
        self,
    ):
        response = self.client.get(
            reverse(
                "document-detail",
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