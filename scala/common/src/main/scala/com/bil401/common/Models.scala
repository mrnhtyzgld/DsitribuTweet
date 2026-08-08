package com.bil401.common

import io.circe.generic.semiauto.{deriveDecoder, deriveEncoder}
import io.circe.{Decoder, Encoder}

/** RecSys 2021 Challenge veri semasi (Table 1).
  *
  * Kaynak: "The 2021 RecSys Challenge Dataset: Fairness is not optional"
  * https://arxiv.org/pdf/2109.08245
  *
  * Orijinal veri TSV formatindadir; liste alanlari 0x01 ile ayrilir.
  * `textTokens` duz metin degil, bert-base-multilingual-cased token ID'leridir.
  */
object RecSysSchema {

  /** Liste tipindeki alanlarin ayraci (orijinal veri setiyle ayni). */
  val ListSep: Char = 0x01.toChar

  /** Table 1'deki kolon sirasi. Producer bu sirayla yazar. */
  val Columns: Vector[String] = Vector(
    "text_tokens",
    "hashtags",
    "tweet_id",
    "present_media",
    "present_links",
    "present_domains",
    "tweet_type",
    "language",
    "tweet_timestamp",
    "engaged_with_user_id",
    "engaged_with_user_follower_count",
    "engaged_with_user_following_count",
    "engaged_with_user_is_verified",
    "engaged_with_user_account_creation",
    "engaging_user_id",
    "engaging_user_follower_count",
    "engaging_user_following_count",
    "engaging_user_is_verified",
    "engaging_user_account_creation",
    "engagee_follows_engager"
  )

  val ColumnCount: Int = Columns.size

  // Sik kullanilan kolonlarin indeksleri
  val IdxTextTokens: Int      = 0
  val IdxHashtags: Int        = 1
  val IdxTweetId: Int         = 2
  val IdxPresentMedia: Int    = 3
  val IdxTweetType: Int       = 6
  val IdxLanguage: Int        = 7
  val IdxTweetTimestamp: Int  = 8
  val IdxAuthorId: Int        = 9
  val IdxAuthorFollowers: Int = 10
}

/** Ham TSV satirindan parse edilmis kayit. */
final case class RawPost(
    tweetId: String,
    textTokens: Array[Int],
    hashtags: Array[String],
    presentMedia: Array[String],
    tweetType: String,
    language: String,
    tweetTimestamp: Long,
    authorId: String,
    authorFollowerCount: Long
)

/** Temizlenmis + metne cevrilmis kayit. posts.cleaned topic'ine JSON yazilir.
  *
  * `text` alani token ID'lerin decode edilmis halidir -- embedding worker
  * dogrudan bunu kullanir.
  */
final case class CleanedPost(
    tweetId: String,
    text: String,
    language: String,
    tweetType: String,
    tweetTimestamp: Long,
    authorId: String,
    authorFollowerCount: Long,
    hashtags: List[String],
    hasMedia: Boolean
)

object CleanedPost {
  implicit val encoder: Encoder[CleanedPost] = deriveEncoder
  implicit val decoder: Decoder[CleanedPost] = deriveDecoder
}
