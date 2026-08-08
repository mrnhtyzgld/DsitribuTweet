package com.bil401.api

class RankingSuite extends munit.FunSuite {

  private val eps = 1e-6

  test("cosine skoru [0,1] araligina tasinir") {
    assertEqualsDouble(Ranking.normalizeSimilarity(1.0), 1.0, eps)
    assertEqualsDouble(Ranking.normalizeSimilarity(0.0), 0.5, eps)
    assertEqualsDouble(Ranking.normalizeSimilarity(-1.0), 0.0, eps)
  }

  test("aralik disi cosine degerleri kirpilir") {
    assertEqualsDouble(Ranking.normalizeSimilarity(2.0), 1.0, eps)
    assertEqualsDouble(Ranking.normalizeSimilarity(-3.0), 0.0, eps)
  }

  test("recency: yeni gonderi 1.0'a yakin") {
    val now = 1700000000L
    assertEqualsDouble(Ranking.recencyScore(now, now), 1.0, eps)
  }

  test("recency: 24 saatlik gonderi ~0.368 (yari omur)") {
    val now = 1700000000L
    val dayOld = now - 24 * 3600
    assertEqualsDouble(Ranking.recencyScore(dayOld, now), math.exp(-1.0), 1e-4)
  }

  test("recency: eski gonderi yeniden dusuk skor alir") {
    val now = 1700000000L
    val fresh = Ranking.recencyScore(now - 3600, now)
    val old = Ranking.recencyScore(now - 72 * 3600, now)
    assert(fresh > old, s"taze=$fresh eski=$old")
  }

  test("recency: gecersiz timestamp 0 dondurur") {
    assertEqualsDouble(Ranking.recencyScore(0L, 1700000000L), 0.0, eps)
    assertEqualsDouble(Ranking.recencyScore(-5L, 1700000000L), 0.0, eps)
  }

  test("recency: gelecek tarihli gonderi 1.0'a kirpilir") {
    val now = 1700000000L
    assertEqualsDouble(Ranking.recencyScore(now + 3600, now), 1.0, eps)
  }

  test("finalScore rapordaki formule uyar") {
    // finalScore = 0.85 * semanticSimilarity + 0.15 * recencyScore
    val now = 1700000000L
    val cosine = 0.6
    val ts = now // taze -> recency = 1.0

    val expected = 0.85 * Ranking.normalizeSimilarity(cosine) + 0.15 * 1.0
    assertEqualsDouble(Ranking.finalScore(cosine, ts, now), expected, eps)
  }

  test("benzerlik agirligi recency'den baskin") {
    val now = 1700000000L
    // Cok benzer ama eski
    val similarOld = Ranking.finalScore(0.9, now - 96 * 3600, now)
    // Az benzer ama taze
    val dissimilarFresh = Ranking.finalScore(-0.2, now, now)
    assert(
      similarOld > dissimilarFresh,
      s"benzerlik baskin olmali: benzer/eski=$similarOld farkli/taze=$dissimilarFresh"
    )
  }

  test("esit benzerlikte taze olan kazanir") {
    val now = 1700000000L
    val fresh = Ranking.finalScore(0.5, now, now)
    val old = Ranking.finalScore(0.5, now - 48 * 3600, now)
    assert(fresh > old, s"taze=$fresh eski=$old")
  }

  test("ozel agirliklar uygulanir") {
    val now = 1700000000L
    // Sadece recency'ye bakan bir yapilandirma
    val score = Ranking.finalScore(0.5, now, now, semanticWeight = 0.0, recencyWeight = 1.0)
    assertEqualsDouble(score, 1.0, eps)
  }
}
