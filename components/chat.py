"""
Chat interface component for Streamlit app.
"""
import streamlit as st
from typing import Optional
from services.azure_openai import AzureOpenAIService, ChatResponse
from services.cost_calculator import CostCalculator, CostBreakdown


def initialize_chat_state():
    """Initialize session state for chat."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    if "cost_calculator" not in st.session_state:
        st.session_state.cost_calculator = CostCalculator()
    if "last_cost_breakdown" not in st.session_state:
        st.session_state.last_cost_breakdown = None


def render_chat_interface(
    openai_service: AzureOpenAIService,
    vte_context: Optional[str] = None,
) -> Optional[CostBreakdown]:
    """
    Render the chat interface and handle user input.

    Args:
        openai_service: Azure OpenAI service instance
        vte_context: Optional VTE data context to include

    Returns:
        CostBreakdown if a new message was sent, None otherwise
    """
    initialize_chat_state()

    st.subheader("Clinical Quality Assistant")
    st.caption("Ask questions about VTE performance, trends, and improvement opportunities")

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask about VTE metrics, trends, or recommendations..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                try:
                    if vte_context:
                        response = openai_service.chat_with_context(
                            user_message=prompt,
                            vte_context=vte_context,
                            conversation_history=st.session_state.conversation_history,
                        )
                    else:
                        response = openai_service.chat(
                            user_message=prompt,
                            conversation_history=st.session_state.conversation_history,
                        )

                    # Display response
                    st.markdown(response.content)

                    # Update conversation history
                    st.session_state.conversation_history.append(
                        {"role": "user", "content": prompt}
                    )
                    st.session_state.conversation_history.append(
                        {"role": "assistant", "content": response.content}
                    )

                    # Add to messages
                    st.session_state.messages.append(
                        {"role": "assistant", "content": response.content}
                    )

                    # Calculate cost
                    cost_breakdown = st.session_state.cost_calculator.calculate_cost(
                        model=response.model,
                        input_tokens=response.input_tokens,
                        output_tokens=response.output_tokens,
                    )
                    st.session_state.last_cost_breakdown = cost_breakdown

                    return cost_breakdown

                except Exception as e:
                    st.error(f"Error getting response: {str(e)}")
                    return None

    return st.session_state.last_cost_breakdown


def render_chat_sidebar():
    """Render chat controls in sidebar."""
    st.sidebar.subheader("Chat Controls")

    if st.sidebar.button("Clear Chat History", type="secondary"):
        st.session_state.messages = []
        st.session_state.conversation_history = []
        st.session_state.last_cost_breakdown = None
        st.rerun()

    # Show message count
    msg_count = len(st.session_state.get("messages", []))
    st.sidebar.caption(f"Messages in session: {msg_count}")


def get_suggested_questions() -> list[str]:
    """Return a list of suggested questions for VTE analytics."""
    return [
        "What is our current VTE prophylaxis rate across all departments?",
        "Which departments are below the 85% target for VTE prevention?",
        "Show me the trend in VTE events over the past 6 months",
        "What are the top opportunities to improve VTE compliance?",
        "Compare performance between ICU and general medicine units",
        "Which physicians have the highest VTE prophylaxis rates?",
        "What factors are associated with VTE events in our data?",
        "Give me a summary of our VTE quality metrics",
    ]


def render_suggested_questions():
    """Render suggested questions as clickable buttons."""
    st.caption("Suggested questions:")
    questions = get_suggested_questions()

    cols = st.columns(2)
    for i, question in enumerate(questions[:4]):
        col = cols[i % 2]
        with col:
            if st.button(question[:50] + "...", key=f"q_{i}", use_container_width=True):
                return question
    return None
