package com.distributweet.api

import org.scalatest.funsuite.AnyFunSuite

import java.time.Instant

class RankingSpec extends AnyFunSuite {
  private val now = Instant.parse("2026-07-11T15:00:00Z")

  test("score combines semantic similarity, recency, and author penalty") {
    val candidate =
      Candidate(
        postId = "post-1",
        text = "CUDA kernel optimization techniques",
        authorId = "author-1",
        language = "en",
        semanticScore = 0.9,
        createdAt = Instant.parse("2026-07-11T14:00:00Z").getEpochSecond
      )

    val noPenalty = Ranking.score(candidate, now, Set.empty)
    val withPenalty = Ranking.score(candidate, now, Set("author-1"))

    assert(noPenalty.finalScore > withPenalty.finalScore)
    assert(noPenalty.recencyScore > 0.95)
  }

  test("rank filters stale posts and respects limit") {
    val fresh =
      Candidate(
        postId = "fresh",
        text = "Fresh Spark streaming post",
        authorId = "author-1",
        language = "en",
        semanticScore = 0.8,
        createdAt = Instant.parse("2026-07-11T14:00:00Z").getEpochSecond
      )
    val stale =
      fresh.copy(postId = "stale", createdAt = Instant.parse("2026-06-01T14:00:00Z").getEpochSecond)

    val ranked = Ranking.rank(List(stale, fresh), now, limit = 10, maxPostAgeHours = 48)

    assert(ranked.map(_.postId) == List("fresh"))
  }
}
