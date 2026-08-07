FROM maven:3.9.8-eclipse-temurin-17 AS builder
WORKDIR /workspace
COPY pom.xml ./
COPY src ./src
RUN mvn -q -DskipTests package

FROM apache/spark:3.5.1
USER root
RUN mkdir -p /opt/distributweet /checkpoints /data && chown -R spark:spark /opt/distributweet /checkpoints /data
COPY --from=builder --chown=spark:spark /workspace/target/spark-stream-0.1.0.jar /opt/distributweet/spark-stream.jar
USER spark

ENTRYPOINT ["/opt/spark/bin/spark-submit", "--class", "com.distributweet.stream.PostCleanerApp", "--master", "local[*]", "/opt/distributweet/spark-stream.jar"]
