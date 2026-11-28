"""Unit tests for F1 race result transformations."""

from datetime import date
from decimal import Decimal

from pyspark.sql import functions as F
from pyspark.sql import types as T

from src.transformations import (
    cast_race_results,
    normalize_strings,
    deduplicate_records,
)


# Data type conversion tests


def test_cast_integer_columns(raw_race_results):
    result = cast_race_results(raw_race_results)

    integer_columns = [
        "season",
        "round",
        "driver_number",
        "grid_position",
        "position",
        "laps_completed",
        "fastest_lap_rank",
        "fastest_lap_number",
    ]

    for column in integer_columns:
        assert isinstance(
            result.schema[column].dataType,
            T.IntegerType,
        )


def test_cast_decimal_points(raw_race_results):
    result = cast_race_results(raw_race_results)

    assert result.schema["points"].dataType == T.DecimalType(6, 2)

    row = result.filter(F.col("season") == 2021).first()

    assert row["points"] == Decimal("12.50")


def test_cast_date_columns(raw_race_results):
    result = cast_race_results(raw_race_results)

    assert isinstance(
        result.schema["race_date"].dataType,
        T.DateType,
    )

    assert isinstance(
        result.schema["date_of_birth"].dataType,
        T.DateType,
    )

    row = result.filter(
        (F.col("driver_id") == "verstappen")
        & (F.col("season") == 2025)
    ).first()

    assert row["race_date"] == date(2025, 3, 16)
    assert row["date_of_birth"] == date(1997, 9, 30)


def test_cast_coordinates_and_race_time(raw_race_results):
    result = cast_race_results(raw_race_results)

    assert isinstance(
        result.schema["latitude"].dataType,
        T.DoubleType,
    )

    assert isinstance(
        result.schema["longitude"].dataType,
        T.DoubleType,
    )

    assert isinstance(
        result.schema["race_time_ms"].dataType,
        T.LongType,
    )

    row = result.filter(
        (F.col("driver_id") == "verstappen")
        & (F.col("season") == 2025)
    ).first()

    assert row["latitude"] == -37.8497
    assert row["longitude"] == 144.968
    assert row["race_time_ms"] == 5400000


def test_cast_preserves_optional_nulls(raw_race_results):
    result = cast_race_results(raw_race_results)

    row = result.filter(
        F.col("driver_id") == "hamilton"
    ).first()

    assert row["race_time_ms"] is None
    assert row["fastest_lap_rank"] is None
    assert row["fastest_lap_number"] is None



# String normalization tests


def test_normalize_trims_whitespace(spark):
    df = spark.createDataFrame(
        [("  Verstappen  ",)],
        ["last_name"],
    )

    result = normalize_strings(df)

    assert result.first()["last_name"] == "Verstappen"


def test_normalize_empty_strings_to_null(spark):
    df = spark.createDataFrame(
        [("",), ("   ",)],
        ["driver_code"],
    )

    result = normalize_strings(df)

    assert all(
        row["driver_code"] is None
        for row in result.collect()
    )


def test_normalize_preserves_existing_nulls(spark):
    df = spark.createDataFrame(
        [(None,)],
        "driver_code STRING",
    )

    result = normalize_strings(df)

    assert result.first()["driver_code"] is None


def test_normalize_preserves_numeric_values(spark):
    df = spark.createDataFrame(
        [("  Norris  ", 25)],
        "last_name STRING, points INT",
    )

    result = normalize_strings(df)
    row = result.first()

    assert row["last_name"] == "Norris"
    assert row["points"] == 25
    assert result.schema["points"].dataType == T.IntegerType()


# Deduplication tests


def test_deduplicate_removes_exact_duplicates(spark):
    df = spark.createDataFrame(
        [
            (2025, 1, "verstappen", 25),
            (2025, 1, "verstappen", 25),
            (2025, 1, "norris", 18),
        ],
        ["season", "round", "driver_id", "points"],
    )

    result = deduplicate_records(df)

    assert result.count() == 2


def test_deduplicate_preserves_unique_records(spark):
    df = spark.createDataFrame(
        [
            (2025, 1, "verstappen", 25),
            (2025, 2, "verstappen", 18),
            (2024, 1, "verstappen", 25),
        ],
        ["season", "round", "driver_id", "points"],
    )

    result = deduplicate_records(df)

    assert result.count() == 3


def test_deduplicate_preserves_conflicting_records(spark):
    df = spark.createDataFrame(
        [
            (2025, 1, "verstappen", 25),
            (2025, 1, "verstappen", 18),
        ],
        ["season", "round", "driver_id", "points"],
    )

    result = deduplicate_records(df)

    assert result.count() == 2
