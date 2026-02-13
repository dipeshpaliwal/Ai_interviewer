import streamlit as st
import asyncio

from interview_practice_system import (
    initialize_preparation_crew,
    evaluate_answer
)

# -------------------------------------------------
# Streamlit Page Config
# -------------------------------------------------
st.set_page_config(page_title="AI Mock Interviewer", page_icon="🤖")
st.title("🤖 AI Mock Interviewer")

# -------------------------------------------------
# Initialize session state
# -------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.interview_started = False
    st.session_state.current_question = None
    st.session_state.correct_answer = None
    st.session_state.preparation_crew = None
    st.session_state.follow_up_question = None
    st.session_state.is_generating_follow_up = False

# -------------------------------------------------
# Sidebar: Interview setup
# -------------------------------------------------
with st.sidebar:
    st.header("Interview Setup")

    company_name = st.text_input("Company Name", "Google")
    role = st.text_input("Position", "Software Engineer")
    difficulty = st.selectbox(
        "Difficulty Level", ["Easy", "Medium", "Hard"], index=1
    )

    if st.button("Start Interview"):
        st.session_state.interview_started = True
        st.session_state.messages = []
        st.session_state.current_question = None
        st.session_state.correct_answer = None
        st.session_state.follow_up_question = None
        st.session_state.is_generating_follow_up = False

        st.session_state.preparation_crew = initialize_preparation_crew(
            company_name, role, difficulty.lower()
        )
        st.rerun()

# -------------------------------------------------
# Display chat history
# -------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -------------------------------------------------
# If interview not started
# -------------------------------------------------
if not st.session_state.interview_started:
    st.info(
        "👋 Set up your interview in the sidebar and click **Start Interview** to begin."
    )
    st.stop()

# -------------------------------------------------
# Generate first question
# -------------------------------------------------
if st.session_state.current_question is None:
    with st.spinner("🤖 Preparing your interview question..."):
        preparation_result = st.session_state.preparation_crew.kickoff()

        st.session_state.current_question = preparation_result.pydantic.question
        st.session_state.correct_answer = (
            preparation_result.pydantic.correct_answer
        )

        st.session_state.messages.append(
            {"role": "assistant", "content": st.session_state.current_question}
        )
        st.rerun()

# -------------------------------------------------
# User input (TEXT ONLY – cloud safe)
# -------------------------------------------------
user_input = st.chat_input("Type your answer here...")

if user_input:
    # Add user answer to chat
    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )

    # -------------------------------------------------
    # Evaluate answer
    # -------------------------------------------------
    with st.spinner("🤖 Evaluating your answer..."):
        evaluation = evaluate_answer(
            question=st.session_state.current_question,
            user_answer=user_input,
            correct_answer=st.session_state.correct_answer,
        )

        st.session_state.messages.append(
            {"role": "assistant", "content": evaluation}
        )

    # -------------------------------------------------
    # Generate follow-up question
    # -------------------------------------------------
    if not st.session_state.is_generating_follow_up:
        st.session_state.is_generating_follow_up = True

        try:
            follow_up_result = asyncio.run(
                generate_follow_up_question(
                    question=st.session_state.current_question,
                    company_name=company_name,
                    role=role,
                    difficulty=difficulty.lower(),
                )
            )

            st.session_state.current_question = follow_up_result.question
            st.session_state.correct_answer = (
                follow_up_result.correct_answer
            )

            st.session_state.messages.append(
                {"role": "assistant", "content": follow_up_result.question}
            )

        except Exception as e:
            st.error(f"Error generating follow-up question: {e}")
            st.session_state.current_question = None

        st.session_state.is_generating_follow_up = False
        st.rerun()
