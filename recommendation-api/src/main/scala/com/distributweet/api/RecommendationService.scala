package com.distributweet.api

import cats.effect.Async
import cats.syntax.all._

import java.time.Instant

final class RecommendationService[F[_]: Async](
    config: AppConfig,
    embeddings: EmbeddingClient[F],
    store: VectorStore[F],
    now: F[Instant]
) {
  def createOrUpdateProfile(userId: String, interests: List[String]): F[UserProfileResponse] = {
    val normalizedInterests = interests.map(_.trim).filter(_.nonEmpty)
    if (normalizedInterests.isEmpty) {
      Async[F].raiseError(new IllegalArgumentException("interests must not be empty"))
    } else {
      val texts = normalizedInterests.map(interest => s"query: $interest")
      for {
        response <- embeddings.embed(texts)
        vector <- VectorMath
          .averageAndNormalize(response.vectors)
          .leftMap(message => new IllegalArgumentException(message))
          .liftTo[F]
        _ <- store.ensureCollection(config.usersCollection)
        _ <- store.upsertUser(userId, vector, normalizedInterests, config.usersCollection)
        timestamp <- now
      } yield UserProfileResponse(userId, normalizedInterests, vector.length, timestamp.toString)
    }
  }

  def feed(userId: String, limit: Int): F[Option[FeedResponse]] = {
    val boundedLimit = math.max(1, math.min(limit, 100))
    val candidateLimit = math.max(config.candidateLimit, boundedLimit * 5)
    for {
      maybeVector <- store.getUserVector(userId, config.usersCollection)
      generatedAt <- now
      response <- maybeVector match {
        case None => Async[F].pure(None)
        case Some(vector) =>
          store.searchPosts(vector, candidateLimit, config.postsCollection).map { candidates =>
            Some(
              FeedResponse(
                userId = userId,
                generatedAt = generatedAt.toString,
                items = Ranking.rank(candidates, generatedAt, boundedLimit, config.maxPostAgeHours)
              )
            )
          }
      }
    } yield response
  }

  def dataset(limit: Int): F[DatasetResponse] = {
    val boundedLimit = math.max(1, math.min(limit, 500))
    for {
      generatedAt <- now
      total <- store.countPosts(config.postsCollection)
      posts <- store.listPosts(boundedLimit, config.postsCollection)
    } yield DatasetResponse(
      generatedAt = generatedAt.toString,
      totalIndexed = total,
      visible = posts.length,
      items = posts
    )
  }

  def demoUsers: F[DemoUsersResponse] =
    Async[F].pure(DemoUsersResponse(DemoProfiles.users))

  def seedDemoUsers(): F[DemoSeedResponse] =
    for {
      profiles <- DemoProfiles.users.traverse(user => createOrUpdateProfile(user.userId, user.interests))
      generatedAt <- now
    } yield DemoSeedResponse(generatedAt = generatedAt.toString, profiles = profiles)
}
