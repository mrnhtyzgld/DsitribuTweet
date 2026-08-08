package com.bil401.common

class TsvParserSuite extends munit.FunSuite {

  private val sep = RecSysSchema.ListSep

  /** Gecerli bir RecSys 2021 TSV satiri kurar. */
  private def row(
      tokens: String = s"101${sep}5000${sep}6000${sep}102",
      tweetId: String = "abc123",
      language: String = "tr",
      timestamp: String = "1700000000",
      hashtags: String = s"spark${sep}kafka"
  ): String = {
    val cols = Array.fill(RecSysSchema.ColumnCount)("")
    cols(RecSysSchema.IdxTextTokens) = tokens
    cols(RecSysSchema.IdxHashtags) = hashtags
    cols(RecSysSchema.IdxTweetId) = tweetId
    cols(RecSysSchema.IdxPresentMedia) = "Photo"
    cols(RecSysSchema.IdxTweetType) = "TopLevel"
    cols(RecSysSchema.IdxLanguage) = language
    cols(RecSysSchema.IdxTweetTimestamp) = timestamp
    cols(RecSysSchema.IdxAuthorId) = "author-1"
    cols(RecSysSchema.IdxAuthorFollowers) = "1234"
    cols.mkString("\t")
  }

  test("sema 20 kolon icermeli (RecSys 2021 Table 1)") {
    assertEquals(RecSysSchema.ColumnCount, 20)
  }

  test("gecerli satir parse edilir") {
    val result = TsvParser.parse(row())
    assert(result.isRight, s"parse basarisiz: $result")
    val post = result.toOption.get
    assertEquals(post.tweetId, "abc123")
    assertEquals(post.textTokens.toList, List(101, 5000, 6000, 102))
    assertEquals(post.language, "tr")
    assertEquals(post.tweetTimestamp, 1700000000L)
    assertEquals(post.hashtags.toList, List("spark", "kafka"))
    assertEquals(post.authorFollowerCount, 1234L)
    assertEquals(post.presentMedia.toList, List("Photo"))
  }

  test("bos tweet_id reddedilir") {
    assert(TsvParser.parse(row(tweetId = "")).isLeft)
  }

  test("bos text_tokens reddedilir") {
    assert(TsvParser.parse(row(tokens = "")).isLeft)
  }

  test("sayisal olmayan text_tokens reddedilir") {
    assert(TsvParser.parse(row(tokens = s"101${sep}abc")).isLeft)
  }

  test("bos language reddedilir") {
    assert(TsvParser.parse(row(language = "")).isLeft)
  }

  test("gecersiz timestamp reddedilir") {
    assert(TsvParser.parse(row(timestamp = "0")).isLeft)
    assert(TsvParser.parse(row(timestamp = "-5")).isLeft)
    assert(TsvParser.parse(row(timestamp = "yok")).isLeft)
  }

  test("eksik kolonlu satir reddedilir") {
    assert(TsvParser.parse("a\tb\tc").isLeft)
  }

  test("bos ve null satir reddedilir") {
    assert(TsvParser.parse("").isLeft)
    assert(TsvParser.parse("   ").isLeft)
    assert(TsvParser.parse(null).isLeft)
  }

  test("bos hashtag listesi bos array verir") {
    val post = TsvParser.parse(row(hashtags = "")).toOption.get
    assertEquals(post.hashtags.toList, List.empty[String])
  }
}
