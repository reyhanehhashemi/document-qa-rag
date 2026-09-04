# Document QA RAG

A Django-based document question answering system that allows users to
upload DOCX documents, extract and index their contents, retrieve
semantically relevant text, and generate document-grounded answers using
a large language model.

The project was designed as a simple, readable, and extensible RAG
(Retrieval-Augmented Generation) application.

## Main Features

- Upload, edit, and delete DOCX documents
- Extract and store the complete text of each document
- Split documents into overlapping semantic-search chunks
- Generate multilingual embeddings
- Store vectors in PostgreSQL using pgvector
- Retrieve relevant chunks using cosine similarity
- Filter retrieval by selected documents
- Configure `top_k` and minimum similarity
- Generate answers using LangChain and OpenRouter
- Avoid generating unsupported answers when no relevant context exists
- Persist question-answer history
- Persist source snapshots for every generated answer
- Preserve answer source history even after a document is deleted
- Manage documents and ask questions through Django Admin
- Complete REST API with validation and standardized errors
- OpenAPI schema, Swagger UI, and ReDoc
- Paginated question-answer history
- API/database health check
- Sample DOCX data and sample questions
- Docker-based PostgreSQL and Django environment
- Gunicorn application server
- WhiteNoise static-file serving
- Automated test suite

## Technology Stack

- Python 3.13
- Django 5.2
- Django REST Framework
- LangChain
- OpenRouter
- Sentence Transformers
- PostgreSQL 16
- pgvector
- python-docx
- drf-spectacular
- Gunicorn
- WhiteNoise
- Docker
- Docker Compose

## Architecture

The high-level RAG flow is:

```text
DOCX upload
    |
    v
Text extraction
    |
    v
Document text stored in PostgreSQL
    |
    v
Text chunking
    |
    v
Multilingual embeddings
    |
    v
pgvector
    |
    +------------------------------+
                                   |
User question                     |
    |                              |
    v                              |
Question embedding                 |
    |                              |
    v                              |
Cosine-similarity retrieval <------+
    |
    v
Relevant document chunks
    |
    v
LangChain prompt
    |
    v
OpenRouter LLM
    |
    v
Grounded answer
    |
    +--> QuestionAnswer history
    |
    +--> QuestionAnswerSource snapshots
```

A more detailed architecture description is available in
[`docs/architecture.md`](docs/architecture.md).

## Project Structure

```text
document-qa-rag/
├── apps/
│   ├── documents/
│   │   ├── api/
│   │   ├── management/
│   │   ├── migrations/
│   │   ├── services/
│   │   └── tests/
│   └── qa/
│       ├── api/
│       ├── services/
│       ├── templates/
│       └── tests/
├── config/
├── docker/
│   ├── postgres/
│   └── web/
├── docs/
│   ├── screenshots/
│   ├── api.md
│   ├── architecture.md
│   ├── openapi-schema.yml
│   └── sample-data.md
├── sample_data/
├── scripts/
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── gunicorn.conf.py
├── manage.py
└── requirements.txt
```

## Prerequisites

Install:

- Docker Desktop
- Docker Compose
- Git

An OpenRouter API key is required for real LLM answers.

Create an account at OpenRouter and configure a model available to your
account.

The first embedding operation may also need internet access to download
the configured Sentence Transformer model. The Hugging Face model cache
is persisted in a Docker volume after it has been downloaded.

## Quick Start with Docker

Clone the repository:

```bash
git clone https://github.com/reyhanehhashemi/document-qa-rag.git
cd document-qa-rag
```

Create the environment file:

```bash
cp .env.example .env
```

Edit `.env` and set at least:

```dotenv
DJANGO_SECRET_KEY=your-secret-key
DB_PASSWORD=your-database-password
OPENROUTER_API_KEY=your-openrouter-key
```

Do not commit `.env`.

Build and start the application:

```bash
docker compose up -d --build
```

Check container health:

```bash
docker compose ps
```

