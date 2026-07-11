from __future__ import annotations

import json
from pathlib import Path

import pytest

from producer.replay import ReplayConfig, load_events, normalize_event, replay


class FakeProducer:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str | None, bytes]] = []
        self.flushed = False

    def produce(self, topic: str, key: str | None, value: bytes, callback=None) -> None:
        self.messages.append((topic, key, value))
        if callback is not None:
            callback(None, type("Message", (), {"key": lambda self: key})())

    def poll(self, timeout: float) -> None:
        return None

    def flush(self, timeout: float | None = None) -> int:
        self.flushed = True
        return 0


def write_jsonl(tmp_path: Path, rows: list[dict]) -> Path:
    path = tmp_path / "posts.jsonl"
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    return path


def test_normalize_event_adds_replay_defaults() -> None:
    event = normalize_event(
        {
            "postId": "post-1",
            "authorId": "author-1",
            "text": "A useful post about Kafka streams",
            "language": "en",
            "createdAt": "2026-07-11T14:35:00Z",
        }
    )

    assert event["eventId"]
    assert event["ingestedAt"].endswith("Z")
    assert event["source"] == "jsonl-replay"


def test_load_events_rejects_missing_required_fields(tmp_path: Path) -> None:
    path = write_jsonl(tmp_path, [{"postId": "post-1"}])

    with pytest.raises(ValueError, match="missing required fields"):
        list(load_events(path))


def test_replay_produces_keyed_messages(tmp_path: Path) -> None:
    path = write_jsonl(
        tmp_path,
        [
            {
                "eventId": "event-1",
                "postId": "post-1",
                "authorId": "author-1",
                "text": "A useful post about Kafka streams",
                "language": "en",
                "createdAt": "2026-07-11T14:35:00Z",
                "ingestedAt": "2026-07-11T14:35:01Z",
                "source": "test",
            }
        ],
    )
    producer = FakeProducer()

    count = replay(
        ReplayConfig(
            file=path,
            bootstrap_servers="unused",
            topic="posts.raw",
            events_per_second=0,
            loop=False,
            max_events=None,
        ),
        producer,
    )

    assert count == 1
    assert producer.flushed is True
    assert producer.messages[0][0] == "posts.raw"
    assert producer.messages[0][1] == "post-1"
    assert json.loads(producer.messages[0][2])["text"] == "A useful post about Kafka streams"
