from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, Protocol

from confluent_kafka import Producer


REQUIRED_FIELDS = {
    "eventId",
    "postId",
    "authorId",
    "text",
    "language",
    "createdAt",
    "ingestedAt",
    "source",
}


class KafkaProducerLike(Protocol):
    def produce(self, topic: str, key: str | None, value: bytes, callback=None) -> None:
        ...

    def poll(self, timeout: float) -> None:
        ...

    def flush(self, timeout: float | None = None) -> int:
        ...


@dataclass(frozen=True)
class ReplayConfig:
    file: Path
    bootstrap_servers: str
    topic: str
    events_per_second: float
    loop: bool
    max_events: int | None


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_events(path: Path) -> Iterable[dict]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                event = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(event, dict):
                raise ValueError(f"{path}:{line_number}: event must be a JSON object")
            yield normalize_event(event)


def normalize_event(event: dict) -> dict:
    normalized = dict(event)
    normalized.setdefault("eventId", str(uuid.uuid4()))
    normalized.setdefault("ingestedAt", now_iso())
    normalized.setdefault("source", "jsonl-replay")
    missing = sorted(field for field in REQUIRED_FIELDS if field not in normalized)
    if missing:
        raise ValueError(f"event is missing required fields: {', '.join(missing)}")
    if not str(normalized["postId"]).strip():
        raise ValueError("event postId must not be empty")
    if not str(normalized["text"]).strip():
        raise ValueError("event text must not be empty")
    return normalized


def delivery_report(err, msg) -> None:
    if err is not None:
        print(f"delivery failed for {msg.key()!r}: {err}", file=sys.stderr)


def replay(config: ReplayConfig, producer: KafkaProducerLike) -> int:
    interval = 0.0 if config.events_per_second <= 0 else 1.0 / config.events_per_second
    sent = 0

    while True:
        for event in load_events(config.file):
            key = str(event["postId"])
            value = json.dumps(event, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            producer.produce(config.topic, key=key, value=value, callback=delivery_report)
            producer.poll(0)
            sent += 1
            if interval > 0:
                time.sleep(interval)
            if config.max_events is not None and sent >= config.max_events:
                producer.flush()
                return sent
        if not config.loop:
            producer.flush()
            return sent


def parse_args(argv: list[str] | None = None) -> ReplayConfig:
    parser = argparse.ArgumentParser(description="Replay JSONL post events to Kafka")
    parser.add_argument("--file", required=True, type=Path, help="JSONL file to replay")
    parser.add_argument(
        "--bootstrap-servers",
        default=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092"),
        help="Kafka bootstrap servers",
    )
    parser.add_argument(
        "--topic",
        default=os.getenv("KAFKA_TOPIC", "posts.raw"),
        help="Kafka topic",
    )
    parser.add_argument(
        "--events-per-second",
        type=float,
        default=float(os.getenv("EVENTS_PER_SECOND", "10")),
        help="Replay speed. Use 0 to disable sleeping.",
    )
    parser.add_argument("--loop", action="store_true", help="Replay the file forever")
    parser.add_argument("--max-events", type=int, default=None, help="Stop after N events")
    args = parser.parse_args(argv)

    return ReplayConfig(
        file=args.file,
        bootstrap_servers=args.bootstrap_servers,
        topic=args.topic,
        events_per_second=args.events_per_second,
        loop=args.loop,
        max_events=args.max_events,
    )


def build_producer(bootstrap_servers: str) -> Producer:
    return Producer(
        {
            "bootstrap.servers": bootstrap_servers,
            "client.id": "distributweet-jsonl-replay",
            "enable.idempotence": True,
            "acks": "all",
            "retries": 5,
        }
    )


def main(argv: list[str] | None = None) -> int:
    config = parse_args(argv)
    producer = build_producer(config.bootstrap_servers)
    count = replay(config, producer)
    print(f"replayed {count} events to {config.topic}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
