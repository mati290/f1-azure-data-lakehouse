
"""F1 Performance Analytics dashboard."""

from charts import (
    create_finish_chart,
    create_grid_vs_finish_chart,
    create_points_chart,
    create_summary_chart,
)

from styles import apply_dashboard_styles
import streamlit as st

from analytics import (
    calculate_kpis,
    filter_results,
    get_circuit_options,
    get_driver_options,
    prepare_results_table,
    summarize_performance,
)
from data_loader import load_dashboard_data


st.set_page_config(
    page_title="F1 Performance Analytics",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)
apply_dashboard_styles()

st.title("🏎️ F1 Performance Analytics")

st.markdown("**Historical race performance dashboard**")

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

st.sidebar.title("🏁 F1 Analytics")

st.sidebar.caption(
    "Azure Data Lakehouse | Gold Analytics"
)

st.sidebar.divider()

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

with st.sidebar.expander("About this project"):
    st.markdown(
        """
        An end-to-end Data Engineering portfolio project.

        **Technology stack**

        - Azure Data Factory
        - Azure Data Lake Storage Gen2
        - Azure Databricks
        - PySpark & Delta Lake
        - SQL Analytics
        - Streamlit & Plotly

        **Data source:** Jolpica F1 API

        [GitHub Repository](https://github.com/mati290/f1-azure-data-lakehouse)
        """
    )

    st.caption(
        "Unofficial, non-commercial educational project."
    )

with st.sidebar.expander("Dataset information"):
    st.write(
        f"Seasons: {metadata['season_from']}"
        f"–{metadata['season_to']}"
    )

    st.write(f"Race results: {len(df):,}")
    st.write(f"Drivers: {df['driver_id'].nunique()}")
    st.write(f"Races: {df['race_id'].nunique()}")

    st.caption(
        f"Snapshot exported: "
        f"{metadata['exported_at_utc']}"
    )

    st.markdown(
        "[Data license – CC BY-NC-SA 4.0]"
        "(https://creativecommons.org/licenses/by-nc-sa/4.0/)"
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


# Performance visualizations

st.divider()

st.subheader("Performance Trends")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.plotly_chart(
        create_points_chart(filtered_df),
        width="stretch",
        key="points_chart",
    )

with chart_col2:
    if (
        filtered_df["is_classified"]
        & filtered_df["finish_position"].notna()
    ).any():
        st.plotly_chart(
            create_finish_chart(filtered_df),
            width="stretch",
            key="finish_chart",
        )
    else:
        st.info(
            "No classified finishing positions "
            "for the selected races."
        )

st.plotly_chart(
    create_grid_vs_finish_chart(filtered_df),
    width="stretch",
    key="grid_vs_finish_chart",
)

st.caption(
    "Non-classified finishing positions and unavailable "
    "starting grid positions are shown as gaps."
)


# Detailed analytics

st.divider()

st.subheader("Detailed Analytics")

results_tab, circuits_tab, constructors_tab = st.tabs(
    [
        "Race Results",
        "Circuit Performance",
        "Constructor Performance",
    ]
)


with results_tab:
    results_table = prepare_results_table(filtered_df)

    st.dataframe(
        results_table,
        hide_index=True,
        width="stretch",
        column_config={
            "Date": st.column_config.DateColumn(
                format="YYYY-MM-DD"
            ),
            "Points": st.column_config.NumberColumn(
                format="%.2f"
            ),
            "Positions gained": st.column_config.NumberColumn(
                format="%+.0f"
            ),
            "Classified": st.column_config.CheckboxColumn(),
        },
    )

    st.caption(
        "Missing finishing positions indicate "
        "non-classified or unavailable results. "
        "Missing grid positions may indicate a pit-lane start "
        "or unavailable starting position."
    )

    csv_data = results_table.to_csv(
        index=False,
        date_format="%Y-%m-%d",
    ).encode("utf-8-sig")

    st.download_button(
        label="Export results to CSV",
        data=csv_data,
        file_name=f"{selected_driver}_race_results.csv",
        mime="text/csv",
        icon=":material/download:",
    )


summary_column_config = {
    "races": st.column_config.NumberColumn(
        "Races",
        format="%d",
    ),
    "total_points": st.column_config.NumberColumn(
        "Total points",
        format="%.2f",
    ),
    "points_per_race": st.column_config.NumberColumn(
        "Points per race",
        format="%.2f",
    ),
    "average_finish": st.column_config.NumberColumn(
        "Avg. finish",
        format="%.2f",
    ),
    "wins": st.column_config.NumberColumn("Wins"),
    "podiums": st.column_config.NumberColumn("Podiums"),
    "dnf_rate": st.column_config.NumberColumn(
        "DNF rate (%)",
        format="%.1f",
    ),
}


with circuits_tab:
    st.caption(
        "Circuit performance across the selected race results."
    )

    circuit_summary = summarize_performance(
        filtered_df,
        group_column="circuit_name",
    )

    if circuit_summary.empty:
        st.info("No circuit performance data available.")
    else:
        st.plotly_chart(
            create_summary_chart(
                circuit_summary,
                group_column="circuit_name",
                title="Top 10 Circuits by Points",
            ),
            width="stretch",
            key="circuit_summary_chart",
        )

        st.dataframe(
            circuit_summary,
            hide_index=True,
            width="stretch",
            column_config={
                **summary_column_config,
                "circuit_name": "Circuit",
            },
        )


with constructors_tab:
    st.caption(
        "Selected driver's performance by constructor."
    )

    constructor_summary = summarize_performance(
        filtered_df,
        group_column="constructor_name",
    )

    if constructor_summary.empty:
        st.info("No constructor performance data available.")
    else:
        st.plotly_chart(
            create_summary_chart(
                constructor_summary,
                group_column="constructor_name",
                title="Points by Constructor",
            ),
            width="stretch",
            key="constructor_summary_chart",
        )

        st.dataframe(
            constructor_summary,
            hide_index=True,
            width="stretch",
            column_config={
                **summary_column_config,
                "constructor_name": "Constructor",
            },
        )


# Snapshot information

st.divider()

st.caption(
    f"Snapshot exported: {metadata['exported_at_utc']} | "
    f"Source: {metadata['source']}"
)

