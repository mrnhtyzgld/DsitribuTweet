# Kubernetes manifestleri (sonraki aşama)

Ara rapor §3.7'de belirtildiği gibi ilk geliştirme ortamı Docker Compose'dur.
Bu dizin, servislerin Kubernetes'e taşınması için hazırlanmış iskelettir.

**Durum:** Bu manifestler henüz bir cluster üzerinde test edilmedi. Asıl
çalıştırma yolu kök dizindeki `docker-compose.yml`'dir.

## Taşıma sırasında dikkat edilecekler

| Bileşen | Compose'daki durum | Kubernetes karşılığı |
|---|---|---|
| Kafka | tek broker, KRaft | StatefulSet + headless Service (veya Strimzi operatörü) |
| Qdrant | tek node, volume | StatefulSet + PersistentVolumeClaim |
| Spark | standalone cluster | Spark on K8s (`spark-submit --master k8s://...`) veya Spark Operator |
| embedding-worker | `deploy.replicas: 2` | Deployment `replicas: N` — consumer group aynı kalır |
| rec-api | tek container | Deployment + Service + HPA |

Ölçekleme mantığı değişmez: embedding worker'ları aynı Kafka consumer group'unda
kaldığı sürece partition'lar pod'lar arasında otomatik dağılır. Compose'daki
`--scale embedding-worker=3` ile K8s'deki `kubectl scale deployment/embedding-worker
--replicas=3` aynı davranışı verir.
