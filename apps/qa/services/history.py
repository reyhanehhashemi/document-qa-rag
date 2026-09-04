from django.db import transaction

from apps.qa.models import (
    QuestionAnswer,
    QuestionAnswerSource,
)

from .rag import answer_question


def normalize_document_ids(document_ids):
    """
    Convert an optional document ID iterable into a reusable list.
    """
    if document_ids is None:
        return None

    return list(
        document_ids
    )


def answer_and_save_question(
    question,
    top_k=5,
    min_similarity=0.20,
    document_ids=None,
):
    """
    Run the RAG pipeline and persist the resulting question,
    answer, retrieval parameters, and source metadata.

    The external LLM call happens before opening the database
    transaction so a slow network request does not keep a database
    transaction open unnecessarily.
    """
    normalized_document_ids = normalize_document_ids(
        document_ids
    )

    rag_result = answer_question(
        question=question,
        top_k=top_k,
        min_similarity=min_similarity,
        document_ids=normalized_document_ids,
    )

    with transaction.atomic():
        question_answer = QuestionAnswer.objects.create(
            question=rag_result.question,
            answer=rag_result.answer,
            top_k=top_k,
            min_similarity=min_similarity,
            document_ids=normalized_document_ids,
        )

        source_objects = [
            QuestionAnswerSource(
                question_answer=question_answer,
                chunk_id=source.chunk_id,
                document_id_snapshot=source.document_id,
                document_title=source.document_title,
                chunk_index=source.chunk_index,
                similarity=source.similarity,
            )
            for source in rag_result.sources
        ]

        if source_objects:
            QuestionAnswerSource.objects.bulk_create(
                source_objects
            )

    return question_answer