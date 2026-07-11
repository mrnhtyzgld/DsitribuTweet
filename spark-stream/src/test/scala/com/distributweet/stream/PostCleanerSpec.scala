package com.distributweet.stream

import org.apache.spark.sql.SparkSession
import org.scalatest.BeforeAndAfterAll
import org.scalatest.funsuite.AnyFunSuite

class PostCleanerSpec extends AnyFunSuite with BeforeAndAfterAll {
  private var spark: SparkSession = _

  override def beforeAll(): Unit = {
    spark =
      SparkSession
        .builder()
        .appName("post-cleaner-test")
        .master("local[2]")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
  }

  override def afterAll(): Unit = {
    if (spark != null) {
      spark.stop()
    }
  }

  test("cleanKafkaValues drops malformed, short, and unsupported-language events") {
    val activeSpark = spark
    import activeSpark.implicits._

    val input =
      Seq(
        """{"eventId":"event-1","postId":"post-1","authorId":"author-1","text":"CUDA kernel optimization techniques","language":"en","createdAt":"2026-07-11T14:35:00Z","ingestedAt":"2026-07-11T14:35:01Z","source":"test"}""",
        """{"eventId":"event-2","postId":"post-2","authorId":"author-2","text":"too short","language":"en","createdAt":"2026-07-11T14:35:00Z","ingestedAt":"2026-07-11T14:35:01Z","source":"test"}""",
        """{"eventId":"event-3","postId":"post-3","authorId":"author-3","text":"A long enough post in an unsupported language","language":"de","createdAt":"2026-07-11T14:35:00Z","ingestedAt":"2026-07-11T14:35:01Z","source":"test"}""",
        """{"eventId":"""
      ).toDF("value")

    val cleaned = PostCleaner.cleanKafkaValues(input, testConfig)
    val postIds = cleaned.select("postId").as[String].collect().toSeq

    assert(postIds == Seq("post-1"))
  }

  test("cleanKafkaValues deduplicates by postId") {
    val activeSpark = spark
    import activeSpark.implicits._

    val input =
      Seq(
        """{"eventId":"event-1","postId":"post-1","authorId":"author-1","text":"CUDA kernel optimization techniques","language":"en","createdAt":"2026-07-11T14:35:00Z","ingestedAt":"2026-07-11T14:35:01Z","source":"test"}""",
        """{"eventId":"event-2","postId":"post-1","authorId":"author-1","text":"CUDA kernel optimization techniques","language":"en","createdAt":"2026-07-11T14:35:00Z","ingestedAt":"2026-07-11T14:36:01Z","source":"test"}"""
      ).toDF("value")

    val cleaned = PostCleaner.cleanKafkaValues(input, testConfig)

    assert(cleaned.count() == 1)
  }

  test("toKafkaOutput keeps a compact keyed JSON event") {
    val activeSpark = spark
    import activeSpark.implicits._

    val input =
      Seq(
        """{"eventId":"event-1","postId":"post-1","authorId":"author-1","text":"CUDA kernel optimization techniques","language":"en","createdAt":"2026-07-11T14:35:00Z","ingestedAt":"2026-07-11T14:35:01Z","source":"test"}"""
      ).toDF("value")

    val output = PostCleaner.toKafkaOutput(PostCleaner.cleanKafkaValues(input, testConfig)).collect()

    assert(output.head.getAs[String]("key") == "post-1")
    assert(output.head.getAs[String]("value").contains("CUDA kernel optimization techniques"))
  }

  private def testConfig: PostCleanerConfig =
    PostCleanerConfig(
      kafkaBootstrapServers = "unused",
      rawTopic = "posts.raw",
      cleanedTopic = "posts.cleaned",
      checkpointDir = "/tmp/checkpoints",
      archiveDir = "/tmp/archive",
      acceptedLanguages = Set("en", "tr"),
      minTextLength = 12,
      watermarkDelay = "2 hours"
    )
}
