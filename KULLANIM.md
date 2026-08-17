# Kullanım Kılavuzu

Sistemi başlatma, durdurma ve sonuçları görme rehberi.

> **Terminal notu:** Bu dosyadaki komutlar **Git Bash** içindir.
> VS Code'da terminal panelinin sağ üstündeki `+` işaretinin yanındaki oka (`∨`)
> tıklayıp **Git Bash** seç. Satır başında `PS C:\...` yazıyorsa PowerShell'desin,
> script'ler orada çalışmaz.
>
> Terminalin proje klasöründe olduğundan emin ol:
> ```bash
> cd ~/Desktop/Projects/Bil401/tweet_project
> ```

---

## Hızlı başvuru

| Ne yapmak istiyorsun | Komut |
|---|---|
| Başlat | `docker compose up -d` |
| Durdur (veriler kalır) | `docker compose stop` |
| Durdur ve temizle | `docker compose down` |
| **Her şeyi sil, sıfırdan başla** | `docker compose down -v` |
| Durumu gör | `docker compose ps` |
| Sonuçları gör | `./scripts/demo.sh` |
| Doğrula | `./scripts/smoke-test.sh` |

---

## 1. Başlatma

### Ön koşul: Docker Desktop açık olmalı

Başlat menüsünden **Docker Desktop** yaz ve aç. Sağ alttaki sistem
tepsisinde balina ikonu belirir. **İkon sabitlenene kadar bekle**
(hareket ediyorsa hâlâ açılıyor demektir, 1-2 dakika sürer).

Hazır olduğunu şöyle kontrol edebilirsin:

```bash
docker info
```

Uzun bir bilgi listesi geliyorsa hazır. `error during connect` diyorsa
henüz açılmamış, biraz daha bekle.

### Sistemi başlat

```bash
docker compose up -d
```

`-d` "arka planda çalış" demek — terminal sana geri döner, sistem çalışmaya
devam eder.

**İlk çalıştırmada** (veya kodu değiştirdikten sonra) şunu kullan:

```bash
docker compose up -d --build
```

Bu 10-15 dakika sürer: Scala derlenir, embedding modeli (~470 MB) indirilir.
Sonraki başlatmalar genelde saniyeler sürer. Varsayılan akış Bright Data
Twitter/X örnek CSV'sini GitHub'dan okuduğu için veri replay anında internet
gerekebilir; internet istemiyorsan CSV'yi lokalde tutup `INPUT_CSV` ile dosya
yolunu verebilirsin.

### Hazır olduğunu anla

```bash
docker compose ps
```

Servisleri listede görmelisin. Sürekli çalışan servislerde `Up` yazmalı;
`data-generator` tek seferlik 1000 post replay ettiği için işini bitirdikten
sonra `Exited (0)` görünmesi normaldir. Bazılarında `(healthy)` de yazar.

