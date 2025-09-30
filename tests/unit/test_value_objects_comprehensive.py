"""Comprehensive unit tests for value objects to improve coverage."""

import pytest

from ai_service.domain.value_objects.confidence import ConfidenceScore
from ai_service.domain.value_objects.processing_method import (
    ProcessingMetadata,
    ProcessingMethod,
)
from ai_service.domain.value_objects.spending_category import (
    CategoryConfidence,
    PaymentMethod,
    SpendingCategory,
)
from ai_service.domain.value_objects.text_content import Language, TextContent


@pytest.mark.unit
class TestConfidenceScoreComprehensive:
    """Comprehensive tests for ConfidenceScore value object."""

    def test_from_percentage(self):
        """Test creating confidence from percentage."""
        conf = ConfidenceScore.from_percentage(85.0)
        assert conf.value == 0.85
        assert conf.to_percentage() == 85.0

    def test_from_percentage_invalid(self):
        """Test invalid percentage values."""
        with pytest.raises(ValueError, match="Percentage must be between 0 and 100"):
            ConfidenceScore.from_percentage(150.0)
        with pytest.raises(ValueError, match="Percentage must be between 0 and 100"):
            ConfidenceScore.from_percentage(-10.0)

    def test_factory_methods(self):
        """Test factory methods."""
        assert ConfidenceScore.low().value == 0.3
        assert ConfidenceScore.medium().value == 0.6
        assert ConfidenceScore.high().value == 0.9
        assert ConfidenceScore.perfect().value == 1.0
        assert ConfidenceScore.zero().value == 0.0

    def test_classification_methods(self):
        """Test classification methods."""
        low = ConfidenceScore.low()
        medium = ConfidenceScore.medium()
        high = ConfidenceScore.high()

        assert low.is_low()
        assert not low.is_medium()
        assert not low.is_high()
        assert not low.is_acceptable()

        assert medium.is_medium()
        assert not medium.is_low()
        assert not medium.is_high()

        assert high.is_high()
        assert not high.is_medium()
        assert not high.is_low()
        assert high.is_acceptable()

    def test_boost_and_reduce(self):
        """Test boost and reduce operations."""
        conf = ConfidenceScore.medium()

        boosted = conf.boost(0.2)
        assert boosted.value == 0.8

        # Test capping at 1.0
        high_conf = ConfidenceScore.high()
        capped = high_conf.boost(0.5)
        assert capped.value == 1.0

        reduced = conf.reduce(0.1)
        assert reduced.value == 0.5

        # Test flooring at 0.0
        low_conf = ConfidenceScore.low()
        floored = low_conf.reduce(0.5)
        assert floored.value == 0.0

    def test_combine_with(self):
        """Test combining confidence scores."""
        conf1 = ConfidenceScore(0.8)
        conf2 = ConfidenceScore(0.6)

        combined = conf1.combine_with(conf2)
        expected = (0.8 * 0.6) ** 0.5
        assert abs(combined.value - expected) < 1e-9

    def test_string_representation(self):
        """Test string representation."""
        high = ConfidenceScore.high()
        medium = ConfidenceScore.medium()
        low = ConfidenceScore.low()

        assert "High" in str(high)
        assert "Medium" in str(medium)
        assert "Low" in str(low)

    def test_comparisons(self):
        """Test comparison operations."""
        low = ConfidenceScore.low()
        medium = ConfidenceScore.medium()
        high = ConfidenceScore.high()

        assert low < medium < high
        assert high > medium > low
        assert low <= medium <= high
        assert high >= medium >= low


@pytest.mark.unit
class TestSpendingCategoryComprehensive:
    """Comprehensive tests for SpendingCategory."""

    def test_from_thai_text(self):
        """Test Thai text mapping."""
        assert SpendingCategory.from_thai_text("อาหาร") == SpendingCategory.FOOD_DINING
        assert SpendingCategory.from_thai_text("รถ") == SpendingCategory.TRANSPORTATION
        assert SpendingCategory.from_thai_text("ทำบุญ") == SpendingCategory.MERIT_MAKING
        assert (
            SpendingCategory.from_thai_text("ไม่รู้จัก") == SpendingCategory.MISCELLANEOUS
        )

    def test_from_text(self):
        """Test category values."""
        # Testing the enum values since from_text method doesn't exist
        assert SpendingCategory.FOOD_DINING.value == "Food & Dining"
        assert SpendingCategory.TRANSPORTATION.value == "Transportation"
        assert SpendingCategory.GROCERIES.value == "Groceries"
        assert SpendingCategory.MISCELLANEOUS.value == "Miscellaneous"

    def test_thai_names(self):
        """Test Thai name retrieval."""
        food_thai = SpendingCategory.FOOD_DINING.get_thai_name()
        assert "อาหาร" in food_thai

        merit_thai = SpendingCategory.MERIT_MAKING.get_thai_name()
        assert "ทำบุญ" in merit_thai

    def test_category_properties(self):
        """Test category properties."""
        # Cultural categories
        assert SpendingCategory.MERIT_MAKING.is_cultural()
        assert SpendingCategory.TEMPLE_DONATIONS.is_cultural()
        assert not SpendingCategory.FOOD_DINING.is_cultural()

        # Essential categories
        assert SpendingCategory.FOOD_DINING.is_essential()
        assert SpendingCategory.HEALTHCARE.is_essential()
        assert not SpendingCategory.ENTERTAINMENT.is_essential()

        # Test existing methods
        assert not SpendingCategory.ENTERTAINMENT.is_cultural()
        assert not SpendingCategory.SHOPPING.is_essential()

    def test_budget_info(self):
        """Test category information."""
        # Test basic category properties since get_budget_info doesn't exist
        assert SpendingCategory.FOOD_DINING.value == "Food & Dining"
        assert SpendingCategory.FOOD_DINING.name == "FOOD_DINING"


