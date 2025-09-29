"""Simple unit tests for ProcessingMethod value object."""

import pytest

from ai_service.domain.value_objects.processing_method import ProcessingMethod


@pytest.mark.unit
class TestProcessingMethod:
    """Test ProcessingMethod value object."""

    def test_processing_method_values(self):
        """Test ProcessingMethod enum values."""
        assert ProcessingMethod.MANUAL_ENTRY == "manual_entry"
        assert ProcessingMethod.OCR_PROCESSING == "ocr_processing"
        assert ProcessingMethod.NLP_PARSING == "nlp_parsing"
        assert ProcessingMethod.LLAMA_ENHANCED == "llama_enhanced"

    def test_processing_method_properties(self):
        """Test processing method properties."""
        manual = ProcessingMethod.MANUAL_ENTRY
        nlp_only = ProcessingMethod.NLP_PARSING
        llama_enhanced = ProcessingMethod.LLAMA_ENHANCED
        nlp_ai = ProcessingMethod.NLP_AI

        # AI enhancement
        assert not manual.is_ai_enhanced()
        assert not nlp_only.is_ai_enhanced()  # NLP alone is not AI enhanced
        assert llama_enhanced.is_ai_enhanced()
        assert nlp_ai.is_ai_enhanced()  # NLP + AI is AI enhanced

        # Local processing
        assert manual.is_local_processing()
        assert nlp_only.is_local_processing()
        assert llama_enhanced.is_local_processing()

        # Display names
        assert manual.get_display_name() == "Manual Entry"
        assert nlp_only.get_display_name() == "NLP Parsing"
        assert llama_enhanced.get_display_name() == "Llama4 Enhanced"
