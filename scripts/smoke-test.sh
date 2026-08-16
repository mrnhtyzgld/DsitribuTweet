#!/usr/bin/env bash
# Uctan uca dogrulama: rapordaki 9 adimin gercekten calistigini kontrol eder.
#
# Kullanim: ./scripts/smoke-test.sh
set -uo pipefail

API="${API:-http://localhost:8081}"
QDRANT="${QDRANT:-http://localhost:6333}"

# Git Bash (Windows) '/opt/...' yollarini Windows yoluna cevirir -> kapat
export MSYS_NO_PATHCONV=1
KAFKA_BIN=/opt/kafka/bin
KAFKA_EXEC="docker exec kafka"

PASS=0
FAIL=0

green() { printf '\033[0;32m%s\033[0m\n' "$1"; }
red()   { printf '\033[0;31m%s\033[0m\n' "$1"; }
blue()  { printf '\033[0;34m%s\033[0m\n' "$1"; }

# Bir topic'teki toplam mesaj sayisini dondurur (partition'lar toplanir)
topic_count() {
  $KAFKA_EXEC $KAFKA_BIN/kafka-get-offsets.sh \
    --bootstrap-server localhost:9092 --topic "$1" 2>/dev/null \
    | awk -F: '{sum += $3} END {print sum+0}'
}

blue "=== 1. Servis durumlari ==="
for svc in kafka qdrant spark-master rec-api embedding-api; do
  if docker ps --filter "name=^${svc}$" --filter "status=running" --format '{{.Names}}' | grep -q .; then
    green "  [OK]   $svc calisiyor"; PASS=$((PASS+1))
  else
    red   "  [HATA] $svc calismiyor"; FAIL=$((FAIL+1))
  fi
done

blue ""
blue "=== 2. Kafka topic'leri ve partition sayisi ==="
for topic in posts.raw posts.cleaned; do
  parts=$($KAFKA_EXEC $KAFKA_BIN/kafka-topics.sh --bootstrap-server localhost:9092 \
    --describe --topic "$topic" 2>/dev/null | grep -c "Partition:")
  if [ "$parts" -eq 3 ]; then
    green "  [OK]   $topic: $parts partition"; PASS=$((PASS+1))
  else
    red   "  [HATA] $topic: $parts partition (3 bekleniyordu)"; FAIL=$((FAIL+1))
  fi
done

blue ""
blue "=== 3. Veri akisi (rapor adim 1-3) ==="
raw=$(topic_count posts.raw)
cleaned=$(topic_count posts.cleaned)

if [ "${raw:-0}" -gt 0 ]; then
  green "  [OK]   posts.raw: $raw mesaj (producer calisiyor)"; PASS=$((PASS+1))
else
  red   "  [HATA] posts.raw bos -- producer calismiyor"; FAIL=$((FAIL+1))
fi

if [ "${cleaned:-0}" -gt 0 ]; then
  green "  [OK]   posts.cleaned: $cleaned mesaj (Spark calisiyor)"; PASS=$((PASS+1))
else
  red   "  [HATA] posts.cleaned bos -- Spark isi calismiyor olabilir"; FAIL=$((FAIL+1))
fi

blue ""
blue "=== 4. Embedding + Qdrant (rapor adim 4-5) ==="
points=$(curl -s "$QDRANT/collections/posts" 2>/dev/null \
  | grep -o '"points_count":[0-9]*' | head -1 | cut -d: -f2)

if [ "${points:-0}" -gt 0 ]; then
  green "  [OK]   Qdrant: $points vektor (embedding worker calisiyor)"; PASS=$((PASS+1))
else
  red   "  [HATA] Qdrant bos -- embedding worker calismiyor olabilir"; FAIL=$((FAIL+1))
fi

vec_size=$(curl -s "$QDRANT/collections/posts" 2>/dev/null \
  | grep -o '"size":[0-9]*' | head -1 | cut -d: -f2)
