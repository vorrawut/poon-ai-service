"""Unit tests for AI learning service."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from src.ai_service.application.services.ai_learning_service import AILearningService
from src.ai_service.domain.entities.ai_training_data import (
    AITrainingData,
    AITrainingDataId,
    FeedbackType,
    ProcessingStatus,
)
from src.ai_service.domain.repositories.ai_training_repository import (
    AITrainingRepository,
)


class TestAILearningService:
    """Unit tests for AILearningService."""

    @pytest.fixture
    def mock_repository(self):
        """Create mock training repository."""
        return AsyncMock(spec=AITrainingRepository)

    @pytest.fixture
    def ai_service(self, mock_repository):
        """Create AI learning service with mocked repository."""
        return AILearningService(mock_repository)

    @pytest.mark.asyncio
    async def test_record_ai_interaction_creates_training_data(
        self, ai_service, mock_repository
    ):
        """Test that recording AI interaction creates proper training data."""
        # Arrange
        input_text = "Buy coffee 150 baht"
        language = "en"
        raw_response = '{"amount": 150, "currency": "THB", "category": "food"}'
        parsed_data = {"amount": 150, "currency": "THB", "category": "food"}
        confidence = 0.9
        processing_time = 800
        model_version = "llama3.2:3b"

        # Act
        result = await ai_service.record_ai_interaction(
            input_text=input_text,
            language=language,
            raw_ai_response=raw_response,
            parsed_ai_data=parsed_data,
            ai_confidence=confidence,
            processing_time_ms=processing_time,
            model_version=model_version,
            user_id="user123",
            session_id="session456",
        )

        # Assert
        assert isinstance(result, AITrainingData)
        assert result.input_text == input_text
        assert result.language == language
        assert result.raw_ai_response == raw_response
        assert result.parsed_ai_data == parsed_data
        assert result.ai_confidence.value == confidence
        assert result.processing_time_ms == processing_time
        assert result.model_version == model_version
        assert result.user_id == "user123"
        assert result.session_id == "session456"
        assert result.status == ProcessingStatus.SUCCESS

        mock_repository.save.assert_called_once_with(result)

    @pytest.mark.asyncio
    async def test_record_processing_failure_marks_as_failed(
        self, ai_service, mock_repository
    ):
        """Test that recording processing failure marks data as failed."""
        # Arrange
        input_text = "invalid text"
        language = "en"
        error_message = "Failed to parse"
        validation_errors = ["Missing amount", "Invalid format"]

        # Act
        result = await ai_service.record_processing_failure(
            input_text=input_text,
            language=language,
            error_message=error_message,
            raw_ai_response="",
            validation_errors=validation_errors,
        )

        # Assert
        assert result.status == ProcessingStatus.FAILED_VALIDATION
        assert result.error_message == error_message
        assert result.validation_errors == validation_errors
        mock_repository.save.assert_called_once_with(result)

    @pytest.mark.asyncio
    async def test_add_user_feedback_success(self, ai_service, mock_repository):
        """Test adding user feedback successfully."""
        # Arrange
        training_data_id = "test-id"
        training_data = AITrainingData(
            id=AITrainingDataId.from_string(training_data_id),
            input_text="test text",
            language="en",
            parsed_ai_data={"category": "food", "amount": 100},
        )
        mock_repository.find_by_id.return_value = training_data
        mock_repository.get_category_mapping_insights.return_value = {}

        corrected_data = {"category": "dining", "amount": 120}

        # Act
        result = await ai_service.add_user_feedback(
            training_data_id=training_data_id,
            feedback_type=FeedbackType.USER_CORRECTION,
            corrected_data=corrected_data,
            admin_notes="User correction",
        )

        # Assert
        assert result is True
        assert training_data.feedback_provided is True
        assert training_data.feedback_type == FeedbackType.USER_CORRECTION
        assert training_data.corrected_data == corrected_data
        assert training_data.admin_notes == "User correction"
        mock_repository.save.assert_called_once_with(training_data)

    @pytest.mark.asyncio
    async def test_add_user_feedback_training_data_not_found(
        self, ai_service, mock_repository
    ):
        """Test adding feedback when training data is not found."""
        # Arrange
        mock_repository.find_by_id.return_value = None

        # Act
        result = await ai_service.add_user_feedback(
            training_data_id="nonexistent-id",
            feedback_type=FeedbackType.USER_CORRECTION,
            corrected_data={"category": "food"},
        )

        # Assert
        assert result is False
        mock_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_dynamic_category_mapping_caches_results(
        self, ai_service, mock_repository
    ):
        """Test that category mappings are cached."""
        # Arrange
        learned_mappings = {"restaurant": "Food & Dining", "hotel": "Travel"}
        mock_repository.get_category_mapping_insights.return_value = learned_mappings

        # Act - First call
        result1 = await ai_service.get_dynamic_category_mapping()
        # Act - Second call (should use cache)
        result2 = await ai_service.get_dynamic_category_mapping()

        # Assert - Should contain learned mappings plus comprehensive ones
        assert "restaurant" in result1
        assert result1["restaurant"] == "Food & Dining"
        assert "hotel" in result1
        assert result1["hotel"] == "Travel"
        assert result1 == result2  # Should be identical (cached)
        # Repository should only be called once due to caching
        mock_repository.get_category_mapping_insights.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_dynamic_category_mapping_cache_expires(
        self, ai_service, mock_repository
    ):
        """Test that category mapping cache expires after time."""
        # Arrange
        expected_mappings = {"restaurant": "Food & Dining"}
        mock_repository.get_category_mapping_insights.return_value = expected_mappings

        # Act - First call
        await ai_service.get_dynamic_category_mapping()

        # Simulate cache expiry by setting last update to old time
        ai_service._last_cache_update = datetime.utcnow() - timedelta(hours=2)

        # Act - Second call (should refresh cache)
        result = await ai_service.get_dynamic_category_mapping()

        # Assert - Should contain learned mappings plus comprehensive ones
        assert "restaurant" in result
        assert result["restaurant"] == "Food & Dining"
        # Repository should be called twice due to cache expiry
        assert mock_repository.get_category_mapping_insights.call_count == 2

    @pytest.mark.asyncio
    async def test_get_processing_insights_aggregates_data(
        self, ai_service, mock_repository
    ):
        """Test that processing insights aggregate data from repository."""
        # Arrange
        mock_repository.get_accuracy_stats.return_value = {
            "total_cases": 100,
            "avg_accuracy": 0.85,
            "avg_confidence": 0.78,
            "success_rate": 0.92,
        }
        mock_repository.count_by_status.return_value = {
            "success": 85,
            "failed_validation": 10,
            "pending_review": 5,
        }
        mock_repository.get_common_error_patterns.return_value = [
            {"error_pattern": "Invalid currency", "count": 8}
        ]
        mock_repository.get_category_mapping_insights.return_value = {
            "restaurant": "Food & Dining"
        }

        # Act
        insights = await ai_service.get_processing_insights()

        # Assert
        assert "overall_stats" in insights
        assert "status_distribution" in insights
        assert "common_errors" in insights
        assert "learned_category_mappings" in insights
        assert "total_mappings_learned" in insights

        assert insights["overall_stats"]["total_cases"] == 100
        assert insights["status_distribution"]["success"] == 85
        assert len(insights["common_errors"]) == 1
        assert insights["total_mappings_learned"] == 1

    @pytest.mark.asyncio
    async def test_get_improvement_suggestions_identifies_issues(
        self, ai_service, mock_repository
    ):
        """Test that improvement suggestions identify various issues."""
        # Arrange
        low_accuracy_cases = [
            AITrainingData(input_text="test1", language="en"),
            AITrainingData(input_text="test2", language="en"),
        ]
        failed_cases = [AITrainingData(input_text="test3", language="th")]
        thai_cases = [
            AITrainingData(
                input_text="test4",
                language="th",
                status=ProcessingStatus.FAILED_VALIDATION,
            ),
            AITrainingData(
                input_text="test5", language="th", status=ProcessingStatus.SUCCESS
            ),
            AITrainingData(
                input_text="test6",
                language="th",
                status=ProcessingStatus.FAILED_VALIDATION,
            ),
        ]

        mock_repository.find_low_accuracy_cases.return_value = low_accuracy_cases
        mock_repository.find_failed_cases.return_value = failed_cases
        mock_repository.find_by_language.return_value = thai_cases

        # Act
        suggestions = await ai_service.get_improvement_suggestions()

        # Assert
        assert len(suggestions) >= 3

        # Check for accuracy improvement suggestion
        accuracy_suggestion = next(
            (s for s in suggestions if s["type"] == "accuracy_improvement"), None
        )
        assert accuracy_suggestion is not None
        assert accuracy_suggestion["cases_count"] == 2
        assert accuracy_suggestion["priority"] == "high"

        # Check for error reduction suggestion
        error_suggestion = next(
            (s for s in suggestions if s["type"] == "error_reduction"), None
        )
        assert error_suggestion is not None
        assert error_suggestion["cases_count"] == 1

        # Check for language-specific suggestion (Thai has 66% failure rate)
        lang_suggestion = next(
            (s for s in suggestions if s["type"] == "language_improvement"), None
        )
        assert lang_suggestion is not None
        assert lang_suggestion["language"] == "th"
        assert abs(lang_suggestion["failure_rate"] - 0.67) < 0.01  # 2/3 ≈ 0.67

    @pytest.mark.asyncio
    async def test_find_similar_successful_cases_filters_by_status(
        self, ai_service, mock_repository
    ):
        """Test that similar cases are filtered to only successful ones."""
        # Arrange
        similar_cases = [
            AITrainingData(
                input_text="coffee 100", language="en", status=ProcessingStatus.SUCCESS
            ),
            AITrainingData(
                input_text="coffee 150",
                language="en",
                status=ProcessingStatus.FAILED_VALIDATION,
            ),
            AITrainingData(
                input_text="coffee 200", language="en", status=ProcessingStatus.SUCCESS
            ),
        ]
        mock_repository.find_similar_inputs.return_value = similar_cases

        # Act
        result = await ai_service.find_similar_successful_cases("coffee 120", "en")

        # Assert
        assert len(result) == 2  # Only successful cases
        assert all(case.status == ProcessingStatus.SUCCESS for case in result)
        mock_repository.find_similar_inputs.assert_called_once_with(
            "coffee 120", "en", limit=5
        )

    @pytest.mark.asyncio
    async def test_cleanup_old_data_calls_repository(self, ai_service, mock_repository):
        """Test that cleanup calls repository with correct parameters."""
        # Arrange
        mock_repository.delete_old_data.return_value = 42

        # Act
        result = await ai_service.cleanup_old_data(days_to_keep=180)

        # Assert
        assert result == 42
        mock_repository.delete_old_data.assert_called_once_with(180)

    @pytest.mark.asyncio
    async def test_get_confidence_calibration_report_calculates_gap(
        self, ai_service, mock_repository
    ):
        """Test confidence calibration report calculation."""
        # Arrange
        mock_repository.get_accuracy_stats.return_value = {
            "avg_confidence": 0.85,
            "avg_accuracy": 0.78,
        }

        # Act
        report = await ai_service.get_confidence_calibration_report()

        # Assert
        assert report["average_confidence"] == 0.85
        assert report["average_accuracy"] == 0.78
        assert abs(report["confidence_accuracy_gap"] - 0.07) < 0.01
        assert "recommendation" in report

    @pytest.mark.asyncio
    async def test_error_handling_in_get_processing_insights(
        self, ai_service, mock_repository
    ):
        """Test error handling in get_processing_insights."""
        # Arrange
        mock_repository.get_accuracy_stats.side_effect = Exception("Database error")

        # Act
        insights = await ai_service.get_processing_insights()

        # Assert
        assert insights == {}  # Should return empty dict on error

    @pytest.mark.asyncio
    async def test_error_handling_in_get_improvement_suggestions(
        self, ai_service, mock_repository
    ):
        """Test error handling in get_improvement_suggestions."""
        # Arrange
        mock_repository.find_low_accuracy_cases.side_effect = Exception(
            "Database error"
        )

        # Act
        suggestions = await ai_service.get_improvement_suggestions()

        # Assert
        assert suggestions == []  # Should return empty list on error

    @pytest.mark.asyncio
    async def test_error_handling_in_find_similar_cases(
        self, ai_service, mock_repository
    ):
        """Test error handling in find_similar_successful_cases."""
        # Arrange
        mock_repository.find_similar_inputs.side_effect = Exception("Database error")

        # Act
        result = await ai_service.find_similar_successful_cases("test", "en")

        # Assert
        assert result == []  # Should return empty list on error

    @pytest.mark.asyncio
    async def test_error_handling_in_cleanup_old_data(
        self, ai_service, mock_repository
    ):
        """Test error handling in cleanup_old_data."""
        # Arrange
        mock_repository.delete_old_data.side_effect = Exception("Database error")

        # Act
        result = await ai_service.cleanup_old_data()

        # Assert
        assert result == 0  # Should return 0 on error

    @pytest.mark.asyncio
    async def test_error_handling_in_confidence_calibration(
        self, ai_service, mock_repository
    ):
        """Test error handling in get_confidence_calibration_report."""
        # Arrange
        mock_repository.get_accuracy_stats.side_effect = Exception("Database error")

        # Act
        report = await ai_service.get_confidence_calibration_report()

        # Assert
        assert report == {}  # Should return empty dict on error


# Cache functionality was removed from AILearningService to simplify the architecture
# The service now uses internal caching without external Redis dependency
