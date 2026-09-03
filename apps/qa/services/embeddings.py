from functools import lru_cache

from django.conf import settings
from sentence_transformers import SentenceTransformer

from .exceptions import EmbeddingServiceError


@lru_cache(maxsize=1)
def get_embedding_model():
    """
    Load and cache the configured SentenceTransformer model.

    The model is loaded only once per Python process.
    """
    try:
        model = SentenceTransformer(
            settings.EMBEDDING_MODEL_NAME,
            device=settings.EMBEDDING_DEVICE,
        )
    except Exception as exc:
        raise EmbeddingServiceError(
            "Unable to load the embedding model."
        ) from exc

    model_dimension = model.get_embedding_dimension()

    if model_dimension != settings.EMBEDDING_DIMENSION:
        raise EmbeddingServiceError(
            (
                "Embedding dimension mismatch. "
                f"Expected {settings.EMBEDDING_DIMENSION}, "
                f"but model returned {model_dimension}."
            )
        )

    return model


def embed_texts(texts):
    """
    Generate normalized embeddings for multiple text values.
    """
    if not texts:
        raise EmbeddingServiceError(
            "At least one text value is required."
        )

    for text in texts:
        if not isinstance(text, str) or not text.strip():
            raise EmbeddingServiceError(
                "Embedding input must contain non-empty strings."
            )

    if settings.EMBEDDING_BATCH_SIZE <= 0:
        raise EmbeddingServiceError(
            "Embedding batch size must be greater than zero."
        )

    model = get_embedding_model()

    try:
        vectors = model.encode(
            texts,
            batch_size=settings.EMBEDDING_BATCH_SIZE,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
    except Exception as exc:
        raise EmbeddingServiceError(
            "Unable to generate text embeddings."
        ) from exc

    if hasattr(vectors, "tolist"):
        vectors = vectors.tolist()

    normalized_vectors = []

    for vector in vectors:
        vector = [
            float(value)
            for value in vector
        ]

        if len(vector) != settings.EMBEDDING_DIMENSION:
            raise EmbeddingServiceError(
                (
                    "Generated embedding has an invalid "
                    f"dimension: {len(vector)}."
                )
            )

        normalized_vectors.append(
            vector
        )

    if len(normalized_vectors) != len(texts):
        raise EmbeddingServiceError(
            "Embedding output count does not match input count."
        )

    return normalized_vectors


def embed_query(text):
    """
    Generate a single normalized query embedding.
    """
    if not isinstance(text, str) or not text.strip():
        raise EmbeddingServiceError(
            "Query text cannot be empty."
        )

    return embed_texts(
        [text]
    )[0]