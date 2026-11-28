
"""F1 Performance Analytics dashboard."""

import streamlit as st

from analytics import (
    calculate_kpis,
    filter_results,
    get_circuit_options,
    get_driver_options,
)
from data_loader import load_dashboard_data


st.set_page_config(
    page_title="F1 Performance Analytics",
    page_icon="🏎️",
    layout="wide",
)

st.title("🏎️ F1 Performance Analytics")

try:
    with st.spinner("Loading Gold analytics snapshot..."):
        df, metadata = load_dashboard_data()

except Exception as exc:
    st.error(f"Unable to load dashboard data: {exc}")
    st.stop()

st.caption(
    "Historical Formula 1 race performance | "
    f"{metadata['season_from']}–{metadata['season_to']}"
)


# Sidebar filters

st.sidebar.header("Filters")

drivers = get_driver_options(df)
circuits = get_circuit_options(df)

driver_ids = list(drivers)

default_driver_index = (
    driver_ids.index("max_verstappen")
    if "max_verstappen" in driver_ids
    else 0
)

selected_driver = st.sidebar.selectbox(
    "Driver",
    options=driver_ids,
    index=default_driver_index,
    format_func=lambda value: drivers[value],
)

selected_circuit = st.sidebar.selectbox(
    "Circuit",
    options=[None, *circuits],
    format_func=lambda value: (
        "All circuits" if value is None else circuits[value]
    ),
)

available_results = filter_results(
    df,
    driver_id=selected_driver,
    circuit_id=selected_circuit,
)

available_races = available_results["race_id"].nunique()

if available_races == 0:
    st.warning(
        "No race results match the selected driver and circuit."
    )
    st.stop()

if available_races == 1:
    last_n = 1
    st.sidebar.caption("1 race available.")
else:
    last_n = st.sidebar.slider(
        "Last N races",
        min_value=1,
        max_value=available_races,
        value=min(10, available_races),
    )

filtered_df = filter_results(
    df,
    driver_id=selected_driver,
    circuit_id=selected_circuit,
    last_n=last_n,
)


# KPI section

kpis = calculate_kpis(filtered_df)

st.subheader(drivers[selected_driver])

st.caption(
    f"Showing {kpis['races']} of {available_races} "
    "matching historical races."
)

col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("Races", kpis["races"])

col2.metric(
    "Total points",
    f"{kpis['total_points']:g}",
)

col3.metric(
    "Avg. finish",
    (
        f"{kpis['average_finish']:.2f}"
        if kpis["average_finish"] is not None
        else "N/A"
    ),
)

col4.metric("Wins", kpis["wins"])

col5.metric("Podiums", kpis["podiums"])

col6.metric(
    "DNF rate",
    (
        f"{kpis['dnf_rate']:.1f}%"
        if kpis["dnf_rate"] is not None
        else "N/A"
    ),
)

st.caption(
    "Average finishing position includes classified results only. "
    "DNF rate excludes drivers who did not start."
)


# Race results preview

st.divider()

st.subheader("Race results")

st.dataframe(
    filtered_df[
        [
            "season",
            "round",
            "race_name",
            "race_date",
            "constructor_name",
            "grid_position",
            "finish_position",
            "points",
            "status",
        ]
    ].sort_values(
        ["season", "round"],
        ascending=False,
    ),
    hide_index=True,
)

st.caption(
    f"Snapshot exported: {metadata['exported_at_utc']} | "
    f"Source: {metadata['source']}"
)
