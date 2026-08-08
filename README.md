# Canlı Veri Akışı Üzerinde İçerik Tabanlı Dağıtık Öneri Sistemi

BIL401 dönem projesi — takip grafiği kullanmadan, kullanıcının belirttiği ilgi
alanları ile sisteme akan gönderiler arasındaki **anlamsal benzerliği** ölçerek
kişiselleştirilmiş bir akış üretir.

Arda Onat Acar (231401010) · Nihat Emre Yüzügüldü (221401009)

---

## Mimari

```
data-generator (Python)          RecSys 2021 şemasında TSV kayıtları
        │
        ▼
   Kafka: posts.raw              3 partition
        │
        ▼
   spark-cleaner (Scala)         Structured Streaming, 2 worker
        │                        parse → doğrula → token decode → dedup
        ▼
   Kafka: posts.cleaned          3 partition
        │
        ▼
   embedding-worker (Python)     2 replica, aynı consumer group
        │                        multilingual MiniLM → 384d vektör
        ▼
   Qdrant                        collection: posts (cosine, 384d)
        ▲
        │ search
   rec-api (Scala/http4s)        /users/{id}/interests · /users/{id}/feed
```

Tüm servisler tek makinede **pseudo-distributed** çalışır: Kafka partition'ları,
Spark executor'ları ve embedding worker'ları gerçekten paralel çalışır, sadece
aynı fiziksel makine üzerindedir.

---

## Veri seti hakkında — önemli not

Proje **RecSys 2021 Challenge** (Twitter) veri setini hedefliyordu. İki engel çıktı:

