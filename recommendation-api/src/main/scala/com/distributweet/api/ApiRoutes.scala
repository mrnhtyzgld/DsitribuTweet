package com.distributweet.api

import cats.effect.Async
import cats.syntax.all._
import fs2.Stream
import org.http4s.{Header, HttpRoutes, Response, Status}
import org.http4s.circe.CirceEntityCodec._
import org.http4s.dsl.Http4sDsl
import org.typelevel.ci.CIString

import java.nio.charset.StandardCharsets

import JsonCodecs._

final class ApiRoutes[F[_]: Async](config: AppConfig, service: RecommendationService[F]) extends Http4sDsl[F] {
  object LimitQueryParam extends OptionalQueryParamDecoderMatcher[Int]("limit")

  val routes: HttpRoutes[F] =
    HttpRoutes.of[F] {
      case GET -> Root =>
        staticResource("index.html", "text/html; charset=utf-8")

      case GET -> Root / "styles.css" =>
        staticResource("styles.css", "text/css; charset=utf-8")

      case GET -> Root / "app.js" =>
        staticResource("app.js", "application/javascript; charset=utf-8")

      case GET -> Root / "health" =>
        Ok(HealthResponse("ok"))

      case GET -> Root / "metrics" =>
        Ok(MetricsResponse("recommendation-api", config.postsCollection, config.usersCollection))

      case GET -> Root / "posts" :? LimitQueryParam(limitParam) =>
        service.dataset(limitParam.getOrElse(100)).flatMap(Ok(_))

      case GET -> Root / "demo" / "users" =>
        service.demoUsers.flatMap(Ok(_))

      case POST -> Root / "demo" / "users" =>
        service.seedDemoUsers().flatMap(Ok(_))

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

  private def staticResource(path: String, contentType: String): F[Response[F]] =
    Async[F]
      .blocking {
        Option(getClass.getResourceAsStream(s"/public/$path")).map { stream =>
          try new String(stream.readAllBytes(), StandardCharsets.UTF_8)
          finally stream.close()
        }
      }
      .flatMap {
        case Some(body) =>
          Async[F].pure(
            Response[F](
              status = Status.Ok,
              body = Stream.emits(body.getBytes(StandardCharsets.UTF_8)).covary[F]
            ).putHeaders(
                Header.Raw(CIString("Content-Type"), contentType),
                Header.Raw(CIString("Cache-Control"), "no-store")
              )
          )
        case None => NotFound()
      }
}
