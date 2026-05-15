import pandas as pd
import streamlit as st

from src.charts import plot_response_hist, plot_borough_bar

# from src.charts import (# CHART FUNCTIONS plot_reports_overtime_bar)
# from src.data import (# KPI FUNCTIONS IF APPLICABLE get_total_events_kpi)


def header_metrics(df: pd.DataFrame) -> None:
    """Rendering header metrics. Placeholder values are intentional."""
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("METRIC 1")
    with c2:
        st.metric("METRIC 2")
    with c3:
        st.metric("METRIC 3")

def body_layout_tabs(df) -> None:
    # body_layout_tabs(df: pd.DataFrame) <--- update this when dataframe is ready
    """Tabs layout with 3 default tabs."""
    t1, t2, t3, t4, t5 = st.tabs(["Holistic Student Engagement","Collection Value", "Institutional Cost Avoidance", "General Student Satisfaction", "Qualitative Impact"])
    with t1:
        st.subheader("Holistic Student Engagement")
        tab_choice = st.radio(''':grey[INSERT CAPTION HERE.]''',
        ["VIS 1: Book A Librarian Reports","VIS 2", "VIS 3"],
        horizontal=True,
        )
        #if tab_choice == "Bar":
            #plot_reports_overtime_bar(df) #<-chart function here
        if tab_choice == "VIS 1: Book A Librarian Reports":
            st.write("CHART FOR BOOK A LIBRARIAN REPORTS")
            # plot_reports_overtime_line(df) #<- new chart function here
        elif tab_choice == "VIS 2":
            st.write("ADDITIONAL CHART FOR HOLISTIC STUDENT ENGAGEMENT")
            # plot_reports_overtime_line_sex(df)  # <- new chart function here
        elif tab_choice == "VIS 3":
            st.write("ADDITIONAL CHART FOR HOLISTIC STUDENT ENGAGEMENT")
            # plot_reports_overtime_line_vax(df)  # <- new chart function here

    with t2:
        st.subheader("Collection Value")
        st.caption("INSERT CAPTION HERE.")
        st.write("Charts for collection value section")
        # plot_patient_ages(df) #<- new chart function here
        # plot_num_reports_sex(df) #<- new chart function here
        # plot_num_reports_loc(df) #<- new chart function here

    with t3:
        st.subheader("Institutional Cost Avoidance")
        st.caption("CAPTION HERE.")
        st.write("Charts for institutional cost avoidance section")
        # plot_most_common_symptoms(df) #<-chart function here

    with t4:
        st.subheader("General Student Satisfaction")
        st.caption("CAPTION HERE.")
        st.write("Charts for general student satisfaction section")

    with t5:
        st.subheader("Qualitative Impact")
        st.caption("CAPTION HERE.")
        st.write("Charts for qualitative impact section")

    # with t6:
        # If we want people to download our data, we'd use this guy in some way.
        # st.dataframe(data=df)
        # st.download_button(
            # label="Download CSV",
            # data=df.to_csv(index=False),
            # file_name="west_states_filtered_v2.csv",
            # mime="text/csv",
            # icon=":material/download:")

        ## Source: https://docs.streamlit.io/develop/api-reference/widgets/st.download_button
        ## Source: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_csv.html