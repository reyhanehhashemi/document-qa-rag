class EmbeddingServiceError(Exception):
    """Raised when embedding generation fails."""


class DocumentIndexingError(Exception):
    """Raised when document vector indexing fails."""


class RetrievalError(Exception):
    """Raised when semantic document retrieval fails."""


class LLMServiceError(Exception):
    """Raised when communication with the LLM fails."""


class LLMConfigurationError(LLMServiceError):
    """Raised when the LLM configuration is invalid."""