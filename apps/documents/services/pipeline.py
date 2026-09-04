import logging
from dataclasses import dataclass

from apps.qa.services.indexing import index_document

from .processing import process_document


logger = logging.getLogger(
    __name__
)


@dataclass(frozen=True)
class DocumentPipelineResult:
    """
    Result of the document ingestion and indexing pipeline.
    """

    success: bool
    error: str = ""


def run_document_pipeline(document):
    """
    Run the complete document ingestion pipeline.

    Flow:

        document
            -> DOCX extraction
            -> chunking
            -> embeddings
            -> vector indexing

    Failures are persisted on the Document model and returned as
    a result instead of being allowed to crash an API request.
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
                "Document pipeline failed "
                "for document %s."
            ),
            document.pk,
        )

        document.refresh_from_db()

        if document.status != document.Status.FAILED:
            document.status = document.Status.FAILED
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

        return DocumentPipelineResult(
            success=False,
            error=str(
                exc
            ),
        )

    document.refresh_from_db()

    return DocumentPipelineResult(
        success=True,
    )