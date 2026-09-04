import logging

from django.contrib import (
    admin,
    messages,
)

from apps.qa.services.indexing import index_document

from .models import (
    Document,
    DocumentChunk,
)
from .services.processing import process_document


logger = logging.getLogger(
    __name__
)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """
    Django Admin interface for document management.

    New documents and replaced files are processed and indexed
    automatically after they are saved.
    """

    list_display = (
        "title",
        "original_filename",
        "status",
        "chunk_count",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "status",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "title",
        "original_filename",
        "text_content",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "original_filename",
        "status",
        "processing_error",
        "chunk_count_display",
        "text_content",
        "created_at",
        "updated_at",
    )

    fields = (
        "title",
        "file",
        "original_filename",
        "status",
        "processing_error",
        "chunk_count_display",
        "text_content",
        "created_at",
        "updated_at",
    )

    actions = (
        "reprocess_selected_documents",
    )

    @admin.display(
        description="Chunks",
    )
    def chunk_count(self, obj):
        if not obj.pk:
            return 0

        return obj.chunks.count()

    @admin.display(
        description="Chunk count",
    )
    def chunk_count_display(self, obj):
        if not obj.pk:
            return 0

        return obj.chunks.count()

    def save_model(
        self,
        request,
        obj,
        form,
        change,
    ):
        """
        Save the document and process it only when:

        - it is a newly uploaded document, or
        - the uploaded file has been replaced.

        Editing only the title must not regenerate embeddings.
        """
        should_process = (
            not change
            or "file" in form.changed_data
        )

        super().save_model(
            request,
            obj,
            form,
            change,
        )

        if should_process:
            self._process_and_index_document(
                request=request,
                document=obj,
            )

    def _process_and_index_document(
        self,
        request,
        document,
        show_message=True,
    ):
        """
        Run the full ingestion pipeline for one document.
        """
        try:
            process_document(
                document
            )

            index_document(
                document
            )

        except Exception as exc:
            logger.exception(
                (
                    "Document processing failed "
                    "for document %s."
                ),
                document.pk,
            )

            document.refresh_from_db()

            if document.status != Document.Status.FAILED:
                document.status = Document.Status.FAILED
                document.processing_error = str(
                    exc
                )

                document.save(
                    update_fields=[
                        "status",
                        "processing_error",
                        "updated_at",
                    ]
                )

            if show_message:
                self.message_user(
                    request,
                    (
                        f'Processing failed for "{document.title}": '
                        f"{exc}"
                    ),
                    level=messages.ERROR,
                )

            return False

        document.refresh_from_db()

        if show_message:
            self.message_user(
                request,
                (
                    f'"{document.title}" was processed '
                    "and indexed successfully."
                ),
                level=messages.SUCCESS,
            )

        return True

    @admin.action(
        description=(
            "Process and index selected documents"
        )
    )
    def reprocess_selected_documents(
        self,
        request,
        queryset,
    ):
        """
        Manually rebuild chunks and embeddings for selected documents.
        """
        successful = 0
        failed = 0

        for document in queryset:
            result = self._process_and_index_document(
                request=request,
                document=document,
                show_message=False,
            )

            if result:
                successful += 1
            else:
                failed += 1

        if successful:
            self.message_user(
                request,
                (
                    f"{successful} document(s) "
                    "processed and indexed successfully."
                ),
                level=messages.SUCCESS,
            )

        if failed:
            self.message_user(
                request,
                (
                    f"{failed} document(s) "
                    "failed during processing."
                ),
                level=messages.ERROR,
            )


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    """
    Read-only inspection interface for generated chunks.
    """

    list_display = (
        "document",
        "chunk_index",
        "character_count",
        "embedding_status",
        "created_at",
    )

    list_filter = (
        "document",
        "created_at",
    )

    search_fields = (
        "document__title",
        "content",
    )

    ordering = (
        "document_id",
        "chunk_index",
    )

    fields = (
        "document",
        "chunk_index",
        "start_index",
        "character_count",
        "embedding_status",
        "content",
        "created_at",
    )

    readonly_fields = (
        "document",
        "chunk_index",
        "start_index",
        "character_count",
        "embedding_status",
        "content",
        "created_at",
    )

    @admin.display(
        boolean=True,
        description="Embedded",
    )
    def embedding_status(self, obj):
        return obj.embedding is not None

    def has_add_permission(
        self,
        request,
    ):
        return False

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        return False