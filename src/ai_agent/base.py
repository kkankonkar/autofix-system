"""Base interfaces for AI agents used by the AutoFix system."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class AIAgent(ABC):
    """Abstract base class for error analysis and fix generation agents."""

    @abstractmethod
    async def analyze_error(self, log_entry: str, code_context: str) -> Dict[str, Any]:
        """Analyze an error and return structured results."""

    @abstractmethod
    async def generate_fix(self, error_analysis: Dict[str, Any], code_context: str) -> Dict[str, Any]:
        """Generate a code fix and return structured results."""


# Made with Bob