from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class PostEvent(BaseModel):
    eventId: str
    postId: str
    authorId: str
    text: str
    language: str
    createdAt: datetime
    ingestedAt: datetime
    source: str

    @field_validator("postId", "authorId", "text")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value


class EmbedRequest(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=256)


class EmbedResponse(BaseModel):
    vectors: list[list[float]]
    model: str
    dimensions: int


class HealthResponse(BaseModel):
    status: str
    modelLoaded: bool
    consumerRunning: bool
