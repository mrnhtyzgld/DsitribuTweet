# Canlı Veri Akışı Üzerinde İçerik Tabanlı Dağıtık Öneri Sistemi

BIL401 dönem projesi — takip grafiği kullanmadan, kullanıcının belirttiği ilgi
alanları ile sisteme akan gönderiler arasındaki **anlamsal benzerliği** ölçerek
kişiselleştirilmiş bir akış üretir.

Arda Onat Acar (231401010) · Nihat Emre Yüzügüldü (221401009)

---

## Mimari

```
data-generator (Python)          Bright Data Twitter/X CSV → iç TSV kayıtları
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

## Veri Seti

Varsayılan demo artık **Bright Data Twitter/X Posts sample** kullanır:
[luminati-io/Twitter-X-dataset-samples](https://github.com/luminati-io/Twitter-X-dataset-samples).
Bu repo `twitter-posts.csv` içinde 1000 public X/Twitter gönderisi sağlar.
Alanlar arasında `id`, `user_posted`, `description`, `date_posted`,
`hashtags`, `followers`, `likes`, `reposts` ve `views` bulunur.

Bu sample, Bright Data'nın daha büyük Twitter/X Posts and Profiles veri
ürününün küçük bir parçasıdır. Databricks Marketplace üzerinde aynı veri
ailesi için 20M kayıtlık paket listelenir:
[Bright Data SAMPLE Twitter/X Data](https://marketplace.databricks.com/details/71cafc8b-8465-4dbd-9a4a-23e4be50b063/Bright-Data_SAMPLE-Twitter-X-Data-Twitter-X-Posts-and-Profiles-Datasets-20M-Records).
Akademik araştırma için daha büyük veri erişimi alınırsa aynı adapter daha
büyük CSV/Parquet export'larına uyarlanabilir.

### CSV → İç Stream Formatı

Spark tarafını sade tutmak için raw Kafka mesajları kompakt bir iç TSV feature
formatında taşınır. `data-generator/brightdata.py`, Bright Data CSV satırlarını
bu formata çevirir:

- `id` → `tweet_id`
- `description` → `bert-base-multilingual-cased` token ID listesi
- `date_posted` → Unix timestamp
- `user_posted` → hash'lenmiş author ID
- `hashtags` → `0x01` ile ayrılmış hashtag listesi
- `photos` / `videos` → media metadata
- `followers`, `following`, `is_verified` → author metadata

Yani dış veri kaynağı CSV'dir; Kafka ve Spark arasındaki iç format ise TSV'dir.
Spark cleaner token ID'leri
[`WordPieceDecoder`](scala/common/src/main/scala/com/bil401/common/WordPieceDecoder.scala)
ile tekrar metne çevirir ve `posts.cleaned` topic'ine JSON yazar. Böylece
embedding worker düz metinle çalışır.

Varsayılan Compose çalıştırması sample CSV'yi GitHub raw URL'sinden okur:

```bash
docker compose up -d --build
```

İsterseniz aynı producer yerel CSV veya önceden dönüştürülmüş iç TSV dosyası da
okuyabilir:

```bash
python data-generator/producer.py --input-csv /path/to/twitter-posts.csv --total 1000 --rate 100
python data-generator/producer.py --input-tsv /path/to/internal-feature.tsv --total 10000 --rate 200
```

---

## Çalıştırma

> Başlatma/durdurma, sonuçları görme ve sorun giderme için ayrıntılı rehber:
> **[KULLANIM.md](KULLANIM.md)**

**Gereksinim:** Docker Desktop (çalışır durumda), ~6 GB boş RAM.

```bash
docker compose up -d --build
```

İlk build uzun sürer (~10-15 dk): Scala bağımlılıkları indirilir, embedding
modeli (~470 MB) ve mBERT vocab dosyası image içine gömülür. Varsayılan demo
ayrıca Bright Data sample CSV'sini GitHub raw URL'sinden okuduğu için ilk veri
replay anında internet gerekir. İnternetsiz demo için CSV'yi önceden indirip
`INPUT_CSV=/path/to/twitter-posts.csv` verebilirsiniz.

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
  -d '{"interests":["Gaza ceasefire","Palestine solidarity","human rights"]}'

# Kişiselleştirilmiş akışı al
curl 'localhost:8081/users/user-1/feed?limit=10'
```

Dönen her gönderide `semanticSimilarity`, `recencyScore` ve `finalScore` ayrı
ayrı görünür — sıralamanın neden o şekilde olduğu izlenebilir.

Veri üreteci varsayılan olarak 1000 satırlık gerçek Twitter/X sample'ını bir kez
okur. `TOTAL_MESSAGES` değeri ilk 10, 100 veya 1000 satırı denemek için
değiştirilebilir.

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
{ "interests": ["Gaza ceasefire", "Palestine solidarity", "human rights"] }
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
`split` sondaki boş alanları atar ve son kolonları boş olan geçerli iç TSV
kayıtları "eksik kolon" diye reddedilir.

---

## Yapılandırma

Başlıca ayarlar `docker-compose.yml` içindeki `environment` blokları:

| Değişken | Servis | Varsayılan | Açıklama |
|---|---|---|---|
| `INPUT_CSV` | data-generator | Bright Data GitHub raw CSV | Okunacak Twitter/X CSV |
| `INPUT_TSV` | data-generator | boş | Opsiyonel iç TSV dosyası |
| `INPUT_OFFSET` | data-generator | 0 | CSV/TSV başlangıcında atlanacak satır |
| `RATE_PER_SEC` | data-generator | 50 | Saniyede gönderilen kayıt |
| `TOTAL_MESSAGES` | data-generator | 1000 | Okunacak maksimum kayıt, 0 = tamamı |
| `BATCH_SIZE` | embedding-worker | 32 | Kafka poll başına mesaj |
| `SEMANTIC_WEIGHT` | rec-api | 0.85 | Benzerlik ağırlığı |
| `RECENCY_WEIGHT` | rec-api | 0.15 | Güncellik ağırlığı |

---

## Kapsam dışı

Ara rapor §7 ile uyumlu olarak bu aşamada ele alınmayanlar: takip grafiği ve
sosyal bağlantılar, collaborative filtering, özel model eğitimi, tıklama tahmini,
güvenlik/moderasyon kuralları, üretim seviyesi hata toleransı.
