# DistribuTweet Final Presentation Plan

Target duration: 20 minutes total.

- Slides: about 14 minutes
- Live demo: about 5 minutes
- Closing buffer: about 1 minute

Suggested split:

- Presenter 1: slides 1-9, about 9 minutes
- Presenter 2: slides 10-16 plus demo, about 11 minutes

The first part explains the motivation, RecSys-style data, Kafka, Spark, and the
distributed pipeline. The second part explains embeddings, vector search,
ranking, the API, tests, limitations, and the live demo.

## Slide 1 - Title And Goal

Time: 45 seconds

Speaker: Presenter 1

On slide:

- DistribuTweet
- Pseudo-distributed content-based recommendation for tweet streams
- Arda Onat Acar, Nihat Emre Yuzuguldu
- Goal: transform a live tweet-like stream into personalized semantic feeds

Transcript:

Hello, today we are presenting DistribuTweet. The goal is to take a live
tweet-like stream and turn it into personalized feeds using content semantics.
We wanted the project to be runnable on a laptop, but still structured like a
real distributed recommendation pipeline, with Kafka, Spark, embedding workers,
Qdrant, and a Scala API.

## Slide 2 - Presentation Roadmap

Time: 45 seconds

Speaker: Presenter 1

On slide:

- Problem and scope
- RecSys 2021 schema and data generation
- Kafka ingestion and Spark cleaning
- Embeddings, Qdrant, ranking, API
- Tests, demo, limitations, future work

Transcript:

We will first explain the problem and scope, then the RecSys 2021-style data
source and the ingestion pipeline. After that, the second part focuses on
semantic embeddings, vector storage, ranking, and the recommendation API. At the
end, we will run the demo scripts and show that the pipeline is really moving
data through the services.

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
- Included: token decode and deduplication
- Included: multilingual embeddings and vector search
- Included: transparent scoring
- Excluded: learned ranking, collaborative filtering, authentication

Transcript:

We kept the first version focused. We implemented the complete data path:
streaming ingestion, validation, token decoding, deduplication, embedding,
vector search, and ranking. We did not train a ranking model and we did not add
collaborative filtering, because those require a larger feedback pipeline. We
also left authentication and moderation outside the project scope.

## Slide 5 - Dataset Target: RecSys Challenge 2021

Time: 1 minute 15 seconds

Speaker: Presenter 1

On slide:

- Target schema: Twitter RecSys Challenge 2021
- Original task: tweet engagement prediction with fairness objectives
- Original text field is tokenized, not plain text
- Local submission uses schema-compatible synthetic data
- Real compatible TSV can be replayed with `--input-tsv`

Transcript:

The data layer targets the Twitter RecSys Challenge 2021 schema. That challenge
was about tweet engagement prediction and fairness-aware recommendation. A key
detail is that tweet text is not published as ordinary plain text; it is
represented as multilingual BERT token IDs. Since the original dataset is large
and not shipped with this submission, our default demo generates synthetic data
with the same twenty-column schema. If a compatible real TSV file is available,
the producer can read it directly with `--input-tsv`.

## Slide 6 - Data Generation And Tokenization

Time: 1 minute 15 seconds

Speaker: Presenter 1

On slide:

- `data-generator/generator.py`
- Same twenty-column RecSys-style TSV shape
- Topic pools: technology, sports, food, travel, finance, art, and more
- `text_tokens` uses real `bert-base-multilingual-cased` token IDs
- Configurable rate and message count

Transcript:

Our generator exists to make the system reproducible. It creates records in the
same style as the RecSys 2021 challenge: a twenty-column TSV row with tweet
metadata, user metadata, and tokenized text. The content is synthetic, but the
`text_tokens` field is produced by the real multilingual BERT tokenizer. This is
important because it means the Spark cleaner has to solve the same type of
token-decoding problem as it would with the real dataset.

## Slide 7 - End-To-End Architecture

Time: 1 minute

Speaker: Presenter 1

On slide:

```text
data-generator / optional TSV
  -> Kafka posts.raw
  -> Scala Spark cleaner
  -> Kafka posts.cleaned
  -> Python embedding workers
  -> Qdrant
  -> Scala recommendation API
```

Transcript:

