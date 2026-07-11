from __future__ import annotations

import os
from dataclasses import dataclass


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return default if value is None else int(value)


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")
    kafka_topic: str = os.getenv("KAFKA_TOPIC", "posts.cleaned")
    kafka_group_id: str = os.getenv("KAFKA_GROUP_ID", "embedding-worker")
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    posts_collection: str = os.getenv("POSTS_COLLECTION", "posts")
    vector_size: int = env_int("VECTOR_SIZE", 384)
    model_name: str = os.getenv("MODEL_NAME", "intfloat/multilingual-e5-small")
    batch_size: int = env_int("BATCH_SIZE", 32)
    poll_timeout_seconds: float = float(os.getenv("POLL_TIMEOUT_SECONDS", "1.0"))
    run_consumer: bool = env_bool("RUN_CONSUMER", True)


def load_settings() -> Settings:
    return Settings()
