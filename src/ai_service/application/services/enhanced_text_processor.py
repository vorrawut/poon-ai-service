"""Enhanced text processing service for ultra-fast and accurate spending analysis."""

from __future__ import annotations

import asyncio
import re
from datetime import datetime
from typing import Any

import structlog

from ...domain.value_objects.spending_category import SpendingCategory
from ...infrastructure.external_apis.llama_client import LlamaClient
from .intelligent_cache_service import get_intelligent_cache
from .intelligent_mapping_service import IntelligentMappingService

logger = structlog.get_logger(__name__)


class SpendingPattern:
    """Represents a spending pattern with extraction rules."""

    def __init__(
        self,
        name: str,
        pattern: str,
        category: str,
        confidence: float,
        extract_amount: callable,
        extract_merchant: callable | None = None,
        extract_description: callable | None = None,
        extract_payment_method: callable | None = None,
    ) -> None:
        """Initialize spending pattern."""
        self.name = name
        self.pattern = re.compile(pattern, re.IGNORECASE | re.UNICODE)
        self.category = category
        self.confidence = confidence
        self.extract_amount = extract_amount
        self.extract_merchant = extract_merchant
        self.extract_description = extract_description
        self.extract_payment_method = extract_payment_method


class EnhancedTextProcessor:
    """Ultra-fast and accurate text processing for spending entries."""

    def __init__(
        self,
        llama_client: LlamaClient | None = None,
        mapping_service: IntelligentMappingService | None = None,
    ) -> None:
        """Initialize enhanced text processor."""
        self._llama_client = llama_client
        self._mapping_service = mapping_service
        self._patterns = self._initialize_patterns()
        self._intelligent_cache = get_intelligent_cache()

        # Warm cache on first initialization
        if not hasattr(self._intelligent_cache, "_warmed"):
            self._intelligent_cache.warm_cache_with_common_patterns()
            self._intelligent_cache._warmed = True

    def _initialize_patterns(self) -> list[SpendingPattern]:
        """Initialize comprehensive spending patterns for Thai and English."""
        patterns = []

        # Thai patterns - Enhanced with comprehensive coverage
        patterns.extend(
            [
                # Food & Dining patterns - Enhanced
                SpendingPattern(
                    name="thai_restaurant",
                    pattern=r"(?:กิน|ทาน|อาหาร|ร้าน|เสวย|สั่ง|ไป)(?:ที่|ใน|@|กับ|ด้วย)?\s*([^0-9]+?)\s*(\d+(?:\.\d+)?)\s*(?:บาท|THB|฿)",
                    category="Food & Dining",
                    confidence=0.9,
                    extract_amount=lambda m: float(m.group(2)),
                    extract_merchant=lambda m: m.group(1).strip(),
                    extract_description=lambda m: f"ทานอาหารที่ {m.group(1).strip()}",
                ),
                SpendingPattern(
                    name="thai_coffee",
                    pattern=r"(?:กาแฟ|coffee|คอฟฟี่|เครื่องดื่ม|ชา|น้ำ|สตาร์บัคส์|starbucks)(?:ที่|ใน|@)?\s*([^0-9]*?)\s*(\d+(?:\.\d+)?)\s*(?:บาท|THB|฿)",
                    category="Food & Dining",
                    confidence=0.85,
                    extract_amount=lambda m: float(m.group(2)),
                    extract_merchant=lambda m: m.group(1).strip() or "ร้านกาแฟ",
                    extract_description=lambda _m: "ซื้อเครื่องดื่ม",
                ),
                SpendingPattern(
                    name="thai_food_delivery",
                    pattern=r"(?:สั่ง|delivery|เดลิเวอรี่|foodpanda|grab\s*food|lineman)(?:ที่|จาก)?\s*([^0-9]+?)\s*(\d+(?:\.\d+)?)\s*(?:บาท|THB|฿)",
                    category="Food & Dining",
                    confidence=0.9,
                    extract_amount=lambda m: float(m.group(2)),
                    extract_merchant=lambda m: m.group(1).strip(),
                    extract_description=lambda m: f"สั่งอาหารจาก {m.group(1).strip()}",
                ),
                # Transportation patterns
                SpendingPattern(
                    name="thai_transport",
                    pattern=r"(?:แท็กซี่|taxi|รถไฟ|BTS|MRT|รถเมล์|รถประจำทาง|รถตู้|มอเตอร์ไซค์|วิน|grab|bolt)\s*(\d+(?:\.\d+)?)\s*(?:บาท|THB|฿)",
                    category="Transportation",
                    confidence=0.9,
                    extract_amount=lambda m: float(m.group(1)),
                    extract_merchant=lambda _m: "การเดินทาง",
                    extract_description=lambda _m: "ค่าเดินทาง",
                ),
                # Shopping patterns
                SpendingPattern(
                    name="thai_shopping",
                    pattern=r"(?:ซื้อ|shopping|ช้อป|ช้อปปิ้ง)(?:ที่|ใน|@)?\s*([^0-9]+?)\s*(\d+(?:\.\d+)?)\s*(?:บาท|THB|฿)",
                    category="Shopping",
                    confidence=0.8,
                    extract_amount=lambda m: float(m.group(2)),
                    extract_merchant=lambda m: m.group(1).strip(),
                    extract_description=lambda m: f"ซื้อของที่ {m.group(1).strip()}",
                ),
                # Travel & Accommodation patterns - Enhanced
                SpendingPattern(
                    name="thai_hotel",
                    pattern=r"(?:โรงแรม|hotel|ที่พัก|รีสอร์ท|resort|จอง)(?:ที่|ใน|@)?\s*([^0-9]+?)\s*(?:(\d+)\s*คืน)?\s*(\d+(?:\.\d+)?)\s*(?:บาท|THB|฿)",
                    category="Travel",
                    confidence=0.95,
                    extract_amount=lambda m: float(m.group(3)),
                    extract_merchant=lambda m: m.group(1).strip(),
                    extract_description=lambda m: f"จองโรงแรม {m.group(1).strip()}"
                    + (f" {m.group(2)} คืน" if m.group(2) else ""),
                ),
                SpendingPattern(
                    name="thai_booking_pattern",
                    pattern=r"จอง(?:โรงแรม|ที่พัก|hotel)(?:ที่|ใน)?\s*([^0-9]+?)\s*(?:(\d+)\s*คืน)?\s*(\d+(?:\.\d+)?)\s*(?:บาท|THB|฿)(?:.*?(?:ด้วย|กับ|ผ่าน)\s*(บัตรเครดิต|เงินสด|credit\s*card|cash))?",
                    category="Travel",
                    confidence=0.95,
                    extract_amount=lambda m: float(m.group(3)),
                    extract_merchant=lambda m: m.group(1).strip(),
                    extract_description=lambda m: f"จองโรงแรมที่ {m.group(1).strip()}"
                    + (f" {m.group(2)} คืน" if m.group(2) else ""),
                    extract_payment_method=lambda m: "Credit Card"
                    if m.group(4)
                    and ("บัตรเครดิต" in m.group(4) or "credit" in m.group(4).lower())
                    else "Cash",
                ),
                # Groceries patterns
                SpendingPattern(
                    name="thai_groceries",
                    pattern=r"(?:ตลาด|supermarket|ซุปเปอร์|เซเว่น|7-11|เทสโก้|บิ๊กซี|ท็อปส์|แม็คโคร)(?:ที่|ใน|@)?\s*([^0-9]*?)\s*(\d+(?:\.\d+)?)\s*(?:บาท|THB|฿)",
                    category="Groceries",
                    confidence=0.9,
                    extract_amount=lambda m: float(m.group(2)),
                    extract_merchant=lambda m: m.group(1).strip() or "ซุปเปอร์มาร์เก็ต",
                    extract_description=lambda _m: "ซื้อของใช้",
                ),
            ]
        )

        # English patterns
        patterns.extend(
            [
                # Food & Dining patterns
                SpendingPattern(
                    name="english_restaurant",
                    pattern=r"(?:eat|dine|lunch|dinner|meal|food)\s+(?:at|in|@)?\s*([^0-9]+?)\s*(\d+(?:\.\d+)?)\s*(?:baht|thb|฿|\$)",
                    category="Food & Dining",
                    confidence=0.9,
                    extract_amount=lambda m: float(m.group(2)),
                    extract_merchant=lambda m: m.group(1).strip(),
                    extract_description=lambda m: f"Meal at {m.group(1).strip()}",
                ),
                SpendingPattern(
                    name="english_coffee",
                    pattern=r"(?:coffee|starbucks|cafe|drink)\s+(?:at|in|@)?\s*([^0-9]*?)\s*(\d+(?:\.\d+)?)\s*(?:baht|thb|฿|\$)",
                    category="Food & Dining",
                    confidence=0.85,
                    extract_amount=lambda m: float(m.group(2)),
                    extract_merchant=lambda m: m.group(1).strip() or "Coffee Shop",
                    extract_description=lambda _m: "Coffee purchase",
                ),
                # Transportation patterns
                SpendingPattern(
                    name="english_transport",
                    pattern=r"(?:taxi|uber|grab|transport|bus|train|bts|mrt|motorcycle|bike)\s*(\d+(?:\.\d+)?)\s*(?:baht|thb|฿|\$)",
                    category="Transportation",
                    confidence=0.9,
                    extract_amount=lambda m: float(m.group(1)),
                    extract_merchant=lambda _m: "Transportation",
                    extract_description=lambda _m: "Transportation cost",
                ),
                # Shopping patterns
                SpendingPattern(
                    name="english_shopping",
                    pattern=r"(?:buy|purchase|shop|shopping)\s+(?:at|in|from)?\s*([^0-9]+?)\s*(\d+(?:\.\d+)?)\s*(?:baht|thb|฿|\$)",
                    category="Shopping",
                    confidence=0.8,
                    extract_amount=lambda m: float(m.group(2)),
                    extract_merchant=lambda m: m.group(1).strip(),
                    extract_description=lambda m: f"Purchase from {m.group(1).strip()}",
                ),
                # Travel & Accommodation patterns
                SpendingPattern(
                    name="english_hotel",
                    pattern=r"(?:hotel|accommodation|resort|booking)\s+(?:at|in)?\s*([^0-9]+?)\s*(?:(\d+)\s*nights?)?\s*(\d+(?:\.\d+)?)\s*(?:baht|thb|฿|\$)",
                    category="Travel",
                    confidence=0.95,
                    extract_amount=lambda m: float(m.group(3)),
                    extract_merchant=lambda m: m.group(1).strip(),
                    extract_description=lambda m: f"Hotel booking at {m.group(1).strip()}"
                    + (f" for {m.group(2)} nights" if m.group(2) else ""),
                ),
                # Groceries patterns
                SpendingPattern(
                    name="english_groceries",
                    pattern=r"(?:grocery|groceries|supermarket|7-eleven|tesco|big\s*c|tops|makro)\s+(?:at|in)?\s*([^0-9]*?)\s*(\d+(?:\.\d+)?)\s*(?:baht|thb|฿|\$)",
                    category="Groceries",
                    confidence=0.9,
                    extract_amount=lambda m: float(m.group(2)),
                    extract_merchant=lambda m: m.group(1).strip() or "Supermarket",
                    extract_description=lambda _m: "Grocery shopping",
                ),
            ]
        )

        # Edge case patterns for better coverage
        patterns.extend(
            [
                # Payment method specific patterns
                SpendingPattern(
                    name="credit_card_payment",
                    pattern=r"(?:บัตรเครดิต|credit\s*card|card).*?(\d+(?:\.\d+)?)\s*(?:บาท|THB|฿)",
                    category="Miscellaneous",
                    confidence=0.7,
                    extract_amount=lambda m: float(m.group(1)),
                    extract_merchant=lambda _m: "ไม่ระบุ",
                    extract_description=lambda m: f"จ่ายด้วยบัตรเครดิต {m.group(1)} บาท",
                    extract_payment_method=lambda _m: "Credit Card",
                ),
                SpendingPattern(
                    name="cash_payment",
                    pattern=r"(?:เงินสด|cash).*?(\d+(?:\.\d+)?)\s*(?:บาท|THB|฿)",
                    category="Miscellaneous",
                    confidence=0.7,
                    extract_amount=lambda m: float(m.group(1)),
                    extract_merchant=lambda _m: "ไม่ระบุ",
                    extract_description=lambda m: f"จ่ายเงินสด {m.group(1)} บาท",
                    extract_payment_method=lambda _m: "Cash",
                ),
                # Cost/fee patterns
                SpendingPattern(
                    name="thai_cost_pattern",
                    pattern=r"ค่า([^0-9]+?)\s*(\d+(?:\.\d+)?)\s*(?:บาท|THB|฿)",
                    category="Miscellaneous",
                    confidence=0.8,
                    extract_amount=lambda m: float(m.group(2)),
                    extract_merchant=lambda m: m.group(1).strip(),
                    extract_description=lambda m: f"ค่า{m.group(1).strip()}",
                ),
                # Amount with location patterns
                SpendingPattern(
                    name="amount_at_location",
                    pattern=r"(\d+(?:\.\d+)?)\s*(?:บาท|THB|฿)(?:ที่|@|at)\s*([^0-9\n]+)",
                    category="Miscellaneous",
                    confidence=0.6,
                    extract_amount=lambda m: float(m.group(1)),
                    extract_merchant=lambda m: m.group(2).strip(),
                    extract_description=lambda m: f"รายจ่าย {m.group(1)} บาท ที่ {m.group(2).strip()}",
                ),
            ]
        )

        # Generic amount patterns (final fallback)
        patterns.extend(
            [
                SpendingPattern(
                    name="generic_amount_thai",
                    pattern=r"(\d+(?:\.\d+)?)\s*(?:บาท|THB|฿)",
                    category="Miscellaneous",
                    confidence=0.4,
                    extract_amount=lambda m: float(m.group(1)),
                    extract_merchant=lambda _m: "ไม่ระบุ",
                    extract_description=lambda m: f"รายจ่าย {m.group(1)} บาท",
                ),
                SpendingPattern(
                    name="generic_amount_english",
                    pattern=r"(\d+(?:\.\d+)?)\s*(?:baht|thb|฿|\$)",
                    category="Miscellaneous",
                    confidence=0.4,
                    extract_amount=lambda m: float(m.group(1)),
                    extract_merchant=lambda _m: "Unknown",
                    extract_description=lambda m: f"Expense {m.group(1)} THB",
                ),
            ]
        )

        return patterns

    async def process_text_fast(
        self, text: str, language: str = "auto"
    ) -> dict[str, Any]:
        """Process text with ultra-fast pattern matching and AI fallback."""
        start_time = datetime.utcnow()

        try:
            # Check intelligent cache first (fastest path)
            cached_result = self._intelligent_cache.get_cached_result(text, language)
            if cached_result:
                processing_time = (
                    datetime.utcnow() - start_time
                ).total_seconds() * 1000
                cached_result["processing_time_ms"] = processing_time
                cached_result[
                    "method"
                ] = f"cache_{cached_result.get('method', 'direct')}"
                logger.info(
                    f"⚡ Cache hit: {processing_time:.0f}ms for {len(text)} chars"
                )
                return cached_result

            # Clean and normalize text
            cleaned_text = self._clean_text(text)

            # Try pattern matching first (fastest)
            pattern_result = await self._try_pattern_matching(cleaned_text, language)
            if pattern_result and pattern_result["confidence"] > 0.7:
                processing_time = (
                    datetime.utcnow() - start_time
                ).total_seconds() * 1000
                result = {
                    **pattern_result,
                    "processing_time_ms": processing_time,
                    "method": "pattern",
                }
                self._intelligent_cache.cache_result(text, language, result)
                logger.info(f"🎯 Pattern matching success: {processing_time:.0f}ms")
                return result

            # Fallback to AI processing with timeout
            if self._llama_client:
                ai_result = await asyncio.wait_for(
                    self._try_ai_processing(cleaned_text, language),
                    timeout=2.0,  # 2 second timeout for AI
                )
                if ai_result and ai_result["confidence"] > 0.6:
                    processing_time = (
                        datetime.utcnow() - start_time
                    ).total_seconds() * 1000
                    result = {
                        **ai_result,
                        "processing_time_ms": processing_time,
                        "method": "ai",
                    }
                    self._intelligent_cache.cache_result(text, language, result)
                    logger.info(f"🤖 AI processing success: {processing_time:.0f}ms")
                    return result

            # Final fallback - extract basic info
            fallback_result = await self._fallback_processing(cleaned_text, language)
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result = {
                **fallback_result,
                "processing_time_ms": processing_time,
                "method": "fallback",
            }

            # Cache fallback results too (they might be useful for similar texts)
            if result.get("confidence", 0) > 0.2:
                self._intelligent_cache.cache_result(text, language, result)

            logger.info(f"🔄 Fallback processing: {processing_time:.0f}ms")
            return result

        except TimeoutError:
            logger.warning("AI processing timeout, using fallback")
            fallback_result = await self._fallback_processing(text, language)
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return {
                **fallback_result,
                "processing_time_ms": processing_time,
                "method": "timeout_fallback",
            }

        except Exception as e:
            logger.error(f"Text processing error: {e}")
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return {
                "amount": 0.0,
                "currency": "THB",
                "merchant": "Error",
                "category": "Miscellaneous",
                "payment_method": "Cash",
                "description": text[:100],
                "confidence": 0.1,
                "processing_time_ms": processing_time,
                "method": "error",
                "error": str(e),
            }

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for processing."""
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text.strip())

        # Normalize currency symbols
        text = text.replace("฿", " บาท")
        text = text.replace("$", " dollar")

        # Normalize common Thai words
        text = re.sub(r"(?:จ่าย|pay|paid)", "จ่าย", text, flags=re.IGNORECASE)
        text = re.sub(r"(?:ซื้อ|buy|bought)", "ซื้อ", text, flags=re.IGNORECASE)

        return text

    async def _try_pattern_matching(
        self, text: str, language: str
    ) -> dict[str, Any] | None:
        """Try to match text against predefined patterns."""
        best_match = None
        best_confidence = 0.0

        for pattern in self._patterns:
            match = pattern.pattern.search(text)
            if match:
                try:
                    amount = pattern.extract_amount(match)
                    if amount <= 0:
                        continue

                    merchant = (
                        pattern.extract_merchant(match)
                        if pattern.extract_merchant
                        else "Unknown"
                    )
                    description = (
                        pattern.extract_description(match)
                        if pattern.extract_description
                        else text[:100]
                    )

                    # Boost confidence for language match
                    confidence = pattern.confidence
                    if (language == "th" and "thai" in pattern.name) or (
                        language == "en" and "english" in pattern.name
                    ):
                        confidence += 0.1

                    if confidence > best_confidence:
                        best_confidence = confidence

                        # Use pattern-specific payment method extraction if available
                        payment_method = (
                            pattern.extract_payment_method(match)
                            if pattern.extract_payment_method
                            else self._infer_payment_method(text)
                        )

                        best_match = {
                            "amount": amount,
                            "currency": "THB",
                            "merchant": merchant.strip(),
                            "category": pattern.category,
                            "payment_method": payment_method,
                            "description": description.strip(),
                            "confidence": confidence,
                            "pattern_name": pattern.name,
                        }

                except (ValueError, AttributeError, IndexError) as e:
                    logger.debug(f"Pattern {pattern.name} extraction failed: {e}")
                    continue

        return best_match

    async def _try_ai_processing(
        self, text: str, language: str
    ) -> dict[str, Any] | None:
        """Try AI processing with optimized prompts."""
        try:
            # Use optimized prompt for faster processing
            if language == "th":
                pass
            else:
                pass

            result = await self._llama_client.parse_spending_text(text, language)

            if result and isinstance(result, dict):
                # Validate and clean AI result
                return await self._validate_ai_result(result, text, language)

        except Exception as e:
            logger.warning(f"AI processing failed: {e}")

        return None

    async def _validate_ai_result(
        self, result: dict[str, Any], original_text: str, language: str = "en"
    ) -> dict[str, Any]:
        """Validate and clean AI processing result."""
        try:
            # Ensure required fields
            amount = float(result.get("amount", 0))
            if amount <= 0:
                return None

            currency = result.get("currency", "THB")
            merchant = str(result.get("merchant", "Unknown")).strip()
            category = result.get("category", "Miscellaneous")

            # Validate category using intelligent mapping
            valid_categories = [cat.value for cat in SpendingCategory]
            if category not in valid_categories:
                category = await self._map_category_intelligent(category, language)

            payment_method = result.get("payment_method") or self._infer_payment_method(
                original_text
            )
            description = str(result.get("description", original_text[:100])).strip()
            confidence = max(0.0, min(1.0, float(result.get("confidence", 0.7))))

            return {
                "amount": amount,
                "currency": currency,
                "merchant": merchant,
                "category": category,
                "payment_method": payment_method,
                "description": description,
                "confidence": confidence,
            }

        except (ValueError, TypeError, KeyError) as e:
            logger.warning(f"AI result validation failed: {e}")
            return None

    async def _fallback_processing(self, text: str, language: str) -> dict[str, Any]:
        """Enhanced fallback processing when patterns and AI fail."""
        # Extract potential amounts with better logic
        amount_patterns = [
            r"(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",  # Formatted numbers with commas
            r"(\d+\.\d{2})",  # Decimal amounts
            r"(\d{3,})",  # Large numbers (likely amounts)
            r"(\d+)",  # Any number as last resort
        ]

        amounts = []
        for pattern in amount_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    # Clean and convert amount
                    clean_amount = match.replace(",", "")
                    amount_val = float(clean_amount)
                    # Reasonable spending range
                    if 5 <= amount_val <= 500000:
                        amounts.append(amount_val)
                except (ValueError, TypeError):
                    continue
            if amounts:  # Use first successful pattern
                break

        amount = amounts[0] if amounts else 0.0

        # Enhanced category inference using intelligent mapping
        initial_category = self._infer_category_from_keywords(text, language)
        category = await self._map_category_intelligent(initial_category, language)

        # Enhanced merchant extraction
        merchant = self._extract_merchant_fallback(text, language)

        # Enhanced payment method inference
        payment_method = self._infer_payment_method(text)

        # Smart description generation
        description = self._generate_smart_description(
            text, language, category, merchant
        )

        # Confidence based on what we could extract
        confidence = 0.2  # Base confidence
        if amount > 0:
            confidence += 0.2
        if category != "Miscellaneous":
            confidence += 0.2
        if merchant not in ["Unknown", "ไม่ระบุ"]:
            confidence += 0.2
        if payment_method != "Cash":
            confidence += 0.1

        return {
            "amount": amount,
            "currency": "THB",
            "merchant": merchant,
            "category": category,
            "payment_method": payment_method,
            "description": description,
            "confidence": min(confidence, 0.9),  # Cap at 0.9 for fallback
            "method": "enhanced_fallback",
            "processing_time_ms": 50,  # Fast fallback
        }

    def _extract_merchant_fallback(self, text: str, language: str) -> str:
        """Extract merchant name from text using fallback logic."""
        # Common merchant patterns
        merchant_patterns = [
            r"(?:ที่|@|at)\s*([^0-9\n]+?)(?:\s*\d|\s*$)",  # "ที่ ร้านอาหาร"
            r"(?:จาก|from)\s*([^0-9\n]+?)(?:\s*\d|\s*$)",  # "จาก ร้านกาแฟ"
            r"([^0-9\n]+?)(?:\s*\d+\s*(?:บาท|THB|฿))",  # "ร้านอาหาร 100 บาท"
        ]

        for pattern in merchant_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                merchant = matches[0].strip()
                # Filter out common non-merchant words
                exclude_words = [
                    "จ่าย",
                    "ซื้อ",
                    "กิน",
                    "ทาน",
                    "paid",
                    "buy",
                    "eat",
                    "spent",
                ]
                if merchant and not any(
                    word in merchant.lower() for word in exclude_words
                ):
                    return merchant

        # Default fallback
        return "ไม่ระบุ" if language == "th" else "Unknown"

    def _generate_smart_description(
        self, text: str, language: str, category: str, merchant: str
    ) -> str:
        """Generate smart description based on extracted information."""
        text_clean = text[:100].strip()

        if language == "th":
            if category == "Food & Dining":
                return (
                    f"ทานอาหารที่ {merchant}"
                    if merchant != "ไม่ระบุ"
                    else f"ทานอาหาร: {text_clean}"
                )
            elif category == "Transportation":
                return f"ค่าเดินทาง: {text_clean}"
            elif category == "Travel":
                return f"ค่าเที่ยว: {text_clean}"
            elif category == "Shopping":
                return (
                    f"ซื้อของที่ {merchant}"
                    if merchant != "ไม่ระบุ"
                    else f"ซื้อของ: {text_clean}"
                )
            else:
                return f"รายจ่าย: {text_clean}"
        else:
            if category == "Food & Dining":
                return (
                    f"Meal at {merchant}"
                    if merchant != "Unknown"
                    else f"Food expense: {text_clean}"
                )
            elif category == "Transportation":
                return f"Transportation: {text_clean}"
            elif category == "Travel":
                return f"Travel expense: {text_clean}"
            elif category == "Shopping":
                return (
                    f"Shopping at {merchant}"
                    if merchant != "Unknown"
                    else f"Shopping: {text_clean}"
                )
            else:
                return f"Expense: {text_clean}"

    def _infer_payment_method(self, text: str) -> str:
        """Infer payment method from text."""
        text_lower = text.lower()

        if any(word in text_lower for word in ["credit", "เครดิต", "บัตร", "card"]):
            return "Credit Card"
        elif any(word in text_lower for word in ["cash", "เงินสด", "เงินสด"]):
            return "Cash"
        elif any(word in text_lower for word in ["transfer", "โอน", "mobile", "app"]):
            return "Bank Transfer"
        else:
            return "Cash"  # Default

    def _infer_category_from_keywords(self, text: str, _language: str) -> str:
        """Infer category from keywords in text."""
        text_lower = text.lower()

        # Food & Dining keywords
        food_keywords = [
            "กิน",
            "ทาน",
            "อาหาร",
            "ร้าน",
            "กาแฟ",
            "เครื่องดื่ม",
            "eat",
            "food",
            "restaurant",
            "coffee",
            "drink",
            "meal",
            "lunch",
            "dinner",
        ]

        # Transportation keywords
        transport_keywords = [
            "แท็กซี่",
            "รถ",
            "เดินทาง",
            "BTS",
            "MRT",
            "วิน",
            "taxi",
            "transport",
            "travel",
            "bus",
            "train",
            "grab",
            "uber",
        ]

        # Shopping keywords
        shopping_keywords = [
            "ซื้อ",
            "ช้อป",
            "ช้อปปิ้ง",
            "buy",
            "shop",
            "shopping",
            "purchase",
        ]

        # Travel keywords
        travel_keywords = [
            "โรงแรม",
            "ที่พัก",
            "เที่ยว",
            "ท่องเที่ยว",
            "hotel",
            "accommodation",
            "vacation",
            "trip",
        ]

        # Check categories
        if any(keyword in text_lower for keyword in food_keywords):
            return "Food & Dining"
        elif any(keyword in text_lower for keyword in transport_keywords):
            return "Transportation"
        elif any(keyword in text_lower for keyword in shopping_keywords):
            return "Shopping"
        elif any(keyword in text_lower for keyword in travel_keywords):
            return "Travel"
        else:
            return "Miscellaneous"

    async def _map_category_intelligent(
        self,
        category: str,
        language: str = "en",
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> str:
        """Map category using intelligent mapping service with fallback."""
        if self._mapping_service:
            try:
                result = await self._mapping_service.map_category(
                    category, language, user_id, session_id
                )
                if result.is_successful():
                    return result.category
            except Exception as e:
                logger.warning(f"Intelligent mapping failed: {e}")

        # Fallback to fuzzy mapping
        return self._map_category_fuzzy(category)

    def _map_category_fuzzy(self, category: str) -> str:
        """Map AI-generated categories to valid categories with fuzzy matching."""
        category_lower = category.lower()

        mapping = {
            "food": "Food & Dining",
            "dining": "Food & Dining",
            "restaurant": "Food & Dining",
            "coffee": "Food & Dining",
            "drink": "Food & Dining",
            "transport": "Transportation",
            "travel": "Travel",
            "taxi": "Transportation",
            "hotel": "Travel",
            "accommodation": "Travel",
            "shop": "Shopping",
            "shopping": "Shopping",
            "grocery": "Groceries",
            "groceries": "Groceries",
            "supermarket": "Groceries",
            "health": "Healthcare",
            "medical": "Healthcare",
            "entertainment": "Entertainment",
            "utility": "Utilities",
            "utilities": "Utilities",
        }

        # Direct match
        if category_lower in mapping:
            return mapping[category_lower]

        # Partial match
        for key, value in mapping.items():
            if key in category_lower or category_lower in key:
                return value

        return "Miscellaneous"

    def clear_cache(self) -> None:
        """Clear processing cache."""
        self._intelligent_cache.clear_cache()
        logger.info("Enhanced text processing cache cleared")

    def get_cache_stats(self) -> dict[str, Any]:
        """Get comprehensive cache statistics."""
        cache_stats = self._intelligent_cache.get_cache_stats()
        return {
            **cache_stats,
            "patterns_count": len(self._patterns),
            "processor_type": "enhanced_with_intelligent_cache",
        }

    def get_processing_stats(self) -> dict[str, Any]:
        """Get processing performance statistics."""
        cache_stats = self.get_cache_stats()
        return {
            "cache_performance": cache_stats,
            "pattern_count": len(self._patterns),
            "ai_client_available": self._llama_client is not None,
            "processing_methods": ["cache", "pattern", "ai", "fallback"],
            "target_response_time_ms": 3000,  # 3 second target
            "cache_first_strategy": True,
        }
