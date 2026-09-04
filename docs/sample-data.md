# Sample Data

The project includes a reproducible English DOCX document for
demonstration and manual testing.

## Sample document

File:

`sample_data/northbridge_student_guide.docx`

Title:

`Northbridge University Student Services Guide`

The document contains fictional information about:

- course registration
- library hours and borrowing
- tuition payments
- student ID cards
- IT support

It also intentionally omits several facts so the RAG system can be
tested for insufficient-context behavior.

## Regenerate the DOCX

The committed sample document can be regenerated with:

```bash
docker compose exec web python scripts/generate_sample_docx.py