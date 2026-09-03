from dataclasses import dataclass

from pgvector.django import CosineDistance

from apps.documents.models import (
    Document,
    DocumentChunk,
)

from .embeddings import embed_query
from .exceptions import (
    EmbeddingServiceError,
    RetrievalError,
)


DEFAULT_TOP_K = 5
DEFAULT_MIN_SIMILARITY = 0.20


@dataclass(frozen=True)
class RetrievedChunk:
    """
    A document chunk returned by semantic retrieval.
    """

    chunk_id: int
    document_id: int
    document_title: str
    chunk_index: int
    content: str
    start_index: int
    similarity: float


def validate_retrieval_parameters(
    question,
    top_k,
    min_similarity,
):
    """
    Validate semantic retrieval input parameters.
    """
    if not isinstance(question, str) or not question.strip():
        raise RetrievalError(
            "Question cannot be empty."
        )

    if (
        not isinstance(top_k, int)
        or isinstance(top_k, bool)
        or top_k <= 0
    ):
        raise RetrievalError(
            "top_k must be a positive integer."
        )

    if (
        not isinstance(
            min_similarity,
            (int, float),
        )
        or isinstance(min_similarity, bool)
    ):
        raise RetrievalError(
            "min_similarity must be a number."
        )

    if not 0.0 <= float(min_similarity) <= 1.0:
        raise RetrievalError(
            "min_similarity must be between 0 and 1."
        )


def retrieve_relevant_chunks(
    question,
    top_k=DEFAULT_TOP_K,
    min_similarity=DEFAULT_MIN_SIMILARITY,
    document_ids=None,
):
    """
    Retrieve the most semantically relevant indexed document chunks.

    Retrieval flow:

        question
            -> embedding
            -> cosine distance
            -> similarity threshold
            -> top-k chunks

    Only chunks belonging to documents with status INDEXED and
    non-null embeddings are eligible.

    Args:
        question:
            User question.

        top_k:
            Maximum number of chunks to return.

        min_similarity:
            Minimum cosine similarity accepted.

        document_ids:
            Optional iterable of Document IDs used to restrict search.

    Returns:
        A list of RetrievedChunk objects ordered from most relevant
        to least relevant.
    """
    validate_retrieval_parameters(
        question=question,
        top_k=top_k,
        min_similarity=min_similarity,
    )

    try:
        query_embedding = embed_query(
            question.strip()
        )
    except EmbeddingServiceError as exc:
        raise RetrievalError(
            "Unable to generate the question embedding."
        ) from exc

    queryset = (
        DocumentChunk.objects
        .select_related(
            "document"
        )
        .filter(
            embedding__isnull=False,
            document__status=Document.Status.INDEXED,
        )
    )

    if document_ids is not None:
        document_ids = list(
            document_ids
        )

        if not document_ids:
            return []

        queryset = queryset.filter(
            document_id__in=document_ids
        )

    maximum_distance = (
        1.0 - float(min_similarity)
    )

    queryset = (
        queryset
        .annotate(
            distance=CosineDistance(
                "embedding",
                query_embedding,
            )
        )
        .filter(
            distance__lte=maximum_distance
        )
        .order_by(
            "distance",
            "id",
        )
    )

    chunks = list(
        queryset[:top_k]
    )

    results = []

    for chunk in chunks:
        similarity = (
            1.0 - float(chunk.distance)
        )

        similarity = max(
            -1.0,
            min(
                1.0,
                similarity,
            ),
        )

        results.append(
            RetrievedChunk(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                document_title=chunk.document.title,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                start_index=chunk.start_index,
                similarity=similarity,
            )
        )

    return results