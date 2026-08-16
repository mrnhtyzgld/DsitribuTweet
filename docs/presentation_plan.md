# DistribuTweet Final Presentation Plan

Target duration: 20 minutes total

- Slides: about 14-15 minutes
- Live demo: about 4-5 minutes
- Closing / questions buffer: about 1 minute

Suggested split:

- Presenter 1: slides 1-9, about 8-9 minutes
- Presenter 2: slides 10-16 plus demo, about 10-11 minutes

The first half explains the problem, dataset, ingestion, and distributed data pipeline. The second half explains semantic recommendation, API behavior, evaluation, demo, and future work.

## Slide 1 - Title And One-Sentence Goal

Time: 45 seconds

Speaker: Presenter 1

On slide:

- DistribuTweet
- A Distributed Content-Based Feed Recommendation Prototype
- Arda Onat Acar, Nihat Emre Yuzuguldu
- Goal: turn tweet-like stream events into personalized semantic feeds.

Transcript:

Hello, today we are presenting DistribuTweet. In one sentence, our project turns tweet-like stream events into personalized semantic feeds. We wanted to build something that is small enough to run locally, but still has the same kind of components used in a distributed recommendation pipeline: Kafka, Spark, embeddings, vector search, and an API layer.

## Slide 2 - Presentation Roadmap

Time: 45 seconds

Speaker: Presenter 1

On slide:

- Part 1: problem, dataset, ingestion, cleaning, scalability
- Part 2: embeddings, Qdrant, ranking, API, demo, evaluation
- Demo: RecSys subset conversion -> replay -> dashboard feed

Transcript:

We split the presentation into two parts. In the first part, I will explain the problem, the RecSys dataset, and the ingestion and cleaning pipeline. In the second part, my teammate will explain embeddings, vector storage, ranking, the API, and the dashboard demo. At the end, we will run the system with a bounded subset of the RecSys data and show a personalized feed.

## Slide 3 - Problem Motivation

Time: 1 minute

Speaker: Presenter 1

On slide:

- A social feed receives more posts than a user can read.
- Chronological order is simple but often irrelevant.
- Follow graphs are useful, but not always available.
- Cold-start users have little behavior history.
- We need a content-based baseline that works from text.

Transcript:

The motivation is the feed ranking problem. A social media platform continuously receives more posts than a user can consume. Chronological ordering is easy to implement, but it does not necessarily show relevant posts. A follow graph helps, but it is not always available, and it does not solve every cold-start case. Since we are working in a course project setting, we decided to build a content-based recommendation baseline. The system should be able to recommend posts using only the meaning of the post and the user's stated interests.

## Slide 4 - Scope And Design Decisions

Time: 1 minute

Speaker: Presenter 1

On slide:

- Included:
  - streaming ingestion
  - validation and deduplication
  - multilingual text embeddings
  - vector retrieval
  - transparent reranking
- Excluded for first version:
  - collaborative filtering
  - learned ranking model
  - authentication and moderation

Transcript:

We intentionally kept the scope focused. The implemented version includes a streaming ingestion path, validation, deduplication, text embeddings, vector retrieval, and a transparent ranking formula. We excluded collaborative filtering and learned ranking from the first version because those require larger feedback pipelines and model training. We also did not build authentication, moderation, or full production reliability. The goal was to make the distributed recommendation path work end to end.

## Slide 5 - Dataset: ACM RecSys Challenge 2020

Time: 1 minute 15 seconds

Speaker: Presenter 1

On slide:

- External data source: Twitter-sponsored ACM RecSys Challenge 2020
- Task: tweet engagement prediction in Twitter Home Timeline
- Large-scale release:
  - 160M public tweets for training
  - 40M public tweets for validation/testing
- Dataset is linked, not zipped, because of size and access terms.

Transcript:

For the main data source, we selected the Twitter-sponsored ACM RecSys Challenge 2020 dataset. It was released for tweet engagement prediction in Twitter's Home Timeline. Twitter's engineering summary describes it as 160 million public tweets for training and 40 million public tweets for validation and testing. We do not include the full dataset in the project zip because it is very large and has external access terms. Instead, the paper and demo guide provide the official dataset link, and the repo contains the converter needed to process a downloaded subset.

## Slide 6 - Dataset Adaptation Strategy

Time: 1 minute 15 seconds

Speaker: Presenter 1

On slide:

- Original file: `training.tsv`
- Format: headerless, Ctrl-A-separated rows
- Adapter maps:
  - `tweet_id` -> `postId`
  - `a_user_id` -> `authorId`
  - `timestamp` -> `createdAt`
  - `text_tokens`, hashtags, domains, links -> `text`
