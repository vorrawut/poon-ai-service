"""Llama client for Ollama integration."""

from __future__ import annotations

from typing import Any

import aiohttp
import structlog

logger = structlog.get_logger(__name__)


class LlamaClient:
    """Client for interacting with Ollama/Llama API."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2:3b",
        timeout: int = 30,
    ) -> None:
        """Initialize Llama client."""
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def health_check(self) -> bool:
        """Check if Ollama service is available."""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/tags") as response:
                return response.status == 200
        except Exception as e:
            logger.debug("Ollama health check failed", error=str(e))
            return False

    async def generate_completion(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Generate text completion using Llama model."""
        try:
            session = await self._get_session()

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                },
            }

            if system_prompt:
                payload["system"] = system_prompt

            if max_tokens:
                payload["options"]["num_predict"] = max_tokens

            async with session.post(
                f"{self.base_url}/api/generate", json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(
                        "Llama API error", status=response.status, error=error_text
                    )
                    return {
                        "success": False,
                        "error": f"API error: {response.status}",
                        "response": None,
                    }

                result = await response.json()

                return {
                    "success": True,
                    "response": result.get("response", ""),
                    "model": result.get("model"),
                    "total_duration": result.get("total_duration"),
                    "load_duration": result.get("load_duration"),
                    "prompt_eval_count": result.get("prompt_eval_count"),
                    "eval_count": result.get("eval_count"),
                }

        except TimeoutError:
            logger.error("Llama API timeout", timeout=self.timeout)
            return {"success": False, "error": "Request timeout", "response": None}
        except Exception as e:
            logger.error("Llama API error", error=str(e))
            return {"success": False, "error": str(e), "response": None}

    async def parse_spending_text(
        self, text: str, language: str = "en", context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Parse spending text using Llama model."""

        system_prompt = """You are an AI assistant specialized in parsing spending transactions from natural language text.
Extract the following information from the input text and return ONLY a valid JSON object:

{
  "merchant": "merchant name",
  "amount": numeric_value,
  "currency": "THB|USD|EUR|etc",
  "category": "Food & Dining|Transportation|Shopping|etc",
  "subcategory": "optional subcategory",
  "payment_method": "Cash|Credit Card|Debit Card|PromptPay|etc",
  "description": "brief description",
  "location": "optional location",
  "confidence": 0.0-1.0
}

Rules:
- Return ONLY the JSON object, no other text
- Use standard category names
- Confidence should reflect how certain you are about the extraction
- If information is missing, use null or reasonable defaults
- For Thai text, understand common Thai spending terms"""

        user_prompt = f"""Parse this spending text: "{text}"

Language: {language}
Context: {context or {}}

Return the JSON object:"""

        result = await self.generate_completion(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.3,  # Lower temperature for more consistent parsing
            max_tokens=200,
        )

        if not result["success"]:
            return result

        try:
            import json

            response_text = result["response"].strip()

            # Try to extract JSON from response
            if response_text.startswith("```json"):
                response_text = (
                    response_text.replace("```json", "").replace("```", "").strip()
                )
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()

            parsed_data = json.loads(response_text)

            return {
                "success": True,
                "parsed_data": parsed_data,
                "raw_response": result["response"],
                "model": result["model"],
                "processing_time_ms": result.get("total_duration", 0) // 1_000_000,
            }

        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse Llama JSON response",
                error=str(e),
                response=result["response"],
            )
            return {
                "success": False,
                "error": f"Invalid JSON response: {e!s}",
                "raw_response": result["response"],
            }

    async def analyze_spending_patterns(
        self,
        spending_entries: list[dict[str, Any]],
        analysis_type: str = "comprehensive",
    ) -> dict[str, Any]:
        """Analyze spending patterns using Llama model."""

        system_prompt = """You are a financial analyst AI. Analyze the provided spending data and return insights as a JSON object:

{
  "insights": [
    {"category": "insight category", "message": "insight description", "severity": "low|medium|high"}
  ],
  "recommendations": [
    {"action": "recommended action", "reason": "explanation", "priority": "low|medium|high"}
  ],
  "patterns": {
    "top_categories": [{"category": "name", "amount": value, "percentage": value}],
    "spending_trends": "description of trends",
    "unusual_transactions": [{"merchant": "name", "amount": value, "reason": "why unusual"}]
  },
  "summary": {
    "total_amount": value,
    "transaction_count": value,
    "average_transaction": value,
    "most_frequent_category": "category name"
  }
}"""

        # Prepare spending data summary
        data_summary = {
            "total_entries": len(spending_entries),
            "entries": spending_entries[:20],  # Limit to avoid token limits
            "analysis_type": analysis_type,
        }

        user_prompt = f"""Analyze this spending data and provide insights:

{data_summary}

Return the JSON analysis:"""

        result = await self.generate_completion(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.5,
            max_tokens=800,
        )

        if not result["success"]:
            return result

        try:
            import json

            response_text = result["response"].strip()

            # Clean up response
            if response_text.startswith("```json"):
                response_text = (
                    response_text.replace("```json", "").replace("```", "").strip()
                )
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()

            analysis_data = json.loads(response_text)

            return {
                "success": True,
                "analysis": analysis_data,
                "raw_response": result["response"],
                "model": result["model"],
                "processing_time_ms": result.get("total_duration", 0) // 1_000_000,
            }

        except json.JSONDecodeError as e:
            logger.error("Failed to parse Llama analysis response", error=str(e))
            return {
                "success": False,
                "error": f"Invalid JSON response: {e!s}",
                "raw_response": result["response"],
            }