1. **Orijinal dağıtım portalı kapandı.** Veri `recsys-twitter.com` üzerinden,
   onaylı bir Twitter Developer hesabıyla dağıtılıyordu. Domain artık veri portalı
   değil. Veri seti platformla sürekli senkron tutuluyordu (silinen tweetler veri
   setinden de çıkarılıyordu — [makale §3.3](https://arxiv.org/pdf/2109.08245)),
   bu da X'in API politikası değiştikten sonra sürdürülemez hale geldi.

2. **Veri setinin odağı farklı.** RecSys 2021 *engagement prediction* için
   tasarlanmış (like/retweet olasılığı, ~200 GB, ~1 milyar satır). Bu proje ise
   içerik tabanlı anlamsal benzerlik yapıyor ve takip grafiğini açıkça kapsam dışı
   bırakıyor — yani veri setinin asıl değerli kısmı (engagement etiketleri,
   follower grafiği) zaten kullanılmayacaktı.

**Yaklaşım:** Veri setinin **şeması** referans alındı, veri sentetik olarak üretiliyor.

`data-generator/generator.py`, [RecSys 2021 makalesinin Table 1](https://arxiv.org/pdf/2109.08245)
şemasını birebir uygular:

- Aynı 20 kolon, aynı sıra, TSV formatı, `0x01` liste ayracı
- `text_tokens` alanı **gerçek** `bert-base-multilingual-cased` token ID'leri
  içerir — sentetik metin gerçek tokenizer'dan geçirilir

Bu sadakat sayesinde gerçek veriye erişim sağlanırsa hattın geri kalanı hiç
değişmez; yalnızca producer dosyadan okumaya geçer:

```bash
python producer.py --input-tsv /path/to/part-00000
```

### Metin neden token ID olarak geliyor?

RecSys 2021, gizlilik gerekçesiyle tweet metnini düz metin olarak yayınlamadı;
metin mBERT tokenizer'ından geçirilip **token ID listesi** olarak dağıtıldı.

Bu bizim için önemli: kullanıcı ilgi alanları düz metin olarak geliyor, tweetler
ise token ID olarak. İkisinin aynı vektör uzayını paylaşması için token'ları
metne geri çevirmemiz gerekiyor. Bu, Spark katmanında
[`WordPieceDecoder`](scala/common/src/main/scala/com/bil401/common/WordPieceDecoder.scala)
ile yapılır — `vocab.txt`'ten `id → token` haritası kurulup WordPiece `##`
birleştirmesi uygulanır (JVM'de Python tokenizer çalıştırmaya gerek kalmadan).

---

## Çalıştırma

> Başlatma/durdurma, sonuçları görme ve sorun giderme için ayrıntılı rehber:
> **[KULLANIM.md](KULLANIM.md)**

**Gereksinim:** Docker Desktop (çalışır durumda), ~6 GB boş RAM.

```bash
docker compose up -d --build
```

İlk build uzun sürer (~10-15 dk): Scala bağımlılıkları indirilir, embedding
modeli (~470 MB) ve mBERT vocab dosyası image içine gömülür. Sonraki
başlatmalar saniyeler sürer ve **internet gerektirmez**.

Durumu izlemek için:

```bash
docker compose ps
docker compose logs -f spark-cleaner
docker compose logs -f embedding-worker
```

### Uçtan uca doğrulama

```bash
./scripts/smoke-test.sh
```

Rapordaki 9 adımın her birini kontrol eder: producer yazıyor mu, Spark
temizliyor mu, worker vektörlüyor mu, API anlamlı sonuç dönüyor mu.

### Manuel deneme

```bash
# İlgi alanlarını kaydet
curl -X POST localhost:8081/users/user-1/interests \
  -H 'Content-Type: application/json' \
  -d '{"interests":["GPU programlama","dagitik sistemler"]}'

# Kişiselleştirilmiş akışı al
curl 'localhost:8081/users/user-1/feed?limit=10'
```

Dönen her gönderide `semanticSimilarity`, `recencyScore` ve `finalScore` ayrı
ayrı görünür — sıralamanın neden o şekilde olduğu izlenebilir.

Veri üreteci tweetleri 10 konu havuzundan üretir (teknoloji, spor, müzik, yemek,
seyahat, oyun, bilim, finans, sağlık, sanat). Bu, önerinin doğru çalıştığını
gözle doğrulanabilir kılar: teknoloji ilgi alanı giren kullanıcıya teknoloji
tweetleri dönmeli, yemek girene yemek tweetleri.

### Dağıtıklık kanıtı (rapor §6)

```bash
./scripts/show-distribution.sh
```

Partition dağılımını, consumer group üyelerini ve Spark worker'larını gösterir.

Ölçekleme testi:

```bash
docker compose up -d --scale embedding-worker=3
./scripts/show-distribution.sh   # partition'lar 3 worker'a yeniden dağılır
```

### Arayüzler

| Servis | Adres |
|---|---|
| Recommendation API | http://localhost:8081 |
| Spark master UI | http://localhost:8080 |
| Spark application UI | http://localhost:4040 |
| Qdrant dashboard | http://localhost:6333/dashboard |
| Embedding servisi | http://localhost:8000/health |

---

## API

### `POST /users/{userId}/interests`

İlgi alanlarını vektörleştirip kullanıcı profili oluşturur (rapor §4, adım 6-7).

```json
{ "interests": ["Scala", "dağıtık sistemler", "GPU programlama"] }
```

Her ilgi alanı ayrı ayrı embed edilir, vektörlerin ortalaması alınıp normalize
edilir. Normalizasyon önemli: aksi halde ilgi alanı sayısı değiştikçe vektörün
boyu değişir ve cosine skorları kayar.

### `GET /users/{userId}/feed?limit=20`

Profil vektörüne en yakın gönderileri döndürür (rapor §4, adım 8-9).

Sıralama formülü (rapor §4.1):

```
finalScore = 0.85 × semanticSimilarity + 0.15 × recencyScore
recencyScore = exp(-yaşSaat / 24)
```

Qdrant cosine skoru `[-1,1]` aralığında döner; `(x+1)/2` ile `[0,1]`'e
normalize edilir ki iki terim aynı ölçekte toplanabilsin. Ağırlıklar
`SEMANTIC_WEIGHT` / `RECENCY_WEIGHT` ile değiştirilebilir.

**Yakın-tekrar eleme:** Feed katmanı, neredeyse aynı içerikli gönderileri
eler (kelime kümeleri arası Jaccard benzerliği ≥ 0.40). Buna ihtiyaç var
çünkü Spark'taki dedup `tweetId` bazlı — farklı kullanıcıların aynı metni
paylaşması geçerli ve ayrı kayıtlardır, ama feed'de aynı cümleyi üst üste
göstermek kullanışsız. Eşik gerçek feed çıktısı ölçülerek kalibre edildi:
aynı içeriğin varyasyonları 0.43–0.55, farklı içerikler 0.0–0.08 aralığında.

Eleme adayların çoğunu düşürebildiği için Qdrant'tan geniş bir havuz
(400 aday) çekilip sıralama sonrası `limit`'e indirilir.

---

## Kullanılan imajlar

| Servis | İmaj | Not |
|---|---|---|
| Kafka | `apache/kafka:3.8.0` | KRaft modu, Zookeeper yok |
| Spark | `apache/spark:3.5.4` | standalone master + 2 worker |
| Qdrant | `qdrant/qdrant:v1.12.4` | |
| Scala build | `sbtscala/scala-sbt:...2.12.21` | multi-stage build |

Not: Bitnami 2025'te Docker Hub kataloğunu kapattığı için `bitnami/kafka` ve
`bitnami/spark` imajları artık çekilemiyor; resmi Apache imajları kullanılıyor.
Bunlar Java 17 tabanlı olduğundan Spark'a `--add-opens` JVM izinleri veriliyor
(`scala/submit.sh` ve compose'daki `SPARK_DAEMON_JAVA_OPTS`).

## Testler

Birim testleri Docker build'in parçasıdır — mantık bozuksa image oluşmaz.

```bash
cd scala && sbt test    # sbt kuruluysa yerelde de çalışır
```

Kapsam: TSV parse ve doğrulama kuralları (`TsvParserSuite`), WordPiece decode
(`WordPieceDecoderSuite`), sıralama formülü (`RankingSuite`).

### Scala sürümü notu

Proje **Scala 2.12** kullanıyor (Spark ekosistemiyle en uyumlu sürüm). 2.13'e
özgü şu API'ler burada **derlenmez** — 2.12 karşılıklarını kullanın:

| 2.13 | 2.12 karşılığı |
|---|---|
| `scala.util.Using` | `try / finally` ile `source.close()` |
| `Either.orElse` | `match { case Right(x) => ...; case Left(_) => ... }` |
| `Option.zip` | `for { a <- optA; b <- optB } yield ...` |
| `String.toDoubleOption` | `scala.util.Try(v.toDouble).toOption` |
| `1_000_000` (alt çizgi) | `1000000` |

Ayrıca `line.split("\t")` yerine **`line.split("\t", -1)`** kullanın: limitsiz
`split` sondaki boş alanları atar ve son kolonları boş olan geçerli RecSys
kayıtları "eksik kolon" diye reddedilir (gerçek veride engagement timestamp
alanları sıklıkla boştur).

---

## Yapılandırma

Başlıca ayarlar `docker-compose.yml` içindeki `environment` blokları:

| Değişken | Servis | Varsayılan | Açıklama |
|---|---|---|---|
| `RATE_PER_SEC` | data-generator | 20 | Saniyede üretilen kayıt |
| `TOTAL_MESSAGES` | data-generator | 0 | 0 = sınırsız |
| `BATCH_SIZE` | embedding-worker | 32 | Kafka poll başına mesaj |
| `SEMANTIC_WEIGHT` | rec-api | 0.85 | Benzerlik ağırlığı |
| `RECENCY_WEIGHT` | rec-api | 0.15 | Güncellik ağırlığı |

---

## Kapsam dışı

Ara rapor §7 ile uyumlu olarak bu aşamada ele alınmayanlar: takip grafiği ve
sosyal bağlantılar, collaborative filtering, özel model eğitimi, tıklama tahmini,
güvenlik/moderasyon kuralları, üretim seviyesi hata toleransı.
