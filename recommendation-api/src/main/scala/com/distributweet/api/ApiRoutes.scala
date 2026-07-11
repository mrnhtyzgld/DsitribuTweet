package com.distributweet.api

import cats.effect.Async
import cats.syntax.all._
import org.http4s.HttpRoutes
import org.http4s.circe.CirceEntityCodec._
import org.http4s.dsl.Http4sDsl

import JsonCodecs._

final class ApiRoutes[F[_]: Async](config: AppConfig, service: RecommendationService[F]) extends Http4sDsl[F] {
  object LimitQueryParam extends OptionalQueryParamDecoderMatcher[Int]("limit")

  val routes: HttpRoutes[F] =
    HttpRoutes.of[F] {
      case GET -> Root / "health" =>
        Ok(HealthResponse("ok"))

      case GET -> Root / "metrics" =>
        Ok(MetricsResponse("recommendation-api", config.postsCollection, config.usersCollection))

      case request @ POST -> Root / "users" / userId / "interests" =>
        request
          .as[InterestsRequest]
          .flatMap(body => service.createOrUpdateProfile(userId, body.interests))
          .flatMap(Ok(_))
          .handleErrorWith(error => BadRequest(Map("error" -> error.getMessage)))

      case GET -> Root / "users" / userId / "feed" :? LimitQueryParam(limitParam) =>
        service.feed(userId, limitParam.getOrElse(20)).flatMap {
          case Some(feed) => Ok(feed)
          case None => NotFound(Map("error" -> s"user profile not found: $userId"))
        }
    }
}
