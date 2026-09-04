from django.conf import settings
from django.core.files import File
from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from apps.documents.models import Document
from apps.documents.services.pipeline import (
    run_document_pipeline,
)


SAMPLE_TITLE = (
    "Northbridge University Student Services Guide"
)

SAMPLE_FILENAME = (
    "northbridge_student_guide.docx"
)


class Command(BaseCommand):
    help = (
        "Load and index the project sample DOCX document."
    )

    def add_arguments(
        self,
        parser,
    ):
        parser.add_argument(
            "--reset",
            action="store_true",
            help=(
                "Delete an existing sample document "
                "and recreate it."
            ),
        )

    def delete_existing_documents(
        self,
        queryset,
    ):
        """
        Delete existing sample records and their stored files.
        """
        for document in queryset:
            if document.file:
                document.file.delete(
                    save=False
                )

            document.delete()

    def handle(
        self,
        *args,
        **options,
    ):
        sample_path = (
            settings.BASE_DIR
            / "sample_data"
            / SAMPLE_FILENAME
        )

        if not sample_path.exists():
            raise CommandError(
                (
                    "Sample DOCX does not exist. "
                    "Generate it first with: "
                    "python scripts/generate_sample_docx.py"
                )
            )

        existing_documents = (
            Document.objects.filter(
                title=SAMPLE_TITLE,
            )
        )

        if options["reset"]:
            self.delete_existing_documents(
                existing_documents
            )

            existing_documents = (
                Document.objects.none()
            )

        existing_document = (
            existing_documents.first()
        )

        if existing_document is not None:
            if (
                existing_document.status
                == Document.Status.INDEXED
            ):
                self.stdout.write(
                    self.style.SUCCESS(
                        (
                            "Sample document is already "
                            "loaded and indexed. "
                            f"ID: {existing_document.id}"
                        )
                    )
                )

                return

            raise CommandError(
                (
                    "A sample document already exists "
                    "but is not indexed. "
                    "Run the command again with --reset."
                )
            )

        with sample_path.open(
            "rb"
        ) as source_file:
            django_file = File(
                source_file,
                name=SAMPLE_FILENAME,
            )

            document = Document.objects.create(
                title=SAMPLE_TITLE,
                file=django_file,
            )

        result = run_document_pipeline(
            document
        )

        document.refresh_from_db()

        if (
            not result.success
            or document.status
            != Document.Status.INDEXED
        ):
            raise CommandError(
                (
                    "Sample document processing failed: "
                    f"{result.error or document.processing_error}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                (
                    "Sample document loaded successfully. "
                    f"ID: {document.id}, "
                    f"status: {document.status}, "
                    f"chunks: {document.chunks.count()}"
                )
            )
        )