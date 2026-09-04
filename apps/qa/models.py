from django.db import models

from apps.documents.models import DocumentChunk


class QuestionAnswer(models.Model):
    """
    A persisted question and its document-grounded answer.
    """

    question = models.TextField()

    answer = models.TextField()

    top_k = models.PositiveIntegerField(
        default=5,
    )

    min_similarity = models.FloatField(
        default=0.20,
    )

    document_ids = models.JSONField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "-created_at",
        ]

        verbose_name = "Question Answer"
        verbose_name_plural = "Question Answers"

    def __str__(self):
        return self.question[:80]


class QuestionAnswerSource(models.Model):
    """
    A snapshot of a document chunk used to answer a question.

    The chunk relation is nullable so question history survives
    when the original document or chunk is deleted.
    """

    question_answer = models.ForeignKey(
        QuestionAnswer,
        on_delete=models.CASCADE,
        related_name="sources",
    )

    chunk = models.ForeignKey(
        DocumentChunk,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="question_answer_sources",
    )

    document_id_snapshot = models.PositiveBigIntegerField()

    document_title = models.CharField(
        max_length=255,
    )

    chunk_index = models.PositiveIntegerField()

    similarity = models.FloatField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "question_answer_id",
            "-similarity",
            "id",
        ]

        verbose_name = "Question Answer Source"
        verbose_name_plural = "Question Answer Sources"

    def __str__(self):
        return (
            f"{self.question_answer_id} - "
            f"{self.document_title} - "
            f"Chunk {self.chunk_index}"
        )