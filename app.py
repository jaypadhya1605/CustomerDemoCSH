"""
Conversational Analytics - Clinical Quality Demo
CommonSpirit Health | Powered by Azure AI Foundry

A Streamlit application for VTE Incentive goal analytics for quality leaders.
Features:
- Conversational AI interface using Azure OpenAI
- Real-time cost tracking (two-track model)
- VTE clinical quality metrics dashboard
- Azure service cost transparency
"""
import streamlit as st
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from services.azure_openai import AzureOpenAIService
from services.cost_calculator import CostCalculator
from components.chat import (
    render_chat_interface,
    render_chat_sidebar,
    initialize_chat_state,
    render_suggested_questions,
)
from components.cost_tracker import (
    render_cost_receipt,
    render_cost_tracker,
    render_cost_timeline,
    render_cost_sidebar,
    render_two_track_explanation,
)
from components.dashboard import (
    load_vte_data,
    get_vte_context,
    render_vte_dashboard,
    render_physician_performance,
)
from config.settings import validate_config, load_pricing


# Page configuration
st.set_page_config(
    page_title="CommonSpirit Health | Conversational Analytics",
    page_icon="💜",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CommonSpirit Health Brand CSS
COMMONSPIRIT_CSS = """
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap');
    
    /* CommonSpirit Brand Colors */
    :root {
        --csh-pink: #BE2BBB;
        --csh-teal: #00856A;
        --csh-dark-teal: #006B56;
        --csh-light-gray: #F5F5F7;
        --csh-dark-gray: #2D2D2D;
        --csh-white: #FFFFFF;
    }
    
    /* Global Styles */
    .stApp {
        font-family: 'Open Sans', sans-serif;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, var(--csh-pink) 0%, #9B1F9B 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(190, 43, 187, 0.2);
    }
    
    .main-header h1 {
        color: white !important;
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
    }
    
    .main-header p {
        color: rgba(255,255,255,0.9);
        margin: 0.5rem 0 0 0;
        font-size: 1rem;
    }
    
    /* Brand logo area */
    .brand-logo {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 1rem;
    }
    
    .brand-logo img {
        height: 40px;
    }
    
    /* Stat cards with teal accent */
    .stat-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 4px solid var(--csh-teal);
        text-align: center;
    }
    
    .stat-card h3 {
        color: var(--csh-teal) !important;
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
    }
    
    .stat-card p {
        color: var(--csh-dark-gray);
        margin: 0.5rem 0 0 0;
        font-size: 0.9rem;
    }
    
    /* Metric styling override */
    [data-testid="stMetricValue"] {
        color: var(--csh-teal) !important;
        font-weight: 700;
    }
    
    [data-testid="stMetricLabel"] {
        color: var(--csh-dark-gray) !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: var(--csh-light-gray);
        border-right: 1px solid #E0E0E0;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1 {
        color: var(--csh-pink) !important;
    }
    
    /* Chat message styling */
    .stChatMessage {
        border-radius: 12px;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: var(--csh-pink);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background-color: #9B1F9B;
        box-shadow: 0 4px 12px rgba(190, 43, 187, 0.3);
    }
    
    /* Secondary button */
    .stButton > button[kind="secondary"] {
        background-color: var(--csh-teal);
    }
    
    .stButton > button[kind="secondary"]:hover {
        background-color: var(--csh-dark-teal);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        color: var(--csh-dark-gray);
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--csh-pink) !important;
        color: white !important;
    }
    
    /* Info boxes */
    .info-box {
        background: linear-gradient(135deg, #E8F5F2 0%, #F0FAF8 100%);
        border-left: 4px solid var(--csh-teal);
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }
    
    /* Cost receipt styling */
    .cost-receipt {
        background: white;
        border: 1px solid #E0E0E0;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .cost-receipt-header {
        background: var(--csh-teal);
        color: white;
        margin: -1.5rem -1.5rem 1rem -1.5rem;
        padding: 1rem 1.5rem;
        border-radius: 12px 12px 0 0;
        font-weight: 600;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem;
        color: var(--csh-dark-gray);
        border-top: 1px solid #E0E0E0;
        margin-top: 2rem;
    }
    
    .footer a {
        color: var(--csh-pink);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: var(--csh-light-gray);
        border-radius: 8px;
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background-color: var(--csh-teal);
    }
    
    /* Selectbox styling */
    [data-baseweb="select"] {
        border-radius: 8px;
    }
    
    /* Azure Cost Card */
    .azure-cost-card {
        background: linear-gradient(135deg, #0078D4 0%, #005A9E 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
</style>
"""

# Inject CSS
st.markdown(COMMONSPIRIT_CSS, unsafe_allow_html=True)


def initialize_services():
    """Initialize Azure OpenAI and cost calculator services."""
    if "openai_service" not in st.session_state:
        try:
            st.session_state.openai_service = AzureOpenAIService()
        except ValueError as e:
            st.session_state.openai_service = None
            st.session_state.service_error = str(e)

    if "cost_calculator" not in st.session_state:
        st.session_state.cost_calculator = CostCalculator()

    if "vte_data" not in st.session_state:
        st.session_state.vte_data = load_vte_data()

    if "vte_context" not in st.session_state:
        st.session_state.vte_context = get_vte_context(st.session_state.vte_data)


def render_header():
    """Render the app header with CommonSpirit branding."""
    st.markdown("""
        <div class="main-header">
            <h1>💜 CommonSpirit Health</h1>
            <p>Conversational Analytics | Clinical Quality Dashboard</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Subtitle with Azure branding
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.caption("🏥 VTE Incentive Goal Analytics for Quality Leaders")
    with col2:
        st.caption("☁️ Powered by Azure AI Foundry")
    with col3:
        st.caption("📊 Real-time Cost Tracking")


def render_sidebar():
    """Render the sidebar with controls and CommonSpirit branding."""
    # CommonSpirit logo/brand area
    st.sidebar.markdown("""
        <div style="text-align: center; padding: 1rem 0; border-bottom: 2px solid #BE2BBB; margin-bottom: 1rem;">
            <h2 style="color: #BE2BBB; margin: 0;">💜 CommonSpirit</h2>
            <p style="color: #00856A; margin: 0.5rem 0 0 0; font-size: 0.85rem; font-weight: 600;">One Care System</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.title("Navigation")

    # Page selection
    page = st.sidebar.radio(
        "Select View",
        ["Chat & Analytics", "VTE Dashboard", "Cost Tracking", "Azure Services", "Settings"],
        key="page_selection",
    )

    st.sidebar.divider()

    # Cost summary (always visible)
    if "cost_calculator" in st.session_state:
        render_cost_sidebar(st.session_state.cost_calculator)

    st.sidebar.divider()

    # Chat controls
    if page == "Chat & Analytics":
        render_chat_sidebar()

    st.sidebar.divider()

    # Pricing info
    with st.sidebar.expander("Pricing Information"):
        pricing = load_pricing()
        st.caption("Model Pricing (per 1K tokens)")
        for model, rates in pricing.get("models", {}).items():
            st.write(f"**{model}**")
            st.caption(f"  Input: ${rates.get('input_per_1k_tokens', 0):.5f}")
            st.caption(f"  Output: ${rates.get('output_per_1k_tokens', 0):.5f}")

    return page


def render_chat_analytics_page():
    """Render the main chat and analytics page."""
    # Check service status
    if st.session_state.get("openai_service") is None:
        st.error(f"Azure OpenAI service not configured: {st.session_state.get('service_error', 'Unknown error')}")
        st.info("Please check your .env file and ensure AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY are set.")
        return

    # Layout: Chat on left, cost receipt on right
    col1, col2 = st.columns([2, 1])

    with col1:
        # Suggested questions
        suggested = render_suggested_questions()

        # Chat interface
        cost_breakdown = render_chat_interface(
            openai_service=st.session_state.openai_service,
            vte_context=st.session_state.vte_context,
        )

    with col2:
        st.subheader("Cost Receipt")
        render_cost_receipt(cost_breakdown)

        # Two-track explanation
        render_two_track_explanation()


def render_vte_dashboard_page():
    """Render the VTE dashboard page."""
    render_vte_dashboard(st.session_state.vte_data)

    st.divider()

    # Physician performance
    render_physician_performance(st.session_state.vte_data)


def render_cost_tracking_page():
    """Render the cost tracking page."""
    render_cost_tracker(st.session_state.cost_calculator)

    st.divider()

    # Cost timeline
    st.subheader("Cost Timeline")
    render_cost_timeline(st.session_state.cost_calculator)

    # Two-track explanation
    render_two_track_explanation()


def render_azure_services_page():
    """Render the Azure Services page with architecture overview and cost estimates."""
    st.subheader("☁️ Azure Services Architecture")
    
    st.markdown("""
    <div class="info-box">
        <strong>Architecture Overview</strong><br>
        This solution leverages Microsoft Azure AI Foundry and related services to deliver 
        conversational analytics for clinical quality improvement.
    </div>
    """, unsafe_allow_html=True)
    
    # Architecture diagram reference
    with st.expander("🏗️ Reference Architecture", expanded=True):
        st.markdown("""
        **Based on:** [Microsoft Foundry Baseline Landing Zone](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/architecture/baseline-microsoft-foundry-landing-zone)
        
        This demo implements a simplified version suitable for proof-of-concept demonstrations:
        
        | Component | Azure Service | Purpose |
        |-----------|--------------|---------|
        | AI Chat | Azure OpenAI (Foundry) | Conversational AI for VTE analytics |
        | Web Hosting | Azure App Service | Host Streamlit application |
        | Monitoring | Azure Log Analytics | Agent tracing & evaluation |
        | Automation | Azure Functions | Workflow automation triggers |
        | Storage | Azure Blob Storage | VTE data storage |
        | CI/CD | GitHub Actions | Automated deployment pipeline |
        """)
    
    st.divider()
    
    # Cost Estimates Section
    st.subheader("💰 Monthly Cost Estimates")
    
    pricing = load_pricing()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Azure AI & Compute Services")
        
        # Estimated usage metrics
        estimated_monthly_requests = st.slider("Estimated Monthly Chat Requests", 100, 10000, 1000, 100)
        avg_tokens_per_request = 2000  # Average input + output
        
        # Calculate AI costs
        model_rates = pricing.get("models", {}).get("gpt-5-mini", {})
        input_rate = model_rates.get("input_per_1k_tokens", 0.00015)
        output_rate = model_rates.get("output_per_1k_tokens", 0.0006)
        avg_cost_per_request = (avg_tokens_per_request / 2 / 1000 * input_rate) + (avg_tokens_per_request / 2 / 1000 * output_rate)
        monthly_ai_cost = avg_cost_per_request * estimated_monthly_requests
        
        azure_services = pricing.get("azure_services", {})
        
        # App Service cost
        app_service_rate = azure_services.get("app_service", {}).get("basic_b1_per_hour", 0.018)
        monthly_app_service = app_service_rate * 24 * 30
        
        st.metric("Azure OpenAI (GPT-5-mini)", f"${monthly_ai_cost:.2f}/mo", 
                  help=f"Based on {estimated_monthly_requests:,} requests/month")
        st.metric("App Service (Basic B1)", f"${monthly_app_service:.2f}/mo",
                  help="24/7 web app hosting")
        
    with col2:
        st.markdown("### Supporting Services")
        
        # Storage
        storage_gb = st.slider("Storage (GB)", 1, 100, 5)
        storage_rate = azure_services.get("storage", {}).get("blob_storage_per_gb", 0.018)
        monthly_storage = storage_gb * storage_rate
        
        # Log Analytics
        log_gb = st.slider("Log Analytics Ingestion (GB/mo)", 1, 50, 5)
        log_rate = azure_services.get("log_analytics", {}).get("ingestion_per_gb", 2.76)
        monthly_logs = log_gb * log_rate
        
        # Azure Functions
        function_executions = estimated_monthly_requests  # Assume 1 function call per request
        function_rate = azure_services.get("functions", {}).get("per_million_executions", 0.20)
        monthly_functions = (function_executions / 1_000_000) * function_rate
        
        st.metric("Blob Storage", f"${monthly_storage:.2f}/mo",
                  help=f"{storage_gb} GB of hot storage")
        st.metric("Log Analytics", f"${monthly_logs:.2f}/mo",
                  help=f"{log_gb} GB data ingestion")
        st.metric("Azure Functions", f"${monthly_functions:.4f}/mo",
                  help=f"{function_executions:,} executions (mostly free tier)")
    
    st.divider()
    
    # Total cost summary
    total_monthly = monthly_ai_cost + monthly_app_service + monthly_storage + monthly_logs + monthly_functions
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #00856A 0%, #006B56 100%); 
                color: white; padding: 1.5rem; border-radius: 12px; text-align: center;">
        <h2 style="margin: 0; color: white;">Estimated Monthly Total: ${total_monthly:.2f}</h2>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Based on selected usage parameters</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.caption("⚠️ These are demo estimates. Actual costs may vary based on region, usage patterns, and enterprise agreements. Check the [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/) for accurate pricing.")
    
    st.divider()
    
    # Azure Functions Workflow Section
    st.subheader("⚡ Azure Functions Workflows")
    
    with st.expander("Automated Workflow Triggers", expanded=True):
        st.markdown("""
        The following Azure Functions automate key workflows in this solution:
        
        | Function | Trigger | Purpose | Est. Cost |
        |----------|---------|---------|-----------|
        | `vte-data-refresh` | Timer (Daily) | Refresh VTE data from source | ~$0.001/run |
        | `alert-threshold-check` | Timer (Hourly) | Check VTE metrics against goals | ~$0.001/run |
        | `cost-aggregator` | Timer (Daily) | Aggregate and report costs | ~$0.001/run |
        | `chat-analytics-logger` | HTTP | Log chat interactions for analysis | ~$0.0002/call |
        
        **Total Functions Cost:** Primarily covered by Azure Functions free grant (1M executions/month)
        """)
    
    st.divider()
    
    # Log Analytics & Monitoring
    st.subheader("📊 Agent Tracing & Evaluation")
    
    with st.expander("Azure Log Analytics Integration", expanded=True):
        st.markdown("""
        **Tracing Capabilities:**
        - 📝 Chat conversation logging with full context
        - ⏱️ Response latency tracking
        - 🎯 Token usage monitoring
        - 💰 Cost attribution per session
        - 🔍 Query performance analysis
        
        **Evaluation Metrics:**
        - Response quality scoring
        - Goal alignment tracking
        - User satisfaction indicators
        - Clinical accuracy validation
        
        **KQL Query Example:**
        ```kusto
        ChatAnalytics
        | where TimeGenerated > ago(24h)
        | summarize 
            TotalRequests = count(),
            AvgLatencyMs = avg(ResponseLatencyMs),
            TotalTokens = sum(TotalTokens),
            EstimatedCost = sum(EstimatedCost)
        | by bin(TimeGenerated, 1h)
        ```
        """)


def render_settings_page():
    """Render the settings page."""
    st.subheader("Configuration")

    # Validate configuration
    is_valid, message = validate_config()
    if is_valid:
        st.success(f"Configuration Status: {message}")
    else:
        st.error(f"Configuration Error: {message}")

    st.divider()

    # Model selection
    st.subheader("Model Settings")
    model_options = ["gpt-5-mini", "gpt-5.2", "gpt-realtime"]
    current_model = st.selectbox(
        "Active Model",
        model_options,
        index=0,
        help="Select the Azure OpenAI model to use for conversations",
    )

    st.divider()

    # Data info
    st.subheader("VTE Data Summary")
    df = st.session_state.vte_data
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Records", len(df))
    with col2:
        st.metric("Date Range", f"{df['Admission_Date'].min().strftime('%Y-%m-%d')} to {df['Admission_Date'].max().strftime('%Y-%m-%d')}")
    with col3:
        st.metric("Departments", df["Department"].nunique())

    if st.button("Reload VTE Data"):
        st.session_state.vte_data = load_vte_data()
        st.session_state.vte_context = get_vte_context(st.session_state.vte_data)
        st.success("VTE data reloaded!")
        st.rerun()

    st.divider()

    # Reset session
    st.subheader("Session Management")
    if st.button("Reset All Session Data", type="secondary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.success("Session reset!")
        st.rerun()


def render_footer():
    """Render the app footer with CommonSpirit branding."""
    st.markdown("""
    <div class="footer">
        <p><strong>💜 CommonSpirit Health</strong> | One Care System, Thousands of Caregivers</p>
        <p style="font-size: 0.85rem;">
            Powered by <a href="https://azure.microsoft.com/products/ai-services/openai-service" target="_blank">Azure AI Foundry</a> | 
            <a href="https://www.commonspirit.org" target="_blank">commonspirit.org</a>
        </p>
        <p style="font-size: 0.75rem; color: #888;">
            Demo Application | Estimated costs are for demonstration purposes only
        </p>
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main application entry point."""
    # Initialize services
    initialize_services()

    # Render header
    render_header()

    # Render sidebar and get selected page
    page = render_sidebar()

    # Render selected page
    if page == "Chat & Analytics":
        render_chat_analytics_page()
    elif page == "VTE Dashboard":
        render_vte_dashboard_page()
    elif page == "Cost Tracking":
        render_cost_tracking_page()
    elif page == "Azure Services":
        render_azure_services_page()
    elif page == "Settings":
        render_settings_page()
    
    # Render footer
    render_footer()


if __name__ == "__main__":
    main()
