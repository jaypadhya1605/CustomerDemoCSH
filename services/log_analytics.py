"""
Azure Log Analytics Integration for Agent Tracing & Evaluation
CommonSpirit Health - Conversational Analytics

Provides:
- Chat conversation logging
- Response latency tracking
- Token usage monitoring
- Cost attribution per session
- Query performance analysis
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
import requests
import hashlib
import hmac
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ChatAnalyticsEvent:
    """Structured event for chat analytics logging."""
    timestamp: str
    session_id: str
    user_query: str
    response_summary: str
    model_used: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_ms: float
    estimated_cost: float
    actual_cost: Optional[float]
    department_context: str
    query_type: str
    response_quality_score: Optional[float]
    error_occurred: bool
    error_message: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentTraceEvent:
    """Structured event for agent execution tracing."""
    timestamp: str
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    duration_ms: float
    status: str  # success, error, timeout
    attributes: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LogAnalyticsClient:
    """
    Client for sending custom logs to Azure Log Analytics workspace.
    Implements the HTTP Data Collector API.
    """
    
    def __init__(
        self,
        workspace_id: Optional[str] = None,
        shared_key: Optional[str] = None
    ):
        self.workspace_id = workspace_id or os.environ.get("LOG_ANALYTICS_WORKSPACE_ID")
        self.shared_key = shared_key or os.environ.get("LOG_ANALYTICS_SHARED_KEY")
        self.api_version = "2016-04-01"
        
        if not self.workspace_id or not self.shared_key:
            logger.warning("Log Analytics credentials not configured. Logging to console only.")
            self.enabled = False
        else:
            self.enabled = True
            
    def _build_signature(self, date: str, content_length: int, method: str, content_type: str, resource: str) -> str:
        """Build the authorization signature for Log Analytics API."""
        x_headers = f"x-ms-date:{date}"
        string_to_hash = f"{method}\n{content_length}\n{content_type}\n{x_headers}\n{resource}"
        bytes_to_hash = bytes(string_to_hash, encoding="utf-8")
        decoded_key = base64.b64decode(self.shared_key)
        encoded_hash = base64.b64encode(
            hmac.new(decoded_key, bytes_to_hash, digestmod=hashlib.sha256).digest()
        ).decode()
        return f"SharedKey {self.workspace_id}:{encoded_hash}"
    
    def send_log(self, log_type: str, data: Dict[str, Any]) -> bool:
        """
        Send a single log entry to Log Analytics.
        
        Args:
            log_type: Custom log type name (will appear as {log_type}_CL)
            data: Dictionary of log data
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.info(f"[{log_type}] {json.dumps(data)}")
            return True
            
        try:
            body = json.dumps([data])
            method = "POST"
            content_type = "application/json"
            resource = "/api/logs"
            
            rfc1123date = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
            content_length = len(body)
            
            signature = self._build_signature(
                rfc1123date, content_length, method, content_type, resource
            )
            
            uri = f"https://{self.workspace_id}.ods.opinsights.azure.com{resource}?api-version={self.api_version}"
            
            headers = {
                "content-type": content_type,
                "Authorization": signature,
                "Log-Type": log_type,
                "x-ms-date": rfc1123date,
                "time-generated-field": "timestamp"
            }
            
            response = requests.post(uri, data=body, headers=headers, timeout=30)
            
            if response.status_code in [200, 202]:
                logger.debug(f"Log sent successfully to {log_type}")
                return True
            else:
                logger.error(f"Failed to send log: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending log to Log Analytics: {str(e)}")
            # Fallback to console logging
            logger.info(f"[{log_type}] {json.dumps(data)}")
            return False
    
    def log_chat_analytics(self, event: ChatAnalyticsEvent) -> bool:
        """Log a chat analytics event."""
        return self.send_log("ChatAnalytics", event.to_dict())
    
    def log_agent_trace(self, event: AgentTraceEvent) -> bool:
        """Log an agent trace event."""
        return self.send_log("AgentTrace", event.to_dict())
    
    def log_cost_event(self, data: Dict[str, Any]) -> bool:
        """Log a cost tracking event."""
        return self.send_log("CostTracking", data)
    
    def log_vte_metrics(self, data: Dict[str, Any]) -> bool:
        """Log VTE clinical metrics."""
        return self.send_log("VTEMetrics", data)


