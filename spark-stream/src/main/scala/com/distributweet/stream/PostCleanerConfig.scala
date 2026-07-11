package com.distributweet.stream

final case class PostCleanerConfig(
    kafkaBootstrapServers: String,
    rawTopic: String,
    cleanedTopic: String,
    checkpointDir: String,
    archiveDir: String,
    acceptedLanguages: Set[String],
    minTextLength: Int,
    watermarkDelay: String
)

object PostCleanerConfig {
  def fromEnv(env: Map[String, String] = sys.env): PostCleanerConfig =
    PostCleanerConfig(
      kafkaBootstrapServers = env.getOrElse("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092"),
      rawTopic = env.getOrElse("RAW_TOPIC", "posts.raw"),
      cleanedTopic = env.getOrElse("CLEANED_TOPIC", "posts.cleaned"),
      checkpointDir = env.getOrElse("CHECKPOINT_DIR", "/tmp/distributweet/checkpoints/post-cleaner"),
      archiveDir = env.getOrElse("ARCHIVE_DIR", "/tmp/distributweet/data/posts"),
      acceptedLanguages = env.getOrElse("ACCEPTED_LANGUAGES", "en,tr").split(",").map(_.trim).filter(_.nonEmpty).toSet,
      minTextLength = env.get("MIN_TEXT_LENGTH").flatMap(v => scala.util.Try(v.toInt).toOption).getOrElse(12),
      watermarkDelay = env.getOrElse("WATERMARK_DELAY", "2 hours")
    )
}
