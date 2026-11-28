
"""Reusable PySpark transformations for F1 race results."""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql import types as T


def cast_race_results(df: DataFrame) -> DataFrame:
    """Convert raw race result fields to their target data types."""

    return (
        df
        .withColumn("season", F.col("season").cast(T.IntegerType()))
        .withColumn("round", F.col("round").cast(T.IntegerType()))
        .withColumn("race_date", F.to_date("race_date", "yyyy-MM-dd"))
        .withColumn("date_of_birth", F.to_date("date_of_birth", "yyyy-MM-dd"))
        .withColumn("latitude", F.col("latitude").cast(T.DoubleType()))
        .withColumn("longitude", F.col("longitude").cast(T.DoubleType()))
        .withColumn("driver_number", F.col("driver_number").cast(T.IntegerType()))
        .withColumn("grid_position", F.col("grid_position").cast(T.IntegerType()))
        .withColumn("position", F.col("position").cast(T.IntegerType()))
        .withColumn("points", F.col("points").cast(T.DecimalType(6, 2)))
        .withColumn("laps_completed", F.col("laps_completed").cast(T.IntegerType()))
        .withColumn("race_time_ms", F.col("race_time_ms").cast(T.LongType()))
        .withColumn("fastest_lap_rank", F.col("fastest_lap_rank").cast(T.IntegerType()))
        .withColumn("fastest_lap_number", F.col("fastest_lap_number").cast(T.IntegerType()))
    )


def normalize_strings(df: DataFrame) -> DataFrame:
    """Trim string values and replace empty strings with NULL."""

    string_columns = [
        field.name
        for field in df.schema.fields
        if isinstance(field.dataType, T.StringType)
    ]

    for column in string_columns:
        df = df.withColumn(
            column,
            F.when(
                F.trim(F.col(column)) == "",
                F.lit(None)
            ).otherwise(F.trim(F.col(column)))
        )

    return df


def deduplicate_records(df: DataFrame) -> DataFrame:
    """Remove exact duplicate records."""

    return df.dropDuplicates()
