"""
Azure Application Insights Tracing Service for Conversational Analytics.
Implements OpenTelemetry tracing for Azure AI Foundry monitoring integration.
"""
import os
from typing import Optional, Dict, Any
import json
from datetime import datetime

# Set environment variable BEFORE any instrumentation
os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = "true"

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Azure Monitor integration
try:
    from azure.monitor.opentelemetry import configure_azure_monitor
    from opentelemetry.instrumentation.openai_v2 import OpenAIInstrumentor
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False
    print("⚠️ Azure Monitor OpenTelemetry packages not installed. Tracing disabled.")


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
                              If not provided, reads from APPLICATIONINSIGHTS_CONNECTION_STRING env var.
        """
        self.connection_string = connection_string or os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        self.is_configured = False
        self.tracer = None
        
        if self.connection_string and TRACING_AVAILABLE:
            self._configure_tracing()
    
    def _configure_tracing(self):
        """Configure Azure Monitor and OpenTelemetry instrumentation."""
        try:
            # Configure Azure Monitor with the connection string
            configure_azure_monitor(connection_string=self.connection_string)
            
            # Instrument OpenAI SDK for automatic tracing
            OpenAIInstrumentor().instrument()
            
            # Get tracer for custom spans
            self.tracer = trace.get_tracer(__name__)
            self.is_configured = True
            print("✅ Application Insights tracing configured successfully!")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not configure tracing: {e}")
            self.is_configured = False
    
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
        
        Args:
            user_message: The user's input message
            assistant_response: The assistant's response
            model: The model used for the response
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            response_time_ms: Response time in milliseconds
            session_id: Optional session identifier
            additional_attributes: Additional custom attributes to include
        """
        if not self.is_configured or not self.tracer:
            return
        
        with self.tracer.start_as_current_span("chat_interaction") as span:
            try:
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
                span.set_attribute("gen_ai.prompt", user_message)
                span.set_attribute("gen_ai.completion", assistant_response)
                span.set_attribute("gen_ai.request.model", model)
                span.set_attribute("gen_ai.usage.prompt_tokens", input_tokens)
                span.set_attribute("gen_ai.usage.completion_tokens", output_tokens)
                span.set_attribute("gen_ai.usage.total_tokens", input_tokens + output_tokens)
                span.set_attribute("response_time_ms", response_time_ms)
                span.set_attribute("gen_ai.system", "azure_openai")
                
                if session_id:
                    span.set_attribute("session.id", session_id)
                
                # Add timestamp
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
                span.set_status(Status(StatusCode.ERROR, str(e)))
    
    def trace_dashboard_view(
        self,
        view_name: str,
        user_action: str,
        data_context: Optional[Dict[str, Any]] = None,
    ):
        """
        Trace dashboard view interactions.
        
        Args:
            view_name: Name of the dashboard view
            user_action: Action performed by the user
            data_context: Optional context about the data being viewed
        """
        if not self.is_configured or not self.tracer:
            return
        
        with self.tracer.start_as_current_span("dashboard_interaction") as span:
            span.set_attribute("view.name", view_name)
            span.set_attribute("user.action", user_action)
            span.set_attribute("timestamp", datetime.utcnow().isoformat())
            
            if data_context:
                for key, value in data_context.items():
                    if isinstance(value, (str, int, float, bool)):
                        span.set_attribute(f"data.{key}", value)
    
    def trace_data_query(
        self,
        query_type: str,
        dataset: str,
        filters: Optional[Dict[str, Any]] = None,
        result_count: int = 0,
        execution_time_ms: float = 0,
    ):
        """
        Trace data query operations.
        
        Args:
            query_type: Type of query (e.g., "vte_metrics", "financial_summary")
            dataset: Dataset being queried
            filters: Query filters applied
            result_count: Number of results returned
            execution_time_ms: Query execution time
        """
        if not self.is_configured or not self.tracer:
            return
        
        with self.tracer.start_as_current_span("data_query") as span:
            span.set_attribute("query.type", query_type)
            span.set_attribute("query.dataset", dataset)
            span.set_attribute("query.result_count", result_count)
            span.set_attribute("query.execution_time_ms", execution_time_ms)
            span.set_attribute("timestamp", datetime.utcnow().isoformat())
            
            if filters:
                span.set_attribute("query.filters", json.dumps(filters))


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
