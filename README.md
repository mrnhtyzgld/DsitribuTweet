# DistribuTweet

DistribuTweet is a small end-to-end content-based recommendation system. It converts bounded subsets of the Twitter-sponsored ACM RecSys Challenge 2020 dataset into replayable post events, ingests them through Kafka, cleans them with Spark Structured Streaming, embeds cleaned text with `intfloat/multilingual-e5-small`, stores vectors in Qdrant, and serves personalized feeds through a Scala http4s API.

## Architecture

```text
RecSys 2020 TSV subset
        -> JSONL converter
        -> JSONL replay
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
make convert-recsys RECSYS_FILE=./data/recsys2020/training.tsv RECSYS_LIMIT=100
make replay
make seed-demo-users
make get-feed
```

The full RecSys dataset is not downloaded automatically. Put the downloaded
`training.tsv` under `data/recsys2020/training.tsv`, then choose a bounded
`RECSYS_LIMIT` for local runs. Use `make replay-sample` only for the tiny bundled
smoke-test dataset.

Open the local dashboard:

```bash
make ui
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
GET  /posts?limit=100
GET  /demo/users
POST /demo/users
GET  /health
GET  /metrics
```

The dashboard at `http://localhost:8080` shows indexed posts from Qdrant, bundled demo users, per-user feeds, and a custom profile form.

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

## RecSys 2020 Data

The full Twitter-sponsored ACM RecSys Challenge 2020 dataset is not stored in
this repository. After downloading `training.tsv` from the challenge site, a
bounded subset can be converted into the internal JSONL event format and replayed
through the same Kafka pipeline:

```bash
make convert-recsys RECSYS_FILE=./data/recsys2020/training.tsv RECSYS_LIMIT=10000
make replay
```

Use smaller values such as `RECSYS_LIMIT=10` or `RECSYS_LIMIT=100` for quick
local checks. The converter reads the original Ctrl-A-separated TSV format and
maps each row to the project event schema. If a BERT `vocab.txt` is available,
pass `RECSYS_VOCAB=./data/recsys2020/vocab.txt` so the converter can decode the
`text_tokens` field. Otherwise it still produces valid events for pipeline
stress tests.

## Qdrant point IDs

Qdrant accepts unsigned integers or UUIDs as point identifiers. The system derives deterministic UUIDs from `postId` and `userId`, while preserving the original IDs in payloads. Replaying the same post therefore upserts the same point instead of creating duplicates.

## Kubernetes Demo

The `infra/k8s` directory contains minimal demo manifests. The Docker Compose flow is the primary target for the first working slice.
