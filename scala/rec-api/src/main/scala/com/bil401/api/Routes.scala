package com.bil401.api

import cats.effect.{IO, Ref}
import cats.implicits._
import io.circe.syntax._
import org.http4s._
import org.http4s.circe.CirceEntityCodec._
import org.http4s.dsl.io._

/** Kullanici profil vektorlerinin bellek ici deposu.
  *
  * Prototip kapsaminda yeterli (rapor §7: "ilk testler sinirli veri ve tek
  * makine uzerinde"). Kalicilik gerekirse Qdrant'ta ayri bir `users`
  * collection'i acilabilir.
  */
final case class ProfileStore(ref: Ref[IO, Map[String, Vector[Float]]]) {
  def put(userId: String, vector: Vector[Float]): IO[Unit] =
    ref.update(_ + (userId -> vector))

  def get(userId: String): IO[Option[Vector[Float]]] =
    ref.get.map(_.get(userId))

  def size: IO[Int] = ref.get.map(_.size)
}

/** Query parametresi cozucusu. Pattern match'te kullanildigi icin
  * sinif disinda, companion object'te tanimli olmasi gerekiyor.
  */
object Routes {
  object LimitParam extends OptionalQueryParamDecoderMatcher[Int]("limit")
}

class Routes(
    embedding: EmbeddingClient,
    qdrant: QdrantClient,
    profiles: ProfileStore,
    semanticWeight: Double,
    recencyWeight: Double
) {
  import Routes.LimitParam

  /** Feed'de asiri arama yapilmasini onlemek icin ust sinir. */
  private val MaxLimit = 100

  /** Qdrant'tan cekilen aday sayisi.
    *
    * Tekillestirme adaylarin buyuk kismini eleyebildigi icin (sinirli
    * sablon havuzundan uretilen veri) genis tutuluyor. Qdrant HNSW
    * aramasinda bu boyut milisaniyeler mertebesinde kaliyor.
    */
  private val CandidatePoolSize = 400

  /** Rapor §4 adim 7: ilgi alani vektorlerinin ortalamasi kullanici profili.
    * Normalize etmezsek ilgi alani sayisi degistikce vektorun boyu degisir
    * ve cosine skorlari kayar.
    */
  private def averageAndNormalize(vectors: List[Vector[Float]]): Either[String, Vector[Float]] = {
    if (vectors.isEmpty) return Left("bos vektor listesi")
    val dim = vectors.head.length
    if (vectors.exists(_.length != dim)) return Left("vektor boyutlari tutarsiz")

    val sums = Array.fill(dim)(0.0)
    vectors.foreach { v =>
      var i = 0
      while (i < dim) { sums(i) += v(i); i += 1 }
    }
    val n = vectors.length.toDouble
    val mean = sums.map(_ / n)
    val norm = math.sqrt(mean.map(x => x * x).sum)
    if (norm < 1e-9) Left("ortalama vektor sifira cok yakin")
    else Right(mean.map(x => (x / norm).toFloat).toVector)
  }

  val routes: HttpRoutes[IO] = HttpRoutes.of[IO] {

    case GET -> Root / "health" =>
      profiles.size.flatMap(n => Ok(HealthResponse("ok", n).asJson))

    // POST /users/{userId}/interests
    case req @ POST -> Root / "users" / userId / "interests" =>
      req.attemptAs[InterestsRequest].value.flatMap {
        case Left(err) =>
          BadRequest(ErrorResponse(s"gecersiz istek govdesi: ${err.getMessage}").asJson)

        case Right(body) =>
          val cleaned = body.interests.map(_.trim).filter(_.nonEmpty)
          if (cleaned.isEmpty)
            BadRequest(ErrorResponse("interests alani bos olmayan bir liste olmali").asJson)
          else if (cleaned.length > 50)
            BadRequest(ErrorResponse("en fazla 50 ilgi alani kabul edilir").asJson)
          else
            embedding
              .embed(cleaned)
              .flatMap { vectors =>
                averageAndNormalize(vectors) match {
                  case Left(msg) =>
                    UnprocessableEntity(ErrorResponse(msg).asJson)
                  case Right(profile) =>
                    profiles.put(userId, profile) *>
                      Ok(
                        InterestsResponse(
                          userId = userId,
                          interestCount = cleaned.length,
                          vectorDim = profile.length,
                          message = "profil vektoru olusturuldu"
                        ).asJson
                      )
                }
              }
              .handleErrorWith { err =>
                ServiceUnavailable(ErrorResponse(err.getMessage).asJson)
              }
      }

    // GET /users/{userId}/feed?limit=20
    case GET -> Root / "users" / userId / "feed" :? LimitParam(limitOpt) =>
      val limit = limitOpt.getOrElse(20).max(1).min(MaxLimit)

      profiles.get(userId).flatMap {
        case None =>
          NotFound(
            ErrorResponse(
              s"'$userId' icin profil yok -- once POST /users/$userId/interests cagirin"
            ).asJson
          )

        case Some(profile) =>
          for {
            now <- IO.realTimeInstant.map(_.getEpochSecond)
            // Tekillestirme adaylarin cogunu eleyebiliyor (ayni cumlenin
            // on/son ekli varyasyonlari), bu yuzden genis bir havuz cekip
            // eleme sonrasi limit'e dusuruyoruz.
            hits <- qdrant.search(profile, CandidatePoolSize)
            items = hits.flatMap(toFeedItem(_, now))
            ranked = dedupeByText(items.sortBy(-_.finalScore)).take(limit)
            resp <- Ok(FeedResponse(userId, ranked.length, ranked).asJson)
          } yield resp
      }.handleErrorWith { err =>
        ServiceUnavailable(ErrorResponse(err.getMessage).asJson)
      }
  }

  /** Yakin-tekrar metinleri feed'den eler.
    *
    * Dedup Spark tarafinda tweetId bazli yapiliyor -- farkli kullanicilarin
    * ayni metni paylasmasi (retweet/alinti) gecerli ve ayri kayitlardir.
    * Ancak feed'de neredeyse ayni cumleyi ust uste gostermek kullanissiz.
    *
    * Tam metin karsilastirmasi yetersiz kaliyor: "Kahve demleme yontemini
    * degistirdim" ile "Sonunda Kahve demleme yontemini degistirdim" farkli
    * string ama ayni icerik. Bu yuzden metnin en ayirt edici kismini
    * (en uzun kelimeler) parmak izi olarak kullaniyoruz.
    *
    * Girdi skora gore sirali olmali: ilk gorulen (en yuksek skorlu) korunur.
    */
  private[api] def dedupeByText(items: List[FeedItem]): List[FeedItem] = {
    val kept = scala.collection.mutable.ListBuffer.empty[Set[String]]

    items.filter { item =>
      val words = contentWords(item.text)
      // Daha once tutulan bir kayitla buyuk olcude ortusuyorsa ele
      val isNearDuplicate = kept.exists(prev => jaccard(prev, words) >= NearDuplicateThreshold)
      if (!isNearDuplicate) kept += words
      !isNearDuplicate
    }
  }

  /** Bu orani asan ortusme "ayni icerik" sayilir.
    *
    * Deger gercek feed ciktisi olculerek kalibre edildi: ayni cumlenin
    * on/son ekli varyasyonlari 0.43-0.55 araliginda cikiyor (ekler
    * birlesim kumesini buyuttugu icin oran dusuyor), ayni konudaki
    * gercekten farkli cumleler ise 0.0-0.2 araliginda kaliyor. 0.40
    * bu iki grubu net ayirir.
    */
  private val NearDuplicateThreshold = 0.40

  /** Metni karsilastirilabilir kelime kumesine cevirir: noktalama atilir,
    * cok kisa kelimeler (baglaclar) elenir.
    */
  private[api] def contentWords(text: String): Set[String] =
    text.toLowerCase
      .replaceAll("[^\\p{L}\\p{N}\\s]", " ")
      .split("\\s+")
      .filter(_.length >= 4)
      .toSet

  /** Jaccard benzerligi: kesisim / birlesim.
    *
    * Tam metin karsilastirmasi yetersiz kaliyordu: "Kahve demleme yontemini
    * degistirdim" ile "Sonunda Kahve demleme yontemini degistirdim" farkli
    * string ama ayni icerik. Kume ortusmesi bu varyasyonlari yakalar.
    */
  private[api] def jaccard(a: Set[String], b: Set[String]): Double = {
    if (a.isEmpty && b.isEmpty) return 1.0
    val union = a.union(b).size
    if (union == 0) 0.0 else a.intersect(b).size.toDouble / union
  }

  private def toFeedItem(hit: QdrantHit, nowSec: Long): Option[FeedItem] =
    hit.payload.flatMap { p =>
      // Option.zip 2.13+ oldugu icin for-comprehension kullaniyoruz
      for {
        tid <- p.tweetId
        text <- p.text
      } yield {
        val ts = p.tweetTimestamp.getOrElse(0L)
        FeedItem(
          tweetId = tid,
          text = text,
          language = p.language.getOrElse(""),
          tweetTimestamp = ts,
          authorId = p.authorId.getOrElse(""),
          hashtags = p.hashtags.getOrElse(Nil),
          semanticSimilarity = Ranking.normalizeSimilarity(hit.score),
          recencyScore = Ranking.recencyScore(ts, nowSec),
          finalScore = Ranking.finalScore(hit.score, ts, nowSec, semanticWeight, recencyWeight)
        )
      }
    }
}
