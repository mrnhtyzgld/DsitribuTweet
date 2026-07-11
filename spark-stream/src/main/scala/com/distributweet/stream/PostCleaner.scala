package com.distributweet.stream

import org.apache.spark.sql.{Column, DataFrame}
import org.apache.spark.sql.functions._

object PostCleaner {
  def cleanKafkaValues(input: DataFrame, config: PostCleanerConfig): DataFrame = {
    val parsed =
      input
        .selectExpr("CAST(value AS STRING) AS rawJson")
        .select(from_json(col("rawJson"), PostEventSchema.schema).as("event"))

    val cleaned =
      parsed
        .where(col("event").isNotNull)
        .select(
          trim(col("event.eventId")).as("eventId"),
          trim(col("event.postId")).as("postId"),
          trim(col("event.authorId")).as("authorId"),
          trim(col("event.text")).as("text"),
          lower(trim(col("event.language"))).as("language"),
          to_timestamp(col("event.createdAt")).as("createdAt"),
          to_timestamp(col("event.ingestedAt")).as("ingestedAt"),
          trim(col("event.source")).as("source")
        )
        .where(requiredString("eventId"))
        .where(requiredString("postId"))
        .where(requiredString("authorId"))
        .where(requiredString("text"))
        .where(length(col("text")) >= lit(config.minTextLength))
        .where(col("language").isin(config.acceptedLanguages.toSeq: _*))
        .where(col("createdAt").isNotNull)
        .where(col("ingestedAt").isNotNull)
        .withColumn("cleanedAt", current_timestamp())

    cleaned
      .withWatermark("createdAt", config.watermarkDelay)
      .dropDuplicates("postId")
  }

  def toKafkaOutput(cleaned: DataFrame): DataFrame =
    cleaned.select(
      col("postId").cast("string").as("key"),
      to_json(
        struct(
          col("eventId"),
          col("postId"),
          col("authorId"),
          col("text"),
          col("language"),
          date_format(col("createdAt"), "yyyy-MM-dd'T'HH:mm:ss'Z'").as("createdAt"),
          date_format(col("ingestedAt"), "yyyy-MM-dd'T'HH:mm:ss'Z'").as("ingestedAt"),
          col("source")
        )
      ).as("value")
    )

  def withArchivePartitions(cleaned: DataFrame): DataFrame =
    cleaned
      .withColumn("date", to_date(col("createdAt")))
      .withColumn("hour", hour(col("createdAt")))

  private def requiredString(name: String): Column =
    col(name).isNotNull && length(trim(col(name))) > 0
}
