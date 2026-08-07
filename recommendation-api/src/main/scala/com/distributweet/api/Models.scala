package com.distributweet.api

final case class InterestsRequest(interests: List[String])
final case class UserProfileResponse(userId: String, interests: List[String], vectorDimensions: Int, updatedAt: String)
final case class HealthResponse(status: String)
final case class MetricsResponse(service: String, postsCollection: String, usersCollection: String)

final case class EmbedRequest(texts: List[String])
final case class EmbedResponse(vectors: List[List[Double]], model: String, dimensions: Int)

final case class PostPayload(
    postId: String,
    text: String,
    authorId: String,
    language: String,
    createdAt: Long,
    createdAtIso: Option[String],
    source: Option[String]
)

final case class Candidate(
    postId: String,
    text: String,
    authorId: String,
    language: String,
    semanticScore: Double,
    createdAt: Long
)

final case class FeedItem(
    postId: String,
    text: String,
    authorId: String,
    semanticScore: Double,
    recencyScore: Double,
    finalScore: Double,
    createdAt: String
)

final case class FeedResponse(userId: String, generatedAt: String, items: List[FeedItem])

final case class DatasetPost(
    postId: String,
    text: String,
    authorId: String,
    language: String,
    createdAt: String,
    source: Option[String]
)

final case class DatasetResponse(generatedAt: String, totalIndexed: Long, visible: Int, items: List[DatasetPost])

final case class DemoUser(userId: String, displayName: String, interests: List[String])
final case class DemoUsersResponse(users: List[DemoUser])
final case class DemoSeedResponse(generatedAt: String, profiles: List[UserProfileResponse])
