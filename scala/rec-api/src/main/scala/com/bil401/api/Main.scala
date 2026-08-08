package com.bil401.api

import cats.effect.{ExitCode, IO, IOApp, Ref}
import com.comcast.ip4s._
import org.http4s.ember.client.EmberClientBuilder
import org.http4s.ember.server.EmberServerBuilder
import org.http4s.server.middleware.Logger
import org.http4s.{HttpApp, Uri}

import scala.concurrent.duration._

/** Scala Recommendation API (rapor §3.6).
  *
  *   POST /users/{id}/interests  -> ilgi alanlarindan profil vektoru olusturur
  *   GET  /users/{id}/feed       -> profile en yakin gonderileri dondurur
  */
object Main extends IOApp {

  private def env(key: String, default: String): String =
    sys.env.getOrElse(key, default)

  /** Sayisal env degeri okur. toDoubleOption 2.13+ oldugu icin
    * 2.12'de Try ile ayni davranisi kuruyoruz.
    */
  private def envDouble(key: String, default: Double): Double =
    sys.env.get(key).flatMap(v => scala.util.Try(v.toDouble).toOption).getOrElse(default)

  override def run(args: List[String]): IO[ExitCode] = {
    val qdrantUrl = env("QDRANT_URL", "http://localhost:6333")
    val embedUrl  = env("EMBED_URL", "http://localhost:8000")
    val collection = env("COLLECTION", "posts")
    val httpPort   = env("HTTP_PORT", "8081").toInt
    val semanticWeight = envDouble("SEMANTIC_WEIGHT", 0.85)
    val recencyWeight  = envDouble("RECENCY_WEIGHT", 0.15)

    val program = for {
      qdrantUri <- IO.fromEither(Uri.fromString(qdrantUrl).left.map(e =>
        new IllegalArgumentException(s"gecersiz QDRANT_URL: $e")))
      embedUri <- IO.fromEither(Uri.fromString(embedUrl).left.map(e =>
        new IllegalArgumentException(s"gecersiz EMBED_URL: $e")))
      port <- IO.fromOption(Port.fromInt(httpPort))(
        new IllegalArgumentException(s"gecersiz HTTP_PORT: $httpPort"))

      _ <- IO.println(
        s"""[rec-api] baslatiliyor
           |  qdrant     : $qdrantUri (collection=$collection)
           |  embedding  : $embedUri
           |  port       : $httpPort
           |  agirliklar : semantic=$semanticWeight recency=$recencyWeight""".stripMargin)

      exit <- EmberClientBuilder
        .default[IO]
        // Embedding cagrilari model yuklemesi nedeniyle ilk seferde yavas olabilir
        .withTimeout(60.seconds)
        .build
        .use { client =>
          for {
            ref <- Ref.of[IO, Map[String, Vector[Float]]](Map.empty)
            profiles = ProfileStore(ref)
            embedding = new EmbeddingClient(client, embedUri)
            qdrant = new QdrantClient(client, qdrantUri, collection)
            routes = new Routes(embedding, qdrant, profiles, semanticWeight, recencyWeight)
            app: HttpApp[IO] = Logger.httpApp(logHeaders = false, logBody = false)(
              routes.routes.orNotFound
            )
            code <- EmberServerBuilder
              .default[IO]
              .withHost(ipv4"0.0.0.0")
              .withPort(port)
              .withHttpApp(app)
              .build
              .use(_ => IO.println(s"[rec-api] dinliyor: 0.0.0.0:$httpPort") *> IO.never)
              .as(ExitCode.Success)
          } yield code
        }
    } yield exit

    program.handleErrorWith { err =>
      IO.println(s"[rec-api] baslatilamadi: ${err.getMessage}").as(ExitCode.Error)
    }
  }
}
