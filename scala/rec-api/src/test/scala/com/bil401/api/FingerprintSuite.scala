package com.bil401.api

import cats.effect.IO
import cats.effect.unsafe.implicits.global
import cats.effect.Ref

/** Feed'deki yakin-tekrar eleme mantiginin testleri.
  *
  * Ureteç sinirli bir sablon havuzundan cektigi icin ayni cumlenin
  * on/son ekli varyasyonlari feed'de yan yana cikiyordu. Bu testler
  * kume ortusmesine dayali elemenin dogru calistigini dogrular.
  */
class FingerprintSuite extends munit.FunSuite {

  private val routes: Routes = {
    val ref = Ref.of[IO, Map[String, Vector[Float]]](Map.empty).unsafeRunSync()
    // Istemciler bu testlerde cagrilmiyor
    new Routes(null, null, ProfileStore(ref), 0.85, 0.15)
  }

  private def sim(a: String, b: String): Double =
    routes.jaccard(routes.contentWords(a), routes.contentWords(b))

  private val base = "Kahve demleme yontemini degistirdim tat farki inanilmaz"

  /** Routes icindeki esikle ayni tutulmali. */
  private val T = 0.40

  // Asagidaki metinler gercek feed ciktisindan alinmistir -- ureteç
  // on/son ekleri bu sekilde uretiyor.

  test("son ek eklenmis metin yakin tekrar sayilir") {
    val a = s"$base Tavsiye ederim ."
    val b = s"Kisa not : $base Devam edecegim ."
    assert(sim(a, b) >= T, s"jaccard=${sim(a, b)}")
  }

  test("uzun son ekli varyasyon yakin tekrar sayilir") {
    val a = s"$base Tavsiye ederim ."
    val b = s"Nihayet ! $base Baska fikri olan var mi ?"
    assert(sim(a, b) >= T, s"jaccard=${sim(a, b)}")
  }

  test("iki farkli on/son ekli varyasyon birbirinin tekrari sayilir") {
    val a = s"Itiraf ediyorum : $base Hala ogreniyorum ."
    val b = s"Nihayet ! $base Baska fikri olan var mi ?"
    assert(sim(a, b) >= T, s"jaccard=${sim(a, b)}")
  }

  test("farkli konudaki metin yakin tekrar sayilmaz") {
    val b = "Kubernetes uzerinde mikroservis dagitimi beklediginden kolaymis"
    assert(sim(base, b) < T, s"jaccard=${sim(base, b)}")
  }

  test("ayni konudaki farkli cumle yakin tekrar sayilmaz") {
    val b = "Bu tarifte tereyagi yerine zeytinyagi kullanmak daha iyi sonuc verdi"
    assert(sim(base, b) < T, s"jaccard=${sim(base, b)}")
  }

  test("ortak kelime iceren farkli cumleler ayri kalir") {
    // Ikisinde de "nihayet" geciyor ama icerik farkli
    val a = "Ekmek mayasini besledim ve nihayet duzgun kabardi"
    val b = "Mangal keyfi icin hava nihayet uygun hale geldi"
    assert(sim(a, b) < T, s"jaccard=${sim(a, b)}")
  }

  test("noktalama ve buyuk/kucuk harf onemsiz") {
    assertEquals(
      routes.contentWords("Verteilte Systeme, sind FASZINIEREND!"),
      routes.contentWords("verteilte systeme sind faszinierend")
    )
  }

  test("bos metin patlatmaz") {
    assertEquals(routes.contentWords(""), Set.empty[String])
    assertEqualsDouble(routes.jaccard(Set.empty, Set.empty), 1.0, 1e-9)
  }

  test("jaccard sinir degerleri") {
    assertEqualsDouble(routes.jaccard(Set("a", "b"), Set("a", "b")), 1.0, 1e-9)
    assertEqualsDouble(routes.jaccard(Set("a"), Set("b")), 0.0, 1e-9)
    assertEqualsDouble(routes.jaccard(Set("a", "b"), Set("a")), 0.5, 1e-9)
  }

  test("dedupeByText en yuksek skorlu kaydi korur") {
    def item(id: String, text: String, score: Double) =
      FeedItem(id, text, "tr", 1700000000L, "a", Nil, score, 1.0, score)

    val input = List(
      item("1", s"$base Tavsiye ederim .", 0.9),
      item("2", s"Kisa not : $base Devam edecegim .", 0.8),
      item("3", "Kubernetes uzerinde mikroservis dagitimi beklediginden kolaymis", 0.7)
    )

    val out = routes.dedupeByText(input)
    assertEquals(out.length, 2)
    assertEquals(out.head.tweetId, "1") // en yuksek skorlu korunmali
    assertEquals(out(1).tweetId, "3")
  }

  test("dedupeByText farkli icerikleri korur") {
    def item(id: String, text: String) =
      FeedItem(id, text, "tr", 1700000000L, "a", Nil, 0.5, 1.0, 0.5)

    val input = List(
      item("1", "Kafka partition sayisini artirinca throughput yukseldi"),
      item("2", "Marathon training week three and my legs have opinions"),
      item("3", "Yeni albumu bastan sona dinledim ve produksiyon muhtesem")
    )
    assertEquals(routes.dedupeByText(input).length, 3)
  }
}
