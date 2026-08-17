"""Bright Data Twitter/X CSV adapter.

The public sample dataset is distributed as ordinary CSV with plain tweet text.
The rest of the pipeline already expects a compact internal TSV format, so this
module maps Bright Data rows into that internal feature row without changing
Kafka, Spark, embedding, Qdrant, or API code.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import time
import urllib.request
from datetime import datetime
from typing import Iterator

import schema


SAMPLE_URL = (
    "https://raw.githubusercontent.com/luminati-io/"
    "Twitter-X-dataset-samples/main/twitter-posts.csv"
)


def open_csv(source: str):
    """Open a local CSV path or HTTP(S) URL as a text stream."""
    if source.startswith(("http://", "https://")):
        with urllib.request.urlopen(source, timeout=60) as response:
            data = response.read().decode("utf-8-sig")
        return io.StringIO(data)
    return open(source, "r", encoding="utf-8-sig", newline="")


def iter_tsv_rows(
    source: str,
    limit: int = 0,
    offset: int = 0,
    tokenizer=None,
) -> Iterator[tuple[str, str]]:
    """Yield ``(tweet_id, internal_tsv_row)`` pairs from a Bright Data CSV."""
    fh = open_csv(source)
    close_after = not isinstance(fh, io.StringIO)

    try:
        reader = csv.DictReader(fh)
        emitted = 0
        for idx, row in enumerate(reader):
            if idx < offset:
                continue
            if limit and emitted >= limit:
                break
            converted = row_to_tsv(row, tokenizer=tokenizer, row_index=idx)
            if converted is None:
                continue
            emitted += 1
            yield converted
    finally:
        if close_after:
            fh.close()


def row_to_tsv(row: dict[str, str], tokenizer=None, row_index: int = 0) -> tuple[str, str] | None:
    text = _clean(row.get("description", ""))
    if not text:
        return None

    if tokenizer is None:
        from generator import get_tokenizer
        tokenizer = get_tokenizer()
    token_ids = tokenizer.encode(
        text,
        add_special_tokens=True,
        truncation=True,
        max_length=128,
    )
    if not token_ids:
        return None

    tweet_id = _clean(row.get("id", "")) or _hashed(f"brightdata-row-{row_index}-{text}")
    author_id = _clean(row.get("user_posted", "")) or _clean(row.get("name", "")) or "unknown"
    timestamp = _parse_timestamp(row.get("date_posted", ""))
    followers = _parse_int(row.get("followers", "0"))
    following = _parse_int(row.get("following", "0"))
    verified = _parse_bool(row.get("is_verified", "false"))
    hashtags = _parse_list(row.get("hashtags", ""))
    media = _media_types(row)
    tweet_type = _tweet_type(row)

    cols = [""] * len(schema.COLUMNS)
    cols[0] = schema.LIST_SEP.join(str(t) for t in token_ids)
    cols[1] = schema.LIST_SEP.join(hashtags)
    cols[2] = tweet_id
    cols[3] = schema.LIST_SEP.join(media)
    cols[4] = schema.LIST_SEP.join(_parse_list(row.get("external_url", "")))
    cols[5] = ""
    cols[6] = tweet_type
    # The public sample does not include a normalized language column. The
    # language value is metadata only in this project, so use ISO "und".
    cols[7] = "und"
    cols[8] = str(timestamp)
    cols[9] = _hashed(author_id)
    cols[10] = str(followers)
    cols[11] = str(following)
    cols[12] = str(verified).lower()
    cols[13] = "0"
    cols[14] = "sample-reader"
    cols[15] = "0"
    cols[16] = "0"
    cols[17] = "false"
    cols[18] = "0"
    cols[19] = "false"

    return tweet_id, "\t".join(cols)


def _clean(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if len(text) >= 2 and text[0] == text[-1] == '"':
        text = text[1:-1].strip()
    if text.lower() in {"", "null", "none", "nan"}:
        return ""
    return text


def _parse_list(value: object) -> list[str]:
    text = _clean(value)
    if not text:
        return []

    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [_clean(item).lstrip("#") for item in parsed if _clean(item)]
        if isinstance(parsed, str):
            cleaned = _clean(parsed).lstrip("#")
            return [cleaned] if cleaned else []
    except json.JSONDecodeError:
        pass

    return [part.strip().lstrip("#") for part in text.split(",") if part.strip()]


def _parse_timestamp(value: object) -> int:
    text = _clean(value)
    if not text:
        return int(time.time())
    try:
        return int(datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp())
    except ValueError:
        return int(time.time())


def _parse_int(value: object) -> int:
    text = _clean(value).replace(",", "")
    if not text:
        return 0
    try:
        return int(float(text))
    except ValueError:
        return 0


def _parse_bool(value: object) -> bool:
    return _clean(value).lower() in {"true", "1", "yes"}


def _media_types(row: dict[str, str]) -> list[str]:
    media: list[str] = []
    if _parse_list(row.get("photos", "")):
        media.append("Photo")
    if _parse_list(row.get("videos", "")):
        media.append("Video")
    return media


def _tweet_type(row: dict[str, str]) -> str:
    if _has_content(row.get("parent_post_details", "")):
        return "Reply"
    if _has_content(row.get("quoted_post", "")):
        return "Quote"
    return "TopLevel"


def _has_content(value: object) -> bool:
    text = _clean(value)
    if not text:
        return False
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return True

    if isinstance(parsed, dict):
        return any(_has_content(item) for item in parsed.values())
    if isinstance(parsed, list):
        return any(_has_content(item) for item in parsed)
    return bool(_clean(parsed))


def _hashed(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:32]
