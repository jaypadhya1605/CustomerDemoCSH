# 💜 CommonSpirit Health - Conversational Analytics
## Clinical Quality Demo | Powered by Azure AI Foundry

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![Azure](https://img.shields.io/badge/Azure-AI%20Foundry-0078D4.svg)](https://azure.microsoft.com/)

---

## 📋 Overview

This application provides **Conversational Analytics** for **VTE (Venous Thromboembolism) Incentive Goal Analytics** designed for healthcare quality leaders at CommonSpirit Health.

### Key Features

| Feature | Description |
|---------|-------------|
| 🤖 **AI Chat Interface** | Natural language queries about VTE performance metrics |
| 📊 **Interactive Dashboard** | Visual analytics for clinical quality tracking |
| 💰 **Real-time Cost Tracking** | Two-track cost model (estimated & actual) |
| ⚡ **Automated Workflows** | Azure Functions for data refresh & alerts |
| 📈 **Agent Tracing** | Log Analytics integration for monitoring |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CommonSpirit Analytics                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  Streamlit   │───▶│ Azure OpenAI │───▶│ GPT-5-mini   │      │
│  │  Web App     │    │  (Foundry)   │    │              │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ App Service  │───▶│    Azure     │───▶│     Log      │      │
│  │   (Linux)    │    │  Functions   │    │  Analytics   │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                    │                   │               │
│         └────────────────────┴───────────────────┘               │
│                              │                                   │
│                    ┌─────────▼─────────┐                        │
│                    │   Blob Storage    │                        │
│                    │   (VTE Data)      │                        │
│                    └───────────────────┘                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Reference Architecture

Based on Microsoft's [Baseline Foundry Landing Zone](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/architecture/baseline-microsoft-foundry-landing-zone) architecture, simplified for POC demonstration.

---

## 💰 Cost Estimates

### Monthly Cost Summary (Demo Workload)

| Service | Configuration | Est. Monthly Cost |
|---------|--------------|-------------------|
| Azure OpenAI (GPT-5-mini) | ~1,000 requests/month | $0.75 - $10.00 |
| App Service | Basic B1 (Linux) | $13.14 |
| Azure Functions | Consumption (free tier) | $0.00 |
| Blob Storage | 5 GB Hot | $0.09 |
| Log Analytics | 5 GB ingestion | $13.80 |
| Application Insights | 1 GB | $2.30 |
| **Total Estimate** | | **~$30 - $40/month** |

> ⚠️ These are demo estimates. Actual costs vary by region, usage, and enterprise agreements.

---

## 🚀 Deployment Guide

### Prerequisites

- Azure subscription with Contributor access
- Azure CLI installed (`az --version`)
- GitHub account (for CI/CD)
- Python 3.11+

### Option 1: Quick Deploy (Azure Portal)

1. Click the "Deploy to Azure" button above
2. Fill in the required parameters
3. Review and create

### Option 2: Azure CLI Deployment

```bash
# Login to Azure
az login

# Set subscription
az account set --subscription "MCAPS-DataAICSA2023-jaypadhya-DEMO"

# Create resource group (if needed)
az group create \
  --name rg-customerDemo-conversationAnalytics-clinical-jp-001 \
  --location eastus2

# Deploy infrastructure
az deployment group create \
  --resource-group rg-customerDemo-conversationAnalytics-clinical-jp-001 \
  --template-file infra/main.bicep \
  --parameters \
    location=eastus2 \
    environmentName=csh-convanalytics \
    appServicePlanSku=B1 \
    azureOpenAiEndpoint="https://mf-custdemo-convanalytics-clinical-jp-001.cognitiveservices.azure.com/" \
    azureOpenAiApiKey="YOUR_API_KEY" \
    azureOpenAiDeployment=gpt-5-mini
```

### Option 3: GitHub Actions CI/CD

1. Fork this repository
2. Configure GitHub Secrets:
   ```
   AZURE_CREDENTIALS        # Service principal JSON
   AZURE_SUBSCRIPTION_ID    # Subscription ID
   AZURE_RESOURCE_GROUP     # Resource group name
   AZURE_OPENAI_ENDPOINT    # OpenAI endpoint URL
   AZURE_OPENAI_API_KEY     # OpenAI API key
   ```
3. Push to `main` branch to trigger deployment

---

## 🛠️ Local Development

### Setup

```bash
# Clone repository
git clone https://github.com/jaypadhya1605/CustomerDemoCSH.git
cd CustomerDemoCSH

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp infra/.env.template .env
# Edit .env with your credentials
```

### Run Locally

```bash
# Start Streamlit app
streamlit run app.py

# Access at http://localhost:8501
```

### Test Azure Functions Locally

```bash
cd functions

# Install Azure Functions Core Tools
npm install -g azure-functions-core-tools@4 --unsafe-perm true

# Start functions
func start
```

---

## 📊 Azure Functions Workflows

| Function | Trigger | Schedule | Purpose |
|----------|---------|----------|---------|
| `vte_data_refresh` | Timer | Daily 6 AM UTC | Refresh VTE data |
| `alert_threshold_check` | Timer | Hourly | Check VTE goals |
| `cost_aggregator` | Timer | Daily midnight | Aggregate costs |
| `chat_analytics_logger` | HTTP | On-demand | Log chat interactions |
| `weekly_report_generator` | Timer | Monday 8 AM | Generate reports |

---

## 📈 Log Analytics Queries

### Example KQL Queries

**Daily Usage Summary:**
```kusto
ChatAnalytics_CL
| where TimeGenerated > ago(24h)
| summarize 
    TotalRequests = count(),
    AvgLatencyMs = avg(latency_ms_d),
    TotalTokens = sum(total_tokens_d),
    TotalCost = sum(estimated_cost_d)
| by bin(TimeGenerated, 1h)
```

**Query Type Distribution:**
```kusto
ChatAnalytics_CL
| where TimeGenerated > ago(7d)
| summarize Count = count() by query_type_s
| render piechart
```

---

## 🎨 CommonSpirit Branding

The application uses CommonSpirit Health's brand colors:

| Element | Color | Hex Code |
|---------|-------|----------|
| Primary (Pink/Magenta) | 💜 | `#BE2BBB` |
| Accent (Teal) | 💚 | `#00856A` |
| Background | ⬜ | `#FFFFFF` |
| Text | ⬛ | `#2D2D2D` |

---

## 📁 Project Structure

```
poc-demo-2/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── .streamlit/
│   └── config.toml          # Streamlit configuration
├── components/
│   ├── chat.py              # Chat interface component
│   ├── dashboard.py         # VTE dashboard component
│   └── cost_tracker.py      # Cost tracking component
├── services/
│   ├── azure_openai.py      # Azure OpenAI service
│   ├── cost_calculator.py   # Cost calculation service
│   └── log_analytics.py     # Log Analytics integration
├── config/
│   └── settings.py          # Application settings
├── pricing/
│   └── prices.yaml          # Azure pricing configuration
├── functions/
│   ├── function_app.py      # Azure Functions (Python v2)
│   ├── host.json            # Functions host configuration
│   └── requirements.txt     # Functions dependencies
├── infra/
│   ├── main.bicep           # Azure infrastructure
│   ├── main.parameters.json # Deployment parameters
│   └── .env.template        # Environment template
├── .github/
│   └── workflows/
│       └── azure-deploy.yml # CI/CD pipeline
└── data/
    └── vte_sample_data.xlsx # Sample VTE data
```

---

## 🔒 Security Considerations

- ✅ HTTPS-only communication
- ✅ Azure AD authentication ready
- ✅ API keys stored in environment variables
- ✅ Private endpoints supported
- ✅ Diagnostic logging enabled
- ✅ TLS 1.2 minimum

---

## 📞 Support

For questions about this demo:
- **Project Lead:** Jay Padhya
- **Repository:** [github.com/jaypadhya1605/CustomerDemoCSH](https://github.com/jaypadhya1605/CustomerDemoCSH)

---

## 📄 License

This is a demonstration project for CommonSpirit Health. All rights reserved.

---

<div align="center">

**💜 CommonSpirit Health | One Care System, Thousands of Caregivers**

*Powered by Azure AI Foundry*

</div>
