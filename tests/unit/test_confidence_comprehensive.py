"""Comprehensive tests for Confidence value object."""


import pytest

from src.ai_service.domain.value_objects.confidence import ConfidenceScore


class TestConfidenceScore:
    """Test ConfidenceScore value object."""

    def test_valid_confidence_creation(self):
        """Test creating valid confidence scores."""
        confidence = ConfidenceScore(0.85)
        assert confidence.value == 0.85
        assert confidence.to_percentage() == 85.0

    def test_confidence_from_percentage(self):
        """Test creating confidence from percentage."""
        confidence = ConfidenceScore.from_percentage(75)
        assert confidence.value == 0.75
        assert confidence.to_percentage() == 75.0

    def test_confidence_boundaries(self):
        """Test confidence at boundaries."""
        # Minimum
        min_confidence = ConfidenceScore(0.0)
        assert min_confidence.value == 0.0
        assert min_confidence.to_percentage() == 0.0

        # Maximum
        max_confidence = ConfidenceScore(1.0)
        assert max_confidence.value == 1.0
        assert max_confidence.to_percentage() == 100.0

    def test_invalid_confidence_values(self):
        """Test invalid confidence values raise errors."""
        with pytest.raises(
            ValueError, match="Confidence score must be between 0.0 and 1.0"
        ):
            ConfidenceScore(-0.1)

        with pytest.raises(
            ValueError, match="Confidence score must be between 0.0 and 1.0"
        ):
            ConfidenceScore(1.1)

        with pytest.raises(
            ValueError, match="Confidence score must be between 0.0 and 1.0"
        ):
            ConfidenceScore(2.0)

    def test_confidence_comparison(self):
        """Test confidence comparison operations."""
        low = ConfidenceScore(0.3)
        medium = ConfidenceScore(0.6)
        high = ConfidenceScore(0.9)

        assert low < medium
        assert medium < high
        assert low < high
        assert high > medium
        assert medium > low

    def test_confidence_equality(self):
        """Test confidence equality."""
        conf1 = ConfidenceScore(0.75)
        conf2 = ConfidenceScore(0.75)
        conf3 = ConfidenceScore(0.80)

        assert conf1 == conf2
        assert conf1 != conf3
        assert hash(conf1) == hash(conf2)
        assert hash(conf1) != hash(conf3)

    def test_confidence_levels(self):
        """Test confidence level classifications."""
        low = ConfidenceScore(0.3)
        medium = ConfidenceScore(0.6)
        high = ConfidenceScore(0.8)

        assert low.is_low()
        assert not low.is_medium()
        assert not low.is_high()

        assert medium.is_medium()
        assert not medium.is_low()
        assert not medium.is_high()

        assert high.is_high()
        assert not high.is_medium()
        assert not high.is_low()

    def test_confidence_string_representation(self):
        """Test string representation of confidence."""
        confidence = ConfidenceScore(0.75)
        assert str(confidence) == "75.0% (Medium)"
        assert repr(confidence) == "ConfidenceScore(0.75)"

    def test_confidence_arithmetic(self):
        """Test confidence arithmetic operations."""
        conf1 = ConfidenceScore(0.6)
        conf2 = ConfidenceScore(0.3)

        # Boost (increase)
        result_boost = conf1.boost(0.1)
        assert result_boost.value == 0.7

        # Reduce (decrease)
        result_reduce = conf1.reduce(0.1)
        assert result_reduce.value == 0.5

        # Combine with other (uses geometric mean)
        result_combine = conf1.combine_with(conf2)
        assert abs(result_combine.value - 0.424) < 0.01  # Approximately geometric mean

    def test_confidence_boost_clamping(self):
        """Test confidence boost clamping to valid range."""
        # Test boost that would exceed 1.0
        high_conf = ConfidenceScore(0.95)
        result = high_conf.boost(0.1)
        assert result.value == 1.0  # Should be clamped

    def test_confidence_reduce_clamping(self):
        """Test confidence reduce clamping to valid range."""
        # Test reduce that would go below 0.0
        low_conf = ConfidenceScore(0.05)
        result = low_conf.reduce(0.1)
        assert result.value == 0.0  # Should be clamped

    def test_confidence_class_methods(self):
        """Test confidence class methods."""
        assert ConfidenceScore.zero().value == 0.0
        assert ConfidenceScore.low().value == 0.3
        assert ConfidenceScore.medium().value == 0.6
        assert ConfidenceScore.high().value == 0.9
        assert ConfidenceScore.perfect().value == 1.0

    def test_confidence_acceptable(self):
        """Test confidence acceptable threshold."""
        low = ConfidenceScore(0.4)
        high = ConfidenceScore(0.8)

        assert not low.is_acceptable()
        assert high.is_acceptable()
