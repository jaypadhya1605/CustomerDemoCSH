"""
VTE Analytics Dashboard component for Streamlit app.
Displays clinical quality metrics, performance-to-goal, and improvement opportunities.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
import random


def load_vte_data(data_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load VTE sample data from Excel file.

    Args:
        data_path: Path to the data file

    Returns:
        DataFrame with VTE data
    """
    if data_path is None:
        data_path = Path(__file__).parent.parent / "data" / "vte_sample_data.xlsx"

    try:
        df = pd.read_excel(data_path)
        return df
    except FileNotFoundError:
        st.warning("VTE data file not found. Using generated sample data.")
        return generate_sample_vte_data()


def generate_sample_vte_data() -> pd.DataFrame:
    """Generate sample VTE data for demonstration."""
    random.seed(42)

    departments = [
        "Medical ICU", "Surgical ICU", "General Medicine",
        "Orthopedics", "Cardiology", "Oncology", "Neurology", "Emergency"
    ]

    physicians = [
        "Dr. Smith", "Dr. Johnson", "Dr. Williams", "Dr. Brown",
        "Dr. Jones", "Dr. Garcia", "Dr. Miller", "Dr. Davis",
        "Dr. Rodriguez", "Dr. Martinez"
    ]

    data = []
    base_date = datetime(2024, 1, 1)

    for i in range(150):
        dept = random.choice(departments)
        # Vary prophylaxis rate by department
        dept_base_rate = {
            "Medical ICU": 0.92, "Surgical ICU": 0.88, "General Medicine": 0.78,
            "Orthopedics": 0.95, "Cardiology": 0.85, "Oncology": 0.82,
            "Neurology": 0.80, "Emergency": 0.72
        }

        prophylaxis_given = random.random() < dept_base_rate.get(dept, 0.80)
        vte_event = random.random() < (0.02 if prophylaxis_given else 0.08)

        admission_date = base_date + timedelta(days=random.randint(0, 180))

        data.append({
            "Patient_ID": f"PT{1000 + i}",
            "Admission_Date": admission_date,
            "Department": dept,
            "Attending_Physician": random.choice(physicians),
            "VTE_Risk_Score": random.choice(["Low", "Moderate", "High"]),
            "Prophylaxis_Given": "Yes" if prophylaxis_given else "No",
            "VTE_Event": "Yes" if vte_event else "No",
            "Length_of_Stay": random.randint(1, 14),
            "Age": random.randint(25, 85),
        })

    return pd.DataFrame(data)


def get_vte_context(df: pd.DataFrame) -> str:
    """
    Generate a text summary of VTE data for AI context.

    Args:
        df: DataFrame with VTE data

    Returns:
        Text summary of the data
    """
    total_patients = len(df)
    prophylaxis_rate = (df["Prophylaxis_Given"] == "Yes").mean() * 100
    vte_event_rate = (df["VTE_Event"] == "Yes").mean() * 100

    dept_rates = df.groupby("Department").apply(
        lambda x: (x["Prophylaxis_Given"] == "Yes").mean() * 100
    ).round(1)

    below_goal = dept_rates[dept_rates < 85].to_dict()

    context = f"""
VTE Analytics Summary:
- Total Patients: {total_patients}
- Overall Prophylaxis Rate: {prophylaxis_rate:.1f}%
- VTE Event Rate: {vte_event_rate:.1f}%
- Target Goal: 85%

Department Performance:
{dept_rates.to_string()}

Departments Below 85% Goal:
{below_goal if below_goal else 'All departments meeting goal'}

Date Range: {df['Admission_Date'].min().strftime('%Y-%m-%d')} to {df['Admission_Date'].max().strftime('%Y-%m-%d')}
"""
    return context


