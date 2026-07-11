package com.distributweet.api

import org.scalatest.funsuite.AnyFunSuite

class IdUtilSpec extends AnyFunSuite {
  test("user and post point ids are deterministic UUIDs") {
    assert(IdUtil.userPointId("burak") == IdUtil.userPointId("burak"))
    assert(IdUtil.postPointId("post-1") == IdUtil.postPointId("post-1"))
    assert(IdUtil.userPointId("burak") != IdUtil.postPointId("burak"))
    assert(IdUtil.userPointId("burak").length == 36)
  }
}
