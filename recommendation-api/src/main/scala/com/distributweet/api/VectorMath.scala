package com.distributweet.api

object VectorMath {
  def averageAndNormalize(vectors: List[List[Double]]): Either[String, List[Double]] =
    vectors match {
      case Nil => Left("at least one vector is required")
      case head :: _ if head.isEmpty => Left("vectors must not be empty")
      case _ if vectors.exists(_.length != vectors.head.length) => Left("all vectors must have the same dimension")
      case _ =>
        val size = vectors.head.length
        val averaged =
          (0 until size).map { index =>
            vectors.map(_(index)).sum / vectors.length.toDouble
          }.toList
        normalize(averaged).toRight("average vector has zero magnitude")
    }

  def normalize(vector: List[Double]): Option[List[Double]] = {
    val magnitude = math.sqrt(vector.map(v => v * v).sum)
    if (magnitude == 0.0) None else Some(vector.map(_ / magnitude))
  }
}
