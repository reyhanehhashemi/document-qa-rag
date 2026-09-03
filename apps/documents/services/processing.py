from .chunking import replace_document_chunks
from .docx_parser import extract_docx_text
from .exceptions import (
    DocumentChunkingError,
    DocumentProcessingError,
    EmptyDocxError,
    InvalidDocxError,
)


def process_document(document):
    """
    Extract text from a document and generate RAG chunks.

    Processing flow:

        uploaded
            -> processing
            -> processed

    On failure:

        processing
            -> failed
    """
    if not document.pk:
        raise DocumentProcessingError(
            "Document must be saved before processing."
        )

    if not document.file:
        document.status = document.Status.FAILED
        document.processing_error = "Document file is missing."
        document.text_content = ""

        document.chunks.all().delete()

        document.save(
            update_fields=[
                "status",
                "processing_error",
                "text_content",
                "updated_at",
            ]
        )

        raise DocumentProcessingError(
            "Document file is missing."
        )

    document.status = document.Status.PROCESSING
    document.processing_error = ""
    document.text_content = ""

    document.chunks.all().delete()

    document.save(
        update_fields=[
            "status",
            "processing_error",
            "text_content",
            "updated_at",
        ]
    )

    try:
        with document.file.open("rb") as file_object:
            extracted_text = extract_docx_text(
                file_object
            )

        document.text_content = extracted_text

        document.save(
            update_fields=[
                "text_content",
                "updated_at",
            ]
        )

        replace_document_chunks(
            document
        )

    except (
        InvalidDocxError,
        EmptyDocxError,
    ) as exc:
        document.status = document.Status.FAILED
        document.processing_error = str(exc)
        document.text_content = ""

        document.chunks.all().delete()

        document.save(
            update_fields=[
                "status",
                "processing_error",
                "text_content",
                "updated_at",
            ]
        )

        raise

    except DocumentChunkingError as exc:
        document.status = document.Status.FAILED
        document.processing_error = str(exc)

        document.chunks.all().delete()

        document.save(
            update_fields=[
                "status",
                "processing_error",
                "updated_at",
            ]
        )

        raise

    except OSError as exc:
        error_message = (
            "Unable to read the uploaded document."
        )

        document.status = document.Status.FAILED
        document.processing_error = error_message
        document.text_content = ""

        document.chunks.all().delete()

        document.save(
            update_fields=[
                "status",
                "processing_error",
                "text_content",
                "updated_at",
            ]
        )

        raise DocumentProcessingError(
            error_message
        ) from exc

    document.status = document.Status.PROCESSED
    document.processing_error = ""

    document.save(
        update_fields=[
            "status",
            "processing_error",
            "updated_at",
        ]
    )

    return document