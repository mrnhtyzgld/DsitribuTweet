# DistribuTweet Demo Guide

This guide is for the final project demo. It matches the current repository
state: the default run reads the public Bright Data Twitter/X 1000-post CSV
sample, converts it into the internal stream format, and publishes it to Kafka.
The producer can also read a local CSV file or an already converted internal TSV
file.

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
- Internet access during default replay, because `data-generator` reads the
  Bright Data sample from GitHub raw unless `INPUT_CSV` points to a local file

After the first successful build, the models are cached in Docker layers. For a
fully offline demo, download the CSV sample beforehand and set `INPUT_CSV` to the
local file path.

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

The `data-generator` service starts automatically, reads:

```text
https://raw.githubusercontent.com/luminati-io/Twitter-X-dataset-samples/main/twitter-posts.csv
```

and publishes the first 1000 converted tweet records to Kafka topic `posts.raw`.

## Main Demo Script

Run:

```bash
./scripts/demo.sh
```

The script shows:

- Bright Data Twitter/X sample replay
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
  -d '{"interests":["Gaza ceasefire","Palestine solidarity","human rights"]}'
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

## Dataset Modes

Default Compose mode uses the public Bright Data sample URL:

```bash
docker compose up -d --build
```

To process only the first 10 or 100 rows, override `TOTAL_MESSAGES`:

```bash
TOTAL_MESSAGES=100 docker compose up -d --build
```

To replay a local Bright Data CSV file:

```bash
python data-generator/producer.py --input-csv /path/to/twitter-posts.csv --total 1000 --rate 100
```

To replay an already converted internal TSV file:

```bash
python data-generator/producer.py --input-tsv /path/to/internal-feature.tsv --total 10000 --rate 200
```

Downstream services do not need to change in any mode, because Kafka receives
the same internal feature schema.

## Stop And Clean Up

Stop containers:

```bash
docker compose down
```

Remove volumes if a clean run is needed:

```bash
docker compose down -v
```