def render_vte_dashboard(df: Optional[pd.DataFrame] = None):
    """
    Render the full VTE analytics dashboard.

    Args:
        df: Optional DataFrame with VTE data (loads from file if not provided)
    """
    if df is None:
        df = load_vte_data()

    st.subheader("VTE Performance Dashboard")

    # Key metrics
    render_key_metrics(df)

    st.divider()

    # Performance by department
    render_department_performance(df)

    st.divider()

    # Trend analysis
    render_trend_analysis(df)

    st.divider()

    # Opportunities for improvement
    render_improvement_opportunities(df)


def render_key_metrics(df: pd.DataFrame):
    """Render key VTE metrics."""
    col1, col2, col3, col4 = st.columns(4)

    total_patients = len(df)
    prophylaxis_rate = (df["Prophylaxis_Given"] == "Yes").mean() * 100
    vte_events = (df["VTE_Event"] == "Yes").sum()
    vte_rate = (df["VTE_Event"] == "Yes").mean() * 100

    with col1:
        st.metric(
            label="Total Patients",
            value=f"{total_patients:,}",
        )

    with col2:
        delta = prophylaxis_rate - 85  # Compare to goal
        st.metric(
            label="Prophylaxis Rate",
            value=f"{prophylaxis_rate:.1f}%",
            delta=f"{delta:+.1f}% vs goal",
            delta_color="normal" if delta >= 0 else "inverse",
        )

    with col3:
        st.metric(
            label="VTE Events",
            value=vte_events,
        )

    with col4:
        st.metric(
            label="VTE Event Rate",
            value=f"{vte_rate:.1f}%",
            delta=f"{-vte_rate:.1f}% target: 0%",
            delta_color="inverse",
        )


def render_department_performance(df: pd.DataFrame):
    """Render performance by department chart."""
    st.subheader("Performance by Department")

    # Calculate metrics by department
    dept_metrics = df.groupby("Department").agg({
        "Prophylaxis_Given": lambda x: (x == "Yes").mean() * 100,
        "VTE_Event": lambda x: (x == "Yes").mean() * 100,
        "Patient_ID": "count",
    }).round(1)
    dept_metrics.columns = ["Prophylaxis_Rate", "VTE_Rate", "Patient_Count"]
    dept_metrics = dept_metrics.reset_index()

    # Sort by prophylaxis rate
    dept_metrics = dept_metrics.sort_values("Prophylaxis_Rate", ascending=True)

    # Create bar chart with goal line
    fig = go.Figure()

    # Add bars
    colors = ["green" if x >= 85 else "red" for x in dept_metrics["Prophylaxis_Rate"]]
    fig.add_trace(go.Bar(
        x=dept_metrics["Prophylaxis_Rate"],
        y=dept_metrics["Department"],
        orientation="h",
        marker_color=colors,
        text=[f"{x:.1f}%" for x in dept_metrics["Prophylaxis_Rate"]],
        textposition="outside",
    ))

    # Add goal line
    fig.add_vline(x=85, line_dash="dash", line_color="black",
                  annotation_text="85% Goal", annotation_position="top")

    fig.update_layout(
        title="VTE Prophylaxis Rate by Department",
        xaxis_title="Prophylaxis Rate (%)",
        yaxis_title="Department",
        xaxis_range=[0, 100],
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)

    # Show data table
    with st.expander("View Department Data"):
        st.dataframe(dept_metrics, use_container_width=True, hide_index=True)


