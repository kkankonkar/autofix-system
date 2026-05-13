"""Hybrid AI agent that prefers Bob CLI and falls back to OpenAI."""

from typing import Any, Dict, Optional

from .base import AIAgent
from .bob_agent import BobAgent
from .openai_agent import OpenAIAgent


class HybridAgent(AIAgent):
    """Primary Bob CLI agent with OpenAI fallback support."""

    def __init__(self, openai_api_key: Optional[str] = None) -> None:
        self.primary_agent = BobAgent()
        self.fallback_agent = OpenAIAgent(api_key=openai_api_key)

    async def analyze_error(self, log_entry: str, code_context: str) -> Dict[str, Any]:
        """Analyze with Bob first, then OpenAI if Bob fails."""
        try:
            return await self.primary_agent.analyze_error(log_entry, code_context)
        except Exception:
            return await self.fallback_agent.analyze_error(log_entry, code_context)

    async def generate_fix(self, error_analysis: Dict[str, Any], code_context: str) -> Dict[str, Any]:
        """Generate fixes with Bob first, then OpenAI if Bob fails."""
        try:
            return await self.primary_agent.generate_fix(error_analysis, code_context)
        except Exception:
            return await self.fallback_agent.generate_fix(error_analysis, code_context)


# Made with Bob