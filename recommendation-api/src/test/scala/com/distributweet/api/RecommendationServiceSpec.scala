package com.distributweet.api

import cats.effect.IO
import cats.effect.unsafe.implicits.global
import org.scalatest.funsuite.AnyFunSuite

import java.time.Instant

class RecommendationServiceSpec extends AnyFunSuite {
  test("seedDemoUsers creates every bundled demo profile") {
    val store = new FakeStore
    val service = newService(store)

    val response = service.seedDemoUsers().unsafeRunSync()

    assert(response.profiles.map(_.userId).toSet == DemoProfiles.users.map(_.userId).toSet)
    assert(store.upsertedUsers.keySet == DemoProfiles.users.map(_.userId).toSet)
  }

  test("dataset clamps limit and includes indexed count") {
    val store = new FakeStore
    val service = newService(store)

    val response = service.dataset(700).unsafeRunSync()

    assert(store.lastListLimit.contains(500))
    assert(response.totalIndexed == 2)
    assert(response.visible == 1)
    assert(response.items.head.postId == "post-1")
  }

  private def newService(store: FakeStore): RecommendationService[IO] =
    new RecommendationService[IO](
      config = AppConfig(
        httpHost = "127.0.0.1",
        httpPort = 8080,
        qdrantUrl = "http://qdrant:6333",
        embeddingUrl = "http://embedding:8001",
        postsCollection = "posts",
        usersCollection = "users",
        vectorSize = 2,
        candidateLimit = 100,
        maxPostAgeHours = 24.0
      ),
      embeddings = new FakeEmbeddings,
      store = store,
      now = IO.pure(Instant.parse("2026-07-11T15:00:00Z"))
    )

  private final class FakeEmbeddings extends EmbeddingClient[IO] {
    override def embed(texts: List[String]): IO[EmbedResponse] =
      IO.pure(EmbedResponse(texts.map(_ => List(1.0, 0.0)), model = "fake", dimensions = 2))
  }

  private final class FakeStore extends VectorStore[IO] {
    var upsertedUsers: Map[String, List[Double]] = Map.empty
    var lastListLimit: Option[Int] = None

    override def ensureCollection(name: String): IO[Unit] =
      IO.unit

    override def upsertUser(userId: String, vector: List[Double], interests: List[String], collection: String): IO[Unit] =
      IO.delay {
        upsertedUsers = upsertedUsers.updated(userId, vector)
      }

    override def getUserVector(userId: String, collection: String): IO[Option[List[Double]]] =
      IO.pure(upsertedUsers.get(userId))

    override def searchPosts(vector: List[Double], limit: Int, collection: String): IO[List[Candidate]] =
      IO.pure(Nil)

    override def countPosts(collection: String): IO[Long] =
      IO.pure(2L)

    override def listPosts(limit: Int, collection: String): IO[List[DatasetPost]] =
      IO.delay {
        lastListLimit = Some(limit)
        List(
          DatasetPost(
            postId = "post-1",
            text = "CUDA kernel optimization techniques",
            authorId = "author-1",
            language = "en",
            createdAt = "2026-07-11T14:35:00Z",
            source = Some("test")
          )
        )
      }
  }
}
