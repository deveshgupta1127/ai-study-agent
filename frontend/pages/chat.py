import streamlit as st

from api_client import (
    get_documents,
    create_chat_session,
    ask_question,
    get_chat_history
)


def show():
    st.title("💬 Chat with Documents")

    token = st.session_state.get("token")

    if not token:
        st.warning("Please login first")
        return

    # ==============================
    # DOCUMENT SELECTOR
    # ==============================
    st.subheader("Select Document (Optional Scope)")

    docs = get_documents(token)

    doc_options = {"All Documents": None}
    for doc in docs:
        doc_options[doc["filename"]] = doc["id"]

    selected_doc_name = st.selectbox(
        "Choose document scope",
        list(doc_options.keys())
    )

    selected_doc_id = doc_options[selected_doc_name]

    # ==============================
    # CREATE SESSION
    # ==============================
    if "chat_session_id" not in st.session_state:
        if st.button("Start Chat"):
            session = create_chat_session(selected_doc_id, token)
            st.session_state.chat_session_id = session["id"]
            st.session_state.chat_history = []

    # ==============================
    # CHAT INTERFACE
    # ==============================
    if "chat_session_id" in st.session_state:

        st.divider()
        st.subheader("Chat")

        # Load history (optional refresh)
        history = get_chat_history(st.session_state.chat_session_id, token)

        # Display history
        for msg in history:
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.write(msg["content"])
            else:
                with st.chat_message("assistant"):
                    st.write(msg["content"])

        # ==============================
        # USER INPUT
        # ==============================
        question = st.chat_input("Ask something about your document...")

        if question:
            with st.chat_message("user"):
                st.write(question)

            with st.spinner("Thinking..."):
                response = ask_question(
                    st.session_state.chat_session_id,
                    question,
                    token
                )

            # Assistant response
            with st.chat_message("assistant"):
                st.write(response["answer"])

                # ==============================
                # SHOW SOURCES
                # ==============================
                if response.get("sources"):
                    with st.expander("Sources"):
                        for src in response["sources"]:
                            st.write(f"- Chunk ID: {src['chunk_id']}")

            # Force refresh
            st.rerun()