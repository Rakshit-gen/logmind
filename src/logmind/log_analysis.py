from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, count


def load_logs(spark: SparkSession, path: str) -> DataFrame:
    return spark.read.json(path)


def find_anomalies(df: DataFrame, top_n: int = 5) -> list[dict]:
    """Rank (service, message) pairs by how many ERROR lines they produced.

    This is the whole point of doing this in Spark: a real incident log
    file can be hundreds of thousands of lines across a dozen services,
    and grouping and counting that is exactly the kind of thing that
    should run in parallel across partitions instead of a python loop.
    """
    errors = df.filter(col("level") == "ERROR")
    ranked = (
        errors.groupBy("service", "message")
        .agg(count("*").alias("error_count"))
        .orderBy(col("error_count").desc())
        .limit(top_n)
    )
    return [row.asDict() for row in ranked.collect()]


def analyze_log_file(spark: SparkSession, path: str, top_n: int = 5) -> list[dict]:
    df = load_logs(spark, path)
    return find_anomalies(df, top_n=top_n)