@pytest.mark.unit
class TestPaymentMethodComprehensive:
    """Comprehensive tests for PaymentMethod."""

    def test_from_thai_text(self):
        """Test Thai text mapping."""
        assert PaymentMethod.from_thai_text("เงินสด") == PaymentMethod.CASH
        assert PaymentMethod.from_thai_text("บัตรเครดิต") == PaymentMethod.CREDIT_CARD
        assert PaymentMethod.from_thai_text("พร้อมเพย์") == PaymentMethod.PROMPTPAY
        assert PaymentMethod.from_thai_text("ไม่รู้") == PaymentMethod.OTHER

    def test_from_text(self):
        """Test payment method values."""
        # Testing the enum values since from_text method doesn't exist
        assert PaymentMethod.CASH.value == "Cash"
        assert PaymentMethod.CREDIT_CARD.value == "Credit Card"
        assert PaymentMethod.PROMPTPAY.value == "PromptPay"
        assert PaymentMethod.OTHER.value == "Other"

    def test_thai_names(self):
        """Test Thai name retrieval."""
        cash_thai = PaymentMethod.CASH.get_thai_name()
        assert cash_thai == "เงินสด"

        promptpay_thai = PaymentMethod.PROMPTPAY.get_thai_name()
        assert promptpay_thai == "พร้อมเพย์"

    def test_payment_properties(self):
        """Test payment method properties."""
        # Digital methods
        assert PaymentMethod.CREDIT_CARD.is_digital()
        assert PaymentMethod.PROMPTPAY.is_digital()
        assert not PaymentMethod.CASH.is_digital()

        # Instant methods
        assert PaymentMethod.CASH.is_instant()
        assert PaymentMethod.PROMPTPAY.is_instant()
        assert not PaymentMethod.CREDIT_CARD.is_instant()

        # Test existing methods
        assert PaymentMethod.CREDIT_CARD.is_digital()
        assert PaymentMethod.PROMPTPAY.is_instant()
        assert not PaymentMethod.CASH.is_digital()


@pytest.mark.unit
class TestProcessingMethodComprehensive:
    """Comprehensive tests for ProcessingMethod."""

    def test_method_properties(self):
        """Test processing method properties."""
        # AI enhanced methods
        assert ProcessingMethod.LLAMA_ENHANCED.is_ai_enhanced()
        assert ProcessingMethod.OPENAI_ENHANCED.is_ai_enhanced()
        assert not ProcessingMethod.MANUAL_ENTRY.is_ai_enhanced()

        # Local processing
        assert ProcessingMethod.MANUAL_ENTRY.is_local_processing()
        assert ProcessingMethod.LLAMA_ENHANCED.is_local_processing()
        assert not ProcessingMethod.OPENAI_ENHANCED.is_local_processing()

        # Automated methods
        assert ProcessingMethod.OCR_PROCESSING.is_automated()
        assert ProcessingMethod.LLAMA_ENHANCED.is_automated()
        assert not ProcessingMethod.MANUAL_ENTRY.is_automated()

    def test_display_names(self):
        """Test display names."""
        manual_display = ProcessingMethod.MANUAL_ENTRY.get_display_name()
        assert manual_display == "Manual Entry"

        llama_display = ProcessingMethod.LLAMA_ENHANCED.get_display_name()
        assert llama_display == "Llama4 Enhanced"

    def test_thai_names(self):
        """Test Thai display names."""
        manual_thai = ProcessingMethod.MANUAL_ENTRY.get_thai_name()
        assert "กรอกข้อมูลเอง" in manual_thai