class ChatTracer:
    """
    High-level tracing for chat interactions.
    Automatically captures timing, tokens, and costs.
    """
    
    def __init__(self, log_client: Optional[LogAnalyticsClient] = None):
        self.log_client = log_client or LogAnalyticsClient()
        self._session_id = self._generate_session_id()
        
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        import uuid
        return str(uuid.uuid4())[:8]
    
    @property
    def session_id(self) -> str:
        return self._session_id
    
    def log_interaction(
        self,
        query: str,
        response: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        estimated_cost: float,
        department: str = "all",
        error: Optional[Exception] = None
    ) -> None:
        """
        Log a complete chat interaction.
        
        Args:
            query: User's question
            response: AI response
            model: Model used for inference
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            latency_ms: Response latency in milliseconds
            estimated_cost: Estimated cost for this request
            department: Department context for the query
            error: Exception if an error occurred
        """
        event = ChatAnalyticsEvent(
            timestamp=datetime.utcnow().isoformat(),
            session_id=self._session_id,
            user_query=query[:500],  # Truncate for storage
            response_summary=response[:200] + "..." if len(response) > 200 else response,
            model_used=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency_ms=latency_ms,
            estimated_cost=estimated_cost,
            actual_cost=None,  # Populated later from Cost Management
            department_context=department,
            query_type=self._classify_query(query),
            response_quality_score=None,  # Can be populated from user feedback
            error_occurred=error is not None,
            error_message=str(error) if error else None
        )
        
        self.log_client.log_chat_analytics(event)
    
    def _classify_query(self, query: str) -> str:
        """Classify the type of user query."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["trend", "over time", "history", "change"]):
            return "trend_analysis"
        elif any(word in query_lower for word in ["compare", "versus", "vs", "between"]):
            return "comparison"
        elif any(word in query_lower for word in ["why", "reason", "cause", "factor"]):
            return "root_cause"
        elif any(word in query_lower for word in ["improve", "recommendation", "suggest", "opportunity"]):
            return "recommendation"
        elif any(word in query_lower for word in ["goal", "target", "threshold", "benchmark"]):
            return "goal_tracking"
        else:
            return "general_inquiry"


# ============================================================================
# KQL Queries for Log Analytics
# ============================================================================
KQL_QUERIES = {
    "daily_usage_summary": """
ChatAnalytics_CL
| where TimeGenerated > ago(24h)
| summarize 
    TotalRequests = count(),
    AvgLatencyMs = avg(latency_ms_d),
    TotalInputTokens = sum(input_tokens_d),
    TotalOutputTokens = sum(output_tokens_d),
    TotalEstimatedCost = sum(estimated_cost_d)
| by bin(TimeGenerated, 1h)
""",
    
    "query_type_distribution": """
ChatAnalytics_CL
| where TimeGenerated > ago(7d)
| summarize Count = count() by query_type_s
| order by Count desc
""",
    
    "department_usage": """
ChatAnalytics_CL
| where TimeGenerated > ago(7d)
| summarize 
    Requests = count(),
    AvgCost = avg(estimated_cost_d)
| by department_context_s
| order by Requests desc
""",
    
    "error_analysis": """
ChatAnalytics_CL
| where TimeGenerated > ago(24h)
| where error_occurred_b == true
| project TimeGenerated, session_id_s, user_query_s, error_message_s
| order by TimeGenerated desc
""",
    
    "latency_percentiles": """
ChatAnalytics_CL
| where TimeGenerated > ago(24h)
| summarize 
    p50 = percentile(latency_ms_d, 50),
    p90 = percentile(latency_ms_d, 90),
    p99 = percentile(latency_ms_d, 99)
| by bin(TimeGenerated, 1h)
""",

    "cost_by_model": """
ChatAnalytics_CL
| where TimeGenerated > ago(7d)
| summarize 
    TotalCost = sum(estimated_cost_d),
    TotalTokens = sum(total_tokens_d),
    RequestCount = count()
| by model_used_s
""",

    "vte_metrics_trend": """
VTEMetrics_CL
| where TimeGenerated > ago(30d)
| summarize 
    AvgProphylaxisRate = avg(prophylaxis_rate_d),
    AvgVTERate = avg(vte_event_rate_d)
| by bin(TimeGenerated, 1d), department_s
"""
}


# Singleton instance for easy import
_default_tracer = None

def get_tracer() -> ChatTracer:
    """Get the default chat tracer instance."""
    global _default_tracer
    if _default_tracer is None:
        _default_tracer = ChatTracer()
    return _default_tracer


def log_chat(query: str, response: str, model: str, input_tokens: int, 
             output_tokens: int, latency_ms: float, estimated_cost: float,
             department: str = "all", error: Optional[Exception] = None) -> None:
    """Convenience function to log a chat interaction."""
    get_tracer().log_interaction(
        query=query,
        response=response,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        estimated_cost=estimated_cost,
        department=department,
        error=error
    )
