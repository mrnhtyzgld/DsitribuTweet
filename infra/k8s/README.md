# Kubernetes Demo

These manifests are a minimal demo target, not a production deployment. Docker Compose remains the primary end-to-end environment.

Build local images:

```bash
docker build -t distributweet/producer:local producer
docker build -t distributweet/spark-stream:local spark-stream
docker build -t distributweet/embedding-worker:local embedding-worker
docker build -t distributweet/recommendation-api:local recommendation-api
```

For `kind`, load the images:

```bash
kind load docker-image distributweet/spark-stream:local
kind load docker-image distributweet/embedding-worker:local
kind load docker-image distributweet/recommendation-api:local
```

Apply core services:

```bash
kubectl apply -k infra/k8s
kubectl -n distributweet get pods
```

Submit the Spark cleaner after the services are running:

```bash
./infra/k8s/spark-submit-post-cleaner.sh
```

Port-forward the API:

```bash
kubectl -n distributweet port-forward svc/recommendation-api 8080:8080
```