def render_trend_analysis(df: pd.DataFrame):
    """Render trend analysis over time."""
    st.subheader("Trend Analysis")

    # Group by month
    df["Month"] = df["Admission_Date"].dt.to_period("M").astype(str)

    monthly_metrics = df.groupby("Month").agg({
        "Prophylaxis_Given": lambda x: (x == "Yes").mean() * 100,
        "VTE_Event": lambda x: (x == "Yes").mean() * 100,
        "Patient_ID": "count",
    }).round(1)
    monthly_metrics.columns = ["Prophylaxis_Rate", "VTE_Rate", "Patient_Count"]
    monthly_metrics = monthly_metrics.reset_index()

    # Create dual-axis chart
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=monthly_metrics["Month"],
        y=monthly_metrics["Prophylaxis_Rate"],
        name="Prophylaxis Rate",
        line=dict(color="blue", width=3),
        mode="lines+markers",
    ))

    fig.add_trace(go.Scatter(
        x=monthly_metrics["Month"],
        y=monthly_metrics["VTE_Rate"],
        name="VTE Event Rate",
        line=dict(color="red", width=3),
        mode="lines+markers",
        yaxis="y2",
    ))

    # Add goal line
    fig.add_hline(y=85, line_dash="dash", line_color="green",
                  annotation_text="85% Goal")

    fig.update_layout(
        title="Monthly VTE Metrics Trend",
        xaxis_title="Month",
        yaxis_title="Prophylaxis Rate (%)",
        yaxis2=dict(
            title="VTE Event Rate (%)",
            overlaying="y",
            side="right",
        ),
        height=400,
        legend=dict(x=0.01, y=0.99),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_improvement_opportunities(df: pd.DataFrame):
    """Render improvement opportunities section."""
    st.subheader("Improvement Opportunities")

    # Identify departments below goal
    dept_rates = df.groupby("Department").apply(
        lambda x: (x["Prophylaxis_Given"] == "Yes").mean() * 100
    ).round(1)

    below_goal = dept_rates[dept_rates < 85].sort_values()

    if len(below_goal) > 0:
        st.warning(f"**{len(below_goal)} departments** are below the 85% goal")

        for dept, rate in below_goal.items():
            gap = 85 - rate
            patients_needed = int((gap / 100) * len(df[df["Department"] == dept]))

            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{dept}**")
            with col2:
                st.write(f"Current: {rate:.1f}%")
            with col3:
                st.write(f"Gap: {gap:.1f}% (~{patients_needed} patients)")
    else:
        st.success("All departments are meeting or exceeding the 85% goal!")

    # Risk stratification
    st.divider()
    st.subheader("Risk Stratification")

    risk_metrics = df.groupby("VTE_Risk_Score").agg({
        "Prophylaxis_Given": lambda x: (x == "Yes").mean() * 100,
        "VTE_Event": lambda x: (x == "Yes").mean() * 100,
        "Patient_ID": "count",
    }).round(1)
    risk_metrics.columns = ["Prophylaxis_Rate", "VTE_Rate", "Count"]

    # Reorder risk levels
    risk_order = ["Low", "Moderate", "High"]
    risk_metrics = risk_metrics.reindex([r for r in risk_order if r in risk_metrics.index])

    fig = px.bar(
        risk_metrics.reset_index(),
        x="VTE_Risk_Score",
        y="Prophylaxis_Rate",
        color="VTE_Risk_Score",
        color_discrete_map={"Low": "green", "Moderate": "orange", "High": "red"},
        text="Prophylaxis_Rate",
        title="Prophylaxis Rate by Risk Level",
    )
    fig.add_hline(y=85, line_dash="dash", line_color="black")
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(showlegend=False)

    st.plotly_chart(fig, use_container_width=True)


def render_physician_performance(df: pd.DataFrame):
    """Render physician performance table."""
    st.subheader("Physician Performance")

    physician_metrics = df.groupby("Attending_Physician").agg({
        "Prophylaxis_Given": lambda x: (x == "Yes").mean() * 100,
        "VTE_Event": lambda x: (x == "Yes").mean() * 100,
        "Patient_ID": "count",
    }).round(1)
    physician_metrics.columns = ["Prophylaxis_Rate", "VTE_Rate", "Patient_Count"]
    physician_metrics = physician_metrics.reset_index()
    physician_metrics = physician_metrics.sort_values("Prophylaxis_Rate", ascending=False)

    # Add status column
    physician_metrics["Status"] = physician_metrics["Prophylaxis_Rate"].apply(
        lambda x: "Meeting Goal" if x >= 85 else "Below Goal"
    )

    st.dataframe(
        physician_metrics,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Prophylaxis_Rate": st.column_config.ProgressColumn(
                "Prophylaxis Rate",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
        },
    )
