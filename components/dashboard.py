"""
VTE Analytics Dashboard component for Streamlit app.
Displays clinical quality metrics, performance-to-goal, and improvement opportunities.
Integrates financial data for comprehensive analytics.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
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
    except PermissionError:
        st.warning("VTE data file is open in another application. Using generated sample data.")
        return generate_sample_vte_data()
    except Exception as e:
        st.warning(f"Error loading VTE data: {e}. Using generated sample data.")
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


def load_financial_data(data_path: Optional[Path] = None) -> Dict[str, pd.DataFrame]:
    """
    Load financial data from Excel file.
    
    Args:
        data_path: Path to the financial data file
        
    Returns:
        Dictionary with DataFrames for each sheet:
        - patient_costs: Per-patient financial data (linked via Patient_ID)
        - dept_budgets: Department budget information
        - azure_costs: Azure platform costs
        - roi_summary: VTE ROI summary
    """
    if data_path is None:
        data_path = Path(__file__).parent.parent / "data" / "vte_financial_data.xlsx"
    
    result = {
        "patient_costs": pd.DataFrame(),
        "dept_budgets": pd.DataFrame(),
        "azure_costs": pd.DataFrame(),
        "roi_summary": pd.DataFrame(),
    }
    
    try:
        xl = pd.ExcelFile(data_path)
        
        if "Patient_Costs" in xl.sheet_names:
            result["patient_costs"] = pd.read_excel(xl, "Patient_Costs")
        if "Department_Budgets" in xl.sheet_names:
            result["dept_budgets"] = pd.read_excel(xl, "Department_Budgets")
        if "Azure_Platform_Costs" in xl.sheet_names:
            result["azure_costs"] = pd.read_excel(xl, "Azure_Platform_Costs")
        if "VTE_ROI_Summary" in xl.sheet_names:
            result["roi_summary"] = pd.read_excel(xl, "VTE_ROI_Summary")
            
        return result
    except FileNotFoundError:
        st.warning("Financial data file not found. Using sample data.")
        return generate_sample_financial_data()
    except PermissionError:
        st.warning("Financial data file is open in another application. Using cached/sample data.")
        return generate_sample_financial_data()
    except Exception as e:
        st.warning(f"Error loading financial data: {e}")
        return generate_sample_financial_data()


def generate_sample_financial_data() -> Dict[str, pd.DataFrame]:
    """Generate sample financial data when file is unavailable."""
    random.seed(42)
    
    # Department budgets
    departments = [
        "Medical ICU", "Surgical ICU", "General Medicine",
        "Orthopedics", "Cardiology", "Oncology", "Neurology", "Emergency"
    ]
    
    dept_budgets = []
    for dept in departments:
        annual_budget = random.randint(4000000, 9500000)
        dept_budgets.append({
            "Department": dept,
            "Cost_Center_Code": f"CC-{dept[:3].upper()}-001",
            "Annual_Budget_USD": annual_budget,
            "Cost_Per_Bed_Day_USD": random.randint(950, 3500),
            "VTE_Prevention_Budget_USD": int(annual_budget * 0.03),
            "Quality_Incentive_Target_USD": int(annual_budget * 0.02),
            "Fiscal_Year": "FY2024",
        })
    
    # Sample patient costs (will be empty if we can't link to clinical data)
    patient_costs = []
    
    # Azure platform costs
    azure_costs = []
    for month in pd.date_range(start="2024-01-01", end="2024-06-30", freq="MS"):
        azure_costs.append({
            "Month": month.strftime("%Y-%m"),
            "Azure_OpenAI_Cost_USD": round(random.uniform(8, 15), 2),
            "App_Service_Cost_USD": round(random.uniform(12, 14), 2),
            "Log_Analytics_Cost_USD": round(random.uniform(10, 18), 2),
            "Storage_Cost_USD": round(random.uniform(0.05, 0.15), 2),
            "Functions_Cost_USD": round(random.uniform(0, 0.50), 2),
            "Total_Platform_Cost_USD": 0,
            "Chat_Requests": random.randint(500, 1500),
            "Tokens_Used": random.randint(800000, 2500000),
        })
    
    azure_df = pd.DataFrame(azure_costs)
    azure_df["Total_Platform_Cost_USD"] = (
        azure_df["Azure_OpenAI_Cost_USD"] + 
        azure_df["App_Service_Cost_USD"] + 
        azure_df["Log_Analytics_Cost_USD"] + 
        azure_df["Storage_Cost_USD"] + 
        azure_df["Functions_Cost_USD"]
    ).round(2)
    
    # ROI Summary
    roi_summary = pd.DataFrame([
        {"Metric": "VTE Events Prevented (Est.)", "Value": 12, "Unit": "Events", "Cost_Impact_USD": 420000},
        {"Metric": "Prophylaxis Program Cost", "Value": 45000, "Unit": "USD", "Cost_Impact_USD": -45000},
        {"Metric": "Net Savings", "Value": 375000, "Unit": "USD", "Cost_Impact_USD": 375000},
        {"Metric": "Quality Incentive Earned", "Value": 125000, "Unit": "USD", "Cost_Impact_USD": 125000},
        {"Metric": "Analytics Platform Cost", "Value": 240, "Unit": "USD", "Cost_Impact_USD": -240},
        {"Metric": "Total ROI", "Value": 499760, "Unit": "USD", "Cost_Impact_USD": 499760},
    ])
    
    return {
        "patient_costs": pd.DataFrame(patient_costs),
        "dept_budgets": pd.DataFrame(dept_budgets),
        "azure_costs": azure_df,
        "roi_summary": roi_summary,
    }


def load_combined_data(
    clinical_path: Optional[Path] = None,
    financial_path: Optional[Path] = None
) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """
    Load and combine clinical and financial data.
    
    Returns:
        Tuple of (clinical_df, financial_dict)
    """
    clinical_df = load_vte_data(clinical_path)
    financial_data = load_financial_data(financial_path)
    
    # Merge patient costs with clinical data if available
    if not financial_data["patient_costs"].empty and "Patient_ID" in financial_data["patient_costs"].columns:
        if "Patient_ID" in clinical_df.columns:
            # Create a combined view
            clinical_df = clinical_df.merge(
                financial_data["patient_costs"],
                on="Patient_ID",
                how="left",
                suffixes=("", "_financial")
            )
    
    return clinical_df, financial_data


def get_vte_context(df: pd.DataFrame, financial_data: Optional[Dict[str, pd.DataFrame]] = None) -> str:
    """
    Generate a text summary of VTE and financial data for AI context.

    Args:
        df: DataFrame with VTE data
        financial_data: Optional dictionary with financial DataFrames

    Returns:
        Text summary of the clinical and financial data
    """
    total_patients = len(df)
    prophylaxis_rate = (df["Prophylaxis_Given"] == "Yes").mean() * 100
    vte_event_rate = (df["VTE_Event"] == "Yes").mean() * 100

    dept_rates = df.groupby("Department").apply(
        lambda x: (x["Prophylaxis_Given"] == "Yes").mean() * 100
    ).round(1)

    below_goal = dept_rates[dept_rates < 85].to_dict()

    context = f"""
