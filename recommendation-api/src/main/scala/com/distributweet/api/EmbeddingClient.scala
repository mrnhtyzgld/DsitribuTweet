package com.distributweet.api

import cats.effect.Async
import cats.syntax.all._
import io.circe.Error
import sttp.client3._
import sttp.client3.circe._
import sttp.model.Uri

import JsonCodecs._

trait EmbeddingClient[F[_]] {
  def embed(texts: List[String]): F[EmbedResponse]
}

final class HttpEmbeddingClient[F[_]: Async](baseUrl: String, backend: SttpBackend[F, Any])
    extends EmbeddingClient[F] {
  private val endpoint: Uri = Uri
    .parse(s"${baseUrl.stripSuffix("/")}/embed")
    .fold(error => throw new IllegalArgumentException(error), identity)

  override def embed(texts: List[String]): F[EmbedResponse] = {
    val request =
      basicRequest
        .post(endpoint)
        .body(EmbedRequest(texts))
        .response(asJson[EmbedResponse])

    request.send(backend).flatMap { response =>
      response.body match {
        case Right(value) => Async[F].pure(value)
        case Left(error: ResponseException[String, Error]) =>
          Async[F].raiseError(new RuntimeException(s"embedding request failed: ${error.getMessage}"))
      }
    }
  }
}
