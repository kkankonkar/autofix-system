"""Hybrid AI agent that prefers Bob CLI and falls back to OpenAI."""

import logging
import os
from typing import Any, Dict, Optional

from .base import AIAgent
from .bob_agent import BobAgent
from .openai_agent import OpenAIAgent

# Configure logger
logger = logging.getLogger(__name__)


class HybridAgent(AIAgent):
    """Primary Bob CLI agent with optional OpenAI fallback support."""

    def __init__(self, openai_api_key: Optional[str] = None) -> None:
        self.primary_agent = BobAgent()

        resolved_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.fallback_agent = OpenAIAgent(api_key=resolved_api_key) if resolved_api_key else None
        
        if self.fallback_agent:
            logger.info("HybridAgent initialized with Bob CLI (primary) and OpenAI (fallback)")
        else:
            logger.info("HybridAgent initialized with Bob CLI only (no fallback)")

    async def analyze_error(self, log_entry: str, code_context: str) -> Dict[str, Any]:
        """Analyze with Bob first, then OpenAI if Bob fails and fallback is configured."""
        try:
            logger.info("Attempting error analysis with primary agent (Bob CLI)")
            return await self.primary_agent.analyze_error(log_entry, code_context)
        except Exception as e:
            logger.warning(f"Primary agent (Bob CLI) failed: {str(e)}")
            if self.fallback_agent is None:
                logger.error("No fallback agent configured, re-raising exception")
                raise
            logger.info("Falling back to OpenAI agent")
            try:
                result = await self.fallback_agent.analyze_error(log_entry, code_context)
                logger.info("Fallback agent (OpenAI) succeeded")
                return result
            except Exception as fallback_error:
                logger.error(f"Fallback agent (OpenAI) also failed: {str(fallback_error)}")
                raise

    async def generate_fix(self, error_analysis: Dict[str, Any], code_context: str) -> Dict[str, Any]:
        """Generate fixes with Bob first, then OpenAI if Bob fails and fallback is configured."""
        try:
            logger.info("Attempting fix generation with primary agent (Bob CLI)")
            return await self.primary_agent.generate_fix(error_analysis, code_context)
        except Exception as e:
            logger.warning(f"Primary agent (Bob CLI) failed: {str(e)}")
            if self.fallback_agent is None:
                logger.error("No fallback agent configured, re-raising exception")
                raise
            logger.info("Falling back to OpenAI agent")
            try:
                result = await self.fallback_agent.generate_fix(error_analysis, code_context)
                logger.info("Fallback agent (OpenAI) succeeded")
                return result
            except Exception as fallback_error:
                logger.error(f"Fallback agent (OpenAI) also failed: {str(fallback_error)}")
                raise


# Made with Bob