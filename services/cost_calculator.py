"""
Cost Calculator for Azure OpenAI usage tracking.
Implements the two-track cost model:
1. Real-time estimated costs (token-based, instant)
2. Actual costs (from Azure Cost Management, delayed)
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import yaml
from pathlib import Path


@dataclass
class CostBreakdown:
    """Breakdown of costs for a single API call."""
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    input_cost: float
    output_cost: float
    total_estimated_cost: float
    actual_cost: Optional[float] = None  # From Azure Cost Management (delayed)
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "Demo Estimate"

    def to_dict(self) -> dict:
        """Convert to dictionary for display."""
        return {
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "input_cost": f"${self.input_cost:.6f}",
            "output_cost": f"${self.output_cost:.6f}",
            "total_estimated_cost": f"${self.total_estimated_cost:.6f}",
            "actual_cost": f"${self.actual_cost:.6f}" if self.actual_cost else "Pending",
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
        }


class CostCalculator:
    """
    Calculate costs for Azure OpenAI API calls.

    Implements two-track model:
    - Estimated: Real-time calculation from token usage × price table
    - Actual: From Azure Cost Management API (delayed, placeholder for now)
    """

    def __init__(self, pricing_path: Optional[Path] = None):
        self.pricing_path = pricing_path or Path(__file__).parent.parent / "pricing" / "prices.yaml"
        self.pricing = self._load_pricing()
        self.session_costs: list[CostBreakdown] = []

    def _load_pricing(self) -> dict:
        """Load pricing from YAML file."""
        try:
            with open(self.pricing_path, "r") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Default pricing if file not found
            return {
                "models": {
                    "gpt-5-mini": {
                        "input_per_1k_tokens": 0.00015,
                        "output_per_1k_tokens": 0.0006,
                    },
                    "gpt-5.2": {
                        "input_per_1k_tokens": 0.0025,
                        "output_per_1k_tokens": 0.01,
                    },
                    "gpt-realtime": {
                        "input_per_1k_tokens": 0.06,
                        "output_per_1k_tokens": 0.24,
                    },
                },
                "metadata": {
                    "disclaimer": "Demo estimates - actual costs may vary"
                }
            }

    def get_model_rates(self, model: str) -> tuple[float, float]:
        """Get input and output rates for a model (per 1K tokens)."""
        models = self.pricing.get("models", {})

        # Normalize model name
        model_key = model.lower().replace("gpt-", "gpt-")
        for key in models:
            if key.lower() == model_key or model_key in key.lower():
                rates = models[key]
                return (
                    rates.get("input_per_1k_tokens", 0.0),
                    rates.get("output_per_1k_tokens", 0.0)
                )

        # Default to gpt-5-mini rates if model not found
        default = models.get("gpt-5-mini", {})
        return (
            default.get("input_per_1k_tokens", 0.00015),
            default.get("output_per_1k_tokens", 0.0006)
        )

    def calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> CostBreakdown:
        """
        Calculate estimated cost for an API call.

        Args:
            model: Model name used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            CostBreakdown with estimated costs
        """
        input_rate, output_rate = self.get_model_rates(model)

        input_cost = (input_tokens / 1000) * input_rate
        output_cost = (output_tokens / 1000) * output_rate
        total_cost = input_cost + output_cost

        breakdown = CostBreakdown(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_estimated_cost=total_cost,
            source=self.pricing.get("metadata", {}).get("disclaimer", "Demo Estimate"),
        )

        self.session_costs.append(breakdown)
        return breakdown

    def get_session_total(self) -> dict:
        """Get total costs for the current session."""
        total_input = sum(c.input_tokens for c in self.session_costs)
        total_output = sum(c.output_tokens for c in self.session_costs)
        total_estimated = sum(c.total_estimated_cost for c in self.session_costs)
        total_actual = sum(
            c.actual_cost for c in self.session_costs if c.actual_cost is not None
        )

        return {
            "request_count": len(self.session_costs),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "total_estimated_cost": total_estimated,
            "total_actual_cost": total_actual if total_actual > 0 else None,
            "costs_by_model": self._costs_by_model(),
        }

    def _costs_by_model(self) -> dict:
        """Group costs by model."""
        by_model = {}
        for cost in self.session_costs:
            if cost.model not in by_model:
                by_model[cost.model] = {
                    "requests": 0,
                    "tokens": 0,
                    "estimated_cost": 0.0,
                }
            by_model[cost.model]["requests"] += 1
            by_model[cost.model]["tokens"] += cost.total_tokens
            by_model[cost.model]["estimated_cost"] += cost.total_estimated_cost
        return by_model

    def clear_session(self):
        """Clear session costs."""
        self.session_costs = []

    def get_cost_history(self) -> list[dict]:
        """Get history of all costs in session."""
        return [c.to_dict() for c in self.session_costs]

    def format_cost_receipt(self, breakdown: CostBreakdown) -> str:
        """Format a cost breakdown as a readable receipt."""
        receipt = f"""
╔══════════════════════════════════════════════════════════════╗
║                     COST RECEIPT                             ║
╠══════════════════════════════════════════════════════════════╣
║  Model: {breakdown.model:<52}║
║  Timestamp: {breakdown.timestamp.strftime('%Y-%m-%d %H:%M:%S'):<48}║
╠══════════════════════════════════════════════════════════════╣
║  TOKEN USAGE                                                 ║
║  ├─ Input tokens:  {breakdown.input_tokens:>10,}                              ║
║  ├─ Output tokens: {breakdown.output_tokens:>10,}                              ║
║  └─ Total tokens:  {breakdown.total_tokens:>10,}                              ║
╠══════════════════════════════════════════════════════════════╣
║  ESTIMATED COST (Real-time)                                  ║
║  ├─ Input cost:    ${breakdown.input_cost:>10.6f}                            ║
║  ├─ Output cost:   ${breakdown.output_cost:>10.6f}                            ║
║  └─ Total:         ${breakdown.total_estimated_cost:>10.6f}                            ║
╠══════════════════════════════════════════════════════════════╣
║  ACTUAL COST (Azure Cost Management)                         ║
║  └─ Status: {'$' + f'{breakdown.actual_cost:.6f}' if breakdown.actual_cost else 'Pending (delayed ~24-48hrs)':<45}║
╠══════════════════════════════════════════════════════════════╣
║  Source: {breakdown.source:<52}║
╚══════════════════════════════════════════════════════════════╝
"""
        return receipt
