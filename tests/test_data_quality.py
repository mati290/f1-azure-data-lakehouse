"""Unit tests for F1 data quality validation rules."""

from decimal import Decimal

import pytest

from src.data_quality import (
    BUSINESS_KEY,
    DataQualityError,
    validate_unique_key,
    validate_nonnegative_points,
)

from src.transformations import deduplicate_records


# Business key validation tests


def test_unique_business_keys_are_accepted(spark):
    df = spark.createDataFrame(
        [
            (2025, 1, "verstappen"),
            (2025, 1, "norris"),
            (2025, 2, "verstappen"),
            (2024, 1, "verstappen"),
        ],
        "season INT, round INT, driver_id STRING",
    )

    validate_unique_key(df, BUSINESS_KEY)


def test_duplicate_business_keys_are_rejected(spark):
    df = spark.createDataFrame(
        [
            (2025, 1, "verstappen"),
            (2025, 1, "verstappen"),
        ],
        "season INT, round INT, driver_id STRING",
    )

    with pytest.raises(
        DataQualityError,
        match="Duplicate business keys",
    ):
        validate_unique_key(df, BUSINESS_KEY)


def test_null_business_keys_are_rejected(spark):
    df = spark.createDataFrame(
        [
            (2025, 1, "verstappen"),
            (2025, 1, None),
        ],
        "season INT, round INT, driver_id STRING",
    )

    with pytest.raises(
        DataQualityError,
        match="Missing values in business key",
    ):
        validate_unique_key(df, BUSINESS_KEY)


def test_empty_key_definition_is_rejected(spark):
    df = spark.createDataFrame(
        [(2025, 1, "verstappen")],
        "season INT, round INT, driver_id STRING",
    )

    with pytest.raises(
        ValueError,
        match="At least one key column is required",
    ):
        validate_unique_key(df, [])


# Race points validation tests


def test_nonnegative_points_are_accepted(spark):
    df = spark.createDataFrame(
        [(25,), (18,), (0,)],
        "points INT",
    )

    validate_nonnegative_points(df)


def test_fractional_points_are_accepted(spark):
    df = spark.createDataFrame(
        [
            (Decimal("12.50"),),
            (Decimal("7.50"),),
            (Decimal("0.00"),),
        ],
        "points DECIMAL(6,2)",
    )

    validate_nonnegative_points(df)


def test_negative_points_are_rejected(spark):
    df = spark.createDataFrame(
        [(25,), (-5,), (18,)],
        "points INT",
    )

    with pytest.raises(
        DataQualityError,
        match="Invalid race points",
    ):
        validate_nonnegative_points(df)


def test_null_points_are_rejected(spark):
    df = spark.createDataFrame(
        [(25,), (None,)],
        "points INT",
    )

    with pytest.raises(
        DataQualityError,
        match="Invalid race points",
    ):
        validate_nonnegative_points(df)


# Combined transformation and validation test


def test_conflicting_records_after_deduplication_are_rejected(spark):
    df = spark.createDataFrame(
        [
            (2025, 1, "verstappen", 25),
            (2025, 1, "verstappen", 25),
            (2025, 1, "verstappen", 18),
        ],
        "season INT, round INT, driver_id STRING, points INT",
    )

    deduplicated = deduplicate_records(df)

    assert deduplicated.count() == 2

    with pytest.raises(
        DataQualityError,
        match="Duplicate business keys",
    ):
        validate_unique_key(deduplicated, BUSINESS_KEY)
