"""Qdrant baglantisi ve upsert islemleri."""

import logging
import os
import time
import uuid

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

import model

log = logging.getLogger(__name__)

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION = os.getenv("COLLECTION", "posts")


def connect(retries: int = 30) -> QdrantClient:
    """Qdrant hazir olana kadar bekler."""
    for attempt in range(1, retries + 1):
        try:
            client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=30)
            client.get_collections()
            log.info("Qdrant'a baglandi: %s:%d", QDRANT_HOST, QDRANT_PORT)
            return client
        except Exception as exc:
            log.warning(
                "Qdrant hazir degil (deneme %d/%d): %s", attempt, retries, exc
            )
            time.sleep(2)
    raise SystemExit(f"Qdrant'a baglanilamadi: {QDRANT_HOST}:{QDRANT_PORT}")


def ensure_collection(client: QdrantClient) -> None:
    """Collection'i idempotent olarak olusturur.

    Birden fazla worker ayni anda baslayabilir; collection zaten varsa
    hata vermeden devam etmeliyiz.
    """
    try:
        existing = {c.name for c in client.get_collections().collections}
        if COLLECTION in existing:
            log.info("collection zaten var: %s", COLLECTION)
            return

        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(
                size=model.VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )
        log.info("collection olusturuldu: %s (%d boyut)", COLLECTION, model.VECTOR_SIZE)
    except Exception as exc:
        # Yaris durumu: baska bir worker bizden once olusturmus olabilir
        existing = {c.name for c in client.get_collections().collections}
        if COLLECTION in existing:
            log.info("collection baska bir worker tarafindan olusturuldu")
            return
        raise RuntimeError(f"collection olusturulamadi: {exc}") from exc


def _point_id(tweet_id: str) -> str:
    """tweet_id'den deterministik UUID uretir.

    Qdrant point id'si UUID veya unsigned int olmak zorunda; tweet_id ise
    hash string. Deterministik olmasi onemli: ayni tweet tekrar gelirse
    yeni kayit degil, ayni kaydin uzerine yazilir (idempotent upsert).
    """
    return str(uuid.uuid5(uuid.NAMESPACE_URL, tweet_id))


def upsert_posts(
    client: QdrantClient,
    posts: list[dict],
    vectors: np.ndarray,
) -> int:
    """Gonderileri vektorleriyle birlikte Qdrant'a yazar."""
    if not posts:
        return 0
    if len(posts) != len(vectors):
        raise ValueError(f"post/vektor sayisi uyusmuyor: {len(posts)} != {len(vectors)}")

    points = [
        PointStruct(
            id=_point_id(post["tweetId"]),
            vector=vec.tolist(),
            payload={
                "tweetId": post["tweetId"],
                "text": post["text"],
                "language": post.get("language", ""),
                "tweetType": post.get("tweetType", ""),
                "tweetTimestamp": post.get("tweetTimestamp", 0),
                "authorId": post.get("authorId", ""),
                "authorFollowerCount": post.get("authorFollowerCount", 0),
                "hashtags": post.get("hashtags", []),
                "hasMedia": post.get("hasMedia", False),
            },
        )
        for post, vec in zip(posts, vectors)
    ]

    client.upsert(collection_name=COLLECTION, points=points, wait=True)
    return len(points)


def count(client: QdrantClient) -> int:
    """Collection'daki nokta sayisi."""
    try:
        return client.count(collection_name=COLLECTION, exact=True).count
    except Exception:
        return 0
