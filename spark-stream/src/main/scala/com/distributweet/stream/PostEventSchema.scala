package com.distributweet.stream

import org.apache.spark.sql.types._

object PostEventSchema {
  val schema: StructType =
    StructType(
      Seq(
        StructField("eventId", StringType, nullable = true),
        StructField("postId", StringType, nullable = true),
        StructField("authorId", StringType, nullable = true),
        StructField("text", StringType, nullable = true),
        StructField("language", StringType, nullable = true),
        StructField("createdAt", StringType, nullable = true),
        StructField("ingestedAt", StringType, nullable = true),
        StructField("source", StringType, nullable = true)
      )
    )
}
