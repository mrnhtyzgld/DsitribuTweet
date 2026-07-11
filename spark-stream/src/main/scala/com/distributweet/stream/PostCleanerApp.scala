package com.distributweet.stream

import org.apache.spark.sql.SparkSession

object PostCleanerApp {
  def main(args: Array[String]): Unit = {
    val config = PostCleanerConfig.fromEnv()
    val spark =
      SparkSession
        .builder()
        .appName("distributweet-post-cleaner")
        .getOrCreate()

    spark.conf.set("spark.sql.session.timeZone", "UTC")

    val raw =
      spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", config.kafkaBootstrapServers)
        .option("subscribe", config.rawTopic)
        .option("startingOffsets", "earliest")
        .option("failOnDataLoss", "false")
        .load()

    val cleaned = PostCleaner.cleanKafkaValues(raw, config)

    val kafkaQuery =
      PostCleaner
        .toKafkaOutput(cleaned)
        .writeStream
        .format("kafka")
        .option("kafka.bootstrap.servers", config.kafkaBootstrapServers)
        .option("topic", config.cleanedTopic)
        .option("checkpointLocation", s"${config.checkpointDir}/kafka")
        .outputMode("append")
        .start()

    val archiveQuery =
      PostCleaner
        .withArchivePartitions(cleaned)
        .writeStream
        .format("parquet")
        .option("path", config.archiveDir)
        .option("checkpointLocation", s"${config.checkpointDir}/parquet")
        .partitionBy("date", "hour")
        .outputMode("append")
        .start()

    spark.streams.awaitAnyTermination()
    kafkaQuery.stop()
    archiveQuery.stop()
  }
}
