"""
Text processing utilities for NLP
"""

import logging
import re
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# Thai language detection patterns
THAI_PATTERN = re.compile(r"[\u0E00-\u0E7F]")
ENGLISH_PATTERN = re.compile(r"[a-zA-Z]")

# Common text cleaning patterns
NOISE_PATTERNS = [
    r"\s+",  # Multiple whitespace
    r"[^\w\s\u0E00-\u0E7F.,!?-]",  # Non-word chars except Thai, punctuation
    r"^[\s\W]+|[\s\W]+$",  # Leading/trailing non-word
]

# Currency patterns
CURRENCY_PATTERNS = {
    "thai_baht": [
        r"฿\s*(\d+(?:,\d{3})*(?:\.\d{2})?)",
        r"(\d+(?:,\d{3})*(?:\.\d{2})?)\s*บาท",
        r"(\d+(?:,\d{3})*(?:\.\d{2})?)\s*THB",
    ],
    "usd": [
        r"\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)",
        r"(\d+(?:,\d{3})*(?:\.\d{2})?)\s*USD",
    ],
    "general": [
        r"(\d+(?:,\d{3})*(?:\.\d{2})?)",  # Any number
    ],
}

# Date patterns
DATE_PATTERNS = [
    r"(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})",  # DD/MM/YYYY
    r"(\d{2,4})[/\-.](\d{1,2})[/\-.](\d{1,2})",  # YYYY/MM/DD
    r"(\d{1,2})\s+(ม\.ค\.|ก\.พ\.|มี\.ค\.|เม\.ย\.|พ\.ค\.|มิ\.ย\.|ก\.ค\.|ส\.ค\.|ก\.ย\.|ต\.ค\.|พ\.ย\.|ธ\.ค\.)\s+(\d{2,4})",  # Thai months
]

# Thai month mapping
THAI_MONTHS = {
    "ม.ค.": 1,
    "มกราคม": 1,
    "ก.พ.": 2,
    "กุมภาพันธ์": 2,
    "มี.ค.": 3,
    "มีนาคม": 3,
    "เม.ย.": 4,
    "เมษายน": 4,
    "พ.ค.": 5,
    "พฤษภาคม": 5,
    "มิ.ย.": 6,
    "มิถุนายน": 6,
    "ก.ค.": 7,
    "กรกฎาคม": 7,
    "ส.ค.": 8,
    "สิงหาคม": 8,
    "ก.ย.": 9,
    "กันยายน": 9,
    "ต.ค.": 10,
    "ตุลาคม": 10,
    "พ.ย.": 11,
    "พฤศจิกายน": 11,
    "ธ.ค.": 12,
    "ธันวาคม": 12,
}


def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""

    try:
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove leading/trailing whitespace
        text = text.strip()

        # Remove control characters but keep Thai characters
        text = re.sub(r"[\x00-\x1F\x7F-\x9F]", "", text)

        return text

    except Exception as e:
        logger.error(f"Text cleaning error: {e!s}")
        return text


def detect_language(text: str) -> str:
    """Detect if text is primarily Thai or English"""
    if not text:
        return "en"

    try:
        thai_chars = len(THAI_PATTERN.findall(text))
        english_chars = len(ENGLISH_PATTERN.findall(text))

        if thai_chars > english_chars:
            return "th"
        else:
            return "en"

    except Exception as e:
        logger.error(f"Language detection error: {e!s}")
        return "en"


def extract_amounts(text: str, language: str = "auto") -> list[float]:
    """Extract monetary amounts from text"""
    amounts = []

    try:
        if language == "auto":
            language = detect_language(text)

        # Try currency-specific patterns first
        if language == "th":
            patterns = CURRENCY_PATTERNS["thai_baht"]
        else:
            patterns = CURRENCY_PATTERNS["usd"]

        # Add general number patterns as fallback
        patterns.extend(CURRENCY_PATTERNS["general"])

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Remove commas and convert to float
                    amount_str = match.replace(",", "")
                    amount = float(amount_str)
                    if 0 < amount < 1000000:  # Reasonable range
                        amounts.append(amount)
                except ValueError:
                    continue

        # Remove duplicates and sort
        amounts = sorted(list(set(amounts)), reverse=True)

        return amounts

    except Exception as e:
        logger.error(f"Amount extraction error: {e!s}")
        return []


