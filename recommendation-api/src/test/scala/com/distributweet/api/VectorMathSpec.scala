package com.distributweet.api

import org.scalatest.funsuite.AnyFunSuite

class VectorMathSpec extends AnyFunSuite {
  test("averageAndNormalize averages and normalizes vectors") {
    val result = VectorMath.averageAndNormalize(List(List(1.0, 0.0), List(0.0, 1.0)))

    assert(result.isRight)
    val vector = result.toOption.get
    assert(math.abs(vector.head - 0.70710678) < 0.0001)
    assert(math.abs(vector(1) - 0.70710678) < 0.0001)
  }

  test("averageAndNormalize rejects mixed dimensions") {
    val result = VectorMath.averageAndNormalize(List(List(1.0), List(1.0, 2.0)))

    assert(result.isLeft)
  }
}
