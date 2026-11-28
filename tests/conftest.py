
"""Shared fixtures for local PySpark unit tests."""

import os
import sys

import pytest
from pyspark.sql import SparkSession


@pytest.fixture(scope="session")
def spark():
    """Create a local Spark session for the entire test suite."""

    os.environ["PYSPARK_PYTHON"] = sys.executable

    session = (
        SparkSession.builder
        .master("local[2]")
        .appName("F1LakehouseTests")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.sql.ansi.enabled", "true")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.driver.host", "127.0.0.1")
        .getOrCreate()
    )

    session.sparkContext.setLogLevel("ERROR")

    yield session

    session.stop()


@pytest.fixture
def raw_race_results(spark):
    """Create synthetic race results with raw string values."""

    columns = [
        "season",
        "round",
        "race_date",
        "date_of_birth",
        "latitude",
        "longitude",
        "driver_number",
        "grid_position",
        "position",
        "points",
        "laps_completed",
        "race_time_ms",
        "fastest_lap_rank",
        "fastest_lap_number",
        "driver_id",
        "driver_code",
        "first_name",
        "last_name",
        "status"
    ]

    records = [
        (
            "2025", "1", "2025-03-16", "1997-09-30",
            "-37.8497", "144.968",
            "1", "3", "1", "25", "58",
            "5400000", "1", "45",
            "verstappen", "VER", "Max",
            "  Verstappen  ", "Finished"
        ),
        (
            "2025", "1", "2025-03-16", "1999-11-13",
            "-37.8497", "144.968",
            "4", "1", "2", "18", "58",
            "5405000", "2", "42",
            "norris", "NOR", "Lando",
            "Norris", "Finished"
        ),
        (
            "2025", "1", "2025-03-16", "1985-01-07",
            "-37.8497", "144.968",
            "44", "8", "10", "0", "20",
            None, None, None,
            "hamilton", "", "Lewis",
            "Hamilton", "Retired"
        ),
        (
            "2021", "12", "2021-08-29", "1997-09-30",
            "50.4372", "5.97139",
            "33", "1", "1", "12.5", "1",
            None, None, None,
            "verstappen", "VER", "Max",
            "Verstappen", "Finished"
        )
    ]

    return spark.createDataFrame(records, columns)
