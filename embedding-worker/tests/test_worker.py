from __future__ import annotations

import json
from datetime import UTC, datetime

from embedding_worker.consumer import parse_message
from embedding_worker.ids import point_id_for_post
from embedding_worker.models import PostEvent
from embedding_worker.qdrant_store import build_points


class FakeMessage:
    def __init__(self, value: bytes | None) -> None:
        self._value = value

    def value(self) -> bytes | None:
        return self._value


def post_event() -> PostEvent:
    return PostEvent(
        eventId="event-1",
        postId="post-1",
        authorId="author-1",
        text="CUDA kernel optimization techniques",
        language="en",
        createdAt=datetime(2026, 7, 11, 14, 35, tzinfo=UTC),
        ingestedAt=datetime(2026, 7, 11, 14, 36, tzinfo=UTC),
        source="test",
    )


def test_point_id_is_deterministic_uuid() -> None:
    first = point_id_for_post("post-1")
    second = point_id_for_post("post-1")

    assert first == second
    assert point_id_for_post("post-2") != first
    assert len(first) == 36


def test_parse_message_reads_post_event() -> None:
    raw = {
        "eventId": "event-1",
        "postId": "post-1",
        "authorId": "author-1",
        "text": "CUDA kernel optimization techniques",
        "language": "en",
        "createdAt": "2026-07-11T14:35:00Z",
        "ingestedAt": "2026-07-11T14:36:00Z",
        "source": "test",
    }

    parsed = parse_message(FakeMessage(json.dumps(raw).encode("utf-8")))

    assert parsed is not None
    assert parsed.postId == "post-1"
    assert parsed.createdAt.year == 2026


def test_build_points_preserves_payload_and_vector() -> None:
    post = post_event()
    vector = [0.1, 0.2, 0.3]

    points = build_points([post], [vector])

    assert points[0].id == point_id_for_post("post-1")
    assert points[0].vector == vector
    assert points[0].payload["postId"] == "post-1"
    assert points[0].payload["createdAt"] == 1783780500
