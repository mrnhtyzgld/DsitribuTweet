package com.bil401.common

class WordPieceDecoderSuite extends munit.FunSuite {

  // Kucuk sahte vocab: index = token id
  private val vocab = Array(
    "[PAD]",    // 0
    "[UNK]",    // 1
    "[CLS]",    // 2
    "[SEP]",    // 3
    "[MASK]",   // 4
    "Spark",    // 5
    "ile",      // 6
    "veri",     // 7
    "##ler",    // 8
    "##i",      // 9
    "isleme",   // 10
    "GPU"       // 11
  )

  private val decoder = WordPieceDecoder.fromTokens(vocab)

  test("basit token dizisi metne cevrilir") {
    assertEquals(decoder.decode(Array(5, 6, 7)), "Spark ile veri")
  }

  test("## onekli parcalar onceki kelimeye bitisir") {
    // veri + ##ler + ##i -> "verileri"
    assertEquals(decoder.decode(Array(7, 8, 9)), "verileri")
  }

  test("ozel token'lar ciktida gorunmez") {
    // [CLS] Spark ile [SEP]
    assertEquals(decoder.decode(Array(2, 5, 6, 3)), "Spark ile")
  }

  test("karisik ornek: ozel token + wordpiece") {
    // [CLS] Spark ile veri ##ler ##i isleme [SEP]
    assertEquals(
      decoder.decode(Array(2, 5, 6, 7, 8, 9, 10, 3)),
      "Spark ile verileri isleme"
    )
  }

  test("bos dizi bos string verir") {
    assertEquals(decoder.decode(Array.empty[Int]), "")
  }

  test("sadece ozel token iceren dizi bos string verir") {
    assertEquals(decoder.decode(Array(2, 3, 0)), "")
  }

  test("vocab disi id'ler sessizce atlanir") {
    // 9999 vocab disinda -- patlamamali
    assertEquals(decoder.decode(Array(5, 9999, 6)), "Spark ile")
  }

  test("negatif id patlatmaz") {
    assertEquals(decoder.decode(Array(-1, 5)), "Spark")
  }

  test("parse + decode birlikte calisir") {
    val sep = TweetFeatureSchema.ListSep
    val cols = Array.fill(TweetFeatureSchema.ColumnCount)("")
    cols(TweetFeatureSchema.IdxTextTokens) = s"2${sep}5${sep}6${sep}7${sep}8${sep}9${sep}3"
    cols(TweetFeatureSchema.IdxTweetId) = "t1"
    cols(TweetFeatureSchema.IdxLanguage) = "tr"
    cols(TweetFeatureSchema.IdxTweetTimestamp) = "1700000000"
    cols(TweetFeatureSchema.IdxTweetType) = "TopLevel"
    cols(TweetFeatureSchema.IdxAuthorId) = "a1"
    cols(TweetFeatureSchema.IdxAuthorFollowers) = "10"

    val post = TsvParser.parse(cols.mkString("\t")).toOption.get
    val cleaned = TsvParser.toCleaned(post, decoder).toOption.get

    assertEquals(cleaned.text, "Spark ile verileri")
    assertEquals(cleaned.tweetId, "t1")
    assertEquals(cleaned.hasMedia, false)
  }

  test("cok kisa decode sonucu reddedilir") {
    val sep = TweetFeatureSchema.ListSep
    val cols = Array.fill(TweetFeatureSchema.ColumnCount)("")
    cols(TweetFeatureSchema.IdxTextTokens) = s"2${sep}3" // sadece ozel token'lar
    cols(TweetFeatureSchema.IdxTweetId) = "t2"
    cols(TweetFeatureSchema.IdxLanguage) = "tr"
    cols(TweetFeatureSchema.IdxTweetTimestamp) = "1700000000"

    val post = TsvParser.parse(cols.mkString("\t")).toOption.get
    assert(TsvParser.toCleaned(post, decoder).isLeft)
  }
}
