"""AI Agent module for error analysis and fix generation."""

from .base import AIAgent
from .bob_agent import BobAgent
from .claude_agent_rest import ClaudeAgentREST
from .openai_agent import OpenAIAgent
from .hybrid_agent import HybridAgent

__all__ = [
    "AIAgent",
    "BobAgent",
    "ClaudeAgentREST",
    "OpenAIAgent",
    "HybridAgent",
]

# Made with Bob
