class DocumentProcessingError(Exception):
    """Base exception for document processing errors."""


class InvalidDocxError(DocumentProcessingError):
    """Raised when an uploaded file is not a valid DOCX document."""


class EmptyDocxError(DocumentProcessingError):
    """Raised when no usable text can be extracted from a DOCX document."""