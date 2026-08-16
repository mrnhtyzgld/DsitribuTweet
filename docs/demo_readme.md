# DistribuTweet Demo Guide

This demo shows the end-to-end pipeline with a bounded subset of the Twitter-sponsored ACM RecSys Challenge 2020 dataset.

## Roles During Demo

- Presenter 1: dataset, ingestion, Kafka, Spark cleaning.
- Presenter 2: embeddings, Qdrant, recommendation API, dashboard, results.

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Downloaded RecSys Challenge 2020 `training.tsv`
- Optional: BERT `vocab.txt` for decoding `text_tokens`

Place the dataset like this:

```bash
mkdir -p data/recsys2020
# Put the downloaded file at:
# data/recsys2020/training.tsv
```

The full dataset is intentionally not included in the zip because it is large and externally licensed. The official dataset page is:

```text
https://www.recsyschallenge.com/2020/
```

## Quick Demo Flow

Start the services:

```bash
make up
make create-topics
```

Convert a bounded subset. For a fast demo, use 100 rows:

```bash
make convert-recsys RECSYS_LIMIT=100
```

If a BERT vocabulary is available:

```bash
make convert-recsys RECSYS_LIMIT=100 RECSYS_VOCAB=./data/recsys2020/vocab.txt
```

Replay the converted subset through Kafka:

```bash
make replay
```

Create demo user profiles and fetch a feed:

```bash
make seed-demo-users
make get-feed
```

Open the dashboard:

```bash
make ui
```

Then visit:

```text
http://localhost:8080
```

## What To Show

1. The pipeline row at the top of the dashboard.
2. Indexed post count after replay.
3. Demo user profiles and their interests.
4. A generated feed with semantic, recency, and final scores.
5. Custom user form with a few interest phrases.

## Scaling The Same Demo

Use the same commands with a larger subset:

```bash
make convert-recsys RECSYS_LIMIT=10000
make replay
```

The downstream architecture does not change for larger subsets. Kafka receives events, Spark validates and deduplicates them, the embedding worker batches indexing work, Qdrant stores vectors, and the Scala API queries the same collections.

## Useful Health Checks

```bash
curl http://localhost:8080/health
curl http://localhost:8001/health
curl "http://localhost:8080/posts?limit=10"
```

## Cleanup

```bash
make down
```

To remove volumes too:

```bash
make clean
```
