
"""F1 Performance Analytics dashboard."""

import streamlit as st

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

st.success("Gold analytics snapshot loaded successfully.")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Race results", f"{len(df):,}")
col2.metric("Seasons", df["season"].nunique())
col3.metric("Drivers", df["driver_id"].nunique())
col4.metric("Races", df["race_id"].nunique())

st.subheader("Dataset preview")

st.dataframe(
    df.head(20),
    hide_index=True,
)

st.caption(
    f"Snapshot exported: {metadata['exported_at_utc']} | "
    f"Source: {metadata['source']}"
)
