FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu ".[model]"

EXPOSE 8001
CMD ["uvicorn", "embedding_worker.main:app", "--host", "0.0.0.0", "--port", "8001"]
