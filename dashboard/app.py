import streamlit as st
from src.data import load_bookings, load_satisfaction, load_satisfaction_both, load_circulation
from src.filters import render_booking_filters, render_satisfaction_filters
from src.charts import (
    plot_bookings_by_year,
    plot_bookings_by_quarter,
    plot_service_type,
    plot_virtual_vs_inperson,
    plot_satisfaction_means,
    plot_satisfaction_comparison,
    plot_circulation,
    plot_circulation_by_year,
)

st.set_page_config(
    page_title="Your Library, Your Impact",
    page_icon="assets/pnwu_logo.png",
    layout="wide",
    initial_sidebar_state="auto"
)

st.markdown("""
<style>
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #1b3764 0%, #366732 100%); }
    [data-testid="stSidebar"] * { color: white !important; }
    .main-header {
        background: linear-gradient(135deg, #1b3764 0%, #366732 100%);
        padding: 1.5rem 2rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
    }
    .main-header h1 { color: white; margin: 0; font-size: 2rem; }
    .main-header p { color: white; opacity: 0.85; margin: 0.3rem 0 0 0; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### YLYI Dashboard")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        ["Home", "Insight Bot"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown(
        "<small>E.R.A.I. Informatics · UW MSIM<br/>PNWU Health Sciences Library</small>",
        unsafe_allow_html=True,
    )

bookings_df = load_bookings()
sat23_df = load_satisfaction(2023)
sat25_df = load_satisfaction(2025)
sat_both_df = load_satisfaction_both()
circ_df = load_circulation()

if page == "Home":
    import base64
    with open("assets/pnwu_logo.png", "rb") as f:
        logo_data = base64.b64encode(f.read()).decode()

    st.markdown(f"""
    <div class="main-header" style="display:flex; align-items:center; gap:1.5rem;">
        <img src="data:image/png;base64,{logo_data}" width="90" style="border-radius:8px;">
        <div>
            <h1 style="margin:0; color:white; font-size:2rem;">Your Library, Your Impact</h1>
            <p style="margin:0.3rem 0 0 0; color:white; opacity:0.85;">PNWU Health Sciences Library · Analytics & Insights Dashboard</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Appointments", len(bookings_df))
    with col2:
        st.metric("Academic Years", bookings_df["AcademicYear"].nunique() if not bookings_df.empty else 0)
    with col3:
        st.metric("2023 Survey Respondents", len(sat23_df))
    with col4:
        st.metric("2025 Survey Respondents", len(sat25_df))

    st.markdown("---")

    t1, t2, t3, t4, t5 = st.tabs([
        "Holistic Student Engagement",
        "Collection Value",
        "Institutional Cost Avoidance",
        "General Student Satisfaction",
        "Qualitative Impact"
    ])

    with t1:
        st.subheader("Holistic Student Engagement")
        st.caption("Book a Librarian appointment trends across four academic years.")
        filtered_df = render_booking_filters(bookings_df, key_prefix="t1")
        if not filtered_df.empty:
            plot_bookings_by_year(filtered_df)
            col1, col2 = st.columns(2)
            with col1:
                plot_service_type(filtered_df)
            with col2:
                plot_virtual_vs_inperson(filtered_df)
            plot_bookings_by_quarter(filtered_df)
            st.info("Strategic plan target: 5% annual growth in student appointments.")

    with t2:
        st.subheader("Collection Value")
        st.caption("Physical book circulation from LibraryWorld, AY21-22 through AY24-25.")
        col_cir1, col_cir2, col_cir3, col_cir4, col_cir5 = st.columns(5)
        with col_cir1:
            st.metric("Total Checkouts", circ_df["Checkout"].sum())
        with col_cir2:
            st.metric("Total Checkins", circ_df["Checkin"].sum())
        with col_cir3:
            st.metric("Total Renewals", circ_df["Renew"].sum())
        with col_cir4:
            st.metric("Total Lost Items", circ_df["Lost"].sum())
        with col_cir5:
            st.metric("Total Found Items", circ_df["Found"].sum())
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Checkouts", "Checkins", "Renews", "Hold", "Lost Items", "Found Items"])

        if circ_df.empty:
            st.error("No circulation data found.")
        else:
            with tab1:

                plot_circulation_by_year(circ_df, "Checkin")
                plot_circulation(circ_df, "Checkin")
            with tab2:
                plot_circulation_by_year(circ_df, "Checkout")
                plot_circulation(circ_df, "Checkout")
            with tab3:

                plot_circulation_by_year(circ_df, "Renew")
                plot_circulation(circ_df, "Renew")
            with tab4:

                plot_circulation_by_year(circ_df, "Hold")
                plot_circulation(circ_df, "Hold")

            with tab5:

                plot_circulation_by_year(circ_df, "Lost")
                plot_circulation(circ_df, "Lost")
            with tab6:

                plot_circulation_by_year(circ_df, "Found")
                plot_circulation(circ_df, "Found")
            st.warning("Physical checkouts dropped from 415 in AY21-22 to 55 in AY24-25 — an 87% decline. Digital usage data coming when database reports are available.")

    with t3:
        st.subheader("Institutional Cost Avoidance")
        st.caption("How much money does the library save PNWU through Interlibrary Loan?")
        st.info("Cost avoidance calculator coming next.")

    with t4:
        st.subheader("General Student Satisfaction")
        st.caption("PNWU Student Satisfaction Survey — library questions only. Scale 1-5.")
        survey_tab1, survey_tab2, survey_tab3 = st.tabs(["2023", "2025", "Year-over-Year"])
        with survey_tab1:
            if sat23_df.empty:
                st.warning("2023 data not found.")
            else:
                filtered_sat23 = render_satisfaction_filters(sat23_df, key_prefix="sat23")
                plot_satisfaction_means(filtered_sat23, 2023)
                st.caption(f"{len(filtered_sat23)} respondents · 57.99% response rate")
        with survey_tab2:
            if sat25_df.empty:
                st.warning("2025 data not found.")
            else:
                filtered_sat25 = render_satisfaction_filters(sat25_df, key_prefix="sat25")
                plot_satisfaction_means(filtered_sat25, 2025)
                st.caption(f"{len(filtered_sat25)} respondents · 62.89% response rate")
        with survey_tab3:
            st.info("2023 and 2025 used different question sets so overlap is limited.")
            plot_satisfaction_comparison(sat_both_df)

    with t5:
        st.subheader("Qualitative Impact")
        st.caption("What students actually said about the library.")
        st.markdown("#### What is Working")
        col1, col2 = st.columns(2)
        with col1:
            st.success('"The library staff have been incredible in providing support and guidance for independent research projects."')
            st.success('"Mary and Jan are extraordinary. They have been such wonderful supports throughout my time at PNWU."')
            st.success('"The library is incredible. I use so many textbooks, databases, everything. Truly, they are the BEST."')
        with col2:
            st.success('"Amazing, effective, and responsive staff, from the leadership on down."')
            st.success('"The quickest I ever received an ILL was two hours after request. They deserve a raise!!!!!"')
            st.success('"I access information through the library databases every day during rotations."')
        st.markdown("#### What Needs Attention")
        col1, col2 = st.columns(2)
        with col1:
            st.error('"I did not even know we had a library."')
            st.error('"When we are on rotations, we cannot meet during normal business hours — that is the only time you can book a librarian."')
        with col2:
            st.error('"Access to further journals and resources for research would be extremely helpful, now we are very limited."')
            st.error('"I wish we had access to more databases, even commonly used ones like Elsevier or Wiley Online."')

    st.markdown("---")

    with open("assets/uw_logo.png", "rb") as f:
        uw_logo = base64.b64encode(f.read()).decode()

    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:1rem; opacity:0.7;">
        <small>Built by E.R.A.I. Informatics (Em Stelter · Rose Brown · AJ Amrous · Ivette Ivanov) · Sponsor: Jan Kuebel-Hernandez</small>
        <div style="display:flex; align-items:center; gap:0.5rem;">
            <small>Powered by</small>
            <img src="data:image/png;base64,{uw_logo}" width="50">
            <small>UW iSchool</small>
        </div>
    </div>
    """, unsafe_allow_html=True)

elif page == "Insight Bot":
    st.markdown("## AI Insights Bot")
    st.info(
        "The AI bot is coming in the next step. "
        "It will use LlamaIndex + ChromaDB "
        "modeled on SJSU Library's KingbotGPT architecture."
    )
