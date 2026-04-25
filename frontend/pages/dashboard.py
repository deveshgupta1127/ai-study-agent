import streamlit as st
import pandas as pd

from api_client import (
    get_dashboard,
    get_topic_mastery,
    get_recommendations
)


def show():
    st.title("📊 Dashboard")
    st.divider()

    token = st.session_state.get("token")

    if not token:
        st.error("You are not logged in")
        return

    try:
        # -------------------------------
        # Fetch Data
        # -------------------------------
        with st.spinner("Loading dashboard..."):
            dashboard = get_dashboard(token)
            mastery = get_topic_mastery(token)
            recommendations = get_recommendations(token)

        # -------------------------------
        # Top Metrics
        # -------------------------------
        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Documents", dashboard["total_docs"])
        col2.metric("Quizzes", dashboard["total_quizzes"])
        col3.metric("Avg Mastery", f"{dashboard['avg_mastery'] * 100:.0f}%")
        col4.metric("Topics Studied", dashboard["topics_studied"])

        st.divider()

        # -------------------------------
        # Mastery Chart
        # -------------------------------
        st.subheader("📈 Topic Mastery")

        if mastery:
            df = pd.DataFrame(mastery)

            df = df[["topic_title", "mastery_score"]]
            df = df.set_index("topic_title")

            st.bar_chart(df)

        else:
            st.info("No progress yet. Take a quiz to start tracking mastery.")

        st.divider()

        # -------------------------------
        # Study Plan (AI)
        # -------------------------------
        st.subheader("🧠 Recommended Study Plan")

        plan = recommendations.get("study_plan", [])

        if plan:
            for item in plan:
                with st.container():
                    st.markdown(f"### {item['topic_title']}")

                    st.write(f"**Action:** {item['recommended_action']}")
                    st.write(f"**Difficulty:** {item['difficulty']}")
                    st.write(f"**Priority:** {item['priority']}")
                    st.write(f"**Estimated Time:** {item['est_minutes']} mins")

                    st.divider()
        else:
            st.info("No recommendations yet. Start practicing to get a study plan.")

        # -------------------------------
        # Recent Activity
        # -------------------------------
        st.subheader("🕒 Recent Activity")

        activity = dashboard.get("recent_activity", [])

        if activity:
            for item in activity:
                st.write(f"• {item['detail']} ({item['timestamp']})")
        else:
            st.info("No recent activity.")

    except Exception as e:
        st.error(f"Failed to load dashboard: {str(e)}")