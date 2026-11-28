
"""Business analytics and filtering for the F1 dashboard."""

import pandas as pd


def get_driver_options(df: pd.DataFrame) -> dict[str, str]:
    """Return driver IDs mapped to display names."""

    drivers = (
        df[["driver_id", "driver_name"]]
        .drop_duplicates(subset="driver_id")
        .sort_values("driver_name")
    )

    return dict(
        zip(drivers["driver_id"], drivers["driver_name"])
    )


def get_circuit_options(df: pd.DataFrame) -> dict[str, str]:
    """Return circuit IDs mapped to display names."""

    circuits = (
        df[["circuit_id", "circuit_name"]]
        .drop_duplicates(subset="circuit_id")
        .sort_values("circuit_name")
    )

    return dict(
        zip(circuits["circuit_id"], circuits["circuit_name"])
    )


def filter_results(
    df: pd.DataFrame,
    driver_id: str,
    circuit_id: str | None = None,
    last_n: int | None = None,
) -> pd.DataFrame:
    """Filter race results by driver, circuit and race count."""

    filtered = df.loc[
        df["driver_id"] == driver_id
    ].copy()

    if circuit_id is not None:
        filtered = filtered.loc[
            filtered["circuit_id"] == circuit_id
        ]

    filtered = filtered.sort_values(
        ["season", "round"],
        ascending=False,
    )

    if last_n is not None:
        if last_n < 1:
            raise ValueError("last_n must be greater than zero.")

        recent_races = (
            filtered["race_id"]
            .drop_duplicates()
            .head(last_n)
        )

        filtered = filtered.loc[
            filtered["race_id"].isin(recent_races)
        ]

    return filtered.sort_values(
        ["season", "round"]
    ).reset_index(drop=True)


def calculate_kpis(df: pd.DataFrame) -> dict:
    """Calculate driver performance KPIs."""

    classified = df.loc[
        df["is_classified"] & df["finish_position"].notna()
    ]

    starters = df.loc[~df["is_dns"]]

    average_finish = (
        float(classified["finish_position"].mean())
        if not classified.empty
        else None
    )

    dnf_rate = (
        float(starters["is_dnf"].mean() * 100)
        if not starters.empty
        else None
    )

    return {
        "races": int(df["race_id"].nunique()),
        "total_points": float(df["points"].sum()),
        "average_finish": average_finish,
        "wins": int(df["is_win"].sum()),
        "podiums": int(df["is_podium"].sum()),
        "dnf_rate": dnf_rate,
    }
