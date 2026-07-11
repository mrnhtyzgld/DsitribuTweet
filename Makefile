COMPOSE ?= docker compose
USER_ID ?= burak
REPLAY_FILE ?= /sample-data/posts.jsonl

.PHONY: up down logs create-topics replay replay-slow replay-fast replay-burst create-profile get-feed test test-python test-scala build clean

up:
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=200

create-topics:
	$(COMPOSE) up kafka-init

replay:
	$(COMPOSE) run --rm producer --file $(REPLAY_FILE) --events-per-second 10

replay-slow:
	$(COMPOSE) run --rm producer --file $(REPLAY_FILE) --events-per-second 1

replay-fast:
	$(COMPOSE) run --rm producer --file $(REPLAY_FILE) --events-per-second 50

replay-burst:
	$(COMPOSE) run --rm producer --file $(REPLAY_FILE) --events-per-second 500

create-profile:
	curl -sS -X POST "http://localhost:8080/users/$(USER_ID)/interests" \
		-H "Content-Type: application/json" \
		-d '{"interests":["Scala distributed systems","CUDA programming","large language model inference"]}' | jq .

get-feed:
	curl -sS "http://localhost:8080/users/$(USER_ID)/feed?limit=20" | jq .

test: test-python test-scala

test-python:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -U pip
	. .venv/bin/activate && pip install -e producer[dev]
	. .venv/bin/activate && pip install -e embedding-worker[dev]
	. .venv/bin/activate && pytest producer/tests embedding-worker/tests

test-scala:
	docker run --rm -v "$$(pwd)/.m2:/root/.m2" -v "$$(pwd)/spark-stream:/workspace" -w /workspace maven:3.9.8-eclipse-temurin-17 mvn -q test
	docker run --rm -v "$$(pwd)/.m2:/root/.m2" -v "$$(pwd)/recommendation-api:/workspace" -w /workspace maven:3.9.8-eclipse-temurin-17 mvn -q test

build:
	$(COMPOSE) build

clean:
	rm -rf .venv
	$(COMPOSE) down -v
