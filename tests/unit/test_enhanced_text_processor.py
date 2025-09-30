"""Unit tests for enhanced text processor."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.ai_service.application.services.enhanced_text_processor import (
    EnhancedTextProcessor,
    SpendingPattern,
)
from src.ai_service.infrastructure.external_apis.llama_client import LlamaClient


class TestEnhancedTextProcessor:
    """Unit tests for EnhancedTextProcessor."""

    @pytest.fixture
    def mock_llama_client(self):
        """Create mock Llama client."""
        client = AsyncMock(spec=LlamaClient)
        client.parse_spending_text.return_value = {
            "amount": 150.0,
            "currency": "THB",
            "merchant": "Test Restaurant",
            "category": "Food & Dining",
            "payment_method": "Cash",
            "description": "Meal at restaurant",
            "confidence": 0.8,
        }
        return client

    @pytest.fixture
    def processor(self, mock_llama_client):
        """Create enhanced text processor."""
        return EnhancedTextProcessor(mock_llama_client)

    @pytest.fixture
    def processor_no_ai(self):
        """Create enhanced text processor without AI."""
        return EnhancedTextProcessor(None)

    @pytest.mark.asyncio
    async def test_thai_restaurant_pattern_matching(self, processor_no_ai):
        """Test Thai restaurant pattern matching."""
        # Arrange
        text = "กินข้าวที่ร้านอาหาร 120 บาท"

        # Act
        result = await processor_no_ai.process_text_fast(text, "th")

        # Assert
        assert result["amount"] == 120.0
        assert result["currency"] == "THB"
        assert result["category"] == "Food & Dining"
        assert result["method"] == "pattern"
        assert result["confidence"] > 0.8
        assert "ร้านอาหาร" in result["merchant"]

    @pytest.mark.asyncio
    async def test_thai_coffee_pattern_matching(self, processor_no_ai):
        """Test Thai coffee pattern matching."""
        # Arrange
        text = "กาแฟ สตาร์บัคส์ 150 บาท"

        # Act
        result = await processor_no_ai.process_text_fast(text, "th")

        # Assert
        assert result["amount"] == 150.0
        assert result["category"] == "Food & Dining"
        assert "สตาร์บัคส์" in result["merchant"]
        assert result["confidence"] > 0.8

    @pytest.mark.asyncio
    async def test_thai_transportation_pattern(self, processor_no_ai):
        """Test Thai transportation pattern matching."""
        # Arrange
        text = "แท็กซี่ 80 บาท"

        # Act
        result = await processor_no_ai.process_text_fast(text, "th")

        # Assert
        assert result["amount"] == 80.0
        assert result["category"] == "Transportation"
        assert result["confidence"] > 0.8

    @pytest.mark.asyncio
    async def test_thai_hotel_pattern(self, processor_no_ai):
        """Test Thai hotel pattern matching."""
        # Arrange
        text = "โรงแรมที่กรุงเทพ 2 คืน 3000 บาท"

        # Act
        result = await processor_no_ai.process_text_fast(text, "th")

        # Assert
        assert result["amount"] == 3000.0
        assert result["category"] == "Travel"
        assert "กรุงเทพ" in result["merchant"]
        assert "2 คืน" in result["description"]

    @pytest.mark.asyncio
    async def test_english_restaurant_pattern(self, processor_no_ai):
        """Test English restaurant pattern matching."""
        # Arrange
        text = "lunch at McDonald's 200 baht"

        # Act
        result = await processor_no_ai.process_text_fast(text, "en")

        # Assert
        assert result["amount"] == 200.0
        assert result["category"] == "Food & Dining"
        assert "McDonald's" in result["merchant"]
        assert result["confidence"] > 0.8

    @pytest.mark.asyncio
    async def test_english_transportation_pattern(self, processor_no_ai):
        """Test English transportation pattern matching."""
        # Arrange
        text = "taxi ride 150 baht"

        # Act
        result = await processor_no_ai.process_text_fast(text, "en")

        # Assert
        assert result["amount"] == 150.0
        assert result["category"] == "Transportation"
        assert result["confidence"] > 0.8

    @pytest.mark.asyncio
    async def test_english_hotel_pattern(self, processor_no_ai):
        """Test English hotel pattern matching."""
        # Arrange
        text = "hotel booking at Hilton 2 nights 5000 baht"

        # Act
        result = await processor_no_ai.process_text_fast(text, "en")

        # Assert
        assert result["amount"] == 5000.0
        assert result["category"] == "Travel"
        assert "Hilton" in result["merchant"]
        assert "2 nights" in result["description"]

    @pytest.mark.asyncio
    async def test_cache_functionality(self, processor_no_ai):
        """Test caching functionality."""
        # Arrange
        text = "กาแฟ 100 บาท"

        # Act - First call
        result1 = await processor_no_ai.process_text_fast(text, "th")
        # Act - Second call (should hit cache)
        result2 = await processor_no_ai.process_text_fast(text, "th")

        # Assert
        assert result1["amount"] == result2["amount"]
        assert result2["method"].startswith("cache_")
        assert result2["processing_time_ms"] < result1["processing_time_ms"]

    @pytest.mark.asyncio
    async def test_similarity_cache_matching(self, processor_no_ai):
        """Test similarity-based cache matching."""
        # Arrange
        text1 = "กาแฟ สตาร์บัคส์ 150 บาท"
        text2 = "กาแฟ starbucks 150 บาท"  # Similar but slightly different

        # Act
        result1 = await processor_no_ai.process_text_fast(text1, "th")
        result2 = await processor_no_ai.process_text_fast(text2, "th")

        # Assert
        assert result1["amount"] == result2["amount"]
        assert result1["category"] == result2["category"]
        # Second result might be from similarity cache
        assert result2["method"] in ["pattern", "similarity_cache", "cache_pattern"]

    @pytest.mark.asyncio
    async def test_ai_fallback_when_pattern_fails(self, processor):
        """Test AI fallback when pattern matching fails."""
        # Arrange
        text = "some complex spending description that doesn't match patterns"

        # Act
        result = await processor.process_text_fast(text, "en")

        # Assert
        assert result["method"] == "ai"
        assert result["amount"] == 150.0  # From mock
        assert result["confidence"] == 0.8

    @pytest.mark.asyncio
    async def test_fallback_processing_when_all_fails(self, processor_no_ai):
        """Test fallback processing when patterns and AI fail."""
        # Arrange
        text = "random text with amount 250 but no clear pattern"

        # Act
        result = await processor_no_ai.process_text_fast(text, "en")

        # Assert
        assert result["method"] == "fallback"
        assert result["amount"] == 250.0  # Extracted from text
        assert result["category"] == "Miscellaneous"
        assert result["confidence"] < 0.5

    @pytest.mark.asyncio
    async def test_payment_method_inference(self, processor_no_ai):
        """Test payment method inference from text."""
        # Arrange
        test_cases = [
            ("กาแฟ 100 บาท ด้วยบัตรเครดิต", "Credit Card"),
            ("taxi 150 baht cash", "Cash"),
            ("โอนเงิน 200 บาท", "Bank Transfer"),
            ("mobile payment 300 baht", "Bank Transfer"),
        ]

        for text, expected_payment in test_cases:
            # Act
            result = await processor_no_ai.process_text_fast(text, "auto")

            # Assert
            assert result["payment_method"] == expected_payment

    @pytest.mark.asyncio
    async def test_category_inference_from_keywords(self, processor_no_ai):
        """Test category inference from keywords."""
        # Arrange
        test_cases = [
            ("ซื้อของ 500 บาท", "Shopping"),
            ("buy groceries 300 baht", "Shopping"),
            ("เดินทาง 100 บาท", "Transportation"),
            ("travel expense 200 baht", "Transportation"),
        ]

        for text, expected_category in test_cases:
            # Act
            result = await processor_no_ai.process_text_fast(text, "auto")

            # Assert
            assert result["category"] == expected_category

    @pytest.mark.asyncio
    async def test_processing_time_performance(self, processor_no_ai):
        """Test processing time performance."""
        # Arrange
        text = "กาแฟ 150 บาท"

        # Act
        result = await processor_no_ai.process_text_fast(text, "th")

        # Assert
        assert result["processing_time_ms"] < 1000  # Should be under 1 second
        assert "processing_time_ms" in result

    @pytest.mark.asyncio
    async def test_confidence_scoring(self, processor_no_ai):
        """Test confidence scoring for different scenarios."""
        # Arrange
        test_cases = [
            ("กาแฟ สตาร์บัคส์ 150 บาท", 0.8),  # High confidence - clear pattern
            ("150 บาท", 0.5),  # Medium confidence - generic amount
            ("some random text", 0.3),  # Low confidence - fallback
        ]

        for text, min_confidence in test_cases:
            # Act
            result = await processor_no_ai.process_text_fast(text, "th")

            # Assert
            assert result["confidence"] >= min_confidence

    @pytest.mark.asyncio
    async def test_error_handling(self, processor_no_ai):
        """Test error handling for invalid inputs."""
        # Arrange
        invalid_texts = ["", "   ", "no numbers here"]

        for text in invalid_texts:
            # Act
            result = await processor_no_ai.process_text_fast(text, "en")

            # Assert
            assert "error" in result or result["amount"] == 0
            assert "processing_time_ms" in result

    @pytest.mark.asyncio
    async def test_ai_timeout_handling(self, processor):
        """Test AI timeout handling."""
        # Arrange
        processor._llama_client.parse_spending_text.side_effect = TimeoutError()
        text = "complex spending text"

        # Act
        result = await processor.process_text_fast(text, "en")

        # Assert
        assert result["method"] == "timeout_fallback"
        assert "processing_time_ms" in result

    def test_cache_stats(self, processor_no_ai):
        """Test cache statistics."""
        # Act
        stats = processor_no_ai.get_cache_stats()

        # Assert
        assert "cache_size" in stats
        assert "hit_rate_percent" in stats
        assert "patterns_count" in stats
        assert stats["processor_type"] == "enhanced_with_intelligent_cache"

    def test_processing_stats(self, processor_no_ai):
        """Test processing statistics."""
        # Act
        stats = processor_no_ai.get_processing_stats()

        # Assert
        assert "cache_performance" in stats
        assert "pattern_count" in stats
        assert "target_response_time_ms" in stats
        assert stats["target_response_time_ms"] == 3000
        assert stats["cache_first_strategy"] is True

    @pytest.mark.asyncio
    async def test_language_auto_detection(self, processor_no_ai):
        """Test automatic language detection."""
        # Arrange
        thai_text = "กาแฟ 150 บาท"
        english_text = "coffee 150 baht"

        # Act
        thai_result = await processor_no_ai.process_text_fast(thai_text, "auto")
        english_result = await processor_no_ai.process_text_fast(english_text, "auto")

        # Assert
        assert thai_result["amount"] == 150.0
        assert english_result["amount"] == 150.0
        assert thai_result["category"] == "Food & Dining"
        assert english_result["category"] == "Food & Dining"

    @pytest.mark.asyncio
    async def test_multiple_amounts_handling(self, processor_no_ai):
        """Test handling of text with multiple amounts."""
        # Arrange
        text = "bought items for 100 baht and 200 baht"

        # Act
        result = await processor_no_ai.process_text_fast(text, "en")

        # Assert
        # Should pick the first valid amount
        assert result["amount"] in [100.0, 200.0]
        assert result["category"] == "Shopping"

    @pytest.mark.asyncio
    async def test_currency_normalization(self, processor_no_ai):
        """Test currency symbol normalization."""
        # Arrange
        test_cases = [
            "coffee 150฿",
            "coffee 150 THB",
            "coffee 150 baht",
            "กาแฟ 150 บาท",
        ]

        for text in test_cases:
            # Act
            result = await processor_no_ai.process_text_fast(text, "auto")

            # Assert
            assert result["amount"] == 150.0
            assert result["currency"] == "THB"

    def test_clear_cache(self, processor_no_ai):
        """Test cache clearing functionality."""
        # Act
        processor_no_ai.clear_cache()
        stats = processor_no_ai.get_cache_stats()

        # Assert
        assert stats["cache_size"] == 0
        assert stats["hit_count"] == 0
        assert stats["miss_count"] == 0


class TestSpendingPattern:
    """Unit tests for SpendingPattern class."""

    def test_pattern_creation(self):
        """Test spending pattern creation."""
        # Arrange & Act
        pattern = SpendingPattern(
            name="test_pattern",
            pattern=r"test (\d+) baht",
            category="Test Category",
            confidence=0.9,
            extract_amount=lambda m: float(m.group(1)),
        )

        # Assert
        assert pattern.name == "test_pattern"
        assert pattern.category == "Test Category"
        assert pattern.confidence == 0.9
        assert pattern.pattern.pattern == r"test (\d+) baht"

    def test_pattern_matching(self):
        """Test pattern matching functionality."""
        # Arrange
        pattern = SpendingPattern(
            name="test_pattern",
            pattern=r"coffee (\d+) baht",
            category="Food & Dining",
            confidence=0.8,
            extract_amount=lambda m: float(m.group(1)),
        )

        # Act
        match = pattern.pattern.search("coffee 150 baht")

        # Assert
        assert match is not None
        assert pattern.extract_amount(match) == 150.0

    def test_pattern_no_match(self):
        """Test pattern when no match found."""
        # Arrange
        pattern = SpendingPattern(
            name="test_pattern",
            pattern=r"coffee (\d+) baht",
            category="Food & Dining",
            confidence=0.8,
            extract_amount=lambda m: float(m.group(1)),
        )

        # Act
        match = pattern.pattern.search("taxi 100 baht")

        # Assert
        assert match is None
