from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from qdrant_client import QdrantClient

from embedding_worker.config import Settings, load_settings
from embedding_worker.consumer import EmbeddingConsumer
from embedding_worker.embedder import get_embedder
from embedding_worker.models import EmbedRequest, EmbedResponse, HealthResponse
from embedding_worker.qdrant_store import QdrantPostStore


logging.basicConfig(level=logging.INFO)

settings: Settings = load_settings()
embedder = get_embedder(settings.model_name)
qdrant_client = QdrantClient(url=settings.qdrant_url)
store = QdrantPostStore(qdrant_client, settings.posts_collection, settings.vector_size)
consumer: EmbeddingConsumer | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global consumer
    store.ensure_collection()
    if settings.run_consumer:
        consumer = EmbeddingConsumer(settings, embedder, store)
        consumer.start()
    yield
    if consumer is not None:
        consumer.stop()


app = FastAPI(title="DistribuTweet Embedding Worker", lifespan=lifespan)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        modelLoaded=embedder is not None,
        consumerRunning=consumer.running if consumer is not None else False,
    )


@app.post("/embed", response_model=EmbedResponse)
def embed(request: EmbedRequest) -> EmbedResponse:
    vectors = embedder.encode(request.texts, batch_size=settings.batch_size)
    dimensions = len(vectors[0]) if vectors else settings.vector_size
    return EmbedResponse(vectors=vectors, model=embedder.model_name, dimensions=dimensions)
