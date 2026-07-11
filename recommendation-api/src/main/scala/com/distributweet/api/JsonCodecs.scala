package com.distributweet.api

import io.circe.{Decoder, Encoder, Json}
import io.circe.generic.semiauto._

object JsonCodecs {
  implicit val interestsRequestDecoder: Decoder[InterestsRequest] = deriveDecoder
  implicit val interestsRequestEncoder: Encoder[InterestsRequest] = deriveEncoder
  implicit val userProfileResponseEncoder: Encoder[UserProfileResponse] = deriveEncoder
  implicit val healthResponseEncoder: Encoder[HealthResponse] = deriveEncoder
  implicit val metricsResponseEncoder: Encoder[MetricsResponse] = deriveEncoder
  implicit val embedRequestEncoder: Encoder[EmbedRequest] = deriveEncoder
  implicit val embedResponseDecoder: Decoder[EmbedResponse] = deriveDecoder
  implicit val postPayloadDecoder: Decoder[PostPayload] = deriveDecoder
  implicit val feedItemEncoder: Encoder[FeedItem] = deriveEncoder
  implicit val feedResponseEncoder: Encoder[FeedResponse] = deriveEncoder

  final case class QdrantRetrieveResponse(result: List[QdrantRetrievedPoint])
  final case class QdrantRetrievedPoint(id: Json, payload: Option[Json], vector: Option[List[Double]])
  final case class QdrantSearchResponse(result: List[QdrantScoredPoint])
  final case class QdrantScoredPoint(id: Json, score: Double, payload: Option[PostPayload])

  implicit val qdrantRetrievedPointDecoder: Decoder[QdrantRetrievedPoint] = deriveDecoder
  implicit val qdrantRetrieveResponseDecoder: Decoder[QdrantRetrieveResponse] = deriveDecoder
  implicit val qdrantScoredPointDecoder: Decoder[QdrantScoredPoint] = deriveDecoder
  implicit val qdrantSearchResponseDecoder: Decoder[QdrantSearchResponse] = deriveDecoder
}
