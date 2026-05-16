import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# PNWU Brand Colors
PACIFIC_BLUE    = "#1b3764"
FOREST_GREEN    = "#366732"
VINEYARD_GREEN  = "#659a41"
NEW_LEAF        = "#99ca3c"
CLOUD_BLUE      = "#72c7f0"
SILVER_GRAY     = "#a4a9ad"
BALANCE_GRAY    = "#616467"
WARNING_RED     = "#c0392b"

def plot_bookings_by_year(df: pd.DataFrame) -> None:
    """
    A big picture chart. How many appointments happened each year?
    Jan's strategic plan 5% annual growth target We can see 
    if the library's hitting it 
    """
    if df.empty:
        st.info("No appointment data available.")
        return

    agg = (
        df.groupby("AcademicYear", as_index=False)
        .size()
        .rename(columns={"size": "Appointments"})
        .sort_values("AcademicYear")
    )

    fig = px.bar(
        agg,
        x="AcademicYear",
        y="Appointments",
        text="Appointments",
        color_discrete_sequence=[CLOUD_BLUE],
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        title="Book a Librarian — Appointments by Academic Year",
        xaxis_title="Academic Year",
        yaxis_title="Total Appointments",
        plot_bgcolor="white",
        paper_bgcolor="white",
        yaxis=dict(gridcolor="#f0f0f0"),
    )
    st.plotly_chart(fig, use_container_width=True)


def plot_bookings_by_quarter(df: pd.DataFrame) -> None:
    """
    Quarterly appointment trend as an area chart.
    Shows seasonality which parts of the year are busiest
    """
    if df.empty:
        st.info("No appointment data available.")
        return

    agg = (
        df.groupby("YearQuarter", as_index=False)
        .size()
        .rename(columns={"size": "Appointments"})
        .sort_values("YearQuarter")
    )

    st.area_chart(
        agg.set_index("YearQuarter")["Appointments"],
        color=FOREST_GREEN,
    )

def plot_service_type(df: pd.DataFrame) -> None:
    """
    What are people booking? Research consultations,
    orientations, special projects? Shows which
    services are being used & which need promotion
    """
    if df.empty or "Service" not in df.columns:
        st.info("No service type data available.")
        return

    agg = (
        df["Service"]
        .value_counts()
        .reset_index()
        .rename(columns={"index": "Service", "count": "Count"})
    )

    fig = px.bar(
        agg,
        x="Count",
        y="Service",
        orientation="h",
        text="Count",
        color_discrete_sequence=[VINEYARD_GREEN],
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        title="Appointments by Service Type",
        xaxis_title="Number of Appointments",
        yaxis_title="",
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(gridcolor="#f0f0f0"),
    )
    st.plotly_chart(fig, use_container_width=True)


def plot_virtual_vs_inperson(df: pd.DataFrame) -> None:
    """
    Shows how appointments are delivered. 
    """
    if df.empty or "Location" not in df.columns:
        st.info("No location data available.")
        return

    # Renamed for clarity
    location_map = {
        "Virtual": "Virtual",
        "PNWU Library or Virtual": "In-Person",
    }
    df = df.copy()
    df["Location"] = df["Location"].replace(location_map)

    agg = df["Location"].value_counts().reset_index()
    agg.columns = ["Location", "Count"]

    fig = px.pie(
        agg,
        names="Location",
        values="Count",
        color_discrete_sequence=[PACIFIC_BLUE, CLOUD_BLUE],
        hole=0.4,
    )
    fig.update_layout(title="Appointment Delivery Method")
    st.plotly_chart(fig, use_container_width=True)


