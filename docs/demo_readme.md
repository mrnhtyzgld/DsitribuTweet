# DistribuTweet Demo Guide

This guide is for the final project demo. It matches the current repository
state: the default run uses a RecSys 2021 feature-schema-compatible synthetic
tweet stream, and the producer can also read a compatible real TSV file with
`--input-tsv`.

## Presenter Split

Presenter 1 covers the dataset, Kafka ingestion, Spark cleaning, and the
pseudo-distributed architecture.

Presenter 2 covers embeddings, Qdrant, ranking, API behavior, smoke tests, and
the live demo commands.

## Prerequisites

- Docker and Docker Compose
- Around 6 GB free memory
- Internet access for the first build, because the Docker images download Scala
  dependencies, the MiniLM embedding model, and the multilingual BERT vocabulary

After the first successful build, the main demo can be restarted locally without
downloading the models again.

## Start The System

If an older demo is already running, stop it first. In this workspace I saw old
`distributweet-*` containers using ports `8080` and `6333`; those ports are
needed by the current Compose file.

```bash
docker compose up -d --build
```

Wait until the API and embedding service are healthy:

```bash
docker compose ps
curl http://localhost:8081/health
curl http://localhost:8000/health
```

The `data-generator` service starts automatically and publishes RecSys
2021-style feature TSV records to Kafka topic `posts.raw`.

## Main Demo Script

Run:

```bash
./scripts/demo.sh
```

The script shows:

- generated RecSys-style tweet stream
- Kafka `posts.raw` partition counts
- Spark cleaner logs
- embedding worker consumer-group distribution
- Qdrant vector collection status
- three personalized feed examples

This is the best script to use during the presentation because it narrates the
pipeline from ingestion to recommendation.

## Smoke Test

Run:

```bash
./scripts/smoke-test.sh
```

This checks that the running services can produce records, clean them, embed
them, store vectors, create a user profile, and return a feed from the API.

## Distribution Proof

Run:

```bash
./scripts/show-distribution.sh
```

This shows Kafka partition distribution, Spark workers, and embedding worker
consumer-group state.

To show horizontal worker scaling:

```bash
docker compose up -d --scale embedding-worker=3
./scripts/show-distribution.sh
```

The Kafka partitions should be redistributed across the available embedding
workers. The default Compose file uses two embedding-worker replicas.

## Manual API Demo

Create a user profile:

```bash
curl -X POST localhost:8081/users/demo-user/interests \
  -H 'Content-Type: application/json' \
  -d '{"interests":["GPU programming","distributed systems","Kafka streaming"]}'
```

Fetch a personalized feed:

```bash
curl 'localhost:8081/users/demo-user/feed?limit=5'
```

Each item contains `semanticSimilarity`, `recencyScore`, and `finalScore`, so the
ranking can be explained during the demo.

## Useful Interfaces

| Service | URL |
|---|---|
| Recommendation API health | `http://localhost:8081/health` |
| Spark master UI | `http://localhost:8080` |
| Spark application UI | `http://localhost:4040` |
| Qdrant dashboard | `http://localhost:6333/dashboard` |
| Embedding service health | `http://localhost:8000/health` |

## Optional Real RecSys TSV Mode

The default Docker Compose run uses the synthetic generator. If a compatible
RecSys 2021 TSV file is available, the producer supports file replay:

```bash
python data-generator/producer.py --input-tsv /path/to/recsys-file.tsv --total 10000 --rate 200
```

Downstream services do not need to change, because the parser uses the same
feature columns and ignores additional engagement label columns when present.

## Stop And Clean Up

Stop containers:

```bash
docker compose down
```

Remove volumes if a clean run is needed:

```bash
docker compose down -v
```