Both `db` and `web` should become healthy.

Run migrations explicitly if needed:

```bash
docker compose exec web python manage.py migrate
```

Create a Django Admin user:

```bash
docker compose exec web python manage.py createsuperuser
```

Load the included sample document:

```bash
docker compose exec web python manage.py load_sample_data
```

Then open:

- Django Admin: `http://localhost:8000/admin/`
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`
- OpenAPI schema: `http://localhost:8000/api/schema/`
- Health check: `http://localhost:8000/api/health/`

## Docker Ports

The default ports are:

| Service | Host | Container |
| --- | ---: | ---: |
| Django / Gunicorn | 8000 | 8000 |
| PostgreSQL | 5433 | 5432 |

PostgreSQL uses host port `5433` by default to avoid conflicts with a
PostgreSQL installation already using `5432` on the host.

Inside Docker, Django connects to PostgreSQL using:

```text
db:5432
```

## Environment Variables

Important variables are documented in `.env.example`.

### Django

```dotenv
DJANGO_SECRET_KEY=
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=
```

### PostgreSQL

```dotenv
DB_NAME=document_qa
DB_USER=document_qa_user
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=5433
POSTGRES_HOST_PORT=5433
```

Docker overrides the application database connection to:

```text
DB_HOST=db
DB_PORT=5432
```

### Embeddings

```dotenv
EMBEDDING_MODEL_NAME=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
EMBEDDING_DEVICE=cpu
EMBEDDING_BATCH_SIZE=32
```

### OpenRouter

```dotenv
OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=thinkingmachines/inkling:free
OPENROUTER_FALLBACK_MODELS=thinkingmachines/inkling-small:free,liquid/lfm-2.5-2.6b:free
OPENROUTER_TEMPERATURE=0
OPENROUTER_MAX_TOKENS=512
OPENROUTER_TIMEOUT_MS=120000
OPENROUTER_MAX_RETRIES=1
```

Free-model availability on OpenRouter may change. Models can therefore
be replaced using environment variables without changing application
code.

### Gunicorn

```dotenv
GUNICORN_WORKERS=1
GUNICORN_THREADS=2
GUNICORN_TIMEOUT=180
GUNICORN_GRACEFUL_TIMEOUT=30
GUNICORN_KEEPALIVE=5
GUNICORN_LOG_LEVEL=info
```

The default configuration intentionally uses one Gunicorn worker because
the embedding model and PyTorch may otherwise be loaded separately by
each worker and consume considerably more memory.

## Django Admin

The Admin interface is the main user interface of the project.

It supports:

- adding DOCX documents
- editing document metadata
- replacing document files
- deleting documents
- automatically processing and indexing uploaded documents
- inspecting generated chunks
- viewing question-answer history
- inspecting source snapshots
- asking new questions directly from Django Admin
- optionally restricting a question to selected indexed documents

A title-only document edit does not unnecessarily regenerate embeddings.

Replacing the DOCX file runs the document processing and indexing
pipeline again.

## Document Processing Pipeline

When a DOCX document is uploaded:

1. the original filename is stored;
2. text is extracted using `python-docx`;
3. the complete text is stored in `Document.text_content`;
4. the text is split into overlapping chunks;
5. chunks are persisted as `DocumentChunk` records;
6. multilingual embeddings are generated;
7. embeddings are stored in pgvector;
8. the document status becomes `indexed`.

Processing failures are recorded in:

```text
status = failed
processing_error = ...
```

## Retrieval

The retrieval service:

1. embeds the user question;
2. searches only indexed document chunks;
3. optionally limits search to selected document IDs;
4. calculates cosine distance using pgvector;
5. converts the result to cosine similarity;
6. applies the configured minimum similarity;
7. returns the best `top_k` chunks.

The API currently accepts:

```text
1 <= top_k <= 10
0.0 <= min_similarity <= 1.0
```

## Grounded Question Answering

Retrieved text is passed through a LangChain prompt to the configured
OpenRouter model.

