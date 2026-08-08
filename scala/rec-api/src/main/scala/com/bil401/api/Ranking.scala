package com.bil401.api

/** Rapor §4.1'deki basit siralama formulu.
  *
  *   finalScore = 0.85 * semanticSimilarity + 0.15 * recencyScore
  *
  * Formul bilincli olarak basit tutulmustur; amac ilk asamada model
  * kalitesini en ust duzeye cikarmak degil, veri akisinin temel
  * bilesenlerini denemektir.
  */
object Ranking {

  /** Qdrant cosine skorunu [0,1] araligina tasir.
    *
    * Qdrant cosine benzerligi [-1,1] dondurur. Iki terimin ayni olcekte
    * olmasi icin normalize etmemiz gerekiyor; aksi halde negatif benzerlik
    * skorlari recency terimini bastirirdi.
    */
  def normalizeSimilarity(cosine: Double): Double = {
    val v = (cosine + 1.0) / 2.0
    math.max(0.0, math.min(1.0, v))
  }

  /** Gonderi ne kadar yeniyse o kadar yuksek skor (0,1].
    *
    * Ustel azalma, 24 saatlik yari omur: 24 saatlik bir gonderi ~0.37,
    * 48 saatlik ~0.14 alir. Gelecek tarihli gonderiler (saat farki
    * kaynakli) 1.0'a kirpilir.
    */
  def recencyScore(tweetTimestampSec: Long, nowSec: Long, halfLifeHours: Double = 24.0): Double = {
    if (tweetTimestampSec <= 0) return 0.0
    val ageHours = (nowSec - tweetTimestampSec).toDouble / 3600.0
    if (ageHours <= 0) 1.0
    else math.exp(-ageHours / halfLifeHours)
  }

  /** Nihai skor. Agirliklar disaridan verilebilir (env ile ayarlanabilir). */
  def finalScore(
      cosine: Double,
      tweetTimestampSec: Long,
      nowSec: Long,
      semanticWeight: Double = 0.85,
      recencyWeight: Double = 0.15
  ): Double =
    semanticWeight * normalizeSimilarity(cosine) +
      recencyWeight * recencyScore(tweetTimestampSec, nowSec)
}
