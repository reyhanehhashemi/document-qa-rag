from unittest.mock import patch

from django.test import TestCase

from apps.documents.models import Document
from apps.documents.services.pipeline import (
    run_document_pipeline,
)


class DocumentPipelineTests(TestCase):
    def create_document(self):
        return Document.objects.create(
            title="Pipeline Test",
            file="documents/pipeline-test.docx",
        )

    @patch(
        "apps.documents.services.pipeline.index_document"
    )
    @patch(
        "apps.documents.services.pipeline.process_document"
    )
    def test_pipeline_processes_and_indexes_document(
        self,
        mocked_process_document,
        mocked_index_document,
    ):
        document = self.create_document()

        result = run_document_pipeline(
            document
        )

        self.assertTrue(
            result.success
        )

        self.assertEqual(
            result.error,
            "",
        )

        mocked_process_document.assert_called_once_with(
            document
        )

        mocked_index_document.assert_called_once_with(
            document
        )

    @patch(
        "apps.documents.services.pipeline.logger.exception"
    )
    @patch(
        "apps.documents.services.pipeline.index_document"
    )
    @patch(
        "apps.documents.services.pipeline.process_document"
    )
    def test_pipeline_failure_marks_document_failed(
        self,
        mocked_process_document,
        mocked_index_document,
        mocked_logger_exception,
    ):
        document = self.create_document()

        mocked_process_document.side_effect = RuntimeError(
            "Processing failed."
        )

        result = run_document_pipeline(
            document
        )

        document.refresh_from_db()

        self.assertFalse(
            result.success
        )

        self.assertEqual(
            result.error,
            "Processing failed.",
        )

        self.assertEqual(
            document.status,
            Document.Status.FAILED,
        )

        self.assertEqual(
            document.processing_error,
            "Processing failed.",
        )

        mocked_index_document.assert_not_called()

        mocked_logger_exception.assert_called_once()