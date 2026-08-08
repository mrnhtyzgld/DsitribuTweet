package com.bil401.common

/** RecSys 2021 TSV satirlarini parse eder ve zorunlu alan kontrolu yapar.
  *
  * Spark job'indan ayri tutuluyor ki Spark ayaga kaldirmadan test edilebilsin.
  */
object TsvParser {

  /** Bir TSV satirini parse eder.
    *
    * @return Right(RawPost) veya Left(reddedilme sebebi)
    */
  def parse(line: String): Either[String, RawPost] = {
    if (line == null || line.trim.isEmpty) return Left("bos satir")

    // limit = -1 sart: varsayilan split sondaki bos alanlari atar ve
    // son kolonlari bos olan gecerli kayitlar "eksik kolon" diye reddedilir.
    val cols = line.split("\t", -1)
    if (cols.length < RecSysSchema.ColumnCount) {
      return Left(s"eksik kolon: ${cols.length} < ${RecSysSchema.ColumnCount}")
    }

    val tweetId = cols(RecSysSchema.IdxTweetId).trim
    if (tweetId.isEmpty) return Left("tweet_id bos")

    val tokensRaw = cols(RecSysSchema.IdxTextTokens).trim
    if (tokensRaw.isEmpty) return Left("text_tokens bos")

    val tokens =
      try {
        tokensRaw.split(RecSysSchema.ListSep).filter(_.nonEmpty).map(_.trim.toInt)
      } catch {
        case _: NumberFormatException => return Left("text_tokens sayisal degil")
      }
    if (tokens.isEmpty) return Left("text_tokens bos liste")

    val language = cols(RecSysSchema.IdxLanguage).trim
    if (language.isEmpty) return Left("language bos")

    val timestamp =
      try cols(RecSysSchema.IdxTweetTimestamp).trim.toLong
      catch { case _: NumberFormatException => return Left("tweet_timestamp gecersiz") }
    if (timestamp <= 0) return Left("tweet_timestamp pozitif olmali")

    val followers =
      try cols(RecSysSchema.IdxAuthorFollowers).trim.toLong
      catch { case _: NumberFormatException => 0L }

    Right(
      RawPost(
        tweetId = tweetId,
        textTokens = tokens,
        hashtags = splitList(cols(RecSysSchema.IdxHashtags)),
        presentMedia = splitList(cols(RecSysSchema.IdxPresentMedia)),
        tweetType = cols(RecSysSchema.IdxTweetType).trim,
        language = language,
        tweetTimestamp = timestamp,
        authorId = cols(RecSysSchema.IdxAuthorId).trim,
        authorFollowerCount = followers
      )
    )
  }

  private def splitList(raw: String): Array[String] = {
    val v = if (raw == null) "" else raw.trim
    if (v.isEmpty) Array.empty
    else v.split(RecSysSchema.ListSep).filter(_.nonEmpty)
  }

  /** Parse edilmis kaydi, metni cozulmus hale getirir. */
  def toCleaned(post: RawPost, decoder: WordPieceDecoder): Either[String, CleanedPost] = {
    val text = decoder.decode(post.textTokens)
    // Cok kisa metinler embedding icin anlamsiz -- eleyelim
    if (text.length < 3) Left("decode sonrasi metin cok kisa")
    else
      Right(
        CleanedPost(
          tweetId = post.tweetId,
          text = text,
          language = post.language,
          tweetType = post.tweetType,
          tweetTimestamp = post.tweetTimestamp,
          authorId = post.authorId,
          authorFollowerCount = post.authorFollowerCount,
          hashtags = post.hashtags.toList,
          hasMedia = post.presentMedia.nonEmpty
        )
      )
  }
}
