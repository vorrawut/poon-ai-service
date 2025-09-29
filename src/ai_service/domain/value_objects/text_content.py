"""Text content value object for processing natural language input."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Any


class Language(str, Enum):
    """Supported languages for text processing."""

    ENGLISH = "en"
    THAI = "th"
    MIXED = "mixed"  # Mixed Thai and English
    AUTO_DETECT = "auto"  # Auto-detect language

    def get_display_name(self) -> str:
        """Get display name for language."""
        names = {
            self.ENGLISH: "English",
            self.THAI: "Thai",
            self.MIXED: "Mixed (Thai/English)",
            self.AUTO_DETECT: "Auto-detect",
        }
        return names.get(self, self.value)


@dataclass(frozen=True)
class TextContent:
    """Immutable text content value object with language detection."""

    content: str
    language: Language | None = None

    def __post_init__(self) -> None:
        """Validate and process text content."""
        if not isinstance(self.content, str):
            msg = f"Content must be a string, got {type(self.content)}"
            raise TypeError(msg)

        if not self.content.strip():
            msg = "Content cannot be empty or whitespace only"
            raise ValueError(msg)

        if len(self.content) > 10000:  # Reasonable limit
            msg = f"Content too long: {len(self.content)} characters (max 10000)"
            raise ValueError(msg)

    @classmethod
    def from_raw_input(cls, raw_input: str) -> TextContent:
        """Create TextContent from raw user input with auto-detection."""
        cleaned_content = cls._clean_text(raw_input)
        detected_language = cls._detect_language(cleaned_content)
        return cls(content=cleaned_content, language=detected_language)

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean text by removing extra whitespace and normalizing."""
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', text.strip())

        # Remove control characters but keep Thai characters
        cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', cleaned)

        return cleaned

    @staticmethod
    def _detect_language(text: str) -> Language:
        """Detect language of text content."""
        # Check for Thai characters (Unicode range for Thai)
        thai_chars = len(re.findall(r'[\u0E00-\u0E7F]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))

        total_alpha = thai_chars + english_chars

        if total_alpha == 0:
            return Language.ENGLISH  # Default for non-alphabetic text

        thai_ratio = thai_chars / total_alpha

        if thai_ratio > 0.7:
            return Language.THAI
        elif thai_ratio > 0.1:
            return Language.MIXED
        else:
            return Language.ENGLISH

    def get_word_count(self) -> int:
        """Get approximate word count."""
        # For Thai text, count by spaces and Thai word boundaries
        if self.language == Language.THAI:
            # Simple approximation for Thai (actual word segmentation is complex)
            return len(self.content.split()) + len(re.findall(r'[\u0E00-\u0E7F]+', self.content))
        else:
            return len(self.content.split())

    def get_character_count(self) -> int:
        """Get character count."""
        return len(self.content)

    def contains_numbers(self) -> bool:
        """Check if text contains numbers."""
        return bool(re.search(r'\d', self.content))

    def extract_numbers(self) -> list[float]:
        """Extract all numbers from text."""
        # Match various number formats including Thai currency
        patterns = [
            r'\d+(?:,\d{3})*(?:\.\d{2})?',  # English format: 1,234.56
            r'\d+(?:\.\d{2})?',  # Simple format: 1234.56
        ]

        numbers = []
        for pattern in patterns:
            matches = re.findall(pattern, self.content)
            for match in matches:
                try:
                    # Remove commas and convert to float
                    num = float(match.replace(',', ''))
                    numbers.append(num)
                except ValueError:
                    continue

        return list(set(numbers))  # Remove duplicates

    def extract_currency_mentions(self) -> list[str]:
        """Extract currency mentions from text."""
        currency_patterns = [
            r'บาท', r'baht', r'฿', r'\$', r'dollar', r'usd',
            r'euro', r'eur', r'€', r'pound', r'gbp', r'£'
        ]

        currencies = []
        for pattern in currency_patterns:
            if re.search(pattern, self.content, re.IGNORECASE):
                currencies.append(pattern)

        return currencies

    def is_likely_spending_text(self) -> bool:
        """Check if text is likely describing a spending transaction."""
        # Keywords that suggest spending
        spending_keywords = [
            # English
            'buy', 'bought', 'purchase', 'paid', 'spend', 'cost', 'price',
            'coffee', 'lunch', 'dinner', 'food', 'restaurant', 'taxi', 'grab',
            'shopping', 'store', 'mall', 'gas', 'fuel', 'grocery',

            # Thai
            'ซื้อ', 'จ่าย', 'ใช้', 'ค่า', 'ราคา', 'อาหาร', 'กิน', 'ข้าว',
            'ร้าน', 'ห้าง', 'ตลาด', 'แท็กซี่', 'รถ', 'น้ำมัน', 'กาแฟ'
        ]

        text_lower = self.content.lower()
        keyword_matches = sum(1 for keyword in spending_keywords if keyword in text_lower)

        # Check for numbers (likely amounts)
        has_numbers = self.contains_numbers()

        # Check for currency mentions
        has_currency = len(self.extract_currency_mentions()) > 0

        return keyword_matches > 0 or (has_numbers and has_currency)

    def get_complexity_score(self) -> float:
        """Get complexity score (0.0 to 1.0) based on text characteristics."""
        factors = []

        # Length factor
        length_factor = min(1.0, len(self.content) / 200)
        factors.append(length_factor)

        # Word count factor
        word_count_factor = min(1.0, self.get_word_count() / 30)
        factors.append(word_count_factor)

        # Language mixing factor
        if self.language == Language.MIXED:
            factors.append(0.8)  # Mixed language is more complex
        elif self.language == Language.THAI:
            factors.append(0.6)  # Thai processing is moderately complex
        else:
            factors.append(0.4)  # English is less complex

        # Number complexity
        numbers = self.extract_numbers()
        if len(numbers) > 3:
            factors.append(0.9)
        elif len(numbers) > 1:
            factors.append(0.6)
        elif len(numbers) == 1:
            factors.append(0.3)
        else:
            factors.append(0.1)

        return sum(factors) / len(factors)

    def truncate(self, max_length: int = 100) -> str:
        """Truncate content for display purposes."""
        if len(self.content) <= max_length:
            return self.content

        return self.content[:max_length - 3] + "..."

    def __str__(self) -> str:
        """String representation."""
        lang_display = self.language.get_display_name() if self.language else "Unknown"
        return f"TextContent({self.truncate(50)}, {lang_display})"

    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        if not isinstance(other, TextContent):
            return False
        return self.content == other.content and self.language == other.language

    def __len__(self) -> int:
        """Get content length."""
        return len(self.content)
