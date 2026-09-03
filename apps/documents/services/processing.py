from .docx_parser import extract_docx_text
from .exceptions import DocumentProcessingError


def process_document(document):
    """
    Extract text from a document file and update its processing state.

    The document moves through the following states:

        uploaded -> processing -> processed

    If processing fails:

        processing -> failed
    """
    if not document.file:
        document.status = document.Status.FAILED
        document.processing_error = "Document file is missing."
        document.text_content = ""

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

    document.save(
        update_fields=[
            "status",
            "processing_error",
            "updated_at",
        ]
    )

    try:
        with document.file.open("rb") as file_object:
            extracted_text = extract_docx_text(file_object)

    except DocumentProcessingError as exc:
        document.status = document.Status.FAILED
        document.processing_error = str(exc)
        document.text_content = ""

        document.save(
            update_fields=[
                "status",
                "processing_error",
                "text_content",
                "updated_at",
            ]
        )

        raise

    except OSError as exc:
        error_message = "Unable to read the uploaded document."

        document.status = document.Status.FAILED
        document.processing_error = error_message
        document.text_content = ""

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

    document.text_content = extracted_text
    document.status = document.Status.PROCESSED
    document.processing_error = ""

    document.save(
        update_fields=[
            "text_content",
            "status",
            "processing_error",
            "updated_at",
        ]
    )

    return document