
"""Integration tests for the Gold analytics snapshot."""

import pandas as pd
import pytest

from data_loader import (
    BUSINESS_KEY,
    REQUIRED_COLUMNS,
    load_dashboard_data,
)


@pytest.fixture(scope="module")
def dashboard_data():
    return load_dashboard_data()


def test_snapshot_is_not_empty(dashboard_data):
    df, _ = dashboard_data

    assert not df.empty


def test_required_columns(dashboard_data):
    df, _ = dashboard_data

    assert REQUIRED_COLUMNS.issubset(df.columns)


def test_business_key_uniqueness(dashboard_data):
    df, _ = dashboard_data

    assert not df.duplicated(BUSINESS_KEY).any()


def test_business_key_not_null(dashboard_data):
    df, _ = dashboard_data

    assert not df[BUSINESS_KEY].isna().any().any()


def test_points_are_valid(dashboard_data):
    df, _ = dashboard_data

    assert pd.api.types.is_numeric_dtype(df["points"])
    assert df["points"].notna().all()
    assert df["points"].ge(0).all()


def test_race_date_type(dashboard_data):
    df, _ = dashboard_data

    assert pd.api.types.is_datetime64_any_dtype(
        df["race_date"]
    )


def test_metadata_record_count(dashboard_data):
    df, metadata = dashboard_data

    assert len(df) == metadata["record_count"]


def test_metadata_season_range(dashboard_data):
    df, metadata = dashboard_data

    assert df["season"].min() == metadata["season_from"]
    assert df["season"].max() == metadata["season_to"]


def test_metadata_export_timestamp(dashboard_data):
    _, metadata = dashboard_data

    timestamp = pd.to_datetime(
        metadata["exported_at_utc"],
        utc=True,
        errors="raise",
    )

    assert pd.notna(timestamp)


def test_classification_flags(dashboard_data):
    df, _ = dashboard_data

    flags = [
        "is_classified",
        "is_win",
        "is_podium",
        "is_dnf",
        "is_dns",
        "is_dsq",
    ]

    for flag in flags:
        assert pd.api.types.is_bool_dtype(df[flag])
        assert df[flag].notna().all()
