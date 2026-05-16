"""Bob CLI-backed AI agent implementation."""

import json
import logging
import os
import subprocess
from typing import Any, Dict

from .base import AIAgent

# Configure logger
logger = logging.getLogger(__name__)


class BobAgent(AIAgent):
    """AI agent that executes prompts through Bob CLI."""

    def __init__(self) -> None:
        self.bob_command = os.getenv("BOB_CLI_COMMAND", "bob")
        self.bob_mode = os.getenv("BOB_MODE", "ask")
        self.timeout_seconds = int(os.getenv("BOB_TIMEOUT_SECONDS", "60"))  # Reduced from 180 to 60 for AWS Fargate
        logger.info(f"BobAgent initialized: command={self.bob_command}, mode={self.bob_mode}, timeout={self.timeout_seconds}s")

    async def _run_bob(self, prompt: str) -> str:
        """Execute Bob CLI with a non-interactive prompt."""
        logger.info(f"Executing Bob CLI with timeout={self.timeout_seconds}s")
        logger.debug(f"Bob CLI prompt: {prompt[:200]}...")  # Log first 200 chars
        
        try:
            result = subprocess.run(
                [self.bob_command, "-p", prompt, "--chat-mode", self.bob_mode, "--yolo"],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )

            if result.returncode != 0:
                stderr = result.stderr.strip() or "Unknown Bob CLI error"
                logger.error(f"Bob CLI failed with return code {result.returncode}: {stderr}")
                raise RuntimeError(f"Bob CLI failed: {stderr}")

            logger.info("Bob CLI executed successfully")
            logger.debug(f"Bob CLI output: {result.stdout[:200]}...")  # Log first 200 chars
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            logger.error(f"Bob CLI timed out after {self.timeout_seconds} seconds")
            raise RuntimeError(f"Bob CLI timed out after {self.timeout_seconds} seconds. Consider using OpenAI fallback.")
        except FileNotFoundError:
            logger.error(f"Bob CLI command '{self.bob_command}' not found")
            raise RuntimeError(f"Bob CLI command '{self.bob_command}' not found. Ensure Bob is installed or use OpenAI fallback.")
        except Exception as e:
            logger.error(f"Unexpected error running Bob CLI: {str(e)}")
            raise

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
        logger.info("Starting error analysis with Bob CLI")
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

        try:
            result = self._parse_json_response(await self._run_bob(prompt))
            logger.info(f"Error analysis completed: error_type={result.get('error_type')}, fixable={result.get('fixable')}")
            return result
        except Exception as e:
            logger.error(f"Error analysis failed: {str(e)}")
            raise

    async def generate_fix(self, error_analysis: Dict[str, Any], code_context: str) -> Dict[str, Any]:
        """Generate a code fix using Bob CLI and return structured JSON."""
        logger.info(f"Starting fix generation for error_type={error_analysis.get('error_type')}")
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

        try:
            result = self._parse_json_response(await self._run_bob(prompt))
            logger.info("Fix generation completed successfully")
            return result
        except Exception as e:
            logger.error(f"Fix generation failed: {str(e)}")
            raise


# Made with Bob