import re
from zipfile import BadZipFile

from docx import Document as WordDocument
from docx.opc.exceptions import PackageNotFoundError
from docx.table import Table
from docx.text.paragraph import Paragraph

from .exceptions import EmptyDocxError, InvalidDocxError


def normalize_inline_text(text):
    """
    Normalize whitespace inside a single paragraph or table cell.
    """
    return re.sub(r"\s+", " ", text).strip()


def extract_paragraph_text(paragraph):
    """
    Extract and normalize text from a DOCX paragraph.
    """
    return normalize_inline_text(paragraph.text)


def extract_table_text(table):
    """
    Extract text from a DOCX table.

    Each row is stored on a separate line and cells are separated by
    a pipe character so the table structure remains understandable
    for later retrieval and LLM processing.
    """
    rows = []

    for row in table.rows:
        cells = [
            normalize_inline_text(cell.text)
            for cell in row.cells
        ]

        if any(cells):
            rows.append(" | ".join(cells))

    return "\n".join(rows)


def clean_document_text(text_blocks):
    """
    Join extracted document blocks while keeping logical separation
    between paragraphs and tables.
    """
    non_empty_blocks = [
        block.strip()
        for block in text_blocks
        if block and block.strip()
    ]

    return "\n\n".join(non_empty_blocks).strip()


def extract_docx_text(source):
    """
    Extract readable text from a DOCX file or file-like object.

    Paragraphs and top-level tables are processed in their original
    document order.

    Raises:
        InvalidDocxError:
            If the file is not a readable DOCX document.

        EmptyDocxError:
            If the document does not contain usable text.
    """
    try:
        if hasattr(source, "seek"):
            source.seek(0)

        word_document = WordDocument(source)

    except (
        PackageNotFoundError,
        BadZipFile,
        KeyError,
        ValueError,
    ) as exc:
        raise InvalidDocxError(
            "The uploaded file is not a valid DOCX document."
        ) from exc

    text_blocks = []

    for item in word_document.iter_inner_content():
        if isinstance(item, Paragraph):
            paragraph_text = extract_paragraph_text(item)

            if paragraph_text:
                text_blocks.append(paragraph_text)

        elif isinstance(item, Table):
            table_text = extract_table_text(item)

            if table_text:
                text_blocks.append(table_text)

    extracted_text = clean_document_text(text_blocks)

    if not extracted_text:
        raise EmptyDocxError(
            "No readable text was found in the DOCX document."
        )

    return extracted_text