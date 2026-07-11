# DistribuTweet

DistribuTweet is a small end-to-end content-based recommendation system. It ingests live-like post events through Kafka, cleans them with Spark Structured Streaming, embeds cleaned text with `intfloat/multilingual-e5-small`, stores vectors in Qdrant, and serves personalized feeds through a Scala http4s API.

## Architecture

```text
JSONL replay / Jetstream-compatible source
        -> Kafka posts.raw
        -> Scala Spark stream processor
        -> Kafka posts.cleaned + Parquet archive
        -> Python embedding worker
        -> Qdrant posts collection
        -> Scala recommendation API
```

The first version is intentionally content-based only. It does not use a follow graph, collaborative filtering, Redis, Cassandra, Schema Registry, model training, authentication, or multi-tenancy.

## Quickstart

```bash
make up
make create-topics
make replay
make create-profile
make get-feed
```

Useful endpoints:

```bash
curl http://localhost:8080/health
curl http://localhost:8001/health
```

The recommendation API exposes:

```text
POST /users/{userId}/interests
GET  /users/{userId}/feed?limit=20
GET  /health
GET  /metrics
```

## Development

Run unit tests:

```bash
make test
```

Run only Python tests:

```bash
make test-python
```

Run Scala tests in Docker:

```bash
make test-scala
```

## Qdrant point IDs

Qdrant accepts unsigned integers or UUIDs as point identifiers. The system derives deterministic UUIDs from `postId` and `userId`, while preserving the original IDs in payloads. Replaying the same post therefore upserts the same point instead of creating duplicates.

## Kubernetes Demo

The `infra/k8s` directory contains minimal demo manifests. The Docker Compose flow is the primary target for the first working slice.
