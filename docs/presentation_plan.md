# DistribuTweet Final Presentation Plan

Target duration: 20 minutes total.

- Slides: about 14 minutes
- Live demo: about 5 minutes
- Closing buffer: about 1 minute

Suggested split:

- Presenter 1: slides 1-9, about 9 minutes
- Presenter 2: slides 10-16 plus demo, about 11 minutes

Presenter 1 explains the motivation, Bright Data Twitter/X dataset, CSV adapter,
Kafka ingestion, Spark cleaning, and pseudo-distributed architecture. Presenter
2 explains embeddings, Qdrant, user profiles, ranking, API, tests, limitations,
and the live demo.

## Slide 1 - Title And Goal

Time: 45 seconds

Speaker: Presenter 1

On slide:

- DistribuTweet
- Pseudo-distributed content-based recommendation for Twitter/X streams
- Arda Onat Acar, Nihat Emre Yuzuguldu
- Goal: transform a public tweet stream into personalized semantic feeds

Transcript:

Hello, today we are presenting DistribuTweet. The goal is to take a stream of
Twitter/X posts and turn it into personalized feeds using content semantics. We
wanted the project to run on a laptop, but still be organized like a real
distributed recommendation pipeline, with Kafka, Spark, embedding workers,
Qdrant, and a Scala API.

## Slide 2 - Presentation Roadmap

Time: 45 seconds

Speaker: Presenter 1

On slide:

- Problem and scope
- Bright Data Twitter/X dataset
- CSV adapter, Kafka ingestion, Spark cleaning
- Embeddings, Qdrant, ranking, API
- Tests, demo, limitations, future work

Transcript:

We will first explain the problem and project scope. Then we will show the data
source: the Bright Data Twitter/X sample and the larger 20 million record data
option. After that we explain how CSV rows enter Kafka, how Spark cleans them,
and how the second half of the system embeds posts, stores vectors, and serves
recommendations.

## Slide 3 - Problem Motivation

Time: 1 minute

Speaker: Presenter 1

On slide:

- Social feeds receive more posts than users can read
- Chronological order does not guarantee relevance
- Follow graphs and engagement history are not always available
- Cold-start users need a first recommendation signal
- Content similarity is a practical baseline

Transcript:

The core problem is feed ranking. A social platform receives many posts, but a
user only sees a small part of them. Chronological ordering is easy, but it often
misses relevance. Follow graphs and engagement histories are useful, but they
are not always available, especially for cold-start users. Our baseline is
content-based recommendation: compare the meaning of posts with the user's
explicit interests.

## Slide 4 - Scope And Design Decisions

Time: 1 minute

Speaker: Presenter 1

On slide:

- Included: streaming ingestion and validation
- Included: CSV-to-stream adapter
- Included: token decode and deduplication
- Included: multilingual embeddings and vector search
- Included: transparent scoring
- Excluded: learned ranking, collaborative filtering, authentication

Transcript:

We kept the first version focused. We implemented the complete data path:
dataset ingestion, validation, token decoding, deduplication, embedding, vector
search, and ranking. We did not train a ranking model and we did not add
collaborative filtering, because those require a larger feedback pipeline. We
also left authentication and moderation outside the project scope.

## Slide 5 - Dataset: Bright Data Twitter/X

Time: 1 minute 30 seconds

Speaker: Presenter 1

On slide:

- Default dataset: Bright Data Twitter/X posts sample
- Source: `luminati-io/Twitter-X-dataset-samples`
- Local demo uses 1000 public post rows from `twitter-posts.csv`
- Fields: `id`, `description`, `date_posted`, `hashtags`, engagement counts
- Larger source: Databricks Marketplace listing with 20M records

Transcript:

For the final version we use the Bright Data Twitter/X posts sample. It is a
public GitHub sample with around one thousand public post records. The important
field for our content-based recommender is `description`, which contains the
post text. The same data family is also available as a larger marketplace
dataset, including a Databricks listing with 20 million records. We do not ship
that large data in the zip, but the system is designed so that larger exports can
be replayed in bounded batches.

## Slide 6 - Data Adapter

Time: 1 minute 15 seconds

Speaker: Presenter 1

On slide:

- `data-generator/brightdata.py`
- Reads CSV from GitHub raw URL or local file
- Converts `description` into mBERT token IDs
- Maps date, author, hashtag, media, follower metadata
- Supports `TOTAL_MESSAGES=10`, `100`, `1000`, etc.

