#!/usr/bin/env bash
# Sunum/demo scripti: sistemin ne yaptigini bastan sona gosterir.
#
# Kullanim: ./scripts/demo.sh
#
# smoke-test.sh dogrulama yapar (OK/HATA), bu script ise anlatir:
# veri nereden geliyor, nasil isleniyor, oneri nasil olusuyor.
set -uo pipefail

export MSYS_NO_PATHCONV=1
API="${API:-http://localhost:8081}"
QDRANT="${QDRANT:-http://localhost:6333}"
KAFKA_BIN=/opt/kafka/bin

title() { printf '\n\033[1;36m%s\033[0m\n' "$1"; printf '\033[2m%s\033[0m\n' "$(printf '─%.0s' {1..70})"; }
note()  { printf '\033[2m%s\033[0m\n' "$1"; }

# ---------------------------------------------------------------------------
title "1. VERI URETIMI  —  RecSys 2021 semasinda tweet akisi"
note "Ureteç, RecSys 2021 Challenge'in 20 kolonlu TSV semasini birebir uretir."
note "Metin alani gercek mBERT token ID'leri icerir (gercek veri setiyle ayni)."
echo
docker logs data-generator 2>&1 | tail -2

# ---------------------------------------------------------------------------
title "2. KAFKA  —  posts.raw topic'i 3 partition'a dagilmis"
note "Rapor §6: 'Kafka topic'leri partition'lara ayrilarak paralel okunabilir'"
echo
docker exec kafka $KAFKA_BIN/kafka-get-offsets.sh \
  --bootstrap-server localhost:9092 --topic posts.raw 2>/dev/null \
  | awk -F: '{printf "   partition %s: %s mesaj\n", $2, $3; t+=$3} END {printf "   ----------------------\n   TOPLAM     : %d mesaj\n", t}'

# ---------------------------------------------------------------------------
title "3. SPARK  —  temizleme + token decode + tekrar eleme"
note "TSV parse -> zorunlu alan kontrolu -> mBERT token'lari metne cevir -> dedup"
echo
docker logs spark-cleaner 2>&1 | grep "\[cleaner\]" | tail -3

# ---------------------------------------------------------------------------
title "4. EMBEDDING  —  metin -> 384 boyutlu vektor"
note "Cok dilli MiniLM modeli; 2 worker ayni consumer group'ta paralel calisiyor."
echo
docker exec kafka $KAFKA_BIN/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 --describe --group embedding-workers 2>/dev/null \
  | awk '/posts.cleaned/ {printf "   partition %s -> worker %s   (lag: %s)\n", $3, $8, $6}'

# ---------------------------------------------------------------------------
title "5. QDRANT  —  vektor veritabani"
curl -s "$QDRANT/collections/posts" 2>/dev/null | python -c "
import json,sys
d=json.load(sys.stdin)['result']
c=d['config']['params']['vectors']
print(f\"   kayitli vektor : {d.get('points_count', 0)}\")
print(f\"   vektor boyutu  : {c['size']}\")
print(f\"   mesafe olcusu  : {c['distance']}\")
print(f\"   durum          : {d.get('status')}\")
" 2>/dev/null

# ---------------------------------------------------------------------------
title "6. ONERI  —  ayni sistem, farkli ilgi alanlari"
note "Her kullanici icin ilgi alanlari vektorlestirilip profil olusturulur,"
note "ardindan Qdrant'ta en yakin gonderiler aranip finalScore ile siralanir."

demo_user() {
  local user="$1"; local label="$2"; shift 2
  local json; json=$(python -c "
import json,sys
print(json.dumps({'interests': sys.argv[1:]}))
" "$@")

  curl -s -X POST "$API/users/$user/interests" \
    -H 'Content-Type: application/json' -d "$json" >/dev/null 2>&1

  printf '\n\033[1m   ▸ ilgi alanlari: %s\033[0m\n' "$label"
  curl -s "$API/users/$user/feed?limit=5" 2>/dev/null | python -c "
import json,sys
try:
    d=json.load(sys.stdin)
    if not d.get('items'):
        print('     (henuz veri yok - birkac saniye bekleyip tekrar deneyin)')
    for i,it in enumerate(d['items'],1):
        print(f\"     {i}. [{it['finalScore']:.3f}] ({it['language']}) {it['text'][:62]}\")
except Exception as e:
    print(f'     (okunamadi: {e})')
"
}

demo_user "demo-tech"  "GPU programlama, dagitik sistemler"  "GPU programlama" "dagitik sistemler"
demo_user "demo-food"  "yemek tarifleri, kahve demleme"      "yemek tarifleri" "kahve demleme"
demo_user "demo-sport" "maraton antrenmani, basketbol"       "maraton antrenmani" "basketbol"

echo
note "Dikkat: sorgu Turkce ama sonuclar Almanca/Ingilizce/Fransizca da olabilir."
note "Cok dilli embedding modeli anlami yakaliyor, kelimeleri degil."

# ---------------------------------------------------------------------------
title "ARAYUZLER"
cat <<EOF
   Spark Master UI   : http://localhost:8080
   Spark Streaming   : http://localhost:4040
   Qdrant dashboard  : http://localhost:6333/dashboard
   Recommendation API: http://localhost:8081/health

   Detayli dogrulama : ./scripts/smoke-test.sh
   Dagitiklik kaniti : ./scripts/show-distribution.sh
EOF
echo
