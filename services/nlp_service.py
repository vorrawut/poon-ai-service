"""
NLP Service for parsing spending text
Local processing with pattern matching and ML models
Cost-efficient approach before AI fallback
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Any

from models.spending_models import NLPResult

logger = logging.getLogger(__name__)


class NLPService:
    """Local NLP service for spending text parsing"""

    def __init__(self, settings):
        self.settings = settings
        self.load_patterns()
        self.load_merchant_database()
        self.load_category_keywords()

    def load_patterns(self):
        """Load regex patterns for text parsing"""
        self.patterns = {
            "amount": [
                # Thai patterns
                r"(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:บาท|฿)",
                r"(?:บาท|฿)\s*(\d+(?:,\d{3})*(?:\.\d{2})?)",
                r"(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:baht)",
                # English patterns
                r"\$(\d+(?:,\d{3})*(?:\.\d{2})?)",
                r"(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:dollars?|usd)",
                # Generic number patterns
                r"(\d+(?:,\d{3})*(?:\.\d{2})?)(?=\s|$)",
            ],
            "merchant": [
                # Location patterns
                r"(?:at|from|ที่|จาก)\s+([a-zA-Zก-๙\s&\'.-]+?)(?:\s+(?:for|with|by|ด้วย|จ่าย)|\s+\d|\s*$)",
                # Brand patterns
                r"(starbucks|mcdonald|kfc|pizza|burger|tesco|lotus|7-eleven|cp|robinson|central|terminal|emporium|siam|mbk)",
                # Generic merchant patterns
                r"([a-zA-Zก-๙\s&\'.-]+?)(?:\s+(?:store|shop|restaurant|cafe|ร้าน|ห้าง))",
            ],
            "date": [
                # Relative dates
                r"(?:yesterday|เมื่อวาน)",
                r"(?:today|วันนี้)",
                r"(?:last\s+(?:week|month)|สัปดาห์ที่แล้ว|เดือนที่แล้ว)",
                # Absolute dates
                r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                r"(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{2,4})",
                r"(\d{1,2}\s+(?:ม\.ค\.|ก\.พ\.|มี\.ค\.|เม\.ย\.|พ\.ค\.|มิ\.ย\.|ก\.ค\.|ส\.ค\.|ก\.ย\.|ต\.ค\.|พ\.ย\.|ธ\.ค\.)\s+\d{2,4})",
            ],
            "payment_method": [
                r"(?:with|by|using|paid|ด้วย|จ่าย)\s*(cash|credit|debit|card|visa|mastercard|promptpay|เงินสด|บัตร|พร้อมเพย์)",
                r"(cash|credit|debit|card|visa|mastercard|promptpay|เงินสด|บัตร|พร้อมเพย์)(?:\s+(?:card|payment))?",
            ],
        }

    def load_merchant_database(self):
        """Load merchant database with normalization"""
        self.merchant_db = {
            # Coffee chains
            "starbucks": {
                "name": "Starbucks Coffee",
                "category": "Food & Dining",
                "subcategory": "Coffee",
            },
            "starbuck": {
                "name": "Starbucks Coffee",
                "category": "Food & Dining",
                "subcategory": "Coffee",
            },
            "สตาร์บัคส์": {
                "name": "Starbucks Coffee",
                "category": "Food & Dining",
                "subcategory": "Coffee",
            },
            # Fast food
            "mcdonald": {
                "name": "McDonald's",
                "category": "Food & Dining",
                "subcategory": "Fast Food",
            },
            "mcdonalds": {
                "name": "McDonald's",
                "category": "Food & Dining",
                "subcategory": "Fast Food",
            },
            "แมคโดนัลด์": {
                "name": "McDonald's",
                "category": "Food & Dining",
                "subcategory": "Fast Food",
            },
            "kfc": {
                "name": "KFC",
                "category": "Food & Dining",
                "subcategory": "Fast Food",
            },
            "เคเอฟซี": {
                "name": "KFC",
                "category": "Food & Dining",
                "subcategory": "Fast Food",
            },
            # Supermarkets
            "tesco": {
                "name": "Tesco Lotus",
                "category": "Groceries",
                "subcategory": "Supermarket",
            },
            "lotus": {
                "name": "Tesco Lotus",
                "category": "Groceries",
                "subcategory": "Supermarket",
            },
            "เทสโก้": {
                "name": "Tesco Lotus",
                "category": "Groceries",
                "subcategory": "Supermarket",
            },
            "โลตัส": {
                "name": "Tesco Lotus",
                "category": "Groceries",
                "subcategory": "Supermarket",
            },
            "7-eleven": {
                "name": "7-Eleven",
                "category": "Groceries",
                "subcategory": "Convenience Store",
            },
            "เซเว่น": {
                "name": "7-Eleven",
                "category": "Groceries",
                "subcategory": "Convenience Store",
            },
            # Shopping malls
            "central": {
                "name": "Central",
                "category": "Shopping",
                "subcategory": "Department Store",
            },
            "เซ็นทรัล": {
                "name": "Central",
                "category": "Shopping",
                "subcategory": "Department Store",
            },
            "terminal": {
                "name": "Terminal 21",
                "category": "Shopping",
                "subcategory": "Shopping Mall",
            },
            "เทอร์มินอล": {
                "name": "Terminal 21",
                "category": "Shopping",
                "subcategory": "Shopping Mall",
            },
            "siam": {
                "name": "Siam Paragon",
                "category": "Shopping",
                "subcategory": "Shopping Mall",
            },
            "สยาม": {
                "name": "Siam Paragon",
                "category": "Shopping",
                "subcategory": "Shopping Mall",
            },
            # Transportation
            "grab": {
                "name": "Grab",
                "category": "Transportation",
                "subcategory": "Ride-sharing",
            },
            "แกร็บ": {
                "name": "Grab",
                "category": "Transportation",
                "subcategory": "Ride-sharing",
            },
            "bts": {
                "name": "BTS Skytrain",
                "category": "Transportation",
                "subcategory": "Public Transport",
            },
            "mrt": {
                "name": "MRT Subway",
                "category": "Transportation",
                "subcategory": "Public Transport",
            },
        }

    def load_category_keywords(self):
        """Load category classification keywords"""
        self.category_keywords = {
            "Food & Dining": [
                "coffee",
                "lunch",
                "dinner",
                "breakfast",
                "restaurant",
                "cafe",
                "food",
                "eat",
                "drink",
                "starbucks",
                "mcdonald",
                "kfc",
                "pizza",
                "burger",
                "noodle",
                "rice",
                "meal",
                "กิน",
                "อาหาร",
                "ร้านอาหาร",
                "กาแฟ",
                "ข้าว",
                "ก๋วยเตี๋ยว",
                "ส้มตำ",
                "ผัดไท",
            ],
            "Transportation": [
                "taxi",
                "grab",
                "uber",
                "bus",
                "bts",
                "mrt",
                "train",
                "fuel",
                "gas",
                "petrol",
                "parking",
                "แท็กซี่",
                "รถ",
                "น้ำมัน",
                "ลิฟต์",
                "จอดรถ",
                "รถไฟ",
                "รถเมล์",
            ],
            "Groceries": [
                "grocery",
                "groceries",
                "supermarket",
                "market",
                "tesco",
                "lotus",
                "big c",
                "makro",
                "ตลาด",
                "ซื้อของ",
                "เทสโก้",
                "โลตัส",
                "บิ๊กซี",
                "แม็คโคร",
            ],
            "Shopping": [
                "shopping",
                "buy",
                "purchase",
                "store",
                "mall",
                "clothes",
                "shirt",
                "shoes",
                "bag",
                "central",
                "robinson",
                "terminal",
                "emporium",
                "siam",
                "mbk",
                "ซื้อ",
                "ห้าง",
                "เสื้อ",
                "กางเกง",
                "รองเท้า",
                "กระเป๋า",
            ],
            "Entertainment": [
                "movie",
                "cinema",
                "theater",
                "game",
                "entertainment",
                "concert",
                "show",
                "หนัง",
                "เกม",
                "คอนเสิร์ต",
                "โรงหนัง",
            ],
            "Healthcare": [
                "hospital",
                "doctor",
                "clinic",
                "medicine",
                "pharmacy",
                "dental",
                "โรงพยาบาล",
                "หมอ",
                "ยา",
                "คลินิก",
                "ทันตแพทย์",
            ],
        }

    async def parse_spending_text(self, text: str, language: str = "en") -> NLPResult:
        """
        Parse spending text using local NLP patterns
        Returns structured spending information
        """
        try:
            text_lower = text.lower()
            result = NLPResult(confidence=0.0)
            confidence_factors = []

            # Extract amount
            amount, amount_confidence = self._extract_amount(text)
            if amount:
                result.amount = amount
                confidence_factors.append(amount_confidence)

            # Extract merchant
            merchant, merchant_confidence = self._extract_merchant(text_lower)
            if merchant:
                result.merchant = merchant
                confidence_factors.append(merchant_confidence)

            # Extract/predict category
            category, subcategory, category_confidence = self._predict_category(
                text_lower, merchant
            )
            if category:
                result.category = category
                result.subcategory = subcategory
                confidence_factors.append(category_confidence)

            # Extract date
            date, date_confidence = self._extract_date(text_lower)
            if date:
                result.date = date
                confidence_factors.append(date_confidence)

            # Extract payment method
            payment_method, payment_confidence = self._extract_payment_method(
                text_lower
            )
            if payment_method:
                result.payment_method = payment_method
                confidence_factors.append(payment_confidence)

            # Generate description
            result.description = self._generate_description(
                result.merchant, result.category, result.amount
            )

            # Calculate overall confidence
            result.confidence = (
                sum(confidence_factors) / len(confidence_factors)
                if confidence_factors
                else 0.0
            )

            # Add extraction details
            result.extraction_details = {
                "patterns_matched": len(confidence_factors),
                "text_length": len(text),
                "language": language,
                "merchant_normalized": merchant in self.merchant_db
                if merchant
                else False,
            }

            logger.info(
                f"NLP parsing completed with {result.confidence:.2f} confidence"
            )
            return result

        except Exception as e:
            logger.error(f"NLP parsing failed: {e!s}")
            raise Exception(f"NLP parsing failed: {e!s}")

    def _extract_amount(self, text: str) -> tuple[float | None, float]:
        """Extract amount from text"""
        for pattern in self.patterns["amount"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    amount_str = match.group(1).replace(",", "")
                    amount = float(amount_str)
                    # Higher confidence for properly formatted amounts
                    confidence = 0.9 if "." in amount_str else 0.8
                    return amount, confidence
                except (ValueError, IndexError):
                    continue
        return None, 0.0

    def _extract_merchant(self, text: str) -> tuple[str | None, float]:
        """Extract and normalize merchant name"""
        # First, check against known merchants
        for merchant_key, merchant_data in self.merchant_db.items():
            if merchant_key in text:
                return merchant_data["name"], 0.95

        # Then try pattern matching
        for pattern in self.patterns["merchant"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                merchant = match.group(1).strip()
                # Clean up merchant name
                merchant = re.sub(r"\s+", " ", merchant)
                merchant = merchant.title()
                return merchant, 0.7

        return None, 0.0

    def _predict_category(
        self, text: str, merchant: str = None
    ) -> tuple[str | None, str | None, float]:
        """Predict category based on text and merchant"""
        # First, check merchant database
        if merchant:
            for merchant_key, merchant_data in self.merchant_db.items():
                if merchant_key in merchant.lower():
                    return (
                        merchant_data["category"],
                        merchant_data.get("subcategory"),
                        0.9,
                    )

        # Then check keywords
        category_scores = {}
        for category, keywords in self.category_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text:
                    score += 1
            if score > 0:
                category_scores[category] = score / len(keywords)

        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            confidence = min(
                category_scores[best_category] * 2, 1.0
            )  # Scale to max 1.0
            return best_category, None, confidence

        return None, None, 0.0

    def _extract_date(self, text: str) -> tuple[datetime | None, float]:
        """Extract date from text"""
        now = datetime.now()

        # Check relative dates first
        if "yesterday" in text or "เมื่อวาน" in text:
            return now - timedelta(days=1), 0.9
        elif "today" in text or "วันนี้" in text:
            return now, 0.9
        elif "last week" in text or "สัปดาห์ที่แล้ว" in text:
            return now - timedelta(weeks=1), 0.8
        elif "last month" in text or "เดือนที่แล้ว" in text:
            return now - timedelta(days=30), 0.8

        # Try absolute date patterns
        for pattern in self.patterns["date"][3:]:  # Skip relative patterns
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    date_str = match.group(1)
                    # Simple date parsing - in production, use proper date parser
                    if "/" in date_str or "-" in date_str:
                        parts = re.split("[/-]", date_str)
                        if len(parts) == 3:
                            day, month, year = map(int, parts)
                            if year < 100:
                                year += 2000
                            return datetime(year, month, day), 0.8
                except (ValueError, IndexError):
                    continue

        return None, 0.0

    def _extract_payment_method(self, text: str) -> tuple[str | None, float]:
        """Extract payment method from text"""
        for pattern in self.patterns["payment_method"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                method = match.group(1) if len(match.groups()) > 0 else match.group(0)
                # Normalize payment method
                method_normalized = self._normalize_payment_method(method)
                return method_normalized, 0.8

        return None, 0.0

    def _normalize_payment_method(self, method: str) -> str:
        """Normalize payment method names"""
        method_lower = method.lower()

        if any(word in method_lower for word in ["cash", "เงินสด"]):
            return "Cash"
        elif any(word in method_lower for word in ["credit", "visa", "mastercard"]):
            return "Credit Card"
        elif any(word in method_lower for word in ["debit", "บัตร"]):
            return "Debit Card"
        elif any(word in method_lower for word in ["promptpay", "พร้อมเพย์"]):
            return "PromptPay"
        elif any(word in method_lower for word in ["transfer", "โอน"]):
            return "Bank Transfer"
        else:
            return method.title()

    def _generate_description(
        self, merchant: str = None, category: str = None, amount: float = None
    ) -> str:
        """Generate a description for the spending entry"""
        parts = []

        if category:
            parts.append(category)
        if merchant:
            parts.append(f"at {merchant}")
        if amount:
            parts.append(f"฿{amount:.2f}")

        return " ".join(parts) if parts else "Spending entry"

    async def parse_batch_entry(self, row: dict[str, Any], text_repr: str) -> NLPResult:
        """Parse a single batch entry (from CSV/Excel)"""
        try:
            result = NLPResult(
                confidence=0.8
            )  # Start with higher confidence for structured data

            # Direct field mapping
            if "amount" in row:
                result.amount = float(str(row["amount"]).replace(",", ""))
            elif "total" in row:
                result.amount = float(str(row["total"]).replace(",", ""))

            if "merchant" in row:
                result.merchant = str(row["merchant"]).strip()
            elif "description" in row:
                result.merchant = str(row["description"]).strip()

            if "category" in row:
                result.category = str(row["category"]).strip()

            if "date" in row:
                # Simple date parsing
                date_str = str(row["date"])
                try:
                    result.date = datetime.fromisoformat(date_str.replace("/", "-"))
                except:
                    result.date = datetime.now()

            # Fill missing fields using NLP
            if not result.category and result.merchant:
                category, subcategory, _ = self._predict_category(
                    result.merchant.lower()
                )
                result.category = category or "Miscellaneous"
                result.subcategory = subcategory

            result.description = self._generate_description(
                result.merchant, result.category, result.amount
            )

            return result

        except Exception as e:
            logger.warning(f"Batch entry parsing failed: {e!s}")
            return NLPResult(confidence=0.0)

    async def suggest_categories(
        self, merchant: str, amount: float, description: str = ""
    ) -> list[str]:
        """Suggest categories based on merchant and context"""
        suggestions = []

        text = f"{merchant} {description}".lower()

        # Score categories
        scores = {}
        for category, keywords in self.category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                scores[category] = score

        # Sort by score and return top suggestions
        sorted_categories = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        suggestions = [cat for cat, score in sorted_categories[:3]]

        # Add default if no matches
        if not suggestions:
            suggestions = ["Miscellaneous"]

        return suggestions

    async def normalize_merchant(self, name: str) -> str:
        """Normalize merchant name"""
        name_lower = name.lower().strip()

        # Check merchant database
        for merchant_key, merchant_data in self.merchant_db.items():
            if merchant_key in name_lower:
                return merchant_data["name"]

        # Basic normalization
        normalized = re.sub(r"\s+", " ", name.strip())
        normalized = normalized.title()

        return normalized
