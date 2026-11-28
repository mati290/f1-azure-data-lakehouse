
"""Reusable data quality checks for F1 race results."""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


BUSINESS_KEY = ["season", "round", "driver_id"]


class DataQualityError(ValueError):
    """Raised when a dataset violates a data quality rule."""


def validate_unique_key(
    df: DataFrame,
    key_columns: list[str]
) -> None:
    """Reject missing or duplicate business keys."""

    if not key_columns:
        raise ValueError("At least one key column is required")

    null_condition = F.col(key_columns[0]).isNull()

    for column in key_columns[1:]:
        null_condition = null_condition | F.col(column).isNull()

    if df.filter(null_condition).limit(1).count() > 0:
        raise DataQualityError(
            f"Missing values in business key: {key_columns}"
        )

    duplicate_keys = (
        df
        .groupBy(*key_columns)
        .count()
        .filter(F.col("count") > 1)
        .count()
    )

    if duplicate_keys > 0:
        raise DataQualityError(
            f"Duplicate business keys detected: {duplicate_keys}"
        )


def validate_nonnegative_points(df: DataFrame) -> None:
    """Reject missing or negative race points."""

    invalid_count = df.filter(
        F.col("points").isNull()
        | (F.col("points") < 0)
    ).count()

    if invalid_count > 0:
        raise DataQualityError(
            f"Invalid race points detected: {invalid_count}"
        )
