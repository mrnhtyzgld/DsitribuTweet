#!/bin/bash
# Spark streaming isini standalone cluster'a submit eder.
set -euo pipefail

MASTER="${SPARK_MASTER_URL:-spark://spark-master:7077}"

echo "[submit] Spark master bekleniyor: ${MASTER}"
host_port="${MASTER#spark://}"
host="${host_port%%:*}"
port="${host_port##*:}"

for i in $(seq 1 60); do
  if (exec 3<>"/dev/tcp/${host}/${port}") 2>/dev/null; then
    echo "[submit] master hazir"
    break
  fi
  [ "$i" = "60" ] && { echo "[submit] master'a ulasilamadi"; exit 1; }
  sleep 2
done

# Java 17'de Spark, JDK ic modullerine erisim icin acik izin ister.
JAVA17_OPTS="--add-opens=java.base/java.lang=ALL-UNNAMED \
--add-opens=java.base/java.lang.invoke=ALL-UNNAMED \
--add-opens=java.base/java.io=ALL-UNNAMED \
--add-opens=java.base/java.net=ALL-UNNAMED \
--add-opens=java.base/java.nio=ALL-UNNAMED \
--add-opens=java.base/java.util=ALL-UNNAMED \
--add-opens=java.base/java.util.concurrent=ALL-UNNAMED \
--add-opens=java.base/sun.nio.ch=ALL-UNNAMED \
--add-opens=java.base/sun.security.action=ALL-UNNAMED"

# 2 worker x 2 core = 4 slot. Executor basina 1 core vererek
# 4 executor'a kadar paralellik saglanir (rapor §6: birden fazla executor).
exec /opt/spark/bin/spark-submit \
  --master "${MASTER}" \
  --class com.bil401.cleaner.CleanerJob \
  --deploy-mode client \
  --conf spark.driver.host="$(hostname -i)" \
  --conf spark.executor.cores=1 \
  --conf spark.executor.memory=512m \
  --conf spark.cores.max=4 \
  --conf spark.sql.streaming.metricsEnabled=true \
  --conf "spark.driver.extraJavaOptions=${JAVA17_OPTS}" \
  --conf "spark.executor.extraJavaOptions=${JAVA17_OPTS}" \
  /app/spark-cleaner.jar
