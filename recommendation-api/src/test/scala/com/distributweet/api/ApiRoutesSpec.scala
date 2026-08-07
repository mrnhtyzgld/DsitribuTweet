package com.distributweet.api

import cats.effect.IO
import cats.effect.unsafe.implicits.global
import org.http4s.implicits._
import org.http4s.{Method, Request, Status}
import org.scalatest.funsuite.AnyFunSuite

import java.time.Instant

class ApiRoutesSpec extends AnyFunSuite {
  test("root serves the dashboard as raw html") {
    val service =
      new RecommendationService[IO](
        config = testConfig,
        embeddings = new FakeEmbeddings,
        store = new FakeStore,
        now = IO.pure(Instant.parse("2026-07-11T15:00:00Z"))
      )
    val routes = new ApiRoutes[IO](testConfig, service).routes.orNotFound

    val response = routes.run(Request[IO](Method.GET, uri"/")).unsafeRunSync()
    val body = response.as[String].unsafeRunSync()

    assert(response.status == Status.Ok)
    assert(body.startsWith("<!doctype html>"))
  }

  private val testConfig: AppConfig =
    AppConfig(
      httpHost = "127.0.0.1",
      httpPort = 8080,
      qdrantUrl = "http://qdrant:6333",
      embeddingUrl = "http://embedding:8001",
      postsCollection = "posts",
      usersCollection = "users",
      vectorSize = 2,
      candidateLimit = 100,
      maxPostAgeHours = 24.0
    )

  private final class FakeEmbeddings extends EmbeddingClient[IO] {
    override def embed(texts: List[String]): IO[EmbedResponse] =
      IO.pure(EmbedResponse(texts.map(_ => List(1.0, 0.0)), model = "fake", dimensions = 2))
  }

  private final class FakeStore extends VectorStore[IO] {
    override def ensureCollection(name: String): IO[Unit] = IO.unit
    override def upsertUser(userId: String, vector: List[Double], interests: List[String], collection: String): IO[Unit] =
      IO.unit
    override def getUserVector(userId: String, collection: String): IO[Option[List[Double]]] = IO.pure(None)
    override def searchPosts(vector: List[Double], limit: Int, collection: String): IO[List[Candidate]] = IO.pure(Nil)
    override def countPosts(collection: String): IO[Long] = IO.pure(0L)
    override def listPosts(limit: Int, collection: String): IO[List[DatasetPost]] = IO.pure(Nil)
  }
}
