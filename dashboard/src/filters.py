import pandas as pd
import streamlit as st


def render_booking_filters(df: pd.DataFrame, key_prefix: str = "") -> pd.DataFrame:
    """
    Filter widgets for the Book a Librarian appointment data.
    Returns a filtered dataframe based on what the user selects.
    key_prefix keeps widget keys unique if used in multiple places.
    """
    col1, col2 = st.columns(2)

    with col1:
        all_years = sorted(df["AcademicYear"].unique().tolist())
        selected_years = st.multiselect(
            "Filter by Academic Year",
            options=all_years,
            default=all_years,
            key=f"{key_prefix}_years"
        )

    with col2:
        all_services = sorted(df["Service"].unique().tolist())
        selected_services = st.multiselect(
            "Filter by Service Type",
            options=all_services,
            default=all_services,
            key=f"{key_prefix}_services"
        )

    filtered = df[
        (df["AcademicYear"].isin(selected_years)) &
        (df["Service"].isin(selected_services))
    ]

    if filtered.empty:
        st.warning("No appointments match your filters.")
        return filtered

    st.caption(f"Showing {len(filtered)} of {len(df)} total appointments")
    return filtered


def render_satisfaction_filters(df: pd.DataFrame, key_prefix: str = "") -> pd.DataFrame:
    """
    Program filter for the student satisfaction survey data.
    Lets Jan or staff slice by DO, PT, OT, MAMS separately.
    Returns a filtered dataframe.
    """
    programs = sorted(df["LevelName"].unique().tolist())
    selected = st.multiselect(
        "Filter by Program",
        options=programs,
        default=programs,
        key=f"{key_prefix}_programs"
    )
    return df[df["LevelName"].isin(selected)]