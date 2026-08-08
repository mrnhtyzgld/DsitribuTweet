package com.bil401.common

import scala.io.Source

/** mBERT token ID'lerini tekrar metne cevirir.
  *
  * RecSys 2021 veri setinde tweet metni duz metin olarak degil,
  * bert-base-multilingual-cased tokenizer'inin urettigi token ID listesi
  * olarak yayinlanmistir (gizlilik gerekcesiyle). Embedding asamasinda
  * anlamli bir metne ihtiyacimiz var, cunku kullanici ilgi alanlari duz
  * metin olarak geliyor ve ikisinin ayni vektor uzayini paylasmasi gerekiyor.
  *
  * JVM tarafinda Python tokenizer'i calistirmak yerine vocab.txt'ten
  * id -> token haritasi kurup WordPiece birlestirmesini kendimiz yapiyoruz.
  * Bu, agir bir bagimlilik eklemeden ayni sonucu verir.
  *
  * @param vocab satir numarasi = token id olacak sekilde token dizisi
  */
class WordPieceDecoder(vocab: Array[String]) extends Serializable {

  /** Ozel token'lar decode ciktisinda gorunmemeli. */
  private val specialTokens: Set[String] =
    Set("[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]")

  /** Token ID listesini okunabilir metne cevirir.
    *
    * WordPiece'te "##" onekli parcalar bir onceki kelimeye bitisir:
    *   ["ku", "##ral"] -> "kural"
    */
  def decode(ids: Array[Int]): String = {
    val sb = new StringBuilder
    var first = true

    var i = 0
    while (i < ids.length) {
      val id = ids(i)
      if (id >= 0 && id < vocab.length) {
        val token = vocab(id)
        if (!specialTokens.contains(token)) {
          if (token.startsWith("##")) {
            // Onceki kelimenin devami -- bosluk koymadan ekle
            sb.append(token.substring(2))
          } else {
            if (!first) sb.append(' ')
            sb.append(token)
            first = false
          }
        }
      }
      i += 1
    }
    sb.toString.trim
  }

  def vocabSize: Int = vocab.length
}

object WordPieceDecoder {

  /** vocab.txt dosyasindan yukler. Dosyada her satir bir token'dir ve
    * satir numarasi (0-indexed) o token'in ID'sidir.
    */
  def fromFile(path: String): WordPieceDecoder = {
    // scala.util.Using 2.13+ ozelligi; 2.12'de try/finally kullaniyoruz
    val source = Source.fromFile(path, "UTF-8")
    val tokens =
      try source.getLines().toArray
      finally source.close()

    require(tokens.nonEmpty, s"vocab dosyasi bos: $path")
    new WordPieceDecoder(tokens)
  }

  /** Testler icin dogrudan token dizisinden kurar. */
  def fromTokens(tokens: Array[String]): WordPieceDecoder =
    new WordPieceDecoder(tokens)
}
