"""Uretilen kayitlari Kafka posts.raw topic'ine yazar.

Iki mod destekler:
  - sentetik (varsayilan): generator.py ile RecSys 2021 semasinda kayit uretir
  - --input-tsv PATH     : gercek RecSys 2021 TSV dosyasini satir satir okur

Ikinci mod, veri setine erisim saglandigi durumda hattin geri kalanini hic
degistirmeden gercek veriye gecebilmek icin vardir.
"""

import argparse
import logging
import os
import signal
import sys
import time

from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

import generator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [producer] %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

_running = True


def _stop(signum, frame):
    global _running
    log.info("kapatma sinyali alindi (%s), durduruluyor", signum)
    _running = False


def connect(bootstrap: str, retries: int = 30) -> KafkaProducer:
    """Kafka hazir olana kadar bekler.

    depends_on healthcheck'i olsa da broker'in topic metadata'sini servis
    etmeye hazir olmasi biraz daha surebiliyor.
    """
    for attempt in range(1, retries + 1):
        try:
            producer = KafkaProducer(
                bootstrap_servers=bootstrap,
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                value_serializer=lambda v: v.encode("utf-8"),
                acks="all",
                linger_ms=50,
                retries=5,
            )
            log.info("Kafka'ya baglandi: %s", bootstrap)
            return producer
        except NoBrokersAvailable:
            log.warning("Kafka hazir degil (deneme %d/%d), 2sn bekleniyor", attempt, retries)
            time.sleep(2)
    raise SystemExit(f"Kafka'ya baglanilamadi: {bootstrap}")


def run_synthetic(producer: KafkaProducer, topic: str, rate: float, total: int, seed: int):
    gen = generator.TweetGenerator(seed=seed)
    log.info("sentetik uretim basliyor: rate=%.1f/sn, toplam=%s", rate, total or "sinirsiz")

    interval = 1.0 / rate if rate > 0 else 0.0
    sent = 0
    topic_counts: dict[str, int] = {}
    t0 = time.time()

    for _tweet_id, row, tweet_topic in gen.generate_with_duplicates():
        if not _running or (total and sent >= total):
            break

        # Key olarak tweet_id kullaniyoruz -> partition dagilimi dengeli olur
        producer.send(topic, key=_tweet_id, value=row)
        sent += 1
        topic_counts[tweet_topic] = topic_counts.get(tweet_topic, 0) + 1

        if sent % 100 == 0:
            elapsed = time.time() - t0
            log.info("gonderildi: %d kayit (%.1f/sn)", sent, sent / max(elapsed, 0.001))

        if interval:
            time.sleep(interval)

    producer.flush()
    log.info("uretim bitti. toplam=%d konu dagilimi=%s", sent, topic_counts)


def run_from_file(producer: KafkaProducer, topic: str, path: str, rate: float, total: int):
    """Gercek RecSys 2021 TSV dosyasindan okur.

    Sema ayni oldugu icin downstream'de hicbir degisiklik gerekmez.
    tweet_id, Table 1'e gore 3. kolondur (0-indexed: 2).
    """
    log.info("dosyadan okuma: %s", path)
    interval = 1.0 / rate if rate > 0 else 0.0
    sent = 0

    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            if not _running or (total and sent >= total):
                break
            line = line.rstrip("\n")
            if not line:
                continue

            parts = line.split("\t")
            if len(parts) < len(generator.COLUMNS):
                log.warning("eksik kolon, satir atlandi (%d kolon)", len(parts))
                continue

            producer.send(topic, key=parts[2], value=line)
            sent += 1
            if sent % 1000 == 0:
                log.info("gonderildi: %d kayit", sent)
            if interval:
                time.sleep(interval)

    producer.flush()
    log.info("dosya okuma bitti. toplam=%d", sent)


def main():
    parser = argparse.ArgumentParser(description="RecSys 2021 semali Kafka producer")
    parser.add_argument("--input-tsv", help="Gercek RecSys 2021 TSV dosyasi (opsiyonel)")
    parser.add_argument("--rate", type=float,
                        default=float(os.getenv("RATE_PER_SEC", "20")),
                        help="saniyede kac kayit")
    parser.add_argument("--total", type=int,
                        default=int(os.getenv("TOTAL_MESSAGES", "0")),
                        help="toplam kayit sayisi (0 = sinirsiz)")
    parser.add_argument("--seed", type=int, default=int(os.getenv("SEED", "42")))
    args = parser.parse_args()

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    bootstrap = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
    topic = os.getenv("TOPIC", "posts.raw")

    producer = connect(bootstrap)
    try:
        if args.input_tsv:
            run_from_file(producer, topic, args.input_tsv, args.rate, args.total)
        else:
            run_synthetic(producer, topic, args.rate, args.total, args.seed)
    finally:
        producer.close(timeout=10)


if __name__ == "__main__":
    sys.exit(main())
