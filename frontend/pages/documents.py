import streamlit as st
from api_client import (
    upload_document,
    get_documents,
    get_document_topics,
    delete_document,
)


def show():
    st.title("Documents")

    # AUTH CHECK
    if "token" not in st.session_state or not st.session_state.token:
        st.warning("Please login first.")
        return

    token = st.session_state.token

    # =========================
    # UPLOAD
    # =========================
    st.subheader("Upload Document")

    uploaded_file = st.file_uploader(
        "Upload PDF, DOCX, or TXT",
        type=["pdf", "docx", "txt"]
    )

    if uploaded_file:
        if st.button("Upload"):
            with st.spinner("Uploading and processing..."):
                try:
                    upload_document(
                        uploaded_file,
                        uploaded_file.name,
                        token
                    )
                    st.success("Uploaded successfully!")
                    st.toast("Processing started")
                    st.rerun()
                except Exception as e:
                    st.error(f"Upload failed: {str(e)}")

    st.divider()

    # =========================
    # DOCUMENT LIST
    # =========================
    st.subheader("Your Documents")

    try:
        documents = get_documents(token)
    except Exception as e:
        st.error(f"Failed to load documents: {str(e)}")
        return

    if not documents:
        st.info("No documents uploaded yet")
        return

    # =========================
    # LOOP DOCUMENTS
    # =========================
    for doc in documents:
        with st.container():
            col1, col2, col3 = st.columns([4, 1, 1])

            # LEFT SIDE
            with col1:
                st.markdown(f"**{doc['filename']}**")
                st.caption(f"Type: {doc['file_type']}")

            # STATUS
            with col2:
                status = doc["status"]

                if status == "done":
                    st.success("Done")
                elif status == "processing":
                    st.warning("Processing")
                elif status == "error":
                    st.error("Error")
                else:
                    st.info(status)

            # ACTION BUTTONS
            with col3:
                # DELETE
                if st.button("🗑", key=f"delete_{doc['id']}"):
                    try:
                        delete_document(doc["id"], token)
                        st.success("Deleted")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

                # RETRY (only if failed)
                if status == "error":
                    if st.button("🔄", key=f"retry_{doc['id']}"):
                        try:
                            reprocess_document(doc["id"], token)
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

            # =========================
            # TOPICS
            # =========================
            if doc["status"] == "done":
                with st.expander("View Topics"):
                    try:
                        topics = get_document_topics(doc["id"], token)

                        if not topics:
                            st.info("No topics found")
                        else:
                            for t in topics:
                                st.markdown(f"### {t['title']}")
                                if t.get("summary"):
                                    st.write(t["summary"])
                                st.caption(f"Difficulty: {t['difficulty_level']}")
                                st.divider()

                    except Exception as e:
                        st.error(f"Failed to load topics: {str(e)}")

            st.divider()