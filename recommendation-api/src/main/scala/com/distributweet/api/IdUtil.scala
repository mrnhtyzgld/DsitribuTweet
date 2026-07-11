package com.distributweet.api

import java.nio.charset.StandardCharsets
import java.util.UUID

object IdUtil {
  def postPointId(postId: String): String =
    deterministicUuid(s"distributweet:post:$postId")

  def userPointId(userId: String): String =
    deterministicUuid(s"distributweet:user:$userId")

  private def deterministicUuid(value: String): String =
    UUID.nameUUIDFromBytes(value.getBytes(StandardCharsets.UTF_8)).toString
}
