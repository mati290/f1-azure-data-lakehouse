
"""Unit tests for dashboard visualizations."""

import pandas as pd
import plotly.graph_objects as go

from analytics import (
    filter_results,
    summarize_performance,
)
from charts import (
    create_finish_chart,
    create_grid_vs_finish_chart,
    create_points_chart,
    create_summary_chart,
    prepare_chart_data,
)


def test_chart_data_order(sample_results):
    filtered = filter_results(
        sample_results,
        driver_id="driver_a",
    )

    chart_df = prepare_chart_data(filtered)

    assert chart_df["round"].tolist() == [1, 2, 3, 4]
    assert chart_df["race_label"].is_unique


def test_chart_unclassified_positions(sample_results):
    chart_df = prepare_chart_data(sample_results)

    unclassified = chart_df.loc[
        ~chart_df["is_classified"]
    ]

    assert unclassified["classified_finish"].isna().all()


def test_chart_invalid_grid_position(sample_results):
    chart_df = prepare_chart_data(sample_results)

    dns = chart_df.loc[
        chart_df["is_dns"]
    ].iloc[0]

    assert pd.isna(dns["starting_position"])


def test_points_chart(sample_results):
    filtered = filter_results(
        sample_results,
        driver_id="driver_a",
    )

    fig = create_points_chart(filtered)

    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert sum(fig.data[0].y) == 43.0


def test_finish_chart(sample_results):
    fig = create_finish_chart(sample_results)

    assert isinstance(fig, go.Figure)
    assert fig.layout.yaxis.autorange == "reversed"
    assert fig.data[0].connectgaps is False


def test_grid_vs_finish_chart(sample_results):
    fig = create_grid_vs_finish_chart(sample_results)

    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2
    assert fig.layout.yaxis.autorange == "reversed"


def test_summary_chart(sample_results):
    filtered = filter_results(
        sample_results,
        driver_id="driver_a",
    )

    summary = summarize_performance(
        filtered,
        group_column="circuit_name",
    )

    fig = create_summary_chart(
        summary,
        group_column="circuit_name",
        title="Circuit Performance",
    )

    assert isinstance(fig, go.Figure)
    assert fig.data[0].orientation == "h"
    assert sum(fig.data[0].x) == 43.0


def test_single_race_chart(sample_results):
    single_race = sample_results.iloc[[0]]

    fig = create_points_chart(single_race)

    assert len(fig.data[0].x) == 1
    assert fig.data[0].y[0] == 25.0