def plot_satisfaction_means(df: pd.DataFrame, year: int) -> None:
    """
    How satisfied are students with each area of the library?
    Scores are 0-5. The dotted line at 3.0 is neutral — anything
    below that line is a problem worth paying attention to.
    Green = strong, yellow = okay, red = needs work.
    """
    if df.empty:
        st.info(f"No satisfaction data available for {year}.")
        return

    question_cols = [
        c for c in df.columns
        if c not in ["LevelName", "SurveyStart", "SurveyEnd",
                     "Enrollments", "Respondents", "ResponseRate",
                     "Survey Year"]
    ]

    means = df[question_cols].mean().reset_index()
    means.columns = ["Question", "Mean Score"]
    means = means.sort_values("Mean Score", ascending=True)

    means["Color"] = means["Mean Score"].apply(
        lambda x: FOREST_GREEN if x >= 3.5
        else CLOUD_BLUE if x >= 3.0
        else WARNING_RED
    )
    

    fig = go.Figure(go.Bar(
        x=means["Mean Score"],
        y=means["Question"],
        orientation="h",
        marker_color=means["Color"],
        text=means["Mean Score"].round(2),
        textposition="outside",
    ))

    fig.add_vline(
        x=3.0,
        line_dash="dot",
        line_color=BALANCE_GRAY,
        annotation_text="Neutral (3.0)",
        annotation_position="top",
    )

    fig.update_layout(
        title=f"Student Satisfaction by Category — {year}",
        xaxis_title="Mean Score (0–5)",
        yaxis_title="",
        xaxis=dict(range=[0, 5.5], gridcolor="#f0f0f0"),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    with st.container():
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(
            '<small>'
            '<span style="color:#366732;">■</span> Strong (3.5+) &nbsp;·&nbsp; '
            '<span style="color:#72c7f0;">■</span> Neutral (3.0–3.5) &nbsp;·&nbsp; '
            '<span style="color:#c0392b;">■</span> Needs attention (below 3.0)'
            '</small>',
            unsafe_allow_html=True
        )

def plot_satisfaction_comparison(df: pd.DataFrame) -> None:
    """
    Did things get better or worse between 2023 and 2025?
    Both years side by side so you can see exactly
    where scores went up, stayed flat, or dropped.
    """
    if df.empty or "Survey Year" not in df.columns:
        st.info("No comparison data available.")
        return

    question_cols = [
        c for c in df.columns
        if c not in ["LevelName", "SurveyStart", "SurveyEnd",
                     "Enrollments", "Respondents", "ResponseRate",
                     "Survey Year"]
    ]

    melted = df.melt(
        id_vars=["Survey Year"],
        value_vars=question_cols,
        var_name="Question",
        value_name="Score",
    )
    means = melted.groupby(
        ["Survey Year", "Question"], as_index=False
    )["Score"].mean()
    means["Survey Year"] = means["Survey Year"].astype(str)

    fig = px.bar(
        means,
        x="Question",
        y="Score",
        color="Survey Year",
        barmode="group",
        color_discrete_map={"2023": PACIFIC_BLUE, "2025": NEW_LEAF},
    )
    fig.update_layout(
        title="Satisfaction Scores: 2023 vs 2025",
        xaxis_title="",
        yaxis_title="Mean Score (0–5)",
        xaxis=dict(tickangle=30),
        yaxis=dict(range=[0, 5.5], gridcolor="#f0f0f0"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend_title="Survey Year",
    )
    st.plotly_chart(fig, use_container_width=True)

def plot_circulation(df: pd.DataFrame) -> None:
    """
    Physical book checkouts by month over time.
    Tells a story of how students are using the library
    """
    if df.empty:
        st.info("No circulation data available.")
        return

    fig = px.line(
        df,
        x="Month",
        y="Checkout",
        color="AcademicYear",
        markers=True,
        color_discrete_sequence=[PACIFIC_BLUE, FOREST_GREEN, VINEYARD_GREEN, NEW_LEAF],
    )
    fig.update_layout(
        title="Physical Book Checkouts by Month",
        xaxis_title="Month",
        yaxis_title="Checkouts",
        plot_bgcolor="white",
        paper_bgcolor="white",
        yaxis=dict(gridcolor="#f0f0f0"),
        legend_title="Academic Year",
    )
    st.plotly_chart(fig, use_container_width=True)


def plot_circulation_by_year(df: pd.DataFrame) -> None:
    """
    Total physical checkouts per academic year as a bar chart
    """
    if df.empty:
        st.info("No circulation data available.")
        return

    agg = df.groupby("AcademicYear", as_index=False)["Checkout"].sum()
    agg = agg.sort_values("AcademicYear")

    fig = px.bar(
        agg,
        x="AcademicYear",
        y="Checkout",
        text="Checkout",
        color_discrete_sequence=[FOREST_GREEN],
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        title="Total Physical Checkouts by Academic Year",
        xaxis_title="Academic Year",
        yaxis_title="Total Checkouts",
        plot_bgcolor="white",
        paper_bgcolor="white",
        yaxis=dict(gridcolor="#f0f0f0"),
    )
    st.plotly_chart(fig, use_container_width=True)