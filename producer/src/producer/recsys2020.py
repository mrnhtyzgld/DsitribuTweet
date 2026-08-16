from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, TextIO


RECSYS_2020_COLUMNS = [
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

SUPPORTED_LANGUAGES = {"en", "tr"}
EVENT_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "distributweet:recsys2020-events")


@dataclass(frozen=True)
class ConvertConfig:
    input: Path
    output: Path | None
    limit: int | None
    offset: int
    delimiter: str
    language_default: str
    bert_vocab: Path | None


def load_vocab(path: Path | None) -> list[str] | None:
    if path is None:
        return None
    return path.read_text(encoding="utf-8").splitlines()


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def recsys_rows(path: Path, delimiter: str = "\x01") -> Iterable[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        for line_number, values in enumerate(reader, start=1):
            if not values:
                continue
            if len(values) != len(RECSYS_2020_COLUMNS):
                raise ValueError(
                    f"{path}:{line_number}: expected {len(RECSYS_2020_COLUMNS)} columns, got {len(values)}"
                )
            row = dict(zip(RECSYS_2020_COLUMNS, values, strict=True))
            row["_line_number"] = str(line_number)
            yield row


def to_post_event(row: dict[str, str], vocab: list[str] | None, language_default: str) -> dict[str, str]:
    tweet_id = require_value(row, "tweet_id")
    author_id = require_value(row, "a_user_id")
    timestamp = parse_timestamp(require_value(row, "timestamp"))
    text = text_from_row(row, vocab)
    language = normalize_language(row.get("language", ""), language_default)

    return {
        "eventId": str(uuid.uuid5(EVENT_NAMESPACE, f"{tweet_id}:{row.get('_line_number', '')}:{row.get('b_user_id', '')}")),
        "postId": tweet_id,
        "authorId": author_id,
        "text": text,
        "language": language,
        "createdAt": timestamp,
        "ingestedAt": now_iso(),
        "source": "recsys2020",
    }


def convert(config: ConvertConfig) -> int:
    vocab = load_vocab(config.bert_vocab)
    written = 0

    with output_handle(config.output) as output:
        for index, row in enumerate(recsys_rows(config.input, config.delimiter)):
            if index < config.offset:
                continue
            if config.limit is not None and written >= config.limit:
                break
            event = to_post_event(row, vocab, config.language_default)
            output.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")))
            output.write("\n")
            written += 1

    return written


def output_handle(path: Path | None):
    if path is None:
        return StdoutContext(sys.stdout)
    return path.open("w", encoding="utf-8")


class StdoutContext:
    def __init__(self, handle: TextIO) -> None:
        self.handle = handle

    def __enter__(self) -> TextIO:
        return self.handle

    def __exit__(self, exc_type, exc, traceback) -> bool:
        return False


def require_value(row: dict[str, str], key: str) -> str:
    value = row.get(key, "").strip()
    if not value:
        raise ValueError(f"missing required RecSys 2020 field: {key}")
    return value


def parse_timestamp(value: str) -> str:
    parsed = datetime.fromtimestamp(int(value), tz=UTC)
    return parsed.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_language(value: str, default: str) -> str:
    normalized = value.strip().lower()
    return normalized if normalized in SUPPORTED_LANGUAGES else default


def text_from_row(row: dict[str, str], vocab: list[str] | None) -> str:
    decoded = decode_text_tokens(row.get("text_tokens", ""), vocab)
    parts = [
        decoded,
        token_list("hashtags", row.get("hashtags", "")),
        token_list("domains", row.get("domains", "")),
        token_list("links", row.get("links", "")),
        row.get("tweet_type", "").strip(),
    ]
    text = " ".join(part for part in parts if part)
    return text if text.strip() else "empty recsys tweet"


def decode_text_tokens(value: str, vocab: list[str] | None) -> str:
    token_ids = [int(token) for token in re.findall(r"\d+", value)]
    if vocab is None:
        return "bert token ids " + " ".join(str(token_id) for token_id in token_ids)

    tokens: list[str] = []
    for token_id in token_ids:
        if token_id < 0 or token_id >= len(vocab):
            continue
        token = vocab[token_id]
        if token in {"[CLS]", "[SEP]", "[PAD]"}:
            continue
        if token.startswith("##") and tokens:
            tokens[-1] = tokens[-1] + token[2:]
        else:
            tokens.append(token)
    return " ".join(tokens)


def token_list(label: str, value: str) -> str:
    tokens = [token for token in re.split(r"[\t, ]+", value.strip()) if token]
    if not tokens:
        return ""
    return f"{label}: " + " ".join(tokens[:12])


def parse_args(argv: list[str] | None = None) -> ConvertConfig:
    parser = argparse.ArgumentParser(description="Convert RecSys Challenge 2020 TSV rows to DistribuTweet JSONL")
    parser.add_argument("--input", required=True, type=Path, help="Path to RecSys 2020 training.tsv")
    parser.add_argument("--output", type=Path, default=None, help="Output JSONL path. Defaults to stdout")
    parser.add_argument("--limit", type=int, default=None, help="Convert at most N rows")
    parser.add_argument("--offset", type=int, default=0, help="Skip the first N rows before converting")
    parser.add_argument(
        "--delimiter",
        default="\\x01",
        help="Input column delimiter. RecSys 2020 uses the Ctrl-A character by default",
    )
    parser.add_argument(
        "--language-default",
        default="en",
        choices=sorted(SUPPORTED_LANGUAGES),
        help="Language to use when the RecSys language field is not an accepted ISO code",
    )
    parser.add_argument(
        "--bert-vocab",
        type=Path,
        default=None,
        help="Optional BERT vocab.txt for decoding text_tokens into readable text",
    )
    args = parser.parse_args(argv)

    return ConvertConfig(
        input=args.input,
        output=args.output,
        limit=args.limit,
        offset=args.offset,
        delimiter=decode_delimiter(args.delimiter),
        language_default=args.language_default,
        bert_vocab=args.bert_vocab,
    )


def decode_delimiter(value: str) -> str:
    decoded = value.encode("utf-8").decode("unicode_escape")
    if len(decoded) != 1:
        raise ValueError("delimiter must decode to exactly one character")
    return decoded


def main(argv: list[str] | None = None) -> int:
    config = parse_args(argv)
    count = convert(config)
    print(f"converted {count} RecSys 2020 rows", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
