import streamlit as st

from ..queries import logs_to_dataframe
from ..classifiers import add_classification_columns
from ..charts import (
    volume_over_time, session_frequency, volume_by_muscle_group,
    exercise_progression, e1rm_progression,
)


def render():
    st.title("Training Analytics")
    df = logs_to_dataframe(st.session_state.user_id)
    if df.empty:
        st.info("No training data yet. Log sessions or import from Hevy to see analytics.")
        return

    df = add_classification_columns(df)
    df["year_week"] = df["date"].dt.strftime("%Y-W%U")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Sessions", df["date"].nunique())
    col2.metric("Total Exercises", df["exercise"].nunique())
    col3.metric("Total Volume (kg)", f"{df['volume'].sum():,.0f}")
    col4.metric("Date Range", f"{(df['date'].max() - df['date'].min()).days} days")

    st.sidebar.markdown("---")
    st.sidebar.subheader("Analytics Filters")
    date_min, date_max = df["date"].min().date(), df["date"].max().date()
    date_range = st.sidebar.date_input("Date range", value=(date_min, date_max), min_value=date_min, max_value=date_max)
    if len(date_range) == 2:
        df = df[(df["date"].dt.date >= date_range[0]) & (df["date"].dt.date <= date_range[1])]

    st.markdown("---")
    st.header("1. Weekly Volume")
    st.plotly_chart(volume_over_time(df), use_container_width=True)

    st.markdown("---")
    st.header("2. Training Frequency")
    st.plotly_chart(session_frequency(df), use_container_width=True)

    st.markdown("---")
    st.header("3. Volume by Muscle Group")
    st.plotly_chart(volume_by_muscle_group(df), use_container_width=True)

    st.markdown("---")
    st.header("4. Exercise Progression")
    exercises = sorted(df["exercise"].unique())
    selected = st.selectbox("Select exercise", exercises)
    if selected:
        st.plotly_chart(exercise_progression(df, selected), use_container_width=True)
        st.plotly_chart(e1rm_progression(df, selected), use_container_width=True)
