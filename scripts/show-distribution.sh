#!/usr/bin/env bash
# Rapor §6 "Planlanan Dagitik Sistem Ozellikleri" iddialarinin kaniti.
#
# Tek makinede pseudo-distributed calisan sistemin gercekten paralel
# oldugunu gosterir. Sunum/rapor icin ekran goruntusu alinabilir.
set -uo pipefail

# Git Bash (Windows) '/opt/...' yollarini Windows yoluna cevirir -> kapat
export MSYS_NO_PATHCONV=1

blue() { printf '\n\033[1;34m%s\033[0m\n' "$1"; }
dim()  { printf '\033[2m%s\033[0m\n' "$1"; }

blue "1) Kafka topic'leri partition'lara ayrilmis"
dim "   (rapor §6: 'Kafka topic'leri partition'lara ayrilarak paralel okunabilir')"
docker exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 \
  --describe --topic posts.raw 2>/dev/null | head -5
echo ""
docker exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 \
  --describe --topic posts.cleaned 2>/dev/null | head -5

blue "2) Embedding worker'lari ayni consumer group'ta partition'lari paylasiyor"
dim "   (rapor §6: 'Birden fazla embedding worker ayni consumer group icinde calisabilir')"
docker exec kafka /opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
  --describe --group embedding-workers 2>/dev/null

echo ""
dim "   Calisan worker replica sayisi:"
docker ps --filter "name=embedding-worker" --format '   - {{.Names}}  ({{.Status}})'

blue "3) Spark cluster'inda birden fazla worker/executor"
dim "   (rapor §6: 'Spark isi birden fazla executor uzerinde paralel isleyebilir')"
docker ps --filter "name=spark-worker" --format '   - {{.Names}}  ({{.Status}})'
echo ""
dim "   Spark master UI: http://localhost:8080"
dim "   Spark app  UI  : http://localhost:4040  (Executors sekmesi)"

# Master UI'dan worker sayisini cekmeye calis
workers=$(curl -s http://localhost:8080/json/ 2>/dev/null \
  | grep -o '"aliveworkers":[0-9]*' | cut -d: -f2)
[ -n "${workers:-}" ] && dim "   Aktif Spark worker sayisi: $workers"

blue "4) Qdrant collection durumu"
curl -s http://localhost:6333/collections/posts 2>/dev/null \
  | python -c "
import json,sys
try:
    d = json.load(sys.stdin)['result']
    print(f\"   nokta sayisi : {d.get('points_count', 0)}\")
    print(f\"   segment      : {d.get('segments_count', 0)}\")
    cfg = d['config']['params']['vectors']
    print(f\"   vektor       : {cfg['size']} boyut, {cfg['distance']}\")
    print(f\"   durum        : {d.get('status', '?')}\")
except Exception as e:
    print(f'   (okunamadi: {e})')
" 2>/dev/null || echo "   (python yok)"

blue "5) Yatay olceklenebilirlik testi"
dim "   Worker sayisini artirip partition'larin yeniden dagildigini gorun:"
echo "     docker compose up -d --scale embedding-worker=3"
echo "     ./scripts/show-distribution.sh"
echo ""
