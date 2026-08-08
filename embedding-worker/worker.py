"""Embedding worker: posts.cleaned -> vektor -> Qdrant.

Iki islevi var:
  1. Kafka consumer dongusu (RUN_CONSUMER=true): temiz gonderileri okur,
     vektorlestirir, Qdrant'a yazar.
  2. HTTP servisi: POST /embed -- rec-api'nin kullanici ilgi alanlarini
     vektore cevirmesi icin. Model zaten bellekte oldugu icin Scala
     tarafinda ayri bir model calistirmaya gerek kalmaz.

Ayni imaj her iki rolde de kullanilir; docker-compose'da consumer'lar
2 replica olarak, HTTP servisi tekil olarak calisir.
"""

import json
import logging
import os
import signal
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

import model
import store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [worker] %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
TOPIC = os.getenv("TOPIC", "posts.cleaned")
GROUP_ID = os.getenv("GROUP_ID", "embedding-workers")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "32"))
EMBED_PORT = int(os.getenv("EMBED_PORT", "8000"))
RUN_CONSUMER = os.getenv("RUN_CONSUMER", "true").lower() != "false"

_running = True
_stats = {"consumed": 0, "upserted": 0, "skipped": 0}


def _stop(signum, frame):
    global _running
    log.info("kapatma sinyali alindi (%s)", signum)
    _running = False


# ---------------------------------------------------------------------------
# HTTP servisi
# ---------------------------------------------------------------------------


class EmbedHandler(BaseHTTPRequestHandler):
    """POST /embed  {"texts": [...]} -> {"vectors": [[...]], "dim": 384}
    GET  /health -> {"status": "ok"}
    """

    def _send(self, code: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            # Modelin gercekten yuklendigini dogrula -- container ayakta ama
            # model yuklenememisse healthy demek yaniltici olur
            try:
                model.get_model()
                self._send(200, {"status": "ok", "stats": _stats})
            except Exception as exc:
                self._send(503, {"status": "model yuklenemedi", "error": str(exc)})
        else:
            self._send(404, {"error": "bulunamadi"})

    def do_POST(self):
        if self.path != "/embed":
            self._send(404, {"error": "bulunamadi"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0:
                self._send(400, {"error": "bos govde"})
                return

            payload = json.loads(self.rfile.read(length))
            texts = payload.get("texts")
            if not isinstance(texts, list) or not texts:
                self._send(400, {"error": "texts alani bos olmayan bir liste olmali"})
                return
            if not all(isinstance(t, str) for t in texts):
                self._send(400, {"error": "texts yalnizca string icermeli"})
                return

            vectors = model.embed(texts)
            self._send(200, {
                "vectors": [v.tolist() for v in vectors],
                "dim": model.VECTOR_SIZE,
            })
        except json.JSONDecodeError:
            self._send(400, {"error": "gecersiz JSON"})
        except Exception as exc:
            log.exception("embed hatasi")
            self._send(500, {"error": str(exc)})

    def log_message(self, fmt, *args):
        # Varsayilan stderr log'u cok gurultulu
        pass


def start_http_server() -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("0.0.0.0", EMBED_PORT), EmbedHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    log.info("HTTP servisi dinliyor: :%d", EMBED_PORT)
    return server


# ---------------------------------------------------------------------------
# Kafka consumer dongusu
# ---------------------------------------------------------------------------


def connect_consumer(retries: int = 30) -> KafkaConsumer:
    for attempt in range(1, retries + 1):
        try:
            consumer = KafkaConsumer(
                TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP,
                group_id=GROUP_ID,
                auto_offset_reset="earliest",
                # Manuel commit: Qdrant'a yazdiktan SONRA commit ediyoruz,
                # boylece at-least-once garantisi saglanir
                enable_auto_commit=False,
                max_poll_records=BATCH_SIZE,
                value_deserializer=lambda v: v.decode("utf-8"),
                consumer_timeout_ms=5000,
            )
            log.info(
                "Kafka'ya baglandi: %s topic=%s group=%s",
                KAFKA_BOOTSTRAP, TOPIC, GROUP_ID,
            )
            return consumer
        except NoBrokersAvailable:
            log.warning("Kafka hazir degil (deneme %d/%d)", attempt, retries)
            time.sleep(2)
    raise SystemExit(f"Kafka'ya baglanilamadi: {KAFKA_BOOTSTRAP}")


def process_batch(client, messages: list) -> None:
    """Bir mesaj grubunu vektorlestirip Qdrant'a yazar."""
    posts = []
    for msg in messages:
        try:
            post = json.loads(msg.value)
        except json.JSONDecodeError:
            _stats["skipped"] += 1
            continue

        text = (post.get("text") or "").strip()
        if not text or not post.get("tweetId"):
            _stats["skipped"] += 1
            continue
        posts.append(post)

    if not posts:
        return

    vectors = model.embed([p["text"] for p in posts])
    try:
        written = store.upsert_posts(client, posts, vectors)
    except Exception as exc:
        # Collection silinmis olabilir (orn. elle temizleme). Yeniden
        # olusturup bir kez daha deniyoruz; aksi halde worker'i yeniden
        # baslatmak gerekirdi.
        if "doesn't exist" in str(exc) or "Not found" in str(exc):
            log.warning("collection kayip, yeniden olusturuluyor")
            store.ensure_collection(client)
            written = store.upsert_posts(client, posts, vectors)
        else:
            raise
    _stats["upserted"] += written


def consume_loop(client) -> None:
    consumer = connect_consumer()
    log.info("tuketim dongusu basladi (batch=%d)", BATCH_SIZE)

    try:
        while _running:
            batches = consumer.poll(timeout_ms=2000, max_records=BATCH_SIZE)
            if not batches:
                continue

            messages = [m for partition_msgs in batches.values() for m in partition_msgs]
            if not messages:
                continue

            _stats["consumed"] += len(messages)
            try:
                process_batch(client, messages)
                # Basarili yazma sonrasi commit -- sirasi onemli
                consumer.commit()
            except Exception:
                log.exception(
                    "batch islenemedi (%d mesaj); commit edilmedi, tekrar denenecek",
                    len(messages),
                )
                continue

            if _stats["consumed"] % 200 < BATCH_SIZE:
                log.info(
                    "tuketilen=%d yazilan=%d atlanan=%d qdrant_toplam=%d",
                    _stats["consumed"], _stats["upserted"], _stats["skipped"],
                    store.count(client),
                )
    finally:
        consumer.close()
        log.info("tuketim dongusu bitti: %s", _stats)


def main():
    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    # Modeli onceden yukle: /health erken 'ok' dememeli
    model.get_model()

    client = store.connect()
    store.ensure_collection(client)

    start_http_server()

    if RUN_CONSUMER:
        consume_loop(client)
    else:
        log.info("RUN_CONSUMER=false -- yalnizca HTTP servisi calisiyor")
        while _running:
            time.sleep(1)


if __name__ == "__main__":
    main()
