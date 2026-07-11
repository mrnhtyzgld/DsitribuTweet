from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass

from confluent_kafka import Consumer, KafkaError, KafkaException, Message

from embedding_worker.config import Settings
from embedding_worker.embedder import Embedder
from embedding_worker.models import PostEvent
from embedding_worker.qdrant_store import QdrantPostStore


logger = logging.getLogger(__name__)


@dataclass
class WorkerStats:
    processed: int = 0
    failed: int = 0


class EmbeddingConsumer:
    def __init__(self, settings: Settings, embedder: Embedder, store: QdrantPostStore) -> None:
        self.settings = settings
        self.embedder = embedder
        self.store = store
        self.stats = WorkerStats()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._consumer = Consumer(
            {
                "bootstrap.servers": settings.kafka_bootstrap_servers,
                "group.id": settings.kafka_group_id,
                "enable.auto.commit": False,
                "auto.offset.reset": "earliest",
                "client.id": "distributweet-embedding-worker",
            }
        )

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.running:
            return
        self.store.ensure_collection()
        self._consumer.subscribe([self.settings.kafka_topic])
        self._thread = threading.Thread(target=self.run_forever, name="embedding-consumer", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=10)
        self._consumer.close()

    def run_forever(self) -> None:
        batch: list[tuple[PostEvent, Message]] = []
        while not self._stop.is_set():
            msg = self._consumer.poll(self.settings.poll_timeout_seconds)
            if msg is None:
                self._flush_batch(batch)
                batch.clear()
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                raise KafkaException(msg.error())
            post = parse_message(msg)
            if post is None:
                self.stats.failed += 1
                self._consumer.commit(message=msg, asynchronous=False)
                continue
            batch.append((post, msg))
            if len(batch) >= self.settings.batch_size:
                self._flush_batch(batch)
                batch.clear()
        self._flush_batch(batch)

    def _flush_batch(self, batch: list[tuple[PostEvent, Message]]) -> None:
        if not batch:
            return
        posts = [item[0] for item in batch]
        messages = [item[1] for item in batch]
        try:
            texts = [f"passage: {post.text}" for post in posts]
            vectors = self.embedder.encode(texts, batch_size=self.settings.batch_size)
            self.store.upsert_posts(posts, vectors)
            for msg in messages:
                self._consumer.commit(message=msg, asynchronous=False)
            self.stats.processed += len(posts)
            logger.info("indexed %s posts", len(posts))
        except Exception:
            self.stats.failed += len(posts)
            logger.exception("failed to index batch; offsets were not committed")


def parse_message(message: Message) -> PostEvent | None:
    try:
        raw = message.value()
        if raw is None:
            return None
        payload = json.loads(raw.decode("utf-8"))
        return PostEvent.model_validate(payload)
    except Exception:
        logger.exception("invalid post event")
        return None
