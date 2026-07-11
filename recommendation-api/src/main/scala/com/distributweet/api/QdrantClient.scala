package com.distributweet.api

import cats.effect.Async
import cats.syntax.all._
import io.circe.{Error, Json}
import io.circe.syntax._
import sttp.client3._
import sttp.client3.circe._
import sttp.model.Uri

import JsonCodecs._

trait VectorStore[F[_]] {
  def ensureCollection(name: String): F[Unit]
  def upsertUser(userId: String, vector: List[Double], interests: List[String], collection: String): F[Unit]
  def getUserVector(userId: String, collection: String): F[Option[List[Double]]]
  def searchPosts(vector: List[Double], limit: Int, collection: String): F[List[Candidate]]
}

final class HttpQdrantClient[F[_]: Async](baseUrl: String, vectorSize: Int, backend: SttpBackend[F, Any])
    extends VectorStore[F] {

  override def ensureCollection(name: String): F[Unit] = {
    val getRequest = basicRequest.get(uriFor(s"/collections/$name"))
    getRequest.send(backend).flatMap { response =>
      if (response.code.isSuccess) Async[F].unit
      else createCollection(name)
    }
  }

  override def upsertUser(userId: String, vector: List[Double], interests: List[String], collection: String): F[Unit] = {
    val body =
      Json.obj(
        "points" -> Json.arr(
          Json.obj(
            "id" -> Json.fromString(IdUtil.userPointId(userId)),
            "vector" -> vector.asJson,
            "payload" -> Json.obj(
              "userId" -> Json.fromString(userId),
              "interests" -> interests.asJson
            )
          )
        )
      )

    sendExpectSuccess(
      basicRequest
        .put(uriFor(s"/collections/$collection/points?wait=true"))
        .contentType("application/json")
        .body(body.noSpaces)
    )
  }

  override def getUserVector(userId: String, collection: String): F[Option[List[Double]]] = {
    val body =
      Json.obj(
        "ids" -> Json.arr(Json.fromString(IdUtil.userPointId(userId))),
        "with_vector" -> Json.fromBoolean(true),
        "with_payload" -> Json.fromBoolean(true)
      )

    val request =
      basicRequest
        .post(uriFor(s"/collections/$collection/points"))
        .contentType("application/json")
        .body(body.noSpaces)
        .response(asJson[QdrantRetrieveResponse])

    sendJson(request).map(_.result.headOption.flatMap(_.vector))
  }

  override def searchPosts(vector: List[Double], limit: Int, collection: String): F[List[Candidate]] = {
    val body =
      Json.obj(
        "vector" -> vector.asJson,
        "limit" -> Json.fromInt(limit),
        "with_payload" -> Json.fromBoolean(true),
        "with_vector" -> Json.fromBoolean(false)
      )

    val request =
      basicRequest
        .post(uriFor(s"/collections/$collection/points/search"))
        .contentType("application/json")
        .body(body.noSpaces)
        .response(asJson[QdrantSearchResponse])

    sendJson(request).map { response =>
      response.result.flatMap { point =>
        point.payload.map { payload =>
          Candidate(
            postId = payload.postId,
            text = payload.text,
            authorId = payload.authorId,
            language = payload.language,
            semanticScore = point.score,
            createdAt = payload.createdAt
          )
        }
      }
    }
  }

  private def createCollection(name: String): F[Unit] = {
    val body =
      Json.obj(
        "vectors" -> Json.obj(
          "size" -> Json.fromInt(vectorSize),
          "distance" -> Json.fromString("Cosine")
        )
      )

    sendExpectSuccess(
      basicRequest
        .put(uriFor(s"/collections/$name"))
        .contentType("application/json")
        .body(body.noSpaces)
    )
  }

  private def sendExpectSuccess(request: Request[Either[String, String], Any]): F[Unit] =
    request.send(backend).flatMap { response =>
      if (response.code.isSuccess) Async[F].unit
      else Async[F].raiseError(new RuntimeException(s"qdrant request failed with ${response.code}: ${response.body}"))
    }

  private def sendJson[A](request: Request[Either[ResponseException[String, Error], A], Any]): F[A] =
    request.send(backend).flatMap { response =>
      response.body match {
        case Right(value) => Async[F].pure(value)
        case Left(error: ResponseException[String, Error]) =>
          Async[F].raiseError(new RuntimeException(s"qdrant request failed: ${error.getMessage}"))
      }
    }

  private def uriFor(path: String): Uri =
    Uri
      .parse(s"${baseUrl.stripSuffix("/")}$path")
      .fold(error => throw new IllegalArgumentException(error), identity)
}
