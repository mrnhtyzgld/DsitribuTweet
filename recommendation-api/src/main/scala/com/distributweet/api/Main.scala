package com.distributweet.api

import cats.effect.{IO, IOApp}
import com.comcast.ip4s.{Host, Port}
import org.http4s.ember.server.EmberServerBuilder
import sttp.client3.asynchttpclient.cats.AsyncHttpClientCatsBackend

import java.time.Instant

object Main extends IOApp.Simple {
  override def run: IO[Unit] = {
    val config = AppConfig.fromEnv()

    AsyncHttpClientCatsBackend.resource[IO]().use { backend =>
      val embeddings = new HttpEmbeddingClient[IO](config.embeddingUrl, backend)
      val store = new HttpQdrantClient[IO](config.qdrantUrl, config.vectorSize, backend)
      val service = new RecommendationService[IO](config, embeddings, store, IO.delay(Instant.now()))
      val routes = new ApiRoutes[IO](config, service).routes.orNotFound

      for {
        _ <- store.ensureCollection(config.usersCollection)
        _ <- store.ensureCollection(config.postsCollection)
        host <- IO.fromOption(Host.fromString(config.httpHost))(new IllegalArgumentException("invalid HTTP_HOST"))
        port <- IO.fromOption(Port.fromInt(config.httpPort))(new IllegalArgumentException("invalid HTTP_PORT"))
        _ <- EmberServerBuilder
          .default[IO]
          .withHost(host)
          .withPort(port)
          .withHttpApp(routes)
          .build
          .useForever
      } yield ()
    }
  }
}
