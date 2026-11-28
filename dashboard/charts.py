
"""Interactive Plotly visualizations for the F1 dashboard."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


F1_RED = "#E10600"
GRID_COLOR = "#94A3B8"


def prepare_chart_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare chronologically ordered chart data."""

    chart_df = df.sort_values(
        ["season", "round"]
    ).copy()

    chart_df["race_label"] = (
        chart_df["season"].astype(str)
        + " R"
        + chart_df["round"].astype(str)
    )

    chart_df["classified_finish"] = chart_df[
        "finish_position"
    ].where(chart_df["is_classified"])

    chart_df["starting_position"] = chart_df[
        "grid_position"
    ].where(chart_df["grid_position"] > 0)

    return chart_df


def apply_chart_layout(
    fig: go.Figure,
    yaxis_title: str,
) -> go.Figure:
    """Apply consistent dashboard chart styling."""

    fig.update_layout(
        height=360,
        margin=dict(l=20, r=20, t=55, b=20),
        xaxis_title="Race",
        yaxis_title=yaxis_title,
        hovermode="closest",
        legend_title_text="",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )

    fig.update_xaxes(
        type="category",
        tickangle=-45,
        showgrid=False,
        nticks=15,
    )

    return fig


def create_points_chart(df: pd.DataFrame) -> go.Figure:
    """Create a points-per-race bar chart."""

    chart_df = prepare_chart_data(df)

    fig = px.bar(
        chart_df,
        x="race_label",
        y="points",
        title="Points by Race",
        color_discrete_sequence=[F1_RED],
        hover_data={
            "race_label": False,
            "race_name": True,
            "constructor_name": True,
            "status": True,
            "points": ":.2f",
        },
        labels={
            "race_name": "Grand Prix",
            "constructor_name": "Constructor",
            "status": "Status",
            "points": "Points",
        },
    )

    fig.update_yaxes(rangemode="tozero")

    return apply_chart_layout(fig, "Points")


def create_finish_chart(df: pd.DataFrame) -> go.Figure:
    """Create a classified finishing-position trend."""

    chart_df = prepare_chart_data(df)

    fig = px.line(
        chart_df,
        x="race_label",
        y="classified_finish",
        title="Finishing Position Trend",
        markers=True,
        color_discrete_sequence=[F1_RED],
        hover_data={
            "race_label": False,
            "race_name": True,
            "constructor_name": True,
            "status": True,
            "classified_finish": ":.0f",
        },
        labels={
            "race_name": "Grand Prix",
            "constructor_name": "Constructor",
            "status": "Status",
            "classified_finish": "Finish",
        },
    )

    fig.update_traces(
        connectgaps=False,
        line=dict(width=2.5),
        marker=dict(size=7),
    )

    fig.update_yaxes(
        autorange="reversed",
        dtick=1,
    )

    return apply_chart_layout(fig, "Finishing position")


def create_grid_vs_finish_chart(
    df: pd.DataFrame,
) -> go.Figure:
    """Compare starting grid and classified finish positions."""

    chart_df = prepare_chart_data(df)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=chart_df["race_label"],
            y=chart_df["starting_position"],
            name="Starting grid",
            mode="lines+markers",
            line=dict(
                color=GRID_COLOR,
                dash="dash",
                width=2,
            ),
            customdata=chart_df["race_name"],
            connectgaps=False,
            hovertemplate=(
                "%{customdata}<br>"
                "Grid: P%{y:.0f}"
                "<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=chart_df["race_label"],
            y=chart_df["classified_finish"],
            name="Finish position",
            mode="lines+markers",
            line=dict(
                color=F1_RED,
                width=2.5,
            ),
            customdata=chart_df["race_name"],
            connectgaps=False,
            hovertemplate=(
                "%{customdata}<br>"
                "Finish: P%{y:.0f}"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(title="Grid vs. Finish")

    fig.update_yaxes(
        autorange="reversed",
        dtick=1,
    )

    return apply_chart_layout(fig, "Position")