def extract_dates(text: str, language: str = "auto") -> list[datetime]:
    """Extract dates from text"""
    dates = []

    try:
        if language == "auto":
            language = detect_language(text)

        for pattern in DATE_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    if len(match) == 3:
                        # Handle different date formats
                        if isinstance(match[1], str) and match[1] in THAI_MONTHS:
                            # Thai month format
                            day = int(match[0])
                            month = THAI_MONTHS[match[1]]
                            year = int(match[2])
                        else:
                            # Numeric format
                            day, month, year = map(int, match)

                        # Handle 2-digit years
                        if year < 100:
                            year += 2000 if year < 50 else 1900

                        # Handle Buddhist Era (Thai calendar)
                        if language == "th" and year > 2400:
                            year -= 543

                        if 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100:
                            date = datetime(year, month, day)
                            dates.append(date)

                except (ValueError, IndexError):
                    continue

        return sorted(dates, reverse=True)

    except Exception as e:
        logger.error(f"Date extraction error: {e!s}")
        return []


def extract_merchant_names(text: str, language: str = "auto") -> list[str]:
    """Extract potential merchant names from text"""
    merchants = []

    try:
        if language == "auto":
            language = detect_language(text)

        # Common merchant patterns
        patterns = [
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",  # Title case words
            r"([A-Z]{2,}(?:\s+[A-Z]{2,})*)",  # All caps
        ]

        # Thai merchant patterns
        if language == "th":
            patterns.extend(
                [
                    r"([\u0E00-\u0E7F]+(?:\s+[\u0E00-\u0E7F]+)*)",  # Thai text
                ]
            )

        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) > 2 and len(match) < 50:  # Reasonable length
                    merchants.append(match.strip())

        # Remove duplicates while preserving order
        seen = set()
        unique_merchants = []
        for merchant in merchants:
            if merchant.lower() not in seen:
                seen.add(merchant.lower())
                unique_merchants.append(merchant)

        return unique_merchants[:5]  # Return top 5

    except Exception as e:
        logger.error(f"Merchant extraction error: {e!s}")
        return []


def normalize_text(text: str) -> str:
    """Normalize text for consistent processing"""
    if not text:
        return ""

    try:
        # Convert to lowercase
        text = text.lower()

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove special characters but keep Thai
        text = re.sub(r"[^\w\s\u0E00-\u0E7F]", " ", text)

        # Trim
        text = text.strip()

        return text

    except Exception as e:
        logger.error(f"Text normalization error: {e!s}")
        return text


def extract_keywords(text: str, min_length: int = 3) -> list[str]:
    """Extract keywords from text"""
    try:
        # Normalize text
        normalized = normalize_text(text)

        # Split into words
        words = normalized.split()

        # Filter by length and common stop words
        stop_words = {
            "the",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "ที่",
            "และ",
            "หรือ",
            "แต่",
            "ใน",
            "บน",
            "เพื่อ",
            "ของ",
            "กับ",
            "โดย",
        }

        keywords = [
            word for word in words if len(word) >= min_length and word not in stop_words
        ]

        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)

        return unique_keywords[:10]  # Return top 10

    except Exception as e:
        logger.error(f"Keyword extraction error: {e!s}")
        return []


def calculate_text_confidence(text: str, extracted_data: dict[str, Any]) -> float:
    """Calculate confidence score based on extracted data quality"""
    try:
        if not text:
            return 0.0

        confidence = 0.0

        # Base confidence from text length and cleanliness
        if len(text) > 10:
            confidence += 0.2

        # Bonus for having amount
        if extracted_data.get("amount") and extracted_data["amount"] > 0:
            confidence += 0.3

        # Bonus for having merchant
        if extracted_data.get("merchant") and len(extracted_data["merchant"]) > 2:
            confidence += 0.2

        # Bonus for having date
        if extracted_data.get("date"):
            confidence += 0.1

        # Bonus for having category
        if extracted_data.get("category"):
            confidence += 0.1

        # Penalty for very short or very long text
        text_length = len(text)
        if text_length < 5:
            confidence -= 0.2
        elif text_length > 1000:
            confidence -= 0.1

        # Ensure confidence is between 0 and 1
        return max(0.0, min(1.0, confidence))

    except Exception as e:
        logger.error(f"Confidence calculation error: {e!s}")
        return 0.5
