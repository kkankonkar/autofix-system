"""OpenAI-backed AI agent implementation."""

import json
import os
from typing import Any, Dict, Optional

from openai import AsyncOpenAI

from .base import AIAgent


class OpenAIAgent(AIAgent):
    """AI agent that executes prompts through the OpenAI API."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        resolved_api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not resolved_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAIAgent")

        self.client = AsyncOpenAI(api_key=resolved_api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    async def analyze_error(self, log_entry: str, code_context: str) -> Dict[str, Any]:
        """Analyze an error using OpenAI and return structured JSON."""
        prompt = f"""
Analyze the following application error and return JSON.

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

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You analyze software failures and return strict JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        if content is None:
            raise ValueError("OpenAI returned an empty analysis response")

        return json.loads(content)

    async def generate_fix(self, error_analysis: Dict[str, Any], code_context: str) -> Dict[str, Any]:
        """Generate a fix using OpenAI and return structured JSON."""
        prompt = f"""
Generate a code fix and return JSON.

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

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You generate safe software fixes and return strict JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        if content is None:
            raise ValueError("OpenAI returned an empty fix response")

        return json.loads(content)


# Made with Bob