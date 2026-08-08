package com.bil401.api

import cats.effect.IO
import io.circe.syntax._
import org.http4s._
import org.http4s.circe.CirceEntityCodec._
import org.http4s.client.Client

/** Embedding servisine (Python worker) HTTP istemcisi.
  *
  * Scala tarafinda MiniLM calistirmak yerine worker'in modelini kullaniyoruz;
  * model zaten orada bellekte duruyor. Rapor §3.6'daki "ilgi alanlarini
  * embedding servisine gonderip" adiminin karsiligi budur.
  */
class EmbeddingClient(client: Client[IO], baseUrl: Uri) {

  def embed(texts: List[String]): IO[List[Vector[Float]]] = {
    if (texts.isEmpty) return IO.raiseError(new IllegalArgumentException("bos metin listesi"))

    val req = Request[IO](
      method = Method.POST,
      uri = baseUrl / "embed"
    ).withEntity(EmbedRequest(texts).asJson)

    client.expect[EmbedResponse](req).map(_.vectors.map(_.toVector)).handleErrorWith { err =>
      IO.raiseError(new RuntimeException(s"embedding servisine ulasilamadi: ${err.getMessage}", err))
    }
  }
}

/** Qdrant REST istemcisi.
  *
  * Resmi Java istemcisi gRPC tabanli ve cats-effect ile entegrasyonu ekstra
  * is gerektiriyor; tek ihtiyacimiz olan "search" oldugu icin REST yeterli.
  */
class QdrantClient(client: Client[IO], baseUrl: Uri, collection: String) {

  def search(vector: Vector[Float], limit: Int): IO[List[QdrantHit]] = {
    val uri = baseUrl / "collections" / collection / "points" / "search"
    val req = Request[IO](method = Method.POST, uri = uri)
      .withEntity(QdrantSearchRequest(vector.toList, limit).asJson)

    client.expect[QdrantSearchResponse](req).map(_.result).handleErrorWith { err =>
      IO.raiseError(new RuntimeException(s"Qdrant aramasi basarisiz: ${err.getMessage}", err))
    }
  }

  /** Collection'daki nokta sayisi -- smoke test ve health icin. */
  def count: IO[Long] = {
    val uri = baseUrl / "collections" / collection / "points" / "count"
    val req = Request[IO](method = Method.POST, uri = uri)
      .withEntity(io.circe.Json.obj("exact" -> io.circe.Json.True))

    client
      .expect[io.circe.Json](req)
      .map(_.hcursor.downField("result").downField("count").as[Long].getOrElse(0L))
      .handleError(_ => 0L)
  }
}
