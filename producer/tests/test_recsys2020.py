from __future__ import annotations

import json
from pathlib import Path

from producer.recsys2020 import ConvertConfig, convert, decode_text_tokens, to_post_event


def recsys_row(**overrides: str) -> dict[str, str]:
    row = {
        "text_tokens": "101\t7592\t2088\t102",
        "hashtags": "spark\tkafka",
        "tweet_id": "tweet-1",
        "media": "",
        "links": "",
        "domains": "",
        "tweet_type": "TopLevel",
        "language": "en",
        "timestamp": "1783780500",
        "a_user_id": "author-1",
        "a_follower_count": "10",
        "a_following_count": "5",
        "a_is_verified": "false",
        "a_account_creation": "1600000000",
        "b_user_id": "reader-1",
        "b_follower_count": "7",
        "b_following_count": "3",
        "b_is_verified": "false",
        "b_account_creation": "1600000001",
        "b_follows_a": "true",
        "reply": "",
        "retweet": "",
        "retweet_comment": "",
        "like": "1783780600",
        "_line_number": "1",
    }
    row.update(overrides)
    return row


def write_recsys_file(tmp_path: Path, rows: list[dict[str, str]]) -> Path:
    path = tmp_path / "training.tsv"
    lines = []
    columns = [
        "text_tokens",
        "hashtags",
        "tweet_id",
        "media",
        "links",
        "domains",
        "tweet_type",
        "language",
        "timestamp",
        "a_user_id",
        "a_follower_count",
        "a_following_count",
        "a_is_verified",
        "a_account_creation",
        "b_user_id",
        "b_follower_count",
        "b_following_count",
        "b_is_verified",
        "b_account_creation",
        "b_follows_a",
        "reply",
        "retweet",
        "retweet_comment",
        "like",
    ]
    for row in rows:
        lines.append("\x01".join(row[column] for column in columns))
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def test_decode_text_tokens_uses_optional_vocab() -> None:
    vocab = ["[PAD]", "[UNK]", "[CLS]", "[SEP]", "hello", "world", "##s"]

    decoded = decode_text_tokens("2\t4\t5\t6\t3", vocab)

    assert decoded == "hello worlds"


def test_to_post_event_maps_recsys_row_to_distributweet_event() -> None:
    event = to_post_event(recsys_row(), vocab=None, language_default="en")

    assert event["postId"] == "tweet-1"
    assert event["authorId"] == "author-1"
    assert event["language"] == "en"
    assert event["createdAt"] == "2026-07-11T14:35:00Z"
    assert event["source"] == "recsys2020"
    assert "bert token ids" in event["text"]
    assert "hashtags: spark kafka" in event["text"]


def test_convert_respects_limit(tmp_path: Path) -> None:
    input_path = write_recsys_file(
        tmp_path,
        [
            recsys_row(tweet_id="tweet-1"),
            recsys_row(tweet_id="tweet-2"),
            recsys_row(tweet_id="tweet-3"),
        ],
    )
    output_path = tmp_path / "out.jsonl"

    count = convert(
        ConvertConfig(
            input=input_path,
            output=output_path,
            limit=2,
            offset=0,
            delimiter="\x01",
            language_default="en",
            bert_vocab=None,
        )
    )

    events = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    assert count == 2
    assert [event["postId"] for event in events] == ["tweet-1", "tweet-2"]