This is the full pipeline. The generator or file producer writes raw TSV records
to Kafka. Spark reads `posts.raw`, parses and cleans the records, decodes the
tokens, and writes JSON to `posts.cleaned`. Embedding workers consume the
cleaned topic, create 384-dimensional vectors, and store them in Qdrant. The
Scala API then searches Qdrant and returns personalized feeds.

## Slide 8 - Kafka And Spark Cleaning

Time: 1 minute 30 seconds

Speaker: Presenter 1

On slide:

- Kafka 3.8.0 in KRaft mode
- Topics: `posts.raw`, `posts.cleaned`
- Three partitions for parallelism
- Spark 3.5.4 standalone cluster
- Cleaner: parse TSV, validate required fields, decode WordPiece tokens
- Deduplicate by tweet ID with event-time watermarking

Transcript:

Kafka is the communication backbone. The producer only writes to Kafka and does
not directly call Spark or the embedding workers. We create the topics with
three partitions so partitioning is visible during the demo. Spark Structured
Streaming consumes the raw topic, parses TSV records according to the RecSys
schema, validates required fields, decodes WordPiece token IDs into text, and
deduplicates by tweet ID. The result is a cleaned JSON stream.

## Slide 9 - Pseudo-Distributed Scalability

Time: 1 minute

Speaker: Presenter 1

On slide:

- One physical machine, separated services
- Kafka partitions distribute input
- Spark has one master and two workers
- Embedding workers share one consumer group
- Qdrant separates vector storage from API logic
- Services can scale without changing the event schema

Transcript:

This is pseudo-distributed because all containers run on one machine. But the
service boundaries are real. Kafka partitions distribute records. Spark has a
master and workers. The embedding services run as consumer-group members, so
more workers can be added. Qdrant stores vectors outside the API process. This
means the same architecture can be moved toward a larger deployment without
rewriting the data model.

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
- Kafka partition counts
- Spark cleaner activity
- Embedding worker group assignment
- Qdrant vector count
- Three different personalized feeds

Transcript:

For the live demo, we start the Compose environment and then run the smoke test.
After that, `demo.sh` walks through the pipeline. It shows the generator logs,
Kafka partition counts, Spark cleaner logs, embedding-worker consumer group
state, Qdrant vector count, and three feed examples. Finally,
`show-distribution.sh` is used to prove the distributed parts: Kafka partitions,
Spark workers, and embedding workers.

## Slide 15 - Evaluation And Tests

Time: 1 minute 15 seconds

Speaker: Presenter 2

On slide:

- Evaluation is functional and qualitative
- Scala tests run during Docker builds
- Tested: TSV parsing and validation
- Tested: WordPiece decoding
- Tested: ranking formula and profile behavior
- Smoke tests validate the running Compose environment

Transcript:

Our evaluation is functional and qualitative. We are not claiming a production
metric such as click-through rate or NDCG. Instead, we verify that the system
works end to end and that the main logic is tested. The Scala tests cover TSV
parsing, validation, WordPiece decoding, ranking, and deterministic behavior.
The smoke test verifies the running Compose environment, which is important
because this project has several services communicating with each other.

## Slide 16 - Limitations And Future Work

Time: 1 minute 30 seconds

Speaker: Presenter 2

On slide:

- Rule-based ranking, no learned model yet
- No collaborative filtering or impression history yet
- Local data are synthetic unless real compatible TSV is supplied
- Future: use engagement labels and fairness fields
- Future: train a ranker and evaluate NDCG
- Future: latency, Kafka lag, and multi-node Kubernetes tests

Transcript:

The main limitation is that ranking is still rule-based. We do not yet learn
from engagement labels, collaborative behavior, or impression history. The
default local data are synthetic, although the schema is designed to match the
RecSys 2021 format. Future work would use real compatible TSV data when
available, train a ranking model, evaluate metrics such as NDCG, add fairness
features from the original challenge, and measure latency and Kafka lag in a
larger deployment. In summary, DistribuTweet demonstrates the architecture of a
semantic feed recommender and makes every step visible in a local demo.

## Timing Summary

- Presenter 1 slides 1-9: about 9 minutes
- Presenter 2 slides 10-13: about 4 minutes
- Live demo slide 14: about 5 minutes
- Evaluation and closing slides 15-16: about 2 minutes
- Total: about 20 minutes
