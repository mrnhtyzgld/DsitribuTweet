package com.bil401.api

import io.circe.generic.semiauto.{deriveDecoder, deriveEncoder}
import io.circe.{Decoder, Encoder}

// --- istekler ---------------------------------------------------------------

final case class InterestsRequest(interests: List[String])
object InterestsRequest {
  implicit val decoder: Decoder[InterestsRequest] = deriveDecoder
  implicit val encoder: Encoder[InterestsRequest] = deriveEncoder
}

// --- yanitlar ---------------------------------------------------------------

final case class InterestsResponse(
    userId: String,
    interestCount: Int,
    vectorDim: Int,
    message: String
)
object InterestsResponse {
  implicit val encoder: Encoder[InterestsResponse] = deriveEncoder
  implicit val decoder: Decoder[InterestsResponse] = deriveDecoder
}

/** Feed'de donen tek bir gonderi.
  *
  * Skorlari ayri ayri donuyoruz ki siralama davranisinin dogru oldugu
  * demo sirasinda gozle dogrulanabilsin.
  */
final case class FeedItem(
    tweetId: String,
    text: String,
    language: String,
    tweetTimestamp: Long,
    authorId: String,
    hashtags: List[String],
    semanticSimilarity: Double,
    recencyScore: Double,
    finalScore: Double
)
object FeedItem {
  implicit val encoder: Encoder[FeedItem] = deriveEncoder
  implicit val decoder: Decoder[FeedItem] = deriveDecoder
}

final case class FeedResponse(
    userId: String,
    count: Int,
    items: List[FeedItem]
)
object FeedResponse {
  implicit val encoder: Encoder[FeedResponse] = deriveEncoder
  implicit val decoder: Decoder[FeedResponse] = deriveDecoder
}

final case class ErrorResponse(error: String)
object ErrorResponse {
  implicit val encoder: Encoder[ErrorResponse] = deriveEncoder
  implicit val decoder: Decoder[ErrorResponse] = deriveDecoder
}

final case class HealthResponse(status: String, profiles: Int)
object HealthResponse {
  implicit val encoder: Encoder[HealthResponse] = deriveEncoder
  implicit val decoder: Decoder[HealthResponse] = deriveDecoder
}

// --- embedding servisi ------------------------------------------------------

final case class EmbedRequest(texts: List[String])
object EmbedRequest {
  implicit val encoder: Encoder[EmbedRequest] = deriveEncoder
  implicit val decoder: Decoder[EmbedRequest] = deriveDecoder
}

final case class EmbedResponse(vectors: List[List[Float]], dim: Int)
object EmbedResponse {
  implicit val decoder: Decoder[EmbedResponse] = deriveDecoder
  implicit val encoder: Encoder[EmbedResponse] = deriveEncoder
}

// --- Qdrant ----------------------------------------------------------------

final case class QdrantSearchRequest(
    vector: List[Float],
    limit: Int,
    with_payload: Boolean = true
)
object QdrantSearchRequest {
  implicit val encoder: Encoder[QdrantSearchRequest] = deriveEncoder
}

final case class QdrantPayload(
    tweetId: Option[String],
    text: Option[String],
    language: Option[String],
    tweetTimestamp: Option[Long],
    authorId: Option[String],
    hashtags: Option[List[String]]
)
object QdrantPayload {
  implicit val decoder: Decoder[QdrantPayload] = deriveDecoder
}

final case class QdrantHit(id: String, score: Double, payload: Option[QdrantPayload])
object QdrantHit {
  // Qdrant point id'si string (UUID) veya sayi olabilir -> ikisini de kabul et.
  // Either.orElse 2.13+ oldugu icin pattern match kullaniyoruz.
  implicit val decoder: Decoder[QdrantHit] = Decoder.instance { c =>
    val idField = c.downField("id")
    val idResult = idField.as[String] match {
      case Right(s) => Right(s)
      case Left(_)  => idField.as[Long].map(_.toString)
    }
    for {
      id <- idResult
      score <- c.downField("score").as[Double]
      payload <- c.downField("payload").as[Option[QdrantPayload]]
    } yield QdrantHit(id, score, payload)
  }
}

final case class QdrantSearchResponse(result: List[QdrantHit])
object QdrantSearchResponse {
  implicit val decoder: Decoder[QdrantSearchResponse] = deriveDecoder
}
