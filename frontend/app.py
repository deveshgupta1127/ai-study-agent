import streamlit as st

from pages import (
    login,
    documents,
    quiz,
    chat,
    dashboard,
    groups,
)


# =========================
# CONFIG
# =========================

st.set_page_config(
    page_title="AI Study Assistant",
    layout="wide"
)


# =========================
# SESSION STATE INIT
# =========================

if "token" not in st.session_state:
    st.session_state.token = None

if "user" not in st.session_state:
    st.session_state.user = None


# =========================
# MAIN ROUTER
# =========================

def main():
    if not st.session_state.token:
        login.show()
    else:
        show_app()


# =========================
# APP (AFTER LOGIN)
# =========================

def show_app():
    st.sidebar.title("📚 AI Study Assistant")

    # ------------------------
    # User Info
    # ------------------------
    if st.session_state.user:
        st.sidebar.markdown(
            f"👤 **{st.session_state.user.get('display_name', '')}**"
        )
        st.sidebar.divider()

    # ------------------------
    # Navigation
    # ------------------------
    page = st.sidebar.radio(
        "Navigation",
        [
            "Dashboard",
            "Documents",
            "Quiz",
            "Chat",
            "Groups",
            "Logout",
        ],
        index=0
    )

    # ------------------------
    # Routing
    # ------------------------
    if page == "Dashboard":
        dashboard.show()

    elif page == "Documents":
        documents.show()

    elif page == "Quiz":
        quiz.show()

    elif page == "Chat":
        chat.show()

    elif page == "Groups":
        groups.show()

    elif page == "Logout":
        handle_logout()


# =========================
# LOGOUT
# =========================

def handle_logout():
    st.session_state.clear()
    st.rerun()


# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    main()