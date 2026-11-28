
"""Data loading and validation for the F1 dashboard."""

import json
from pathlib import Path

import pandas as pd
import streamlit as st


DATA_DIR = Path(__file__).resolve().parent / "data"

SNAPSHOT_PATH = DATA_DIR / "race_results.parquet"
METADATA_PATH = DATA_DIR / "metadata.json"

BUSINESS_KEY = ["season", "round", "driver_id"]

REQUIRED_COLUMNS = {
    "race_id",
    "season",
    "round",
    "race_name",
    "race_date",
    "driver_id",
    "driver_name",
    "driver_code",
    "constructor_id",
    "constructor_name",
    "circuit_id",
    "circuit_name",
    "country",
    "grid_position",
    "finish_position",
    "positions_gained",
    "points",
    "status",
    "is_classified",
    "is_win",
    "is_podium",
    "is_dnf",
    "is_dns",
    "is_dsq",
}


@st.cache_data(show_spinner=False)
def load_race_results() -> pd.DataFrame:
    """Load, validate and normalize the Gold snapshot."""

    if not SNAPSHOT_PATH.is_file():
        raise FileNotFoundError(
            f"Dashboard snapshot not found: {SNAPSHOT_PATH}"
        )

    df = pd.read_parquet(SNAPSHOT_PATH)

    if df.empty:
        raise ValueError("Dashboard snapshot is empty.")

    missing_columns = REQUIRED_COLUMNS - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    df["race_date"] = pd.to_datetime(
        df["race_date"],
        errors="raise",
    )

    df["points"] = pd.to_numeric(
        df["points"],
        errors="raise",
    ).astype("float64")

    if df[BUSINESS_KEY].isna().any().any():
        raise ValueError("Missing business key values.")

    if df.duplicated(BUSINESS_KEY).any():
        raise ValueError("Duplicate race result business keys.")

    if df["race_date"].isna().any():
        raise ValueError("Missing race dates.")

    if df["points"].isna().any() or (df["points"] < 0).any():
        raise ValueError("Invalid race points detected.")

    return df.sort_values(
        ["season", "round", "driver_id"]
    ).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_metadata() -> dict:
    """Load snapshot metadata."""

    if not METADATA_PATH.is_file():
        raise FileNotFoundError(
            f"Snapshot metadata not found: {METADATA_PATH}"
        )

    with METADATA_PATH.open("r", encoding="utf-8") as file:
        metadata = json.load(file)

    required_fields = {
        "source",
        "exported_at_utc",
        "season_from",
        "season_to",
        "record_count",
    }

    missing_fields = required_fields - set(metadata)

    if missing_fields:
        raise ValueError(
            f"Missing metadata fields: {sorted(missing_fields)}"
        )

    return metadata


def load_dashboard_data() -> tuple[pd.DataFrame, dict]:
    """Load dashboard data and verify metadata consistency."""

    df = load_race_results()
    metadata = load_metadata()

    if len(df) != metadata["record_count"]:
        raise ValueError(
            "Snapshot record count does not match metadata."
        )

    if int(df["season"].min()) != metadata["season_from"]:
        raise ValueError("Invalid starting season in metadata.")

    if int(df["season"].max()) != metadata["season_to"]:
        raise ValueError("Invalid ending season in metadata.")

    return df, metadata
