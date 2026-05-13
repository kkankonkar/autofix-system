"""Bob CLI-backed AI agent implementation."""

import json
import os
import subprocess
from typing import Any, Dict

from .base import AIAgent


class BobAgent(AIAgent):
    """AI agent that executes prompts through Bob CLI."""

    def __init__(self) -> None:
        self.bob_command = os.getenv("BOB_CLI_COMMAND", "bob")
        self.bob_mode = os.getenv("BOB_MODE", "ask")
        self.timeout_seconds = int(os.getenv("BOB_TIMEOUT_SECONDS", "180"))

    async def _run_bob(self, prompt: str) -> str:
        """Execute Bob CLI with a non-interactive prompt."""
        result = subprocess.run(
            [self.bob_command, "-p", prompt, "--chat-mode", self.bob_mode, "--yolo"],
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
        )

        if result.returncode != 0:
            stderr = result.stderr.strip() or "Unknown Bob CLI error"
            raise RuntimeError(f"Bob CLI failed: {stderr}")

        return result.stdout.strip()

    @staticmethod
    def _parse_json_response(content: str) -> Dict[str, Any]:
        """Parse Bob output into JSON, allowing fenced code blocks."""
        normalized = content.strip()

        if "```json" in normalized:
            start = normalized.find("```json") + 7
            end = normalized.find("```", start)
            normalized = normalized[start:end].strip()
        elif normalized.startswith("```") and normalized.endswith("```"):
            normalized = normalized[3:-3].strip()
            if normalized.startswith("json"):
                normalized = normalized[4:].strip()

        return json.loads(normalized)

    async def analyze_error(self, log_entry: str, code_context: str) -> Dict[str, Any]:
        """Analyze an error using Bob CLI and return structured JSON."""
        prompt = f"""
Analyze the following application error and return ONLY valid JSON.

Return this schema:
{{
  "error_type": "string",
  "file_path": "string",
  "line_number": 0,
  "function_name": "string or null",
  "root_cause": "string",
  "fixable": true,
  "confidence": 0.0,
  "repository": "string"
}}

Error Log:
{log_entry}

Code Context:
{code_context}
""".strip()

        return self._parse_json_response(await self._run_bob(prompt))

    async def generate_fix(self, error_analysis: Dict[str, Any], code_context: str) -> Dict[str, Any]:
        """Generate a code fix using Bob CLI and return structured JSON."""
        prompt = f"""
Generate a fix for the following error analysis and return ONLY valid JSON.

Return this schema:
{{
  "original_code": "string",
  "fixed_code": "string",
  "explanation": "string",
  "commit_message": "string",
  "pr_description": "string",
  "test_suggestions": ["string"]
}}

Error Analysis:
{json.dumps(error_analysis, indent=2)}

Code Context:
{code_context}
""".strip()

        return self._parse_json_response(await self._run_bob(prompt))


# Made with Bob