VTE Clinical Analytics Summary:
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

    # Add financial context if available
    if financial_data:
        # Patient costs summary
        if not financial_data.get("patient_costs", pd.DataFrame()).empty:
            pc = financial_data["patient_costs"]
            context += f"""
Financial Summary (Patient Costs):
- Total Patient Costs: ${pc['Total_Cost_USD'].sum():,.2f}
- Average Cost per Patient: ${pc['Total_Cost_USD'].mean():,.2f}
- Total VTE Treatment Costs: ${pc['VTE_Treatment_Cost_USD'].sum():,.2f}
- Average VTE Treatment Cost (when event occurred): ${pc[pc['VTE_Treatment_Cost_USD'] > 0]['VTE_Treatment_Cost_USD'].mean():,.2f}
- Total Prophylaxis Costs: ${pc['Prophylaxis_Cost_USD'].sum():,.2f}
"""
            # Cost by department
            dept_costs = pc.groupby("Department")["Total_Cost_USD"].sum().round(2)
            context += f"""
Cost by Department:
{dept_costs.to_string()}
"""

        # Department budgets
        if not financial_data.get("dept_budgets", pd.DataFrame()).empty:
            db = financial_data["dept_budgets"]
            context += f"""
Department Budget Information:
- Total Annual Budget: ${db['Annual_Budget_USD'].sum():,.2f}
- Total VTE Prevention Budget: ${db['VTE_Prevention_Budget_USD'].sum():,.2f}
- Total Quality Incentive Target: ${db['Quality_Incentive_Target_USD'].sum():,.2f}
"""

        # ROI Summary
        if not financial_data.get("roi_summary", pd.DataFrame()).empty:
            roi = financial_data["roi_summary"]
            context += f"""
VTE Prevention ROI Summary:
"""
            for _, row in roi.iterrows():
                context += f"- {row['Metric']}: {row['Value']} {row['Unit']} (Impact: ${row['Cost_Impact_USD']:,.2f})\n"

        # Azure platform costs
        if not financial_data.get("azure_costs", pd.DataFrame()).empty:
            az = financial_data["azure_costs"]
            context += f"""
Azure Analytics Platform Costs (6 months):
- Total Platform Cost: ${az['Total_Platform_Cost_USD'].sum():,.2f}
- Total Chat Requests: {az['Chat_Requests'].sum():,}
- Total Tokens Used: {az['Tokens_Used'].sum():,}
"""

    return context