- Supports `--limit` and `--offset`
- Example: first 10, 100, or 10000 rows

Transcript:

The RecSys file is not directly in our event schema. It is a headerless TSV file separated by the Ctrl-A character. So we added an adapter in the producer package. It maps tweet IDs into post IDs, author IDs into author IDs, Unix timestamps into ISO timestamps, and text-related columns into our text field. The important part is that the converter supports limit and offset. That means on a personal laptop we can process the first 10, 100, or 10000 rows, while the downstream pipeline sees the same schema it would see for a much larger run.

## Slide 7 - End-To-End Architecture

Time: 1 minute

Speaker: Presenter 1

On slide:

```text
RecSys TSV subset
  -> JSONL converter
  -> Kafka posts.raw
  -> Spark stream cleaner
  -> Kafka posts.cleaned + Parquet archive
  -> Embedding worker
  -> Qdrant vector DB
  -> Scala API + dashboard
```

Transcript:

This is the complete architecture. We start from a bounded RecSys subset and convert it into JSONL. The producer replays JSONL events into Kafka. Spark consumes the raw topic, validates events, deduplicates them, and writes the cleaned stream back to Kafka. In parallel, it archives cleaned records as Parquet. The embedding worker consumes cleaned posts, generates vectors, and stores them in Qdrant. Finally, the Scala API reads from Qdrant and serves the feed and dashboard.

## Slide 8 - Kafka And Spark Cleaning Layer

Time: 1 minute 30 seconds

Speaker: Presenter 1

On slide:

- Kafka topics:
  - `posts.raw`
  - `posts.cleaned`
  - `recommendation.events`
- Spark Structured Streaming:
  - JSON parsing
  - required-field checks
  - language filtering
  - minimum text length
  - event-time watermark
  - deduplication by `postId`
- Output: cleaned Kafka topic + Parquet archive

Transcript:

Kafka decouples the services. The producer does not call Spark or the embedding worker directly; it only publishes events to `posts.raw`. Spark Structured Streaming then reads that topic. The cleaner parses JSON, checks required fields, filters unsupported languages and very short texts, converts timestamps, applies an event-time watermark, and deduplicates by post ID. The output goes to `posts.cleaned`, and a Parquet archive is written at the same time. This gives us a clean online stream and an offline record of processed data.

## Slide 9 - Distributed Scalability Story

Time: 1 minute

Speaker: Presenter 1

On slide:

- Kafka topics use partitions.
- Spark can scale with more executors.
- Embedding workers can scale as a consumer group.
- Qdrant stores vectors separately from API logic.
- API can be replicated because profile/feed operations are stateless around Qdrant.
- Docker Compose for local demo, Kubernetes manifests for cluster demo.

Transcript:

Although the demo runs locally, the service boundaries were chosen for scale. Kafka topics can be partitioned. Spark can run with more executors. Multiple embedding workers can share the same consumer group and index posts in parallel. Qdrant separates vector storage from the API. The recommendation API itself can be replicated because it stores profiles and posts in Qdrant. Docker Compose is the main demo target, and Kubernetes manifests are included as a minimal cluster deployment example. I will now hand over to the recommendation side.

## Slide 10 - Embeddings And Qdrant

Time: 1 minute 15 seconds

Speaker: Presenter 2

On slide:

- Model: `intfloat/multilingual-e5-small`
- Vector size: 384
- Post format: `passage: <post text>`
- Query format: `query: <interest text>`
- Qdrant collections:
  - `posts`
  - `users`
- Deterministic UUIDs make replay idempotent.

Transcript:

The recommendation part starts with semantic embeddings. We use `intfloat/multilingual-e5-small`, which produces 384-dimensional vectors. We follow the E5 convention by encoding posts with the `passage:` prefix and user interests with the `query:` prefix. Qdrant stores two collections: one for post vectors and one for user profile vectors. We also derive deterministic UUIDs from post IDs and user IDs, so if the same data is replayed, Qdrant updates the same point instead of creating duplicates.

## Slide 11 - User Profile Construction

Time: 1 minute

Speaker: Presenter 2

On slide:

- User gives explicit interest phrases.
- Empty interests are removed.
- Each phrase is embedded.
- Vectors are averaged.
- Average vector is normalized.
- Result is stored in Qdrant `users` collection.

Transcript:

In this version, user profiles are explicit. A user gives a list of interests, for example Scala distributed systems, CUDA programming, or football transfer news. The API removes empty values, embeds every phrase, averages the vectors, and normalizes the average. This gives one vector representation for the user. That vector is stored in Qdrant, so later feed requests can retrieve it without recomputing the profile every time.