The prompt instructs the model to:

- answer only from the supplied document context;
- not introduce unsupported external knowledge;
- use the same language as the user question;
- state when the documents do not provide enough information.

If retrieval returns no sufficiently relevant chunks, the application
does not call the LLM. It returns a deterministic insufficient-context
message instead.

For example:

```text
The available documents do not contain enough information to answer this question.
```

This reduces unnecessary LLM calls and limits hallucination in obvious
no-context cases.

## Question-Answer History

Every successful question operation creates a `QuestionAnswer` record.

For retrieved contexts, the system also stores
`QuestionAnswerSource` snapshots containing:

- source document ID
- source document title
- source chunk index
- similarity score
- chunk relation when still available

The source uses `SET_NULL` for its chunk relationship and stores snapshot
metadata separately. As a result, question history remains meaningful
even if the original document is later deleted.

## REST API

Base API URL:

```text
http://localhost:8000/api/v1/
```

Main endpoints:

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/v1/documents/` | List documents |
| POST | `/api/v1/documents/` | Upload and index DOCX |
| GET | `/api/v1/documents/{id}/` | Document detail |
| PUT | `/api/v1/documents/{id}/` | Replace document |
| PATCH | `/api/v1/documents/{id}/` | Partial update |
| DELETE | `/api/v1/documents/{id}/` | Delete document |
| POST | `/api/v1/questions/ask/` | Ask a grounded question |
| GET | `/api/v1/questions/` | Paginated QA history |
| GET | `/api/v1/questions/{id}/` | QA history detail |
| GET | `/api/health/` | API/database health |

Detailed API examples are available in
[`docs/api.md`](docs/api.md).

The generated OpenAPI definition is committed at:

[`docs/openapi-schema.yml`](docs/openapi-schema.yml)

Interactive documentation is available at:

```text
http://localhost:8000/api/docs/
http://localhost:8000/api/redoc/
```

## API Error Format

Validation errors use a consistent format:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed.",
    "details": {
      "question": [
        "This field may not be blank."
      ]
    }
  }
}
```

Other API errors use the same envelope:

```json
{
  "error": {
    "code": "not_found",
    "message": "Resource not found."
  }
}
```

## Question History Pagination

Question history is paginated by default.

Example:

```text
GET /api/v1/questions/?page=1&page_size=10
```

Response structure:

```json
{
  "count": 25,
  "next": "http://localhost:8000/api/v1/questions/?page=2&page_size=10",
  "previous": null,
  "results": []
}
```

The default page size is `20`, and the maximum configurable page size is
`100`.

## Sample Data

The repository contains:

```text
sample_data/northbridge_student_guide.docx
sample_data/sample_questions.json
```

The sample document contains fictional university information suitable
for testing retrieval and grounded answers.

Generate the DOCX again with:

```bash
docker compose exec web python scripts/generate_sample_docx.py
```

Load and index it with:

```bash
docker compose exec web python manage.py load_sample_data
```

Reset and recreate it with:

```bash
docker compose exec web python manage.py load_sample_data --reset
```

More details are available in
[`docs/sample-data.md`](docs/sample-data.md).

## Example API Question

First obtain an indexed document ID:

```bash
curl -s http://localhost:8000/api/v1/documents/
```

Then ask:

```bash
curl -X POST \
  http://localhost:8000/api/v1/questions/ask/ \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How much is the late tuition payment fee?",
    "document_ids": [DOCUMENT_ID],
    "top_k": 3,
    "min_similarity": 0.2
  }'
```

The included sample document contains the fact:

```text
A late payment fee of 25 US dollars is applied when tuition is paid
after the deadline.
```

The exact wording of an LLM-generated response may vary, but the factual
answer should remain grounded in the retrieved source.

## Health Check

```bash
curl http://localhost:8000/api/health/
```

Example:

```json
{
  "status": "ok",
  "database": "ok",
  "version": "1.0.0"
}
```

