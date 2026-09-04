from types import SimpleNamespace
from unittest.mock import (
    patch,
)

from django.contrib.admin.sites import (
    AdminSite,
)
from django.test import (
    RequestFactory,
    TestCase,
)

from apps.documents.admin import (
    DocumentAdmin,
)
from apps.documents.models import (
    Document,
)


class DocumentAdminTests(TestCase):
    def setUp(self):
        self.site = AdminSite()

        self.model_admin = DocumentAdmin(
            Document,
            self.site,
        )

        self.request = (
            RequestFactory().post(
                "/admin/documents/document/"
            )
        )

    @patch.object(
        DocumentAdmin,
        "message_user",
    )
    @patch(
        "apps.documents.admin.index_document"
    )
    @patch(
        "apps.documents.admin.process_document"
    )
    def test_new_document_is_processed_and_indexed(
        self,
        mocked_process_document,
        mocked_index_document,
        mocked_message_user,
    ):
        document = Document(
            title="New Document",
            file="documents/new-document.docx",
        )

        form = SimpleNamespace(
            changed_data=[
                "title",
                "file",
            ]
        )

        self.model_admin.save_model(
            request=self.request,
            obj=document,
            form=form,
            change=False,
        )

        mocked_process_document.assert_called_once_with(
            document
        )

        mocked_index_document.assert_called_once_with(
            document
        )

        mocked_message_user.assert_called_once()

    @patch.object(
        DocumentAdmin,
        "message_user",
    )
    @patch(
        "apps.documents.admin.index_document"
    )
    @patch(
        "apps.documents.admin.process_document"
    )
    def test_title_only_change_does_not_reprocess(
        self,
        mocked_process_document,
        mocked_index_document,
        mocked_message_user,
    ):
        document = Document.objects.create(
            title="Original Title",
            file="documents/original.docx",
        )

        document.title = "Updated Title"

        form = SimpleNamespace(
            changed_data=[
                "title",
            ]
        )

        self.model_admin.save_model(
            request=self.request,
            obj=document,
            form=form,
            change=True,
        )

        mocked_process_document.assert_not_called()

        mocked_index_document.assert_not_called()

        mocked_message_user.assert_not_called()

    @patch.object(
        DocumentAdmin,
        "message_user",
    )
    @patch(
        "apps.documents.admin.index_document"
    )
    @patch(
        "apps.documents.admin.process_document"
    )
    def test_file_change_reprocesses_document(
        self,
        mocked_process_document,
        mocked_index_document,
        mocked_message_user,
    ):
        document = Document.objects.create(
            title="File Change",
            file="documents/original.docx",
        )

        document.file = (
            "documents/replacement.docx"
        )

        form = SimpleNamespace(
            changed_data=[
                "file",
            ]
        )

        self.model_admin.save_model(
            request=self.request,
            obj=document,
            form=form,
            change=True,
        )

        mocked_process_document.assert_called_once_with(
            document
        )

        mocked_index_document.assert_called_once_with(
            document
        )

    @patch.object(
        DocumentAdmin,
        "message_user",
    )
    @patch(
        "apps.documents.admin.index_document"
    )
    @patch(
        "apps.documents.admin.process_document"
    )
    def test_processing_failure_marks_document_failed(
        self,
        mocked_process_document,
        mocked_index_document,
        mocked_message_user,
    ):
        mocked_process_document.side_effect = RuntimeError(
            "Processing failed."
        )

        document = Document(
            title="Broken Document",
            file="documents/broken.docx",
        )

        form = SimpleNamespace(
            changed_data=[
                "file",
            ]
        )

        self.model_admin.save_model(
            request=self.request,
            obj=document,
            form=form,
            change=False,
        )

        document.refresh_from_db()

        self.assertEqual(
            document.status,
            Document.Status.FAILED,
        )

        self.assertEqual(
            document.processing_error,
            "Processing failed.",
        )

        mocked_index_document.assert_not_called()

        mocked_message_user.assert_called_once()