## Slide 12 - Candidate Retrieval And Ranking

Time: 1 minute 30 seconds

Speaker: Presenter 2

On slide:

- Candidate retrieval: cosine search over post vectors.
- Candidate count is larger than final feed size.
- Stale posts are filtered by max age.
- Final score:

```text
0.85 * semanticSimilarity
+ 0.15 * recencyScore
- authorPenalty
```

- Scores are returned for inspection.

Transcript:

When a feed request arrives, the API retrieves the user vector and searches the Qdrant posts collection with cosine similarity. We retrieve more candidates than the final requested feed size, because we still need to apply recency and diversity rules. Stale posts are filtered by maximum age. Then the ranker computes a final score: 85 percent semantic similarity, 15 percent recency, minus a small author penalty. The author penalty prevents the feed from showing too many consecutive posts from the same author. We return semantic, recency, and final scores in the API so the result is explainable during the demo.

## Slide 13 - API And Dashboard

Time: 1 minute

Speaker: Presenter 2

On slide:

- Scala 2.13, cats-effect, http4s
- Key endpoints:
  - `POST /users/{userId}/interests`
  - `GET /users/{userId}/feed`
  - `GET /posts`
  - `GET /demo/users`
  - `GET /health`
- Dashboard:
  - indexed posts
  - demo users
  - feed cards
  - score breakdowns

Transcript:

The API is written in Scala using cats-effect and http4s. It exposes endpoints for creating user profiles, fetching feeds, listing indexed posts, seeding demo users, and health checks. The root endpoint serves a small dashboard. The dashboard is useful because it turns the backend into something visible: we can see indexed posts, demo users, generated feeds, and the score breakdown for each recommended item.

## Slide 14 - Live Demo Script

Time: 4 to 5 minutes

Speaker: Presenter 2, with Presenter 1 assisting if needed

On slide:

```bash
make up
make create-topics
make convert-recsys RECSYS_LIMIT=100
make replay
make seed-demo-users
make get-feed
make ui
```

Show:

- `http://localhost:8080`
- indexed post count
- one demo user's feed
- one custom profile

Transcript:

For the live demo, we start the services with Docker Compose, create the Kafka topics, convert a bounded RecSys subset, and replay it through Kafka. Then we seed demo user profiles and fetch an example feed. In the browser dashboard, first we show that posts are indexed. Then we open one of the demo users and show the recommended feed. Finally, we create a custom profile with a few interest phrases and show that the system generates a feed for it using the same API.

## Slide 15 - Evaluation And Test Coverage

Time: 1 minute 15 seconds

Speaker: Presenter 2

On slide:

- Evaluation type: functional and qualitative
- Producer tests:
  - RecSys conversion
  - conversion limits
  - JSONL replay validation
- Spark tests:
  - malformed records
  - unsupported language
  - short text
  - duplicate posts
- API/ranking tests:
  - profile seeding
  - vector averaging
  - score formula
  - stale post filtering

Transcript:

Our evaluation is functional and qualitative. We are not claiming a production recommender benchmark such as click-through rate or NDCG. Instead, we verify that the pipeline works and that important behavior is tested. Producer tests cover RecSys conversion, conversion limits, and JSONL replay validation. Spark tests cover malformed data, language filtering, short text filtering, and deduplication. API and ranking tests cover profile creation, vector averaging, score calculation, and stale post filtering.

## Slide 16 - Limitations, Future Work, And Closing

Time: 1 minute 30 seconds

Speaker: Presenter 2

On slide:

- Limitations:
  - rule-based ranking
  - no collaborative filtering yet
  - no impression history yet
  - RecSys token text needs vocabulary/preprocessing
- Future work:
  - use engagement columns
  - train ranking model
  - larger RecSys runs
  - latency and Kafka lag metrics
  - multi-replica Kubernetes test

Transcript:

The main limitation is that the current ranker is rule-based. The RecSys dataset contains engagement columns, so a natural next step is to use those columns for training or tuning a learned ranking model. Another limitation is that RecSys provides tokenized tweet text, so semantic quality depends on decoding or preprocessing the tokens correctly. For future work, we would run larger RecSys subsets or the full corpus, add latency and Kafka lag metrics, and test a multi-replica Kubernetes deployment. To summarize, DistribuTweet shows that a semantic feed recommender can be built from modular distributed components and demonstrated locally with bounded subsets of a large Twitter dataset.

## Timing Summary

- Presenter 1 slides 1-9: about 8.5 minutes
- Presenter 2 slides 10-13: about 4.75 minutes
- Live demo slide 14: about 4.5 minutes
- Evaluation and closing slides 15-16: about 2.75 minutes
- Total: about 20 minutes