The Docker web service also uses this endpoint for its container
healthcheck.

## Running Tests

Run the complete application test suite:

```bash
docker compose exec web python manage.py test \
  apps.documents.tests apps.qa.tests
```

At the current project stage the suite contains 88 automated tests.

Run Django system checks:

```bash
docker compose exec web python manage.py check
```

Check for unexpected migrations:

```bash
docker compose exec web python manage.py \
  makemigrations --check --dry-run
```

Validate the OpenAPI schema:

```bash
docker compose exec web python manage.py spectacular \
  --file docs/openapi-schema.yml \
  --validate
```

## Production-Style Serving

The Docker web container uses Gunicorn rather than Django's development
server.

Static application assets, including Django Admin and API documentation
assets, are served through WhiteNoise.

The container startup sequence performs static-file collection and then
starts Gunicorn.

This configuration is appropriate for project delivery and local
containerized demonstration. A real internet-facing deployment would
normally add infrastructure such as HTTPS termination, external secrets
management, backups, monitoring, and stricter API access control.

## Design Decisions

### Django Admin instead of a custom frontend

The project specification requires Django Admin as the user interface.
Using Admin keeps the application focused on document processing and RAG
rather than unnecessary frontend complexity.

### PostgreSQL and pgvector

Document metadata, history, chunks, and vector embeddings live in the
same database. This keeps the architecture simple and avoids introducing
a separate vector database for the project scope.

### Multilingual Sentence Transformer

A multilingual embedding model allows English and Persian questions and
documents to use the same retrieval pipeline.

### LangChain

LangChain is used around the model interaction and RAG flow, keeping
prompt/model orchestration isolated from API and persistence code.

### Service layer

Document processing, indexing, retrieval, LLM access, RAG, and history
logic are implemented in service modules rather than directly inside
views or models.

This keeps Django models, API views, and Admin code easier to understand
and extend.

### Source snapshots

Source metadata is copied into question history instead of relying only
on live foreign-key relations. This makes historical answers more robust
when source documents are changed or deleted.

### Deterministic no-context response

If no chunk passes the retrieval threshold, calling an LLM adds cost and
can increase hallucination risk. The application therefore returns a
predefined insufficient-context response.

## Current Limitations

The implementation intentionally favors simplicity for the project
scope.

Current limitations include:

- only DOCX uploads are supported;
- embeddings are generated synchronously during document processing;
- large documents may therefore make upload/index operations slow;
- there is no background job queue such as Celery;
- API endpoints are intentionally available without API authentication;
- Django Admin remains login-protected;
- the project does not implement per-user document ownership;
- retrieval uses vector similarity without a separate reranking model;
- free OpenRouter models may change availability or rate limits;
- the first embedding-model load may require a network download;
- one Gunicorn worker is used by default to limit embedding-model memory
  consumption;
- local uploaded media is stored on the application filesystem rather
  than object storage.

These are deliberate scope trade-offs rather than hidden behavior.

## Security Notes

- `.env` is ignored by Git.
- Never commit OpenRouter API keys.
- Use a strong Django secret key outside local development.
- Use non-default database credentials outside local development.
- Enable secure cookies and SSL redirect when deploying behind HTTPS.
- Restrict API access if this project is exposed publicly.

## Screenshots

Delivery screenshots are stored in:

[`docs/screenshots/`](docs/screenshots/)

They demonstrate Django Admin document management, question answering,
history, and API documentation.

## Documentation

- [Architecture](docs/architecture.md)
- [API Guide](docs/api.md)
- [Generated OpenAPI Schema](docs/openapi-schema.yml)
- [Sample Data](docs/sample-data.md)
- [Screenshots](docs/screenshots/README.md)

## Stopping the Application

```bash
docker compose down
```

Do not use `docker compose down -v` unless you intentionally want to
delete the PostgreSQL and Hugging Face cache volumes.

## License / Project Scope

This repository is an educational Document Question Answering project
implemented for an LLM/Django assignment.