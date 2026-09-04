import tempfile
from unittest.mock import patch

from django.core.management import (
    call_command,
)
from django.test import (
    TestCase,
    override_settings,
)

from apps.documents.models import Document
from apps.documents.services.pipeline import (
    DocumentPipelineResult,
)


class LoadSampleDataCommandTests(
    TestCase
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

    def mark_document_indexed(
        self,
        document,
    ):
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

        return DocumentPipelineResult(
            success=True,
        )

    @patch(
        (
            "apps.documents.management.commands."
            "load_sample_data.run_document_pipeline"
        )
    )
    def test_command_creates_sample_document(
        self,
        mocked_pipeline,
    ):
        mocked_pipeline.side_effect = (
            self.mark_document_indexed
        )

        call_command(
            "load_sample_data"
        )

        self.assertEqual(
            Document.objects.count(),
            1,
        )

        document = (
            Document.objects.get()
        )

        self.assertEqual(
            document.title,
            (
                "Northbridge University "
                "Student Services Guide"
            ),
        )

        self.assertEqual(
            document.original_filename,
            "northbridge_student_guide.docx",
        )

        self.assertEqual(
            document.status,
            Document.Status.INDEXED,
        )

        mocked_pipeline.assert_called_once_with(
            document
        )

    @patch(
        (
            "apps.documents.management.commands."
            "load_sample_data.run_document_pipeline"
        )
    )
    def test_command_is_idempotent_when_sample_is_indexed(
        self,
        mocked_pipeline,
    ):
        Document.objects.create(
            title=(
                "Northbridge University "
                "Student Services Guide"
            ),
            file=(
                "documents/"
                "northbridge_student_guide.docx"
            ),
            status=Document.Status.INDEXED,
        )

        call_command(
            "load_sample_data"
        )

        self.assertEqual(
            Document.objects.count(),
            1,
        )

        mocked_pipeline.assert_not_called()

    @patch(
        (
            "apps.documents.management.commands."
            "load_sample_data.run_document_pipeline"
        )
    )
    def test_reset_replaces_existing_sample(
        self,
        mocked_pipeline,
    ):
        mocked_pipeline.side_effect = (
            self.mark_document_indexed
        )

        existing_document = (
            Document.objects.create(
                title=(
                    "Northbridge University "
                    "Student Services Guide"
                ),
                file=(
                    "documents/"
                    "old-sample.docx"
                ),
                status=Document.Status.INDEXED,
            )
        )

        old_id = (
            existing_document.id
        )

        call_command(
            "load_sample_data",
            "--reset",
        )

        self.assertEqual(
            Document.objects.count(),
            1,
        )

        new_document = (
            Document.objects.get()
        )

        self.assertNotEqual(
            new_document.id,
            old_id,
        )

        self.assertEqual(
            new_document.status,
            Document.Status.INDEXED,
        )

        mocked_pipeline.assert_called_once_with(
            new_document
        )