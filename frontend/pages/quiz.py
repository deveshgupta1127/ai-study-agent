import streamlit as st

from api_client import (
    get_documents,
    get_document_topics,
    generate_quiz,
    get_quiz,
    submit_quiz,
    get_quiz_results
)

def show():
    st.title("Quiz generator")

    token=st.session_state.get("token")

    if not token:
        st.warning("Please login first")

    st.subheader("Select Document")
    docs=get_documents(token)

    if not docs:
        st.info("No documents upload yet")
        return
    
    doc_map={doc["filename"]: doc["id"] for doc in docs}
    selected_doc=st.selectbox("Choose document",list(doc_map.keys()))

    doc_id= doc_map[selected_doc]

    topics= get_document_topics(doc_id, token)

    if not topics:
        st.warning("No topics found for this document")
        return
    
    topic_map={t["title"]: t["id"] for t in topics}

    selected_topic=st.selectbox("Choose topic", list(topic_map.keys()))

    topic_id=topic_map[selected_topic]

    st.subheader("Quiz Settings")

    quiz_type = st.selectbox("Quiz Type", ["mcq", "short_answer"])
    difficulty = st.slider("Difficulty (1-5)", 1, 5, 3)
    num_questions = st.slider("Number of Questions", 1, 10, 5)

    # ==============================
    # GENERATE QUIZ
    # ==============================
    if st.button("Generate Quiz"):
        with st.spinner("Generating quiz..."):
            quiz = generate_quiz(
                topic_id,
                quiz_type,
                difficulty,
                num_questions,
                token
            )

            st.session_state.quiz_id = quiz["id"]
            st.session_state.quiz_data = quiz

    # ==============================
    # SHOW QUIZ
    # ==============================
    if "quiz_data" in st.session_state:
        quiz = st.session_state.quiz_data

        st.subheader("Answer Questions")

        answers = {}

        for i, q in enumerate(quiz["questions"]):
            st.markdown(f"**Q{i+1}. {q['question_text']}**")

            if quiz["quiz_type"] == "mcq":
                answers[q["id"]] = st.radio(
                    f"Select answer {i+1}",
                    q["options"],
                    key=f"q_{q['id']}"
                )
            else:
                answers[q["id"]] = st.text_input(
                    f"Your answer {i+1}",
                    key=f"q_{q['id']}"
                )

            st.divider()

        # ==============================
        # SUBMIT QUIZ
        # ==============================
        if st.button("Submit Quiz"):
            formatted_answers = [
                {"question_id": qid, "answer": ans}
                for qid, ans in answers.items()
            ]

            result = submit_quiz(
                st.session_state.quiz_id,
                formatted_answers,
                token
            )

            st.session_state.quiz_result = result

    # ==============================
    # SHOW RESULTS
    # ==============================
    if "quiz_result" in st.session_state:
        result = st.session_state.quiz_result

        st.subheader("Results")

        st.success(f"Score: {result['correct']} / {result['total']}")

        for r in result["results"]:
            st.markdown(f"**Question ID:** {r['question_id']}")
            st.write(f"Your Answer: {r['user_answer']}")
            st.write(f"Correct Answer: {r['correct_answer']}")

            if r["is_correct"]:
                st.success("Correct ✅")
            else:
                st.error("Incorrect ❌")

            if r.get("explanation"):
                with st.expander("Explanation"):
                    st.write(r["explanation"])

            st.divider()