from dataclasses import dataclass

from .exceptions import (
    LLMServiceError,
    RAGServiceError,
    RetrievalError,
)
from .llm import generate_llm_response
from .retriever import (
    DEFAULT_MIN_SIMILARITY,
    DEFAULT_TOP_K,
    retrieve_relevant_chunks,
)


NO_CONTEXT_ANSWER = (
    "اطلاعات کافی برای پاسخ‌گویی در اسناد موجود نیست."
)

NO_CONTEXT_ANSWER_EN = (
    "The available documents do not contain enough information "
    "to answer this question."
)


SYSTEM_PROMPT = """
You are a document question answering assistant.

You must answer the user's question using only the document context
provided to you.

Rules:
1. Use only information explicitly supported by the provided context.
2. Do not use outside knowledge, assumptions, or invented facts.
3. If the context does not contain enough information to answer the
   question, clearly say that the available documents do not contain
   enough information.
4. Answer in the same language as the user's question.
5. Be concise, clear, and factual.
6. Do not invent document names, quotations, citations, or sources.
7. Do not claim that something is stated in the documents unless it is
   supported by the provided context.
""".strip()


@dataclass(frozen=True)
class RAGSource:
    """
    Metadata for a document chunk used as RAG context.
    """

    chunk_id: int
    document_id: int
    document_title: str
    chunk_index: int
    similarity: float


@dataclass(frozen=True)
class RAGAnswer:
    """
    Final result produced by the RAG pipeline.
    """

    question: str
    answer: str
    sources: tuple[RAGSource, ...]


def contains_persian_or_arabic_text(text):
    """
    Return True when the text contains Persian or Arabic characters.

    This lightweight check lets deterministic no-context responses
    follow the language of the user's question without introducing
    another external dependency.
    """
    return any(
        "\u0600" <= character <= "\u06ff"
        for character in text
    )


def get_no_context_answer(question):
    """
    Return the deterministic no-context message in the question's
    language.
    """
    if contains_persian_or_arabic_text(
        question
    ):
        return NO_CONTEXT_ANSWER

    return NO_CONTEXT_ANSWER_EN


def build_context(
    retrieved_chunks,
):
    """
    Convert retrieved document chunks into structured LLM context.
    """
    if not retrieved_chunks:
        return ""

    context_blocks = []

    for position, chunk in enumerate(
        retrieved_chunks,
        start=1,
    ):
        context_blocks.append(
            "\n".join(
                [
                    f"[Source {position}]",
                    (
                        "Document: "
                        f"{chunk.document_title}"
                    ),
                    (
                        "Chunk index: "
                        f"{chunk.chunk_index}"
                    ),
                    (
                        "Similarity: "
                        f"{chunk.similarity:.4f}"
                    ),
                    "Content:",
                    chunk.content.strip(),
                ]
            )
        )

    return "\n\n".join(
        context_blocks
    )


def build_user_prompt(
    question,
    context,
):
    """
    Build the user prompt containing the retrieved document context.
    """
    return (
        "Use the document context below to answer the question.\n\n"
        "DOCUMENT CONTEXT\n"
        "================\n"
        f"{context}\n\n"
        "QUESTION\n"
        "========\n"
        f"{question.strip()}\n\n"
        "Answer using only the document context."
    )


def build_sources(
    retrieved_chunks,
):
    """
    Build source metadata returned with the generated answer.
    """
    return tuple(
        RAGSource(
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            document_title=chunk.document_title,
            chunk_index=chunk.chunk_index,
            similarity=chunk.similarity,
        )
        for chunk in retrieved_chunks
    )


def answer_question(
    question,
    top_k=DEFAULT_TOP_K,
    min_similarity=DEFAULT_MIN_SIMILARITY,
    document_ids=None,
):
    """
    Answer a question using retrieval-augmented generation.

    Flow:

        question
            -> semantic retrieval
            -> context construction
            -> OpenRouter LLM
            -> grounded answer

    If no sufficiently relevant document chunks are found, the LLM is
    not called and a deterministic insufficient-context answer is
    returned in the language of the question.
    """
    if not isinstance(question, str) or not question.strip():
        raise RAGServiceError(
            "Question cannot be empty."
        )

    clean_question = question.strip()

    try:
        retrieved_chunks = retrieve_relevant_chunks(
            question=clean_question,
            top_k=top_k,
            min_similarity=min_similarity,
            document_ids=document_ids,
        )
    except RetrievalError as exc:
        raise RAGServiceError(
            "Unable to retrieve relevant document content."
        ) from exc

    if not retrieved_chunks:
        return RAGAnswer(
            question=clean_question,
            answer=get_no_context_answer(
                clean_question
            ),
            sources=(),
        )

    context = build_context(
        retrieved_chunks
    )

    user_prompt = build_user_prompt(
        question=clean_question,
        context=context,
    )

    try:
        generated_answer = generate_llm_response(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
    except LLMServiceError as exc:
        raise RAGServiceError(
            "Unable to generate the document-based answer."
        ) from exc

    return RAGAnswer(
        question=clean_question,
        answer=generated_answer,
        sources=build_sources(
            retrieved_chunks
        ),
    )