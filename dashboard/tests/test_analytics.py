
"""Unit tests for dashboard business analytics."""

import pandas as pd
import pytest

from analytics import (
    calculate_kpis,
    filter_results,
    get_circuit_options,
    get_driver_options,
    prepare_results_table,
    summarize_performance,
)


def test_driver_options(sample_results):
    options = get_driver_options(sample_results)

    assert options == {
        "driver_a": "Driver A",
        "driver_b": "Driver B",
    }


def test_circuit_options(sample_results):
    options = get_circuit_options(sample_results)

    assert options == {
        "circuit_a": "Circuit A",
        "circuit_b": "Circuit B",
    }


def test_filter_by_driver(sample_results):
    result = filter_results(
        sample_results,
        driver_id="driver_a",
    )

    assert len(result) == 4
    assert result["driver_id"].eq("driver_a").all()


def test_filter_by_circuit(sample_results):
    result = filter_results(
        sample_results,
        driver_id="driver_a",
        circuit_id="circuit_a",
    )

    assert len(result) == 2
    assert result["circuit_id"].eq("circuit_a").all()


def test_filter_last_n_races(sample_results):
    result = filter_results(
        sample_results,
        driver_id="driver_a",
        last_n=2,
    )

    assert len(result) == 2
    assert result["round"].tolist() == [3, 4]


def test_combined_filters(sample_results):
    result = filter_results(
        sample_results,
        driver_id="driver_a",
        circuit_id="circuit_a",
        last_n=1,
    )

    assert len(result) == 1
    assert result.iloc[0]["round"] == 3


def test_invalid_last_n(sample_results):
    with pytest.raises(ValueError):
        filter_results(
            sample_results,
            driver_id="driver_a",
            last_n=0,
        )


def test_empty_filter_result(sample_results):
    result = filter_results(
        sample_results,
        driver_id="unknown_driver",
    )

    assert result.empty


def test_kpi_calculations(sample_results):
    result = filter_results(
        sample_results,
        driver_id="driver_a",
    )

    kpis = calculate_kpis(result)

    assert kpis["races"] == 4
    assert kpis["total_points"] == 43.0
    assert kpis["average_finish"] == 1.5
    assert kpis["wins"] == 1
    assert kpis["podiums"] == 2
    assert kpis["dnf_rate"] == pytest.approx(
        100 / 3
    )


def test_empty_kpis(sample_results):
    kpis = calculate_kpis(
        sample_results.iloc[0:0]
    )

    assert kpis["races"] == 0
    assert kpis["total_points"] == 0
    assert kpis["average_finish"] is None
    assert kpis["wins"] == 0
    assert kpis["podiums"] == 0
    assert kpis["dnf_rate"] is None


def test_unclassified_result(sample_results):
    result = sample_results.loc[
        sample_results["is_dnf"]
    ]

    kpis = calculate_kpis(result)

    assert kpis["average_finish"] is None
    assert kpis["dnf_rate"] == 100.0


def test_dns_excluded_from_dnf_rate(sample_results):
    result = sample_results.loc[
        sample_results["is_dns"]
    ]

    kpis = calculate_kpis(result)

    assert kpis["dnf_rate"] is None


def test_results_table(sample_results):
    filtered = filter_results(
        sample_results,
        driver_id="driver_a",
    )

    result = prepare_results_table(filtered)

    assert len(result) == 4
    assert result["Round"].tolist() == [4, 3, 2, 1]
    assert "Grand Prix" in result.columns
    assert "Positions gained" in result.columns


def test_results_table_missing_positions(sample_results):
    result = prepare_results_table(sample_results)

    dns = result.loc[
        result["Status"] == "Did not start"
    ].iloc[0]

    assert pd.isna(dns["Grid"])
    assert pd.isna(dns["Finish"])
    assert pd.isna(dns["Positions gained"])


def test_circuit_summary(sample_results):
    filtered = filter_results(
        sample_results,
        driver_id="driver_a",
    )

    summary = summarize_performance(
        filtered,
        group_column="circuit_name",
    )

    assert len(summary) == 2
    assert summary["total_points"].sum() == 43.0

    circuit_a = summary.loc[
        summary["circuit_name"] == "Circuit A"
    ].iloc[0]

    assert circuit_a["races"] == 2
    assert circuit_a["total_points"] == 25.0
    assert circuit_a["points_per_race"] == 12.5
    assert circuit_a["average_finish"] == 1.0


def test_constructor_summary(sample_results):
    filtered = filter_results(
        sample_results,
        driver_id="driver_a",
    )

    summary = summarize_performance(
        filtered,
        group_column="constructor_name",
    )

    assert len(summary) == 2
    assert summary["total_points"].sum() == 43.0

    team_a = summary.loc[
        summary["constructor_name"] == "Team A"
    ].iloc[0]

    assert team_a["total_points"] == 43.0
    assert team_a["races"] == 2
    assert team_a["podiums"] == 2


def test_invalid_summary_column(sample_results):
    with pytest.raises(ValueError):
        summarize_performance(
            sample_results,
            group_column="invalid_column",
        )


def test_empty_summary(sample_results):
    summary = summarize_performance(
        sample_results.iloc[0:0],
        group_column="circuit_name",
    )

    assert summary.empty
    assert "total_points" in summary.columns
