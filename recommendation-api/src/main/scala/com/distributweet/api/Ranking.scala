package com.distributweet.api

import java.time.{Duration, Instant}
import scala.collection.mutable

object Ranking {
  def rank(candidates: List[Candidate], now: Instant, limit: Int, maxPostAgeHours: Double): List[FeedItem] = {
    val fresh =
      candidates
        .filter(candidate => ageHours(candidate, now) <= maxPostAgeHours)
        .sortBy(candidate => -candidate.semanticScore)

    val selected = mutable.ListBuffer.empty[FeedItem]
    val remaining = mutable.ListBuffer.from(fresh)

    while (selected.length < limit && remaining.nonEmpty) {
      val recentAuthors = selected.takeRight(2).map(_.authorId).toSet
      val scored =
        remaining.map { candidate =>
          val item = score(candidate, now, recentAuthors)
          candidate -> item
        }
      val (bestCandidate, bestItem) = scored.maxBy { case (_, item) => item.finalScore }
      selected += bestItem
      remaining -= bestCandidate
    }

    selected.toList
  }

  def score(candidate: Candidate, now: Instant, recentAuthors: Set[String]): FeedItem = {
    val recency = math.exp(-ageHours(candidate, now) / 24.0)
    val penalty = if (recentAuthors.contains(candidate.authorId)) 0.10 else 0.0
    val finalScore = 0.85 * candidate.semanticScore + 0.15 * recency - penalty
    FeedItem(
      postId = candidate.postId,
      text = candidate.text,
      authorId = candidate.authorId,
      semanticScore = round(candidate.semanticScore),
      recencyScore = round(recency),
      finalScore = round(finalScore),
      createdAt = Instant.ofEpochSecond(candidate.createdAt).toString
    )
  }

  private def ageHours(candidate: Candidate, now: Instant): Double = {
    val created = Instant.ofEpochSecond(candidate.createdAt)
    val duration = Duration.between(created, now)
    math.max(0.0, duration.toMillis.toDouble / 3600000.0)
  }

  private def round(value: Double): Double =
    BigDecimal(value).setScale(6, BigDecimal.RoundingMode.HALF_UP).toDouble
}