if [ "${vec_size:-0}" -eq 384 ]; then
  green "  [OK]   vektor boyutu: 384"; PASS=$((PASS+1))
else
  red   "  [HATA] vektor boyutu: ${vec_size:-yok} (384 bekleniyordu)"; FAIL=$((FAIL+1))
fi

blue ""
blue "=== 5. Oneri API'si (rapor adim 6-9) ==="

if curl -sf "$API/health" >/dev/null 2>&1; then
  green "  [OK]   /health yanit veriyor"; PASS=$((PASS+1))
else
  red   "  [HATA] /health yanit vermiyor"; FAIL=$((FAIL+1))
fi

# Teknoloji ilgi alanlari
resp=$(curl -s -X POST "$API/users/test-tech/interests" \
  -H 'Content-Type: application/json' \
  -d '{"interests":["GPU programlama","dagitik sistemler","Kafka stream isleme"]}' 2>/dev/null)

if echo "$resp" | grep -q '"vectorDim":384'; then
  green "  [OK]   profil vektoru olusturuldu (384 boyut)"; PASS=$((PASS+1))
else
  red   "  [HATA] profil olusturulamadi: $resp"; FAIL=$((FAIL+1))
fi

feed=$(curl -s "$API/users/test-tech/feed?limit=5" 2>/dev/null)
count=$(echo "$feed" | grep -o '"count":[0-9]*' | head -1 | cut -d: -f2)

if [ "${count:-0}" -gt 0 ]; then
  green "  [OK]   feed dondu: $count gonderi"; PASS=$((PASS+1))
else
  red   "  [HATA] feed bos: $feed"; FAIL=$((FAIL+1))
fi

blue ""
blue "=== 6. Anlamsal eslesme kalitesi ==="
echo "  'GPU programlama, dagitik sistemler' icin ilk 5 sonuc:"
echo "$feed" | python -c "
import json,sys
try:
    d = json.load(sys.stdin)
    for i, it in enumerate(d.get('items', [])[:5], 1):
        print(f\"    {i}. [{it['finalScore']:.3f}] {it['text'][:70]}\")
except Exception as e:
    print(f'    (cozumlenemedi: {e})')
" 2>/dev/null || echo "    (python yok, ham cikti atlandi)"

# Farkli bir ilgi alani belirgin sekilde farkli sonuc vermeli
curl -s -X POST "$API/users/test-food/interests" \
  -H 'Content-Type: application/json' \
  -d '{"interests":["yemek tarifleri","kahve demleme"]}' >/dev/null 2>&1

feed2=$(curl -s "$API/users/test-food/feed?limit=5" 2>/dev/null)
echo ""
echo "  'yemek tarifleri, kahve demleme' icin ilk 5 sonuc:"
echo "$feed2" | python -c "
import json,sys
try:
    d = json.load(sys.stdin)
    for i, it in enumerate(d.get('items', [])[:5], 1):
        print(f\"    {i}. [{it['finalScore']:.3f}] {it['text'][:70]}\")
except Exception as e:
    print(f'    (cozumlenemedi: {e})')
" 2>/dev/null || echo "    (python yok)"

# Iki feed'in ayni olmamasi gerekir -- ayniysa oneri calismiyor demektir
ids1=$(echo "$feed"  | grep -o '"tweetId":"[^"]*"' | sort | head -5)
ids2=$(echo "$feed2" | grep -o '"tweetId":"[^"]*"' | sort | head -5)
if [ -n "$ids1" ] && [ "$ids1" != "$ids2" ]; then
  green "  [OK]   farkli ilgi alanlari farkli sonuc veriyor"; PASS=$((PASS+1))
else
  red   "  [HATA] iki farkli profil ayni sonucu dondurdu -- oneri calismiyor"; FAIL=$((FAIL+1))
fi

blue ""
blue "=== Ozet ==="
green "  basarili: $PASS"
if [ "$FAIL" -gt 0 ]; then
  red "  basarisiz: $FAIL"
  exit 1
fi
green "  TUM KONTROLLER GECTI"
