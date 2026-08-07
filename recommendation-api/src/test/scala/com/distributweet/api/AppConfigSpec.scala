package com.distributweet.api

import org.scalatest.funsuite.AnyFunSuite

class AppConfigSpec extends AnyFunSuite {
  test("default max post age keeps bundled demo data visible across restarts") {
    val config = AppConfig.fromEnv(Map.empty)

    assert(config.maxPostAgeHours == 24.0 * 90.0)
  }

  test("environment can override max post age") {
    val config = AppConfig.fromEnv(Map("MAX_POST_AGE_HOURS" -> "12"))

    assert(config.maxPostAgeHours == 12.0)
  }
}
