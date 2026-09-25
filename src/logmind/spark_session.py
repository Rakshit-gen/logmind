from pyspark.sql import SparkSession


def get_spark(app_name: str = "logmind") -> SparkSession:
    # local[2] and 1g on purpose, this runs on a laptop alongside everything
    # else you have open, local[*] grabs every core and is unfriendly.
    return (
        SparkSession.builder.appName(app_name)
        .master("local[2]")
        .config("spark.driver.memory", "1g")
        .config("spark.sql.shuffle.partitions", "8")
        .getOrCreate()
    )
