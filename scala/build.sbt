ThisBuild / organization := "com.bil401"
ThisBuild / version      := "0.1.0"

// Spark 3.5 Scala 2.13'u de destekliyor, ama 2.12 ekosistemi daha stabil.
// Iki modul de 2.12'de kalarak cross-build karmasikligindan kaciniyoruz.
ThisBuild / scalaVersion := "2.12.20"

// Not: 2.13'e ozgu API'ler (scala.util.Using, Either.orElse, Option.zip,
// String.toDoubleOption) burada derlenmez -- 2.12 karsiliklarini kullanin.
ThisBuild / scalacOptions ++= Seq(
  "-deprecation",
  "-feature",
  "-unchecked"
)

// Calisma zamanindaki apache/spark:3.5.4 imajiyla ayni surum olmali
val sparkVersion  = "3.5.4"
val http4sVersion = "0.23.27"
val circeVersion  = "0.14.9"

lazy val mergeStrategySettings = assembly / assemblyMergeStrategy := {
  case PathList("META-INF", "services", _ @_*) => MergeStrategy.concat
  case PathList("META-INF", _ @_*)             => MergeStrategy.discard
  case "module-info.class"                     => MergeStrategy.discard
  case x if x.endsWith("/module-info.class")   => MergeStrategy.discard
  case _                                       => MergeStrategy.first
}

// Ortak model + JSON codec'leri. Hem Spark isi hem API bunu kullanir.
lazy val common = (project in file("common"))
  .settings(
    name := "common",
    libraryDependencies ++= Seq(
      "io.circe" %% "circe-core"    % circeVersion,
      "io.circe" %% "circe-generic" % circeVersion,
      "io.circe" %% "circe-parser"  % circeVersion,
      "org.scalameta" %% "munit" % "1.0.0" % Test
    )
  )

lazy val sparkCleaner = (project in file("spark-cleaner"))
  .dependsOn(common)
  .settings(
    name := "spark-cleaner",
    libraryDependencies ++= Seq(
      // Cluster tarafindan saglaniyor -> Provided (fat jar'i sismesin)
      "org.apache.spark" %% "spark-core" % sparkVersion % Provided,
      "org.apache.spark" %% "spark-sql"  % sparkVersion % Provided,
      // Kafka connector fat jar'a girmeli
      "org.apache.spark" %% "spark-sql-kafka-0-10" % sparkVersion,
      "org.scalameta" %% "munit" % "1.0.0" % Test
    ),
    assembly / assemblyJarName := "spark-cleaner.jar",
    mergeStrategySettings
  )

lazy val recApi = (project in file("rec-api"))
  .dependsOn(common)
  .settings(
    name := "rec-api",
    libraryDependencies ++= Seq(
      "org.http4s" %% "http4s-ember-server" % http4sVersion,
      "org.http4s" %% "http4s-ember-client" % http4sVersion,
      "org.http4s" %% "http4s-circe"        % http4sVersion,
      "org.http4s" %% "http4s-dsl"          % http4sVersion,
      "io.circe"   %% "circe-generic"       % circeVersion,
      "io.circe"   %% "circe-parser"        % circeVersion,
      "org.slf4j"   % "slf4j-simple"        % "2.0.13",
      "org.scalameta" %% "munit" % "1.0.0" % Test
    ),
    assembly / assemblyJarName := "rec-api.jar",
    mergeStrategySettings
  )

lazy val root = (project in file("."))
  .aggregate(common, sparkCleaner, recApi)
  .settings(name := "distributweet", publish / skip := true)
