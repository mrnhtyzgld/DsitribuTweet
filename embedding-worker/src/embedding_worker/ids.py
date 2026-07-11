from __future__ import annotations

import uuid


POST_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "distributweet:posts")


def point_id_for_post(post_id: str) -> str:
    return str(uuid.uuid5(POST_NAMESPACE, post_id))
