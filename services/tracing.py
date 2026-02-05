"""
Azure Application Insights Tracing Service for Conversational Analytics.
Implements OpenTelemetry tracing for Azure AI Foundry monitoring integration.

Based on: https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/trace-application
"""
import os
from typing import Optional, Dict, Any
import json
from datetime import datetime

# CRITICAL: Set environment variable BEFORE any instrumentation
# This enables capturing message content (inputs/outputs) in traces
os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = "true"

# Flag to track if tracing is available
TRACING_AVAILABLE = False
_tracing_initialized = False

# Try to import tracing packages
try:
    from azure.monitor.opentelemetry import configure_azure_monitor
    from opentelemetry.instrumentation.openai_v2 import OpenAIInstrumentor
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    TRACING_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Azure Monitor OpenTelemetry packages not installed. Tracing disabled. Error: {e}")
    configure_azure_monitor = None
    OpenAIInstrumentor = None
    trace = None


def initialize_tracing(connection_string: Optional[str] = None) -> bool:
    """
    Initialize OpenTelemetry tracing with Azure Monitor.
    
    IMPORTANT: This must be called BEFORE creating any OpenAI clients!
    
    Args:
        connection_string: Application Insights connection string.
                          If not provided, reads from APPLICATIONINSIGHTS_CONNECTION_STRING env var.
    
    Returns:
        True if tracing was configured successfully, False otherwise.
    """
    global _tracing_initialized
    
    if _tracing_initialized:
        print("ℹ️ Tracing already initialized")
        return True
    
    if not TRACING_AVAILABLE:
        print("⚠️ Tracing packages not available")
        return False
    
    conn_str = connection_string or os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    
    if not conn_str:
        print("⚠️ No Application Insights connection string provided. Tracing disabled.")
        return False
    
    try:
        # Step 1: Configure Azure Monitor with the connection string
        # This sets up the OpenTelemetry exporter to send traces to App Insights
        configure_azure_monitor(connection_string=conn_str)
        print("✅ Azure Monitor configured")
        
        # Step 2: Instrument the OpenAI SDK
        # This automatically captures all OpenAI API calls as spans
        OpenAIInstrumentor().instrument()
        print("✅ OpenAI SDK instrumented for tracing")
        
        _tracing_initialized = True
        print("✅ Application Insights tracing configured successfully!")
        return True
        
    except Exception as e:
        print(f"⚠️ Warning: Could not configure tracing: {e}")
        return False


def get_tracer(name: str = __name__):
    """
    Get an OpenTelemetry tracer for custom spans.
    
    Args:
        name: Name for the tracer (typically __name__)
        
    Returns:
        Tracer instance or None if tracing not available
    """
    if not TRACING_AVAILABLE or trace is None:
        return None
    return trace.get_tracer(name)


class TracingService:
    """
    Service for Application Insights tracing integration with Azure AI Foundry.
    Enables tracing and monitoring visibility in the Foundry portal.
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize the tracing service.
        
        Args:
            connection_string: Application Insights connection string.
        """
        self.connection_string = connection_string or os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        self.is_configured = initialize_tracing(self.connection_string)
        self.tracer = get_tracer(__name__) if self.is_configured else None
    
    def trace_chat_interaction(
        self,
        user_message: str,
        assistant_response: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        response_time_ms: float,
        session_id: Optional[str] = None,
        additional_attributes: Optional[Dict[str, Any]] = None,
    ):
        """
        Trace a chat interaction with full input/output capture.
        
        Note: With OpenAIInstrumentor, OpenAI calls are automatically traced.
        This method adds additional custom spans for business context.
        """
        if not self.is_configured or not self.tracer:
            return
        
        try:
            with self.tracer.start_as_current_span("chat_interaction") as span:
                # Add input event for Azure AI Foundry visibility
                span.add_event(
                    name="gen_ai.content.prompt",
                    attributes={
                        "gen_ai.prompt": user_message,
                        "gen_ai.system": "azure_openai"
                    }
                )
                
                # Add output event
                span.add_event(
                    name="gen_ai.content.completion",
                    attributes={
                        "gen_ai.completion": assistant_response,
                        "gen_ai.system": "azure_openai"
                    }
                )
                
                # Set span attributes for metrics
                span.set_attribute("gen_ai.request.model", model)
                span.set_attribute("gen_ai.usage.prompt_tokens", input_tokens)
                span.set_attribute("gen_ai.usage.completion_tokens", output_tokens)
                span.set_attribute("gen_ai.usage.total_tokens", input_tokens + output_tokens)
                span.set_attribute("response_time_ms", response_time_ms)
                span.set_attribute("gen_ai.system", "azure_openai")
                
                if session_id:
                    span.set_attribute("session.id", session_id)
                
                span.set_attribute("timestamp", datetime.utcnow().isoformat())
                
                # Add any additional custom attributes
                if additional_attributes:
                    for key, value in additional_attributes.items():
                        if isinstance(value, (str, int, float, bool)):
                            span.set_attribute(key, value)
                        else:
                            span.set_attribute(key, json.dumps(value))
                
                span.set_status(Status(StatusCode.OK))
                
        except Exception as e:
            print(f"⚠️ Error tracing chat interaction: {e}")
    
    def trace_dashboard_view(
        self,
        view_name: str,
        user_action: str,
        data_context: Optional[Dict[str, Any]] = None,
    ):
        """Trace dashboard view interactions."""
        if not self.is_configured or not self.tracer:
            return
        
        try:
            with self.tracer.start_as_current_span("dashboard_interaction") as span:
                span.set_attribute("view.name", view_name)
                span.set_attribute("user.action", user_action)
                span.set_attribute("timestamp", datetime.utcnow().isoformat())
                
                if data_context:
                    for key, value in data_context.items():
                        if isinstance(value, (str, int, float, bool)):
                            span.set_attribute(f"data.{key}", value)
        except Exception as e:
            print(f"⚠️ Error tracing dashboard view: {e}")


# Singleton instance for app-wide tracing
_tracing_service: Optional[TracingService] = None


def get_tracing_service() -> TracingService:
    """Get or create the singleton tracing service instance."""
    global _tracing_service
    if _tracing_service is None:
        _tracing_service = TracingService()
    return _tracing_service


def init_tracing(connection_string: Optional[str] = None) -> TracingService:
    """
    Initialize tracing with an optional connection string.
    
    Args:
        connection_string: Application Insights connection string
        
    Returns:
        TracingService instance
    """
    global _tracing_service
    _tracing_service = TracingService(connection_string)
    return _tracing_service
