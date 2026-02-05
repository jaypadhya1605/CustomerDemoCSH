"""
Cost tracking component for Streamlit app.
Displays real-time estimated costs and cumulative session costs.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Optional
from services.cost_calculator import CostBreakdown, CostCalculator


def render_cost_receipt(breakdown: Optional[CostBreakdown]):
    """
    Render a cost receipt for the last API call.

    Args:
        breakdown: CostBreakdown from the last API call
    """
    if not breakdown:
        st.info("No costs recorded yet. Start a conversation to see cost tracking.")
        return

    st.subheader("Cost Receipt")

    # Create columns for the receipt
    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            label="Model Used",
            value=breakdown.model,
        )
        st.metric(
            label="Total Tokens",
            value=f"{breakdown.total_tokens:,}",
        )

    with col2:
        st.metric(
            label="Estimated Cost",
            value=f"${breakdown.total_estimated_cost:.6f}",
        )
        st.metric(
            label="Actual Cost",
            value="Pending" if breakdown.actual_cost is None else f"${breakdown.actual_cost:.6f}",
            help="Actual costs from Azure Cost Management are delayed 24-48 hours",
        )

    # Token breakdown
    with st.expander("Token Breakdown", expanded=True):
        token_data = {
            "Type": ["Input", "Output"],
            "Tokens": [breakdown.input_tokens, breakdown.output_tokens],
            "Cost": [breakdown.input_cost, breakdown.output_cost],
        }
        df = pd.DataFrame(token_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

    # Source disclaimer
    st.caption(f"Source: {breakdown.source}")
    st.caption(f"Timestamp: {breakdown.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")


def render_cost_tracker(cost_calculator: CostCalculator):
    """
    Render the full cost tracking dashboard.

    Args:
        cost_calculator: CostCalculator instance with session data
    """
    st.subheader("Session Cost Tracking")

    session_total = cost_calculator.get_session_total()

    if session_total["request_count"] == 0:
        st.info("No API calls made yet. Start a conversation to track costs.")
        return

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="API Requests",
            value=session_total["request_count"],
        )

    with col2:
        st.metric(
            label="Total Tokens",
            value=f"{session_total['total_tokens']:,}",
        )

    with col3:
        st.metric(
            label="Estimated Cost",
            value=f"${session_total['total_estimated_cost']:.6f}",
        )

    with col4:
        actual = session_total.get("total_actual_cost")
        st.metric(
            label="Actual Cost",
            value="Pending" if actual is None else f"${actual:.6f}",
        )

    st.divider()

    # Cost by model breakdown
    if session_total["costs_by_model"]:
        st.subheader("Cost by Model")

        model_data = []
        for model, data in session_total["costs_by_model"].items():
            model_data.append({
                "Model": model,
                "Requests": data["requests"],
                "Tokens": data["tokens"],
                "Estimated Cost": f"${data['estimated_cost']:.6f}",
            })

        df_models = pd.DataFrame(model_data)
        st.dataframe(df_models, use_container_width=True, hide_index=True)

        # Pie chart for cost distribution
        if len(model_data) > 1:
            fig = px.pie(
                df_models,
                values=[float(d["estimated_cost"].replace("$", "")) for d in model_data],
                names=[d["Model"] for d in model_data],
                title="Cost Distribution by Model",
            )
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Cost history
    with st.expander("Cost History", expanded=False):
        history = cost_calculator.get_cost_history()
        if history:
            df_history = pd.DataFrame(history)
            st.dataframe(df_history, use_container_width=True, hide_index=True)
        else:
            st.info("No cost history available.")


def render_cost_timeline(cost_calculator: CostCalculator):
    """Render a timeline chart of costs."""
    history = cost_calculator.session_costs

    if len(history) < 2:
        return

    # Create timeline data
    timeline_data = []
    cumulative_cost = 0.0

    for i, cost in enumerate(history):
        cumulative_cost += cost.total_estimated_cost
        timeline_data.append({
            "Request #": i + 1,
            "Timestamp": cost.timestamp,
            "Request Cost": cost.total_estimated_cost,
            "Cumulative Cost": cumulative_cost,
            "Model": cost.model,
        })

    df = pd.DataFrame(timeline_data)

    # Create figure with dual y-axis
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df["Request #"],
        y=df["Request Cost"],
        name="Request Cost",
        marker_color="lightblue",
    ))

    fig.add_trace(go.Scatter(
        x=df["Request #"],
        y=df["Cumulative Cost"],
        name="Cumulative Cost",
        line=dict(color="red", width=2),
        yaxis="y2",
    ))

    fig.update_layout(
        title="Cost Over Time",
        xaxis_title="Request #",
        yaxis_title="Request Cost ($)",
        yaxis2=dict(
            title="Cumulative Cost ($)",
            overlaying="y",
            side="right",
        ),
        legend=dict(x=0.01, y=0.99),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_cost_sidebar(cost_calculator: CostCalculator):
    """Render cost summary in sidebar."""
    st.sidebar.subheader("Cost Summary")

    session_total = cost_calculator.get_session_total()

    st.sidebar.metric(
        label="Session Total",
        value=f"${session_total['total_estimated_cost']:.6f}",
    )

    st.sidebar.metric(
        label="Total Tokens",
        value=f"{session_total['total_tokens']:,}",
    )

    if st.sidebar.button("Reset Costs", type="secondary"):
        cost_calculator.clear_session()
        st.rerun()


def render_two_track_explanation():
    """Render explanation of the two-track cost model."""
    with st.expander("Understanding Cost Tracking", expanded=False):
        st.markdown("""
        ### Two-Track Cost Model

        This demo uses a two-track approach to cost tracking:

        **1. Estimated Cost (Real-time)**
        - Calculated instantly after each API call
        - Based on token usage × pricing table
        - Provides immediate visibility into workload costs

        **2. Actual Cost (Authoritative)**
        - Sourced from Azure Cost Management
        - Delayed 24-48 hours due to Azure processing
        - Represents actual billed amounts

        ### Why Two Tracks?

        Azure Cost Management doesn't provide real-time cost data. By using
        estimated costs, you get immediate feedback while still having access
        to authoritative billing data when it becomes available.

        ### Workload-Based Costing

        Costs are driven by:
        - **Token consumption**: Input and output tokens processed
        - **Model selection**: Different models have different rates
        - **Request volume**: More requests = more costs

        This is different from traditional "platform cost" models where you
        pay a fixed fee regardless of usage.
        """)