@pytest.mark.unit
class TestTextContentComprehensive:
    """Comprehensive tests for TextContent."""

    def test_from_raw_input(self):
        """Test creating from raw input."""
        text = TextContent.from_raw_input("  Hello   world  ")
        assert text.content == "Hello world"

    def test_language_detection(self):
        """Test language detection."""
        english_text = TextContent.from_raw_input("Hello world")
        assert english_text.language == Language.ENGLISH

        thai_text = TextContent.from_raw_input("สวัสดีครับ")
        assert thai_text.language == Language.THAI

        mixed_text = TextContent.from_raw_input("Hello สวัสดี")
        assert mixed_text.language == Language.MIXED

    def test_word_count(self):
        """Test word counting."""
        text = TextContent.from_raw_input("Hello world test")
        assert text.get_word_count() == 3

    def test_number_extraction(self):
        """Test number extraction."""
        text = TextContent.from_raw_input("I spent 120.50 baht and got 15% discount")
        numbers = text.extract_numbers()
        assert 120.50 in numbers
        assert 15.0 in numbers

    def test_currency_mentions(self):
        """Test currency mention extraction."""
        text = TextContent.from_raw_input("I spent 100 baht and $50")
        currencies = text.extract_currency_mentions()
        assert any("baht" in c for c in currencies)
        assert any("$" in c for c in currencies)

    def test_spending_text_detection(self):
        """Test spending text detection."""
        spending_text = TextContent.from_raw_input("I bought coffee for 50 baht")
        assert spending_text.is_likely_spending_text()

        non_spending_text = TextContent.from_raw_input("The weather is nice today")
        assert not non_spending_text.is_likely_spending_text()

    def test_complexity_score(self):
        """Test complexity scoring."""
        simple_text = TextContent.from_raw_input("Coffee 100")
        complex_text = TextContent.from_raw_input(
            "I bought expensive coffee at the fancy café for 150 baht with my credit card"
        )

        assert simple_text.get_complexity_score() < complex_text.get_complexity_score()

    def test_truncation(self):
        """Test text truncation."""
        long_text = TextContent.from_raw_input("A" * 200)
        truncated = long_text.truncate(50)
        assert len(truncated) <= 50
        assert truncated.endswith("...")

    def test_validation(self):
        """Test text validation."""
        with pytest.raises(
            ValueError, match="Content cannot be empty or whitespace only"
        ):
            TextContent.from_raw_input("")

        with pytest.raises(
            ValueError, match="Content cannot be empty or whitespace only"
        ):
            TextContent.from_raw_input("   ")

        with pytest.raises(ValueError, match="Content too long"):
            TextContent.from_raw_input("A" * 20000)  # Too long


@pytest.mark.unit
class TestCategoryConfidence:
    """Test CategoryConfidence dataclass."""

    def test_creation(self):
        """Test creating category confidence."""
        cat_conf = CategoryConfidence(
            category=SpendingCategory.FOOD_DINING,
            confidence=0.8,
            reasoning="Contains food keywords",
        )
        assert cat_conf.category == SpendingCategory.FOOD_DINING
        assert cat_conf.confidence == 0.8
        assert cat_conf.reasoning == "Contains food keywords"

    def test_reliability(self):
        """Test reliability check."""
        reliable = CategoryConfidence(SpendingCategory.FOOD_DINING, 0.8)
        unreliable = CategoryConfidence(SpendingCategory.FOOD_DINING, 0.5)

        assert reliable.is_reliable()
        assert not unreliable.is_reliable()

    def test_validation(self):
        """Test confidence validation."""
        with pytest.raises(
            ValueError, match=r"Confidence must be between 0\.0 and 1\.0"
        ):
            CategoryConfidence(SpendingCategory.FOOD_DINING, 1.5)

        with pytest.raises(
            ValueError, match=r"Confidence must be between 0\.0 and 1\.0"
        ):
            CategoryConfidence(SpendingCategory.FOOD_DINING, -0.1)


@pytest.mark.unit
class TestProcessingMetadata:
    """Test ProcessingMetadata dataclass."""

    def test_creation(self):
        """Test creating processing metadata."""
        metadata = ProcessingMetadata(
            method=ProcessingMethod.LLAMA_ENHANCED,
            processing_time_ms=150,
            model_used="llama3.2:3b",
        )

        assert metadata.method == ProcessingMethod.LLAMA_ENHANCED
        assert metadata.processing_time_ms == 150
        assert metadata.model_used == "llama3.2:3b"

    def test_optional_fields(self):
        """Test optional field handling."""
        metadata = ProcessingMetadata(method=ProcessingMethod.MANUAL_ENTRY)
        assert metadata.processing_time_ms is None
        assert metadata.model_used is None
        assert metadata.api_calls_made == 0
        assert metadata.cost_incurred == 0.0
