"""
Llama4 Service for local AI processing
Connects to local Llama4 instance via Ollama
Cost-free alternative to OpenAI
"""

import asyncio
from datetime import datetime
import json
import logging
from typing import Any

import httpx

from models.spending_models import (
    AIAnalysis,
    NLPResult,
    OCRResult,
    SpendingEntry,
)

logger = logging.getLogger(__name__)


class LlamaService:
    """Local Llama4 service using Ollama"""

    def __init__(self, settings):
        self.settings = settings
        self.ollama_url = getattr(settings, "ollama_url", "http://localhost:11434")
        self.model = getattr(
            settings, "llama_model", "llama2"
        )  # Will be llama4 when available
        self.max_retries = 3
        self.request_timeout = 60  # Longer timeout for local models

    async def _check_ollama_connection(self) -> bool:
        """Check if Ollama service is running"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama connection check failed: {e!s}")
            return False

    async def _call_llama(self, prompt: str, system_prompt: str = None) -> str:
        """Make API call to local Llama via Ollama"""
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.request_timeout) as client:
                    payload = {
                        "model": self.model,
                        "prompt": prompt,
                        "system": system_prompt
                        or "You are a helpful financial assistant. Always respond with valid JSON.",
                        "stream": False,
                        "options": {"temperature": 0.1, "top_p": 0.9, "top_k": 40},
                    }

                    response = await client.post(
                        f"{self.ollama_url}/api/generate", json=payload
                    )

                    if response.status_code == 200:
                        result = response.json()
                        return result.get("response", "").strip()
                    else:
                        logger.error(
                            f"Llama API error: {response.status_code} - {response.text}"
                        )

            except asyncio.TimeoutError:
                logger.warning(
                    f"Llama request timeout, attempt {attempt + 1}/{self.max_retries}"
                )
                if attempt == self.max_retries - 1:
                    raise Exception("Llama request timeout after all retries")
                await asyncio.sleep(2**attempt)  # Exponential backoff

            except Exception as e:
                logger.error(f"Llama API error on attempt {attempt + 1}: {e!s}")
                if attempt == self.max_retries - 1:
                    raise Exception(f"Llama API failed: {e!s}")
                await asyncio.sleep(2**attempt)

        raise Exception("Llama API failed after all retries")

    async def enhance_nlp_result(
        self, text: str, nlp_result: NLPResult, language: str = "en"
    ) -> NLPResult:
        """
        Enhance NLP result using local Llama4
        """
        try:
            logger.info("🦙 Enhancing NLP result with Llama4...")

            if not await self._check_ollama_connection():
                logger.error("Ollama service not available")
                return nlp_result

            system_prompt = """You are an expert at parsing financial transaction text.
            Extract and correct spending information from the given text.
            Always respond with valid JSON only."""

            prompt = self._create_nlp_enhancement_prompt(text, nlp_result, language)

            response = await self._call_llama(prompt, system_prompt)
            enhanced_data = self._parse_llama_response(response)

            # Merge with existing result, Llama takes precedence for missing fields
            enhanced_result = NLPResult(
                merchant=enhanced_data.get("merchant") or nlp_result.merchant,
                amount=enhanced_data.get("amount") or nlp_result.amount,
                category=enhanced_data.get("category") or nlp_result.category,
                subcategory=enhanced_data.get("subcategory") or nlp_result.subcategory,
                date=enhanced_data.get("date") or nlp_result.date,
                payment_method=enhanced_data.get("payment_method")
                or nlp_result.payment_method,
                description=enhanced_data.get("description") or nlp_result.description,
                confidence=max(0.85, nlp_result.confidence + 0.2),  # Llama boost
                reasoning=enhanced_data.get("reasoning", "Llama4 enhanced"),
                extraction_details={
                    **nlp_result.extraction_details,
                    "llama_enhanced": True,
                    "llama_model": self.model,
                },
            )

            logger.info(
                f"✅ Llama4 enhancement completed, confidence boosted to {enhanced_result.confidence:.2f}"
            )
            return enhanced_result

        except Exception as e:
            logger.error(f"❌ Llama4 enhancement failed: {e!s}")
            # Return original result if Llama fails
            return nlp_result

    async def create_spending_entry(
        self, ocr_result: OCRResult, nlp_result: NLPResult, language: str = "en"
    ) -> NLPResult:
        """
        Create comprehensive spending entry using OCR + NLP + Llama4
        """
        try:
            logger.info("🧠 Creating spending entry with Llama4 analysis...")

            if not await self._check_ollama_connection():
                logger.error("Ollama service not available")
                return nlp_result

            system_prompt = """You are a financial data extraction expert.
            Analyze OCR text and NLP results to create accurate spending entries.
            Always respond with valid JSON only."""

            prompt = self._create_comprehensive_prompt(ocr_result, nlp_result, language)

            response = await self._call_llama(prompt, system_prompt)
            llama_data = self._parse_llama_response(response)

            # Create enhanced result
            enhanced_result = NLPResult(
                merchant=llama_data.get("merchant", "Llama Processed Entry"),
                amount=llama_data.get("amount", 0.0),
                category=llama_data.get("category", "Miscellaneous"),
                subcategory=llama_data.get("subcategory"),
                date=llama_data.get("date", datetime.utcnow()),
                payment_method=llama_data.get("payment_method"),
                description=llama_data.get("description", "Llama processed receipt"),
                confidence=0.9,  # High confidence for Llama processing
                reasoning=llama_data.get("reasoning", "Comprehensive Llama4 analysis"),
                extraction_details={
                    "llama_processed": True,
                    "ocr_confidence": ocr_result.confidence,
                    "nlp_confidence": nlp_result.confidence,
                    "llama_model": self.model,
                },
            )

            logger.info("✅ Llama4 spending entry created successfully")
            return enhanced_result

        except Exception as e:
            logger.error(f"❌ Llama4 spending entry creation failed: {e!s}")
            # Fallback to NLP result
            return nlp_result

    async def enhance_text_parsing(
        self,
        text: str,
        nlp_result: NLPResult,
        language: str = "en",
        context: dict[str, Any] = None,
    ) -> NLPResult:
        """
        Enhanced text parsing for voice/chat input using Llama4
        """
        try:
            logger.info("💬 Enhancing text parsing with Llama4...")

            if not await self._check_ollama_connection():
                logger.error("Ollama service not available")
                return nlp_result

            system_prompt = """You are a natural language processing expert for financial transactions.
            Parse natural language spending descriptions into structured data.
            Always respond with valid JSON only."""

            prompt = self._create_text_parsing_prompt(
                text, nlp_result, language, context
            )

            response = await self._call_llama(prompt, system_prompt)
            llama_data = self._parse_llama_response(response)

            enhanced_result = NLPResult(
                merchant=llama_data.get("merchant")
                or nlp_result.merchant
                or "Voice/Chat Entry",
                amount=llama_data.get("amount") or nlp_result.amount or 0.0,
                category=llama_data.get("category")
                or nlp_result.category
                or "Miscellaneous",
                subcategory=llama_data.get("subcategory") or nlp_result.subcategory,
                date=llama_data.get("date") or nlp_result.date or datetime.utcnow(),
                payment_method=llama_data.get("payment_method")
                or nlp_result.payment_method,
                description=llama_data.get("description") or text[:100],
                confidence=0.88,
                reasoning=llama_data.get("reasoning", "Llama4 enhanced text parsing"),
                extraction_details={
                    **nlp_result.extraction_details,
                    "llama_text_enhanced": True,
                    "original_text": text,
                },
            )

            logger.info("✅ Text parsing enhancement completed with Llama4")
            return enhanced_result

        except Exception as e:
            logger.error(f"❌ Text parsing enhancement failed: {e!s}")
            return nlp_result

    async def analyze_spending_patterns(
        self, entries: list[SpendingEntry], analysis_type: str = "comprehensive"
    ) -> AIAnalysis:
        """
        Llama4-powered spending pattern analysis
        """
        try:
            logger.info(f"📊 Analyzing {len(entries)} spending entries with Llama4...")

            if not await self._check_ollama_connection():
                raise Exception("Ollama service not available")

            # Prepare data for analysis
            spending_summary = self._prepare_spending_summary(entries)

            system_prompt = """You are a financial advisor and data analyst.
            Analyze spending patterns and provide actionable insights.
            Always respond with valid JSON only."""

            prompt = self._create_analysis_prompt(spending_summary, analysis_type)

            response = await self._call_llama(prompt, system_prompt)
            analysis_data = self._parse_analysis_response(response)

            analysis = AIAnalysis(
                total_entries=len(entries),
                analysis_type=analysis_type,
                insights=analysis_data.get("insights", []),
                recommendations=analysis_data.get("recommendations", []),
                patterns=analysis_data.get("patterns", {}),
                anomalies=analysis_data.get("anomalies", []),
                confidence=0.85,
                created_at=datetime.utcnow(),
            )

            logger.info("✅ Spending analysis completed with Llama4")
            return analysis

        except Exception as e:
            logger.error(f"❌ Spending analysis failed: {e!s}")
            raise Exception(f"Llama4 analysis failed: {e!s}")

    def _create_nlp_enhancement_prompt(
        self, text: str, nlp_result: NLPResult, language: str
    ) -> str:
        """Create prompt for NLP enhancement"""
        return f"""
        Analyze this spending text and extract structured information. The local NLP system had low confidence.

        Text: "{text}"
        Language: {language}

        Current extraction (low confidence):
        - Merchant: {nlp_result.merchant or 'Not found'}
        - Amount: {nlp_result.amount or 'Not found'}
        - Category: {nlp_result.category or 'Not found'}
        - Payment Method: {nlp_result.payment_method or 'Not found'}

        Please extract and correct:
        1. Merchant/Store name (clean and normalize)
        2. Amount in numbers (remove currency symbols)
        3. Most appropriate category from: Food & Dining, Transportation, Groceries, Shopping, Entertainment, Healthcare, Bills & Services, Travel, Education, Miscellaneous
        4. Subcategory if applicable
        5. Payment method: Cash, Credit Card, Debit Card, Bank Transfer, PromptPay, Mobile Banking, Digital Wallet, Other
        6. Brief reasoning for your decisions

        Return JSON format only:
        {{"merchant": "...", "amount": 0.00, "category": "...", "subcategory": "...", "payment_method": "...", "description": "...", "reasoning": "..."}}
        """

    def _create_comprehensive_prompt(
        self, ocr_result: OCRResult, nlp_result: NLPResult, language: str
    ) -> str:
        """Create comprehensive analysis prompt"""
        return f"""
        Analyze this receipt using OCR text and NLP results to create a complete spending entry.

        OCR Text (confidence: {ocr_result.confidence:.2f}):
        "{ocr_result.text}"

        NLP Results (confidence: {nlp_result.confidence:.2f}):
        - Merchant: {nlp_result.merchant}
        - Amount: {nlp_result.amount}
        - Category: {nlp_result.category}
        - Payment Method: {nlp_result.payment_method}

        Please provide the most accurate extraction by combining both sources:
        1. Merchant name (clean and standardized)
        2. Total amount (look for "total", "รวม", or final amount)
        3. Best category from: Food & Dining, Transportation, Groceries, Shopping, Entertainment, Healthcare, Bills & Services, Travel, Education, Miscellaneous
        4. Subcategory if clear from context
        5. Payment method if mentioned
        6. Transaction date if found
        7. Brief description
        8. Your reasoning process

        Return JSON format:
        {{"merchant": "...", "amount": 0.00, "category": "...", "subcategory": "...", "payment_method": "...", "date": "YYYY-MM-DD", "description": "...", "reasoning": "..."}}
        """

    def _create_text_parsing_prompt(
        self,
        text: str,
        nlp_result: NLPResult,
        language: str,
        context: dict[str, Any] = None,
    ) -> str:
        """Create text parsing prompt for voice/chat"""
        context_info = ""
        if context:
            context_info = f"\nAdditional context: {json.dumps(context)}"

        return f"""
        Parse this natural language spending description into structured data:

        Text: "{text}"
        Language: {language}{context_info}

        Current NLP extraction:
        - Merchant: {nlp_result.merchant}
        - Amount: {nlp_result.amount}
        - Category: {nlp_result.category}

        Please extract:
        1. Merchant/business name
        2. Amount spent (numbers only)
        3. Most suitable category
        4. Payment method if mentioned
        5. When it happened (relative to today)
        6. Clean description

        Examples of good parsing:
        "Coffee at Starbucks 120 baht by card" → Merchant: Starbucks, Amount: 120, Category: Food & Dining, Payment: Credit Card
        "ซื้อข้าว 50 บาท เงินสด" → Merchant: Restaurant, Amount: 50, Category: Food & Dining, Payment: Cash

        Return JSON:
        {{"merchant": "...", "amount": 0.00, "category": "...", "payment_method": "...", "date": "YYYY-MM-DD", "description": "...", "reasoning": "..."}}
        """

    def _create_analysis_prompt(
        self, spending_summary: dict[str, Any], analysis_type: str
    ) -> str:
        """Create spending analysis prompt"""
        return f"""
        Analyze these spending patterns and provide insights:

        Spending Summary:
        {json.dumps(spending_summary, indent=2)}

        Analysis Type: {analysis_type}

        Please provide:
        1. Key insights about spending patterns
        2. Actionable recommendations for better financial health
        3. Detected patterns (weekly, monthly, category-based)
        4. Any anomalies or unusual spending
        5. Opportunities for savings

        Focus on practical, actionable advice that helps users improve their financial habits.

        Return JSON format:
        {{
            "insights": [
                {{"title": "...", "description": "...", "impact": "high/medium/low"}},
                ...
            ],
            "recommendations": [
                {{"action": "...", "reason": "...", "potential_savings": 0.00}},
                ...
            ],
            "patterns": {{
                "weekly": "...",
                "monthly": "...",
                "categories": "..."
            }},
            "anomalies": [
                {{"description": "...", "amount": 0.00, "date": "..."}},
                ...
            ]
        }}
        """

    def _prepare_spending_summary(self, entries: list[SpendingEntry]) -> dict[str, Any]:
        """Prepare spending data summary for analysis"""
        total_amount = sum(entry.amount for entry in entries)

        # Group by category
        categories = {}
        for entry in entries:
            cat = entry.category
            if cat not in categories:
                categories[cat] = {"count": 0, "total": 0.0, "avg": 0.0}
            categories[cat]["count"] += 1
            categories[cat]["total"] += entry.amount

        for cat in categories:
            categories[cat]["avg"] = categories[cat]["total"] / categories[cat]["count"]

        # Group by merchant
        merchants = {}
        for entry in entries:
            merchant = entry.merchant
            if merchant not in merchants:
                merchants[merchant] = {"count": 0, "total": 0.0}
            merchants[merchant]["count"] += 1
            merchants[merchant]["total"] += entry.amount

        return {
            "total_entries": len(entries),
            "total_amount": total_amount,
            "average_transaction": total_amount / len(entries) if entries else 0,
            "categories": categories,
            "top_merchants": dict(
                sorted(merchants.items(), key=lambda x: x[1]["total"], reverse=True)[
                    :10
                ]
            ),
            "date_range": {
                "start": min(entry.date for entry in entries).isoformat()
                if entries
                else None,
                "end": max(entry.date for entry in entries).isoformat()
                if entries
                else None,
            },
        }

    def _parse_llama_response(self, response: str) -> dict[str, Any]:
        """Parse Llama response JSON"""
        try:
            # Clean response (remove markdown code blocks if present)
            if response.startswith("```json"):
                response = response[7:-3]
            elif response.startswith("```"):
                response = response[3:-3]

            # Try to extract JSON from response
            import re

            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                response = json_match.group()

            return json.loads(response)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Llama response as JSON: {e!s}")
            logger.debug(f"Raw response: {response}")
            return {}

    def _parse_analysis_response(self, response: str) -> dict[str, Any]:
        """Parse analysis response with fallback"""
        try:
            return self._parse_llama_response(response)
        except Exception as e:
            logger.error(f"Failed to parse analysis response: {e!s}")
            return {
                "insights": [
                    {
                        "title": "Analysis Error",
                        "description": "Failed to parse Llama response",
                        "impact": "low",
                    }
                ],
                "recommendations": [],
                "patterns": {},
                "anomalies": [],
            }

    async def get_model_info(self) -> dict[str, Any]:
        """Get information about the current Llama model"""
        try:
            if not await self._check_ollama_connection():
                return {"error": "Ollama service not available"}

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    current_model = next(
                        (m for m in models if m["name"].startswith(self.model)), None
                    )
                    return {
                        "model": self.model,
                        "available": current_model is not None,
                        "details": current_model,
                        "all_models": [m["name"] for m in models],
                    }
                else:
                    return {
                        "error": f"Failed to get model info: {response.status_code}"
                    }
        except Exception as e:
            return {"error": f"Failed to get model info: {e!s}"}
