from django.db import transaction
from langchain_text_splitters import RecursiveCharacterTextSplitter

from apps.documents.models import DocumentChunk

from .exceptions import DocumentChunkingError


DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200


def build_text_splitter(
    chunk_size=DEFAULT_CHUNK_SIZE,
    chunk_overlap=DEFAULT_CHUNK_OVERLAP,
):
    """
    Build the LangChain text splitter used by the RAG ingestion pipeline.
    """
    if chunk_size <= 0:
        raise DocumentChunkingError(
            "Chunk size must be greater than zero."
        )

    if chunk_overlap < 0:
        raise DocumentChunkingError(
            "Chunk overlap cannot be negative."
        )

    if chunk_overlap >= chunk_size:
        raise DocumentChunkingError(
            "Chunk overlap must be smaller than chunk size."
        )

    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        add_start_index=True,
        is_separator_regex=False,
    )


def split_document_text(
    text,
    chunk_size=DEFAULT_CHUNK_SIZE,
    chunk_overlap=DEFAULT_CHUNK_OVERLAP,
):
    """
    Split document text into LangChain document chunks.

    Each returned LangChain Document contains:
        - page_content
        - metadata["start_index"]
    """
    if not text or not text.strip():
        raise DocumentChunkingError(
            "Document text is empty and cannot be chunked."
        )

    splitter = build_text_splitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    chunks = splitter.create_documents(
        [text]
    )

    chunks = [
        chunk
        for chunk in chunks
        if chunk.page_content.strip()
    ]

    if not chunks:
        raise DocumentChunkingError(
            "No usable chunks were generated from the document."
        )

    return chunks


@transaction.atomic
def replace_document_chunks(
    document,
    chunk_size=DEFAULT_CHUNK_SIZE,
    chunk_overlap=DEFAULT_CHUNK_OVERLAP,
):
    """
    Replace all stored chunks for a document.

    This makes re-processing idempotent: old chunks are deleted and
    replaced instead of being duplicated.
    """
    if not document.pk:
        raise DocumentChunkingError(
            "Document must be saved before chunks can be created."
        )

    split_chunks = split_document_text(
        text=document.text_content,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    document.chunks.all().delete()

    chunk_objects = []

    for chunk_index, chunk in enumerate(split_chunks):
        content = chunk.page_content.strip()

        start_index = chunk.metadata.get(
            "start_index",
            0,
        )

        if start_index is None or start_index < 0:
            start_index = 0

        chunk_objects.append(
            DocumentChunk(
                document=document,
                chunk_index=chunk_index,
                content=content,
                start_index=start_index,
                character_count=len(content),
            )
        )

    return DocumentChunk.objects.bulk_create(
        chunk_objects
    )