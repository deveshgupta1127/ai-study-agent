import streamlit as st

from api_client import (
    create_group,
    join_group,
    get_groups,
    share_document,
    get_group_documents,
    get_documents,
)


def show():
    st.title("👥 Study Groups")
    st.divider()

    token = st.session_state.get("token")

    if not token:
        st.error("You are not logged in")
        return

    # -------------------------------
    # Create Group
    # -------------------------------
    st.subheader("➕ Create Group")

    with st.form("create_group"):
        group_name = st.text_input("Group Name")
        submit_create = st.form_submit_button("Create")

        if submit_create:
            if not group_name:
                st.error("Group name required")
            else:
                try:
                    res = create_group(group_name, token)
                    st.success(f"Group created! Invite code: {res['invite_code']}")
                except Exception as e:
                    st.error(str(e))

    st.divider()

    # -------------------------------
    # Join Group
    # -------------------------------
    st.subheader("🔑 Join Group")

    with st.form("join_group"):
        invite_code = st.text_input("Invite Code")
        submit_join = st.form_submit_button("Join")

        if submit_join:
            try:
                join_group(invite_code, token)
                st.success("Joined group successfully")
            except Exception as e:
                st.error(str(e))

    st.divider()

    # -------------------------------
    # List Groups
    # -------------------------------
    st.subheader("📋 Your Groups")

    try:
        groups = get_groups(token)
    except Exception as e:
        st.error(str(e))
        return

    if not groups:
        st.info("You are not part of any groups yet")
        return

    # -------------------------------
    # Show Each Group
    # -------------------------------
    for group in groups:
        with st.expander(f"{group['name']} (Members: {group['member_count']})"):

            st.write(f"**Invite Code:** `{group['invite_code']}`")

            # -------------------------------
            # Share Document
            # -------------------------------
            st.subheader("📤 Share Document")

            user_docs = get_documents(token)

            doc_options = {
                doc["filename"]: doc["id"]
                for doc in user_docs
            }

            if doc_options:
                selected_doc = st.selectbox(
                    "Select document",
                    options=list(doc_options.keys()),
                    key=f"share_{group['id']}"
                )

                if st.button("Share", key=f"btn_{group['id']}"):
                    try:
                        share_document(
                            group["id"],
                            doc_options[selected_doc],
                            token
                        )
                        st.success("Document shared")
                    except Exception as e:
                        st.error(str(e))
            else:
                st.info("No documents to share")

            st.divider()

            # -------------------------------
            # Group Documents
            # -------------------------------
            st.subheader("📄 Group Documents")

            try:
                group_docs = get_group_documents(group["id"], token)

                if group_docs:
                    for doc in group_docs:
                        st.write(f"- {doc['filename']} ({doc['status']})")
                else:
                    st.info("No documents shared yet")

            except Exception as e:
                st.error(str(e))