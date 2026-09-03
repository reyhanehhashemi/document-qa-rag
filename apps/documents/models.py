from pathlib import Path

from django.core.validators import FileExtensionValidator
from django.db import models


class Document(models.Model):
    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        PROCESSING = "processing", "Processing"
        INDEXED = "indexed", "Indexed"
        FAILED = "failed", "Failed"

    title = models.CharField(
        max_length=255,
    )

    file = models.FileField(
        upload_to="documents/%Y/%m/%d/",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["docx"],
                message="Only DOCX files are supported.",
            )
        ],
        max_length=500,
    )

    original_filename = models.CharField(
        max_length=255,
        blank=True,
        editable=False,
    )

    text_content = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UPLOADED,
    )

    processing_error = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Document"
        verbose_name_plural = "Documents"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.file:
            current_file_name = self.file.name

            if self.pk:
                previous_file_name = (
                    type(self)
                    .objects.filter(pk=self.pk)
                    .values_list("file", flat=True)
                    .first()
                )

                if previous_file_name != current_file_name:
                    self.original_filename = Path(current_file_name).name

            elif not self.original_filename:
                self.original_filename = Path(current_file_name).name

        super().save(*args, **kwargs)