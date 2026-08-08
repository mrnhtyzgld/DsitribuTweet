package com.bil401.cleaner

import com.bil401.common._
import io.circe.syntax._
import org.apache.spark.sql.functions._
import org.apache.spark.sql.{Dataset, SparkSession}

/** Spark Structured Streaming isi: posts.raw -> posts.cleaned
  *
  * Rapor §3.3'teki akis:
  *   Kafka posts.raw
  *     -> TSV parse et
  *     -> zorunlu alanlari kontrol et
  *     -> token ID'leri metne cevir
  *     -> tweetId tekrarlarini kaldir
  *     -> Kafka posts.cleaned
  *
  * Bu is oneri karari vermez; gorevi yalnizca veri akisini guvenilir ve
  * duzenli hale getirmektir.
  */
object CleanerJob {

  def main(args: Array[String]): Unit = {
    val kafkaBootstrap = env("KAFKA_BOOTSTRAP", "kafka:9092")
    val sourceTopic    = env("SOURCE_TOPIC", "posts.raw")
    val sinkTopic      = env("SINK_TOPIC", "posts.cleaned")
    val checkpointDir  = env("CHECKPOINT_DIR", "/checkpoints")
    val vocabPath      = env("VOCAB_PATH", "/app/vocab.txt")

    val spark = SparkSession
      .builder()
      .appName("tweet-recsys-cleaner")
      // Kucuk demo veri seti icin 200 shuffle partition asiri; 6 yeterli
      // (2 worker x 2 core = 4 slot)
      .config("spark.sql.shuffle.partitions", "6")
      .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")
    import spark.implicits._

    // Vocab'i bir kez okuyup executor'lara broadcast ediyoruz.
    // Her satirda dosyadan okumak felaket olurdu.
    val decoder   = WordPieceDecoder.fromFile(vocabPath)
    val bDecoder  = spark.sparkContext.broadcast(decoder)
    println(s"[cleaner] vocab yuklendi: ${decoder.vocabSize} token ($vocabPath)")

    // Reddedilen kayitlari saymak icin accumulator'lar
    val rejected = spark.sparkContext.longAccumulator("rejected_records")
    val accepted = spark.sparkContext.longAccumulator("accepted_records")

    val raw = spark.readStream
      .format("kafka")
      .option("kafka.bootstrap.servers", kafkaBootstrap)
      .option("subscribe", sourceTopic)
      .option("startingOffsets", "earliest")
      // Batch basina sinir: bellek patlamasini onler
      .option("maxOffsetsPerTrigger", "2000")
      .load()

    val cleaned: Dataset[CleanedPost] = raw
      .selectExpr("CAST(value AS STRING) AS line")
      .as[String]
      .flatMap { line =>
        TsvParser.parse(line) match {
          case Left(_) =>
            rejected.add(1)
            None
          case Right(post) =>
            TsvParser.toCleaned(post, bDecoder.value) match {
              case Left(_) =>
                rejected.add(1)
                None
              case Right(c) =>
                accepted.add(1)
                Some(c)
            }
        }
      }

    // Dedup: ayni tweetId tekrar gelirse birini tut.
    // Watermark ZORUNLU -- olmadan streaming dedup state'i sinirsiz buyur.
    val deduped = cleaned
      .withColumn("eventTime", to_timestamp(from_unixtime($"tweetTimestamp")))
      .withWatermark("eventTime", "10 minutes")
      .dropDuplicates("tweetId")
      .drop("eventTime")
      .as[CleanedPost]

    // Kafka sink key/value bekler: key = tweetId (partition dagilimi icin)
    val output = deduped.map { p =>
      (p.tweetId, p.asJson.noSpaces)
    }.toDF("key", "value")

    val query = output.writeStream
      .format("kafka")
      .option("kafka.bootstrap.servers", kafkaBootstrap)
      .option("topic", sinkTopic)
      .option("checkpointLocation", checkpointDir)
      .outputMode("append")
      .start()

    println(s"[cleaner] basladi: $sourceTopic -> $sinkTopic (checkpoint: $checkpointDir)")

    // Ilerlemeyi periyodik logla -- demo sirasinda ne oldugunu gormek icin
    val monitor = new Thread(() => {
      while (query.isActive) {
        Thread.sleep(30000)
        Option(query.lastProgress).foreach { p =>
          println(
            s"[cleaner] batch=${p.batchId} girdi=${p.numInputRows} " +
              s"kabul=${accepted.value} red=${rejected.value}"
          )
        }
      }
    })
    monitor.setDaemon(true)
    monitor.start()

    query.awaitTermination()
  }

  private def env(key: String, default: String): String =
    sys.env.getOrElse(key, default)
}
