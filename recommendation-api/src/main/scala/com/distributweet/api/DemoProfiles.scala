package com.distributweet.api

object DemoProfiles {
  val users: List[DemoUser] =
    List(
      DemoUser(
        userId = "burak",
        displayName = "Burak",
        interests = List(
          "Scala distributed systems",
          "Apache Spark structured streaming",
          "Kafka consumer reliability",
          "large language model inference",
          "CUDA and GPU programming"
        )
      ),
      DemoUser(
        userId = "deniz",
        displayName = "Deniz",
        interests = List(
          "football transfer news",
          "Barcelona midfield signings",
          "Formula 1 race strategy",
          "European football tactics"
        )
      ),
      DemoUser(
        userId = "aylin",
        displayName = "Aylin",
        interests = List(
          "Turkish politics",
          "municipal policy debates",
          "election analysis",
          "public institutions in Turkey"
        )
      ),
      DemoUser(
        userId = "mert",
        displayName = "Mert",
        interests = List(
          "machine learning systems",
          "vector databases",
          "recommendation retrieval",
          "multilingual embeddings"
        )
      ),
      DemoUser(
        userId = "selin",
        displayName = "Selin",
        interests = List(
          "sourdough bread recipes",
          "home cooking techniques",
          "coffee brewing",
          "urban gardening"
        )
      )
    )
}