def render_vte_dashboard(df: Optional[pd.DataFrame] = None, financial_data: Optional[Dict[str, pd.DataFrame]] = None):
    """
    Render the full VTE analytics dashboard.

    Args:
        df: Optional DataFrame with VTE data (loads from file if not provided)
        financial_data: Optional dictionary with financial DataFrames
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


def render_financial_dashboard(financial_data: Dict[str, pd.DataFrame], clinical_df: Optional[pd.DataFrame] = None):
    """
    Render the financial analytics dashboard.
    
    Args:
        financial_data: Dictionary with financial DataFrames
        clinical_df: Optional clinical DataFrame for cross-referencing
    """
    st.subheader("💰 Financial Analytics")
    
    # Check if we have financial data
    if all(df.empty for df in financial_data.values()):
        st.info("Financial data not available. Please ensure vte_financial_data.xlsx is present in the data folder.")
        return
    
    # Tabs for different financial views
    tab1, tab2, tab3, tab4 = st.tabs([
        "Patient Costs", "Department Budgets", "VTE ROI", "Platform Costs"
    ])
    
    with tab1:
        render_patient_cost_analysis(financial_data.get("patient_costs", pd.DataFrame()), clinical_df)
    
    with tab2:
        render_department_budget_analysis(financial_data.get("dept_budgets", pd.DataFrame()))
    
    with tab3:
        render_roi_summary(financial_data.get("roi_summary", pd.DataFrame()))
    
    with tab4:
        render_platform_costs(financial_data.get("azure_costs", pd.DataFrame()))


def render_patient_cost_analysis(patient_costs: pd.DataFrame, clinical_df: Optional[pd.DataFrame] = None):
    """Render patient cost analysis."""
    if patient_costs.empty:
        st.info("Patient cost data not available.")
        return
    
    st.subheader("Patient Cost Analysis")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Patient Costs",
            f"${patient_costs['Total_Cost_USD'].sum():,.0f}",
        )
    
    with col2:
        st.metric(
            "Average Cost/Patient",
            f"${patient_costs['Total_Cost_USD'].mean():,.0f}",
        )
    
    with col3:
        vte_costs = patient_costs['VTE_Treatment_Cost_USD'].sum()
        st.metric(
            "VTE Treatment Costs",
            f"${vte_costs:,.0f}",
            help="Total costs for treating VTE events"
        )
    
    with col4:
        prophylaxis_costs = patient_costs['Prophylaxis_Cost_USD'].sum()
        st.metric(
            "Prophylaxis Costs",
            f"${prophylaxis_costs:,.0f}",
            help="Total costs for VTE prevention"
        )
    
    st.divider()
    
    # Cost distribution by department
    if "Department" in patient_costs.columns:
        st.subheader("Cost by Department")
        
        dept_costs = patient_costs.groupby("Department").agg({
            "Total_Cost_USD": "sum",
            "VTE_Treatment_Cost_USD": "sum",
            "Patient_ID": "count"
        }).round(2)
        dept_costs.columns = ["Total Cost", "VTE Treatment Cost", "Patients"]
        dept_costs = dept_costs.reset_index()
        dept_costs["Avg Cost/Patient"] = (dept_costs["Total Cost"] / dept_costs["Patients"]).round(2)
        
        fig = px.bar(
            dept_costs,
            x="Department",
            y="Total Cost",
            color="VTE Treatment Cost",
            color_continuous_scale="Reds",
            title="Total Cost by Department (colored by VTE treatment costs)",
        )
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("View Department Cost Data"):
            st.dataframe(dept_costs, use_container_width=True, hide_index=True)
    
    # Cost category breakdown
    if "Cost_Category" in patient_costs.columns:
        st.subheader("Cost by Category")
        
        category_costs = patient_costs.groupby("Cost_Category")["Total_Cost_USD"].agg(["sum", "mean", "count"])
        category_costs.columns = ["Total", "Average", "Patients"]
        
        fig = px.pie(
            category_costs.reset_index(),
            values="Total",
            names="Cost_Category",
            title="Cost Distribution by Category",
            color_discrete_map={"Standard Care": "#00856A", "VTE Event": "#BE2BBB"}
        )
        st.plotly_chart(fig, use_container_width=True)


def render_department_budget_analysis(dept_budgets: pd.DataFrame):
    """Render department budget analysis."""
    if dept_budgets.empty:
        st.info("Department budget data not available.")
        return
    
    st.subheader("Department Budget Overview")
    
    # Key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total Annual Budget",
            f"${dept_budgets['Annual_Budget_USD'].sum():,.0f}",
        )
    
    with col2:
        st.metric(
            "VTE Prevention Budget",
            f"${dept_budgets['VTE_Prevention_Budget_USD'].sum():,.0f}",
        )
    
    with col3:
        st.metric(
            "Quality Incentive Target",
            f"${dept_budgets['Quality_Incentive_Target_USD'].sum():,.0f}",
        )
    
    st.divider()
    
    # Budget comparison chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name="Annual Budget",
        x=dept_budgets["Department"],
        y=dept_budgets["Annual_Budget_USD"],
        marker_color="#00856A"
    ))
    
    fig.add_trace(go.Bar(
        name="VTE Prevention Budget",
        x=dept_budgets["Department"],
        y=dept_budgets["VTE_Prevention_Budget_USD"],
        marker_color="#BE2BBB"
    ))
    
    fig.update_layout(
        title="Department Budgets Comparison",
        barmode="group",
        xaxis_title="Department",
        yaxis_title="Budget (USD)",
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Full data table
    with st.expander("View Full Budget Data"):
        st.dataframe(dept_budgets, use_container_width=True, hide_index=True)


def render_roi_summary(roi_summary: pd.DataFrame):
    """Render VTE Prevention ROI summary."""
    if roi_summary.empty:
        st.info("ROI summary data not available.")
        return
    
    st.subheader("VTE Prevention Return on Investment")
    
    # Find key metrics
    total_roi = roi_summary[roi_summary["Metric"] == "Total ROI"]["Cost_Impact_USD"].values
    if len(total_roi) > 0:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #00856A 0%, #006B56 100%); 
                    color: white; padding: 1.5rem; border-radius: 12px; text-align: center; margin-bottom: 1rem;">
            <h2 style="margin: 0; color: white;">Estimated Annual ROI: ${total_roi[0]:,.0f}</h2>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Through VTE prevention and quality incentives</p>
        </div>
        """, unsafe_allow_html=True)
    
    # ROI breakdown
    st.subheader("ROI Breakdown")
    
    for _, row in roi_summary.iterrows():
        impact = row['Cost_Impact_USD']
        color = "green" if impact > 0 else "red"
        sign = "+" if impact > 0 else ""
        
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"**{row['Metric']}**")
        with col2:
            st.write(f"{row['Value']:,} {row['Unit']}")
        with col3:
            st.markdown(f"<span style='color: {color};'>{sign}${impact:,.0f}</span>", unsafe_allow_html=True)
    
    # Waterfall chart
    fig = go.Figure(go.Waterfall(
        name="ROI",
        orientation="v",
        x=roi_summary["Metric"],
        y=roi_summary["Cost_Impact_USD"],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        increasing={"marker": {"color": "#00856A"}},
        decreasing={"marker": {"color": "#BE2BBB"}},
        totals={"marker": {"color": "#0078D4"}}
    ))
    
    fig.update_layout(
        title="ROI Waterfall Analysis",
        showlegend=False,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_platform_costs(azure_costs: pd.DataFrame):
    """Render Azure platform costs."""
    if azure_costs.empty:
        st.info("Platform cost data not available.")
        return
    
    st.subheader("Azure Analytics Platform Costs")
    
    # Key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total Platform Cost (6mo)",
            f"${azure_costs['Total_Platform_Cost_USD'].sum():,.2f}",
        )
    
    with col2:
        st.metric(
            "Total Chat Requests",
            f"{azure_costs['Chat_Requests'].sum():,}",
        )
    
    with col3:
        st.metric(
            "Total Tokens Used",
            f"{azure_costs['Tokens_Used'].sum():,}",
        )
    
    st.divider()
    
    # Monthly trend
    st.subheader("Monthly Cost Trend")
    
    fig = go.Figure()
    
    for col in ["Azure_OpenAI_Cost_USD", "App_Service_Cost_USD", "Log_Analytics_Cost_USD"]:
        fig.add_trace(go.Bar(
            name=col.replace("_USD", "").replace("_", " "),
            x=azure_costs["Month"],
            y=azure_costs[col],
        ))
    
    fig.update_layout(
        barmode="stack",
        title="Monthly Azure Costs Breakdown",
        xaxis_title="Month",
        yaxis_title="Cost (USD)",
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Usage metrics
    st.subheader("Usage Metrics")
    
    fig2 = go.Figure()
    
    fig2.add_trace(go.Scatter(
        x=azure_costs["Month"],
        y=azure_costs["Chat_Requests"],
        name="Chat Requests",
        mode="lines+markers",
        line=dict(color="#BE2BBB", width=3),
    ))
    
    fig2.add_trace(go.Scatter(
        x=azure_costs["Month"],
        y=azure_costs["Tokens_Used"] / 10000,  # Scale for visibility
        name="Tokens Used (10K)",
        mode="lines+markers",
        line=dict(color="#00856A", width=3),
        yaxis="y2"
    ))
    
    fig2.update_layout(
        title="Platform Usage Over Time",
        xaxis_title="Month",
        yaxis_title="Chat Requests",
        yaxis2=dict(title="Tokens Used (10K)", overlaying="y", side="right"),
    )
    
    st.plotly_chart(fig2, use_container_width=True)
    
    # Full data
    with st.expander("View Full Platform Cost Data"):
        st.dataframe(azure_costs, use_container_width=True, hide_index=True)
