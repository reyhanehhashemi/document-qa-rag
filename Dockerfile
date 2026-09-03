FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

# Install CPU-only PyTorch explicitly.
RUN python -m pip install --upgrade pip \
    && python -m pip install \
        torch==2.13.0 \
        --index-url https://download.pytorch.org/whl/cpu

# Install the remaining project dependencies.
RUN python -m pip install -r /app/requirements.txt

COPY . /app/

ENTRYPOINT ["sh", "/app/entrypoint.sh"]

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]