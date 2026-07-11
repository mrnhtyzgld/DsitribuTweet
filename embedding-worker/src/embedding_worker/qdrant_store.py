from __future__ import annotations

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from tenacity import retry, stop_after_attempt, wait_exponential

from embedding_worker.ids import point_id_for_post
from embedding_worker.models import PostEvent


class QdrantPostStore:
    def __init__(self, client: QdrantClient, collection_name: str, vector_size: int) -> None:
        self.client = client
        self.collection_name = collection_name
        self.vector_size = vector_size

    def ensure_collection(self) -> None:
        if self.client.collection_exists(self.collection_name):
            return
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
        )

    @retry(wait=wait_exponential(multiplier=0.5, min=0.5, max=8), stop=stop_after_attempt(5))
    def upsert_posts(self, posts: list[PostEvent], vectors: list[list[float]]) -> None:
        if len(posts) != len(vectors):
            raise ValueError("posts and vectors must have the same length")
        points = build_points(posts, vectors)
        self.client.upsert(collection_name=self.collection_name, points=points, wait=True)


def build_points(posts: list[PostEvent], vectors: list[list[float]]) -> list[PointStruct]:
    points: list[PointStruct] = []
    for post, vector in zip(posts, vectors, strict=True):
        points.append(
            PointStruct(
                id=point_id_for_post(post.postId),
                vector=vector,
                payload={
                    "postId": post.postId,
                    "text": post.text,
                    "authorId": post.authorId,
                    "language": post.language,
                    "createdAt": int(post.createdAt.timestamp()),
                    "createdAtIso": post.createdAt.isoformat().replace("+00:00", "Z"),
                    "source": post.source,
                },
            )
        )
    return points
