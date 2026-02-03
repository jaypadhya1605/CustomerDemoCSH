"""
Configuration settings for Conversational Analytics - Clinical Quality Demo
"""
import os
from pathlib import Path
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
PRICING_PATH = BASE_DIR / "pricing" / "prices.yaml"
DATA_PATH = BASE_DIR / "data"

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini")

# Available models
AVAILABLE_MODELS = {
    "gpt-5-mini": {
        "endpoint": "https://mf-custdemo-convanalytics-clinical-jp-001.cognitiveservices.azure.com/",
        "deployment": "gpt-5-mini",
    },
    "gpt-5.2": {
        "endpoint": "https://foundry-prov-empathyai-poc-jp-001.cognitiveservices.azure.com/",
        "deployment": "gpt-5.2",
    },
    "gpt-realtime": {
        "endpoint": "https://foundry-prov-empathyai-poc-jp-001.cognitiveservices.azure.com/",
        "deployment": "gpt-realtime",
    },
}

def load_pricing():
    """Load pricing configuration from YAML file."""
    try:
        with open(PRICING_PATH, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {
            "models": {
                "gpt-5-mini": {"input_per_1k_tokens": 0.00015, "output_per_1k_tokens": 0.0006},
                "gpt-5.2": {"input_per_1k_tokens": 0.0025, "output_per_1k_tokens": 0.01},
                "gpt-realtime": {"input_per_1k_tokens": 0.06, "output_per_1k_tokens": 0.24},
            },
            "metadata": {"disclaimer": "Demo estimates - actual costs may vary"}
        }

def get_model_pricing(model_name: str) -> dict:
    """Get pricing for a specific model."""
    pricing = load_pricing()
    return pricing.get("models", {}).get(model_name, {
        "input_per_1k_tokens": 0.0,
        "output_per_1k_tokens": 0.0
    })

def validate_config() -> tuple[bool, str]:
    """Validate that all required configuration is present."""
    if not AZURE_OPENAI_ENDPOINT:
        return False, "AZURE_OPENAI_ENDPOINT is not set"
    if not AZURE_OPENAI_API_KEY:
        return False, "AZURE_OPENAI_API_KEY is not set"
    return True, "Configuration valid"

# VTE Analytics Configuration
VTE_GOAL_PERCENTAGE = 85.0  # Target VTE prophylaxis rate
VTE_DEPARTMENTS = [
    "Medical ICU",
    "Surgical ICU",
    "General Medicine",
    "Orthopedics",
    "Cardiology",
    "Oncology",
    "Neurology",
    "Emergency"
]