Transcript:

The raw sample is CSV, but our Kafka and Spark path uses a compact internal TSV
feature format. The adapter maps `id` to tweet ID, `description` to tokenized
text, `date_posted` to a Unix timestamp, and user and hashtag fields to metadata.
The text is converted with the multilingual BERT tokenizer. This keeps Spark's
job realistic: it decodes token IDs back into text before sending posts to the
embedding workers. We can also process only the first 10, 100, or 1000 rows by
changing `TOTAL_MESSAGES`.

## Slide 7 - End-To-End Architecture

Time: 1 minute

Speaker: Presenter 1

On slide:

```text
Bright Data CSV sample
  -> CSV-to-TSV adapter
  -> Kafka posts.raw
  -> Scala Spark cleaner
  -> Kafka posts.cleaned
  -> Python embedding workers
  -> Qdrant
  -> Scala recommendation API
```

Transcript:

This is the full pipeline. The producer reads the Bright Data CSV, converts each
row into our internal tweet feature format, and writes raw messages to Kafka.
Spark reads `posts.raw`, validates the records, decodes tokens, removes
duplicates, and writes JSON to `posts.cleaned`. Embedding workers consume the
cleaned topic, create 384-dimensional vectors, and store them in Qdrant. The
Scala API then searches Qdrant and returns personalized feeds.

## Slide 8 - Kafka And Spark Cleaning

Time: 1 minute 30 seconds

Speaker: Presenter 1

On slide:

- Kafka 3.8.0 in KRaft mode
- Topics: `posts.raw`, `posts.cleaned`
- Three partitions for visible parallelism
- Spark 3.5.4 standalone cluster
- Cleaner: parse TSV, validate required fields, decode WordPiece tokens
- Deduplicate by tweet ID with event-time watermarking

Transcript:

Kafka is the communication backbone. The producer only writes to Kafka and does
not directly call Spark or the embedding workers. We create the topics with
three partitions so partitioning is visible during the demo. Spark Structured
Streaming consumes the raw topic, parses the internal TSV records, validates
required fields, decodes WordPiece token IDs into text, and deduplicates by
tweet ID. The result is a cleaned JSON stream.

## Slide 9 - Pseudo-Distributed Scalability

Time: 1 minute

Speaker: Presenter 1

On slide:

- One physical machine, separated services
- Kafka partitions distribute input
- Spark has one master and two workers
- Embedding workers share one consumer group
- Qdrant separates vector storage from API logic
- Larger datasets use the same event schema and batching boundary

Transcript:

This is pseudo-distributed because all containers run on one machine. But the
service boundaries are real. Kafka partitions distribute records. Spark has a
master and workers. The embedding services run as consumer-group members, so
more workers can be added. Qdrant stores vectors outside the API process. The
same event schema can be used for a 1000-row sample or a larger Bright Data
export.

## Slide 10 - Embeddings And Qdrant

Time: 1 minute 15 seconds

Speaker: Presenter 2

On slide:

- Model: `paraphrase-multilingual-MiniLM-L12-v2`
- Vector size: 384
- Embedding workers consume `posts.cleaned`
- Qdrant collection: `posts`
- Distance metric: cosine
- Separate HTTP embedding service for user interests

Transcript:

The recommendation part begins after Spark produces cleaned text. Python
embedding workers consume the cleaned Kafka topic and encode each post with the
multilingual MiniLM sentence-transformer model. The vectors have 384 dimensions
and are stored in Qdrant using cosine distance. We also run one HTTP-only
embedding service from the same image. The Scala API calls this service when a
user creates an interest profile.

## Slide 11 - User Profile Construction

Time: 1 minute

Speaker: Presenter 2

On slide:

- User sends explicit interest phrases
- Empty phrases are removed
- Each phrase is embedded
- Vectors are averaged
- Average vector is normalized
- Profile is stored in the API process for the prototype

Transcript:

Users are represented by explicit interest phrases. For example, a user might
enter distributed systems, GPU programming, and Kafka streaming. The API removes
empty phrases, embeds each phrase, averages the vectors, and normalizes the
result. In this prototype the profile vectors are stored in memory by the API.
That is enough for the demo, and a future version could move profiles into a
separate Qdrant `users` collection.

## Slide 12 - Retrieval And Ranking

Time: 1 minute 30 seconds

Speaker: Presenter 2

