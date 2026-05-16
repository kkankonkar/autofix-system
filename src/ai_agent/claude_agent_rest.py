"""Claude AI agent implementation using direct REST API calls instead of SDK."""

import json
import os
import re
from typing import Any, Dict, Optional

import httpx

from .base import AIAgent


class ClaudeAgentREST(AIAgent):
    """AI agent that uses Claude API via direct HTTP requests (no SDK required)."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None) -> None:
        """Initialize Claude agent with API key and optional custom base URL."""
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for ClaudeAgentREST")

        # Support custom base URL for Azure OpenAI-style deployments
        self.base_url = base_url or os.getenv("CLAUDE_API_BASE_URL", "https://api.anthropic.com")
        self.api_version = os.getenv("CLAUDE_API_VERSION", "2023-06-01")
        
        # Model configuration
        self.model = os.getenv("CLAUDE_MODEL", "claude-3-opus-20240229")
        self.max_tokens = int(os.getenv("CLAUDE_MAX_TOKENS", "4096"))
        
        # HTTP client configuration
        self.timeout = float(os.getenv("CLAUDE_TIMEOUT", "60.0"))

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for Claude API requests."""
        if not self.api_key:
            raise ValueError("API key is required")
        return {
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version,
            "content-type": "application/json",
        }

    def _extract_json(self, content: str) -> Dict[str, Any]:
        """Extract JSON from Claude response, handling markdown code blocks."""
        # Try direct JSON parse first
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Try to extract from markdown code block
        json_pattern = r'```json\s*(.*?)\s*```'
        match = re.search(json_pattern, content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON object in text
        json_obj_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        match = re.search(json_obj_pattern, content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        
        raise ValueError(f"Failed to extract valid JSON from Claude response: {content[:200]}...")

    async def _make_request(self, system: str, user_prompt: str) -> str:
        """Make HTTP request to Claude API."""
        url = f"{self.base_url}/v1/messages"
        
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": system,
            "messages": [
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.0
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                headers=self._get_headers(),
                json=payload
            )
            
            # Handle errors
            if response.status_code != 200:
                error_detail = response.text
                raise ValueError(
                    f"Claude API request failed with status {response.status_code}: {error_detail}"
                )
            
            # Parse response
            response_data = response.json()
            
            # Extract content from response
            if "content" not in response_data or not response_data["content"]:
                raise ValueError("Claude API returned empty content")
            
            # Claude returns content as array of content blocks
            content_blocks = response_data["content"]
            if not content_blocks or "text" not in content_blocks[0]:
                raise ValueError("Claude API response missing text content")
            
            return content_blocks[0]["text"]

    async def analyze_error(self, log_entry: str, code_context: str) -> Dict[str, Any]:
        """Analyze an error using Claude REST API and return structured JSON."""
        system_prompt = (
            "You are an expert software error analyzer. "
            "You analyze application errors and return ONLY valid JSON. "
            "Do not include any explanatory text outside the JSON object."
        )
        
        user_prompt = f"""
Analyze the following application error and return ONLY a JSON object with this exact schema:

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

Return ONLY the JSON object, no other text.
""".strip()

        content = await self._make_request(system_prompt, user_prompt)
        return self._extract_json(content)

    async def generate_fix(self, error_analysis: Dict[str, Any], code_context: str) -> Dict[str, Any]:
        """Generate a fix using Claude REST API and return structured JSON."""
        system_prompt = (
            "You are an expert software engineer who generates safe code fixes. "
            "You return ONLY valid JSON with the fix details. "
            "Do not include any explanatory text outside the JSON object."
        )
        
        user_prompt = f"""
Generate a code fix and return ONLY a JSON object with this exact schema:

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

Return ONLY the JSON object, no other text.
""".strip()

        content = await self._make_request(system_prompt, user_prompt)
        return self._extract_json(content)


# Made with Bob