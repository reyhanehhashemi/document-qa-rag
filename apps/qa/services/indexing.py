from django.db import transaction

from apps.documents.models import DocumentChunk

from .embeddings import embed_texts
from .exceptions import (
    DocumentIndexingError,
    EmbeddingServiceError,
)


def mark_indexing_failed(document, message):
    """
    Mark a document as failed without deleting its extracted text
    or generated chunks.
    """
    document.status = document.Status.FAILED
    document.processing_error = message

    document.save(
        update_fields=[
            "status",
            "processing_error",
            "updated_at",
        ]
    )


def index_document(document):
    """
    Generate and persist embeddings for all chunks of a document.

    Successful flow:

        processed -> indexed

    On failure:

        processed -> failed
    """
    if not document.pk:
        raise DocumentIndexingError(
            "Document must be saved before indexing."
        )

    chunks = list(
        document.chunks.order_by(
            "chunk_index"
        )
    )

    if not chunks:
        error_message = (
            "Document does not contain any chunks to index."
        )

        mark_indexing_failed(
            document,
            error_message,
        )

        raise DocumentIndexingError(
            error_message
        )

    chunk_texts = [
        chunk.content
        for chunk in chunks
    ]

    try:
        embeddings = embed_texts(
            chunk_texts
        )
    except EmbeddingServiceError as exc:
        error_message = str(exc)

        mark_indexing_failed(
            document,
            error_message,
        )

        raise DocumentIndexingError(
            error_message
        ) from exc

    if len(embeddings) != len(chunks):
        error_message = (
            "Embedding count does not match document chunk count."
        )

        mark_indexing_failed(
            document,
            error_message,
        )

        raise DocumentIndexingError(
            error_message
        )

    with transaction.atomic():
        for chunk, embedding in zip(
            chunks,
            embeddings,
            strict=True,
        ):
            chunk.embedding = embedding

        DocumentChunk.objects.bulk_update(
            chunks,
            [
                "embedding",
            ],
        )

        document.status = document.Status.INDEXED
        document.processing_error = ""

        document.save(
            update_fields=[
                "status",
                "processing_error",
                "updated_at",
            ]
        )

    return document