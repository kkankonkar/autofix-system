"""Hybrid AI agent that prefers Bob CLI and falls back to Claude/OpenAI."""

import os
from typing import Any, Dict, Optional

from .base import AIAgent
from .bob_agent import BobAgent
from .claude_agent_rest import ClaudeAgentREST
from .openai_agent import OpenAIAgent


class HybridAgent(AIAgent):
    """Primary Bob CLI agent with optional Claude/OpenAI fallback support."""

    def __init__(self, fallback_api_key: Optional[str] = None, base_url: Optional[str] = None) -> None:
        self.primary_agent = BobAgent()

        # Determine fallback agent based on configuration
        fallback_type = os.getenv("AI_AGENT_FALLBACK", "claude").lower()
        
        if fallback_type == "claude":
            resolved_api_key = fallback_api_key or os.getenv("ANTHROPIC_API_KEY")
            resolved_base_url = base_url or os.getenv("CLAUDE_API_BASE_URL")
            self.fallback_agent = ClaudeAgentREST(
                api_key=resolved_api_key,
                base_url=resolved_base_url
            ) if resolved_api_key else None
        elif fallback_type == "openai":
            resolved_api_key = fallback_api_key or os.getenv("OPENAI_API_KEY")
            self.fallback_agent = OpenAIAgent(api_key=resolved_api_key) if resolved_api_key else None
        else:
            self.fallback_agent = None

    async def analyze_error(self, log_entry: str, code_context: str) -> Dict[str, Any]:
        """Analyze with Bob first, then fallback agent if Bob fails and fallback is configured."""
        try:
            return await self.primary_agent.analyze_error(log_entry, code_context)
        except Exception:
            if self.fallback_agent is None:
                raise
            return await self.fallback_agent.analyze_error(log_entry, code_context)

    async def generate_fix(self, error_analysis: Dict[str, Any], code_context: str) -> Dict[str, Any]:
        """Generate fixes with Bob first, then fallback agent if Bob fails and fallback is configured."""
        try:
            return await self.primary_agent.generate_fix(error_analysis, code_context)
        except Exception:
            if self.fallback_agent is None:
                raise
            return await self.fallback_agent.generate_fix(error_analysis, code_context)


# Made with Bob