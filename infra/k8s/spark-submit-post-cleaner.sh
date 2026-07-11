#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-distributweet}"
SPARK_IMAGE="${SPARK_IMAGE:-distributweet/spark-stream:local}"
K8S_MASTER="${K8S_MASTER:-k8s://https://kubernetes.default.svc}"

spark-submit \
  --master "$K8S_MASTER" \
  --deploy-mode cluster \
  --name distributweet-post-cleaner \
  --class com.distributweet.stream.PostCleanerApp \
  --conf spark.kubernetes.namespace="$NAMESPACE" \
  --conf spark.kubernetes.container.image="$SPARK_IMAGE" \
  --conf spark.kubernetes.authenticate.driver.serviceAccountName=default \
  --conf spark.executor.instances=1 \
  --conf spark.executor.memory=1g \
  --conf spark.driver.memory=1g \
  --conf spark.kubernetes.driverEnv.KAFKA_BOOTSTRAP_SERVERS=kafka:9092 \
  --conf spark.kubernetes.driverEnv.RAW_TOPIC=posts.raw \
  --conf spark.kubernetes.driverEnv.CLEANED_TOPIC=posts.cleaned \
  --conf spark.kubernetes.driverEnv.CHECKPOINT_DIR=/tmp/distributweet/checkpoints/post-cleaner \
  --conf spark.kubernetes.driverEnv.ARCHIVE_DIR=/tmp/distributweet/data/posts \
  --conf spark.kubernetes.driverEnv.ACCEPTED_LANGUAGES=en,tr \
  --conf spark.kubernetes.driverEnv.MIN_TEXT_LENGTH=12 \
  --conf spark.kubernetes.driverEnv.WATERMARK_DELAY="2 hours" \
  local:///opt/distributweet/spark-stream.jar
