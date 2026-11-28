
"""Visual styling for the F1 dashboard."""

import streamlit as st


def apply_dashboard_styles() -> None:
    """Apply custom dashboard styles."""

    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
                max-width: 1600px;
            }

            h1 {
                font-weight: 800;
                letter-spacing: -0.04em;
            }

            h2, h3 {
                font-weight: 600;
            }

            [data-testid="stMetric"] {
                background-color: #1A1F2B;
                border: 1px solid #303746;
                border-top: 3px solid #E10600;
                border-radius: 10px;
                padding: 16px;
                min-height: 110px;
            }

            [data-testid="stMetricValue"] {
                font-weight: 700;
                font-size: 1.8rem;
            }

            [data-testid="stSidebar"] {
                border-right: 1px solid #303746;
            }

            [data-testid="stDataFrame"] {
                border-radius: 8px;
            }

            .stTabs [data-baseweb="tab-list"] {
                gap: 12px;
            }

            .stTabs [data-baseweb="tab"] {
                font-weight: 600;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