On slide:

- Qdrant retrieves a candidate pool
- Cosine score is normalized from `[-1,1]` to `[0,1]`
- Recency score: `exp(-ageHours / 24)`
- Final score: `0.85 * semantic + 0.15 * recency`
- Near-duplicate text is filtered with Jaccard similarity
- Scores are returned for inspection

Transcript:

For a feed request, the API searches Qdrant with the user vector and retrieves a
larger candidate pool than the requested feed size. Cosine similarity is mapped
from `[-1,1]` to `[0,1]`, then combined with a recency score. The final formula
is 85 percent semantic similarity and 15 percent recency. After sorting, the API
filters near-duplicate text variants using Jaccard similarity over word sets.
The response returns semantic, recency, and final scores, so the ranking is easy
to explain.

## Slide 13 - API And Interfaces

Time: 1 minute

Speaker: Presenter 2

On slide:

- `POST /users/{userId}/interests`
- `GET /users/{userId}/feed?limit=20`
- `GET /health`
- Recommendation API: `localhost:8081`
- Spark master UI: `localhost:8080`
- Qdrant dashboard: `localhost:6333/dashboard`

Transcript:

The API is written in Scala with http4s and Circe. The main endpoint for profile
creation is `POST /users/{userId}/interests`. The main feed endpoint is
`GET /users/{userId}/feed`. The service also exposes a health endpoint. During
the demo we can also open the Spark master UI and Qdrant dashboard to show that
the system is not just returning mocked data.

## Slide 14 - Live Demo Script

Time: 5 minutes

Speaker: Presenter 2, Presenter 1 assists with terminals if needed

On slide:

```bash
docker compose up -d --build
./scripts/smoke-test.sh
./scripts/demo.sh
./scripts/show-distribution.sh
```

Show:

- Service health
- Bright Data sample replay logs
- Kafka partition counts
- Spark cleaner activity
- Embedding worker group assignment
- Qdrant vector count
- Three different personalized feeds

Transcript:

For the live demo, we start the Compose environment and then run the smoke test.
After that, `demo.sh` walks through the pipeline. It shows the dataset replay
logs, Kafka partition counts, Spark cleaner logs, embedding-worker consumer
group state, Qdrant vector count, and three feed examples. Finally,
`show-distribution.sh` is used to prove the distributed parts: Kafka partitions,
Spark workers, and embedding workers.

## Slide 15 - Evaluation And Tests

Time: 1 minute 15 seconds

Speaker: Presenter 2

On slide:

- Evaluation is functional and qualitative
- Python tests cover Bright Data CSV conversion
- Scala tests run during Docker builds
- Tested: TSV parsing and validation
- Tested: WordPiece decoding
- Tested: ranking formula and profile behavior
- Smoke tests validate the running Compose environment

Transcript:

Our evaluation is functional and qualitative. We are not claiming a production
metric such as click-through rate or NDCG. Instead, we verify that the system
works end to end and that the main logic is tested. Python tests cover the CSV
adapter. Scala tests cover TSV parsing, validation, WordPiece decoding, ranking,
and deterministic behavior. The smoke test verifies the running Compose
environment, which is important because this project has several services
communicating with each other.

## Slide 16 - Limitations And Future Work

Time: 1 minute 30 seconds

Speaker: Presenter 2

On slide:

- Rule-based ranking, no learned model yet
- No collaborative filtering or impression history yet
- Public sample is small and not topic-balanced
- Future: process larger Bright Data export, e.g. 20M records
- Future: use engagement counts and train a ranker
- Future: latency, Kafka lag, and multi-node Kubernetes tests

Transcript:

The main limitation is that ranking is still rule-based. We do not yet learn
from engagement counts, collaborative behavior, or impression history. The
public sample is useful for a real-data demo, but it is small and not balanced
as a recommender benchmark. Future work would process a larger Bright Data
export, such as the 20 million record dataset, train a ranking model, evaluate
metrics such as NDCG, and measure latency and Kafka lag in a larger deployment.
In summary, DistribuTweet demonstrates the architecture of a semantic feed
recommender and makes every step visible in a local demo.

## Timing Summary

- Presenter 1 slides 1-9: about 9 minutes
- Presenter 2 slides 10-13: about 4 minutes
- Live demo slide 14: about 5 minutes
- Evaluation and closing slides 15-16: about 2 minutes
- Total: about 20 minutes
