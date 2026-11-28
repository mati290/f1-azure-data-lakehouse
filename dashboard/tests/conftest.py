
"""Shared fixtures for dashboard tests."""

import sys
from pathlib import Path

import pandas as pd
import pytest


DASHBOARD_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(DASHBOARD_DIR))


@pytest.fixture
def sample_results() -> pd.DataFrame:
    """Return deterministic synthetic race results."""

    columns = [
        "race_id",
        "season",
        "round",
        "driver_id",
        "driver_name",
        "circuit_id",
        "circuit_name",
        "constructor_name",
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
    ]

    records = [
        [
            "2024_1", 2024, 1, "driver_a", "Driver A",
            "circuit_a", "Circuit A", "Team A",
            2, 1, 1, 25.0, "Finished",
            True, True, True, False, False, False,
        ],
        [
            "2024_2", 2024, 2, "driver_a", "Driver A",
            "circuit_b", "Circuit B", "Team A",
            3, 2, 1, 18.0, "Finished",
            True, False, True, False, False, False,
        ],
        [
            "2024_3", 2024, 3, "driver_a", "Driver A",
            "circuit_a", "Circuit A", "Team B",
            5, None, None, 0.0, "Engine",
            False, False, False, True, False, False,
        ],
        [
            "2024_4", 2024, 4, "driver_a", "Driver A",
            "circuit_b", "Circuit B", "Team B",
            0, None, None, 0.0, "Did not start",
            False, False, False, False, True, False,
        ],
        [
            "2024_1", 2024, 1, "driver_b", "Driver B",
            "circuit_a", "Circuit A", "Team B",
            1, 3, -2, 15.0, "Finished",
            True, False, True, False, False, False,
        ],
    ]

    df = pd.DataFrame(records, columns=columns)

    df["race_name"] = "Test Grand Prix"

    df["race_date"] = pd.to_datetime(
        "2024-01-01"
    ) + pd.to_timedelta(df["round"] * 7, unit="D")

    return df
