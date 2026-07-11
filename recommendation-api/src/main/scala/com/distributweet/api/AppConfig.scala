package com.distributweet.api

final case class AppConfig(
    httpHost: String,
    httpPort: Int,
    qdrantUrl: String,
    embeddingUrl: String,
    postsCollection: String,
    usersCollection: String,
    vectorSize: Int,
    candidateLimit: Int,
    maxPostAgeHours: Double
)

object AppConfig {
  def fromEnv(env: Map[String, String] = sys.env): AppConfig =
    AppConfig(
      httpHost = env.getOrElse("HTTP_HOST", "0.0.0.0"),
      httpPort = env.get("HTTP_PORT").flatMap(v => scala.util.Try(v.toInt).toOption).getOrElse(8080),
      qdrantUrl = env.getOrElse("QDRANT_URL", "http://localhost:6333"),
      embeddingUrl = env.getOrElse("EMBEDDING_URL", "http://localhost:8001"),
      postsCollection = env.getOrElse("POSTS_COLLECTION", "posts"),
      usersCollection = env.getOrElse("USERS_COLLECTION", "users"),
      vectorSize = env.get("VECTOR_SIZE").flatMap(v => scala.util.Try(v.toInt).toOption).getOrElse(384),
      candidateLimit = env.get("CANDIDATE_LIMIT").flatMap(v => scala.util.Try(v.toInt).toOption).getOrElse(100),
      maxPostAgeHours = env.get("MAX_POST_AGE_HOURS").flatMap(v => scala.util.Try(v.toDouble).toOption).getOrElse(24.0 * 14.0)
    )
}