Servisler sırayla başlar (Kafka → Spark → worker'lar), hepsinin hazır olması
**yaklaşık 1-2 dakika** sürer. Hemen `demo.sh` çalıştırırsan boş sonuç
alabilirsin — biraz bekle.

Veri akmaya başladı mı kontrolü:

```bash
docker compose logs --tail 3 data-generator
```

`gonderildi: ... kayit` satırları görüyorsan Bright Data örnek postları Kafka'ya
replay edilmeye başlamış.

---

## 2. Durdurma

Üç farklı seviye var. Farkı iyi anla — yanlışını seçersen ya yerin dolar ya
verin gider.

### `stop` — geçici ara (en sık kullanacağın)

```bash
docker compose stop
```

Konteynerler durur ama silinmez. Veriler yerinde. Devam etmek için:

```bash
docker compose start
```

Bilgisayarı kapatacaksan, yemeğe gideceksen bunu kullan.

### `down` — konteynerleri sil, veriyi tut

```bash
docker compose down
```

Konteynerler silinir, **ama Kafka mesajları ve Qdrant vektörleri kalır**
(bunlar "volume" denen ayrı alanlarda durur). Tekrar `up -d` dediğinde
sistem kaldığı yerden devam eder.

### `down -v` — her şeyi sil

```bash
docker compose down -v
```

Konteynerler **ve tüm veriler** silinir. Bir dahaki başlatmada Kafka boş,
Qdrant boş olur; sistem sıfırdan veri toplamaya başlar.

Ne zaman kullanmalı:
- Demo öncesi temiz bir başlangıç istiyorsan
- Bir şeyler karıştıysa ve baştan başlamak istiyorsan

> İndirilen imajlar (~8 GB) silinmez, sadece veriler gider. Yani yeniden
> başlatmak yine hızlı olur.

---

## 3. Sonuçları görme

### En kolayı: demo script'i

```bash
./scripts/demo.sh
```

Sistemin ne yaptığını 6 adımda anlatır: veri replay → Kafka → Spark →
embedding → Qdrant → öneri. En altta üç farklı kullanıcı için feed örneği
gösterir.

**Sunumda bunu kullan.**

### Tarayıcıdan görsel arayüzler

Sistem çalışırken bu adresleri aç:

| Adres | Ne göreceksin |
|---|---|
| http://localhost:6333/dashboard | **Qdrant** — kaç vektör var, içeriklerine bak |
| http://localhost:8080 | **Spark Master** — 2 worker paralel çalışıyor |
| http://localhost:4040 | **Spark Streaming** — batch grafiği, işleme hızı |
| http://localhost:8081/health | API sağlık kontrolü (basit JSON döner) |

> `localhost:4040` bazen açılmaz — Spark uygulaması yeniden başladığında
> port 4041'e kayar. `docker compose logs spark-cleaner | grep 404` ile
> hangi portta olduğunu görebilirsin.

### Kendi ilgi alanınla dene

İki adım, sırası önemli:

```bash
# 1) Kendini tanıt
curl -X POST localhost:8081/users/arda/interests -H 'Content-Type: application/json' -d '{"interests":["Gaza ceasefire","Palestine solidarity","human rights"]}'

# 2) Feed'ini al
curl 'localhost:8081/users/arda/feed?limit=10'
```

`arda` yerine istediğin ismi, köşeli parantez içine istediğin ilgi alanlarını
yaz. Birinci adımı atlarsan "profil yok" hatası alırsın.

**Okunabilir çıktı için** (Python varsa):

```bash
curl -s 'localhost:8081/users/arda/feed?limit=10' | python -c "import json,sys; [print(f\"{i['finalScore']:.3f}  {i['text'][:70]}\") for i in json.load(sys.stdin)['items']]"
```

### Sistem düzgün çalışıyor mu?

```bash
./scripts/smoke-test.sh
```

15 maddeyi kontrol eder. Hepsinde `[OK]` ve sonda `TUM KONTROLLER GECTI`
görmelisin.

### Dağıtıklık kanıtı (rapor §6 için)

```bash
./scripts/show-distribution.sh
```

Partition'ların worker'lara nasıl dağıldığını gösterir. Sunumda ekran
görüntüsü alacağın yer burası.

---

## 4. Ölçekleme denemesi

Raporun "yatay ölçeklenebilir" iddiasını canlı göstermek için:

```bash
# Worker sayısını 3'e çıkar
docker compose up -d --scale embedding-worker=3

# Yeniden dağılımı gör (30 saniye bekle, Kafka dengeleme yapıyor)
./scripts/show-distribution.sh

# Normale dön
docker compose up -d --scale embedding-worker=2
```

3 partition'ın 3 ayrı worker'a dağıldığını göreceksin. Kod değişmeden
sadece replica sayısıyla ölçekleniyor — sunumda etkileyici bir an.

---

## 5. Log okuma

Bir şeyin çalışıp çalışmadığını anlamanın en doğrudan yolu:

```bash
docker compose logs --tail 20 data-generator    # kaç tweet üretildi
docker compose logs --tail 20 spark-cleaner     # kaç kayıt temizlendi
docker compose logs --tail 20 embedding-worker  # vektörler yazılıyor mu
docker compose logs --tail 20 rec-api           # API istekleri
```

Canlı izlemek için `--tail 20` yerine `-f` kullan (çıkmak için `Ctrl+C`):

```bash
docker compose logs -f spark-cleaner
```

---

## 6. Sorun giderme

### "error during connect" / "cannot find the file specified"

Docker Desktop kapalı. Aç ve balina ikonu sabitlenene kadar bekle.

### "port is already allocated"

Bir port başka bir program tarafından kullanılıyor. Hangi servisin
çakıştığını bul, o programı kapat veya `docker-compose.yml` içindeki port
numarasını değiştir (örn. `"8081:8081"` → `"9081:8081"`).

### Feed boş dönüyor

Sistem daha yeni başlamıştır, Qdrant'a veri yazılması 1-2 dakika sürer.
Kontrol et:

```bash
curl -s localhost:6333/collections/posts | grep -o '"points_count":[0-9]*'
```

Sayı 0'dan büyükse veri var demektir.

### Bir servis sürekli yeniden başlıyor

Log'una bak, sebebi orada yazar:

```bash
docker compose logs --tail 50 <servis-adi>
```

### Hiçbir şey anlamadım, baştan başlamak istiyorum

```bash
docker compose down -v
docker compose up -d --build
```

İkinci komut 10-15 dakika sürer ama her şeyi sıfırdan ve temiz kurar.

### Terminal komutları çalışmıyor, garip hatalar veriyor

PowerShell'desin. Git Bash'e geç (bu dosyanın başındaki nota bak).

---

## 7. Sunum günü sırası

Önerilen akış:

1. **Önceden** (sunumdan 5 dk önce): `docker compose up -d` — sistemin ısınması için
2. `docker compose ps` — "11 servis çalışıyor" de
3. http://localhost:8080 aç — "Spark 2 worker ile paralel çalışıyor"
4. `./scripts/show-distribution.sh` — "3 partition, worker'lara dağılmış" (rapor §6)
5. `./scripts/demo.sh` — uçtan uca akışı göster
6. **Canlı deneme**: hocanın söylediği bir ilgi alanını gir, feed'i göster

Altıncı madde en etkilisi — önceden hazırlanmadığın belli olur.

**Yedek plan:** İnternet veya Docker sorun çıkarırsa `./scripts/demo.sh`
çıktısını önceden bir dosyaya kaydet:

```bash
./scripts/demo.sh > demo-ciktisi.txt 2>&1
```
