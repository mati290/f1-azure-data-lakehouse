
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


def prepare_results_table(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare a presentation-friendly race results table."""

    results = df.sort_values(
        ["season", "round"],
        ascending=False,
    ).copy()

    results["finish_position"] = results[
        "finish_position"
    ].where(results["is_classified"]).astype("Int64")

    results["grid_position"] = results[
        "grid_position"
    ].where(results["grid_position"] > 0).astype("Int64")

    results["positions_gained"] = results[
        "positions_gained"
    ].where(
        results["is_classified"]
        & results["grid_position"].notna()
    )

    columns = {
        "season": "Season",
        "round": "Round",
        "race_name": "Grand Prix",
        "race_date": "Date",
        "circuit_name": "Circuit",
        "constructor_name": "Constructor",
        "grid_position": "Grid",
        "finish_position": "Finish",
        "positions_gained": "Positions gained",
        "points": "Points",
        "status": "Status",
        "is_classified": "Classified",
    }

    return results[list(columns)].rename(columns=columns)


def summarize_performance(
    df: pd.DataFrame,
    group_column: str,
) -> pd.DataFrame:
    """Aggregate performance by circuit or constructor."""

    allowed_columns = {
        "circuit_name",
        "constructor_name",
    }

    if group_column not in allowed_columns:
        raise ValueError(
            f"Unsupported grouping column: {group_column}"
        )

    records = []

    for group_name, group_df in df.groupby(group_column):
        kpis = calculate_kpis(group_df)

        races = kpis["races"]

        records.append(
            {
                group_column: group_name,
                "races": races,
                "total_points": kpis["total_points"],
                "points_per_race": (
                    kpis["total_points"] / races
                    if races > 0
                    else None
                ),
                "average_finish": kpis["average_finish"],
                "wins": kpis["wins"],
                "podiums": kpis["podiums"],
                "dnf_rate": kpis["dnf_rate"],
            }
        )

    columns = [
        group_column,
        "races",
        "total_points",
        "points_per_race",
        "average_finish",
        "wins",
        "podiums",
        "dnf_rate",
    ]

    return pd.DataFrame(
        records,
        columns=columns,
    ).sort_values(
        ["total_points", "races"],
        ascending=False,
    ).reset_index(drop=True)
