"""Unit tests for AI training data entity."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import pytest

from src.ai_service.domain.entities.ai_training_data import (
    AITrainingData,
    AITrainingDataId,
    FeedbackType,
    ProcessingStatus,
)
from src.ai_service.domain.value_objects.confidence import ConfidenceScore


class TestAITrainingDataId:
    """Unit tests for AITrainingDataId value object."""

    def test_generate_creates_unique_ids(self):
        """Test that generate creates unique IDs."""
        # Act
        id1 = AITrainingDataId.generate()
        id2 = AITrainingDataId.generate()

        # Assert
        assert isinstance(id1, AITrainingDataId)
        assert isinstance(id2, AITrainingDataId)
        assert id1 != id2
        assert id1.value != id2.value

    def test_from_string_creates_id(self):
        """Test creating ID from string."""
        # Arrange
        test_value = "test-id-123"

        # Act
        training_id = AITrainingDataId.from_string(test_value)

        # Assert
        assert training_id.value == test_value

    def test_from_string_validates_input(self):
        """Test that from_string validates input."""
        # Test empty string
        with pytest.raises(
            ValueError, match="AITrainingDataId must be a non-empty string"
        ):
            AITrainingDataId.from_string("")

        # Test None
        with pytest.raises(
            ValueError, match="AITrainingDataId must be a non-empty string"
        ):
            AITrainingDataId.from_string(None)

    def test_string_representation(self):
        """Test string representation of ID."""
        # Arrange
        test_value = "test-id-456"
        training_id = AITrainingDataId.from_string(test_value)

        # Act & Assert
        assert str(training_id) == test_value

    def test_equality(self):
        """Test equality comparison."""
        # Arrange
        id1 = AITrainingDataId.from_string("same-id")
        id2 = AITrainingDataId.from_string("same-id")
        id3 = AITrainingDataId.from_string("different-id")

        # Assert
        assert id1 == id2
        assert id1 != id3
        assert id1 != "not-an-id"  # Different type

    def test_hash(self):
        """Test that IDs are hashable."""
        # Arrange
        id1 = AITrainingDataId.from_string("test-id")
        id2 = AITrainingDataId.from_string("test-id")

        # Act & Assert
        assert hash(id1) == hash(id2)
        assert {id1, id2} == {id1}  # Set deduplication works


class TestProcessingStatus:
    """Unit tests for ProcessingStatus enum."""

    def test_enum_values(self):
        """Test that enum has expected values."""
        assert ProcessingStatus.SUCCESS == "success"
        assert ProcessingStatus.FAILED_VALIDATION == "failed_validation"
        assert ProcessingStatus.FAILED_AI_PARSING == "failed_ai_parsing"
        assert ProcessingStatus.PENDING_REVIEW == "pending_review"

    def test_enum_iteration(self):
        """Test iterating over enum values."""
        statuses = list(ProcessingStatus)
        assert len(statuses) == 4
        assert ProcessingStatus.SUCCESS in statuses


class TestFeedbackType:
    """Unit tests for FeedbackType enum."""

    def test_enum_values(self):
        """Test that enum has expected values."""
        assert FeedbackType.USER_CORRECTION == "user_correction"
        assert FeedbackType.ADMIN_VALIDATION == "admin_validation"
        assert FeedbackType.MODEL_IMPROVEMENT == "model_improvement"

    def test_enum_iteration(self):
        """Test iterating over enum values."""
        types = list(FeedbackType)
        assert len(types) == 3
        assert FeedbackType.USER_CORRECTION in types


class TestAITrainingData:
    """Unit tests for AITrainingData entity."""

    def test_default_initialization(self):
        """Test default initialization of training data."""
        # Act
        training_data = AITrainingData()

        # Assert
        assert isinstance(training_data.id, AITrainingDataId)
        assert training_data.input_text == ""
        assert training_data.language == "en"
        assert training_data.user_id is None
        assert training_data.session_id is None
        assert training_data.raw_ai_response == ""
        assert training_data.parsed_ai_data == {}
        assert isinstance(training_data.ai_confidence, ConfidenceScore)
        assert training_data.ai_confidence.value == 0.0
        assert training_data.processing_time_ms == 0
        assert training_data.model_version == ""
        assert training_data.status == ProcessingStatus.SUCCESS
        assert training_data.error_message is None
        assert training_data.validation_errors == []
        assert training_data.final_spending_data == {}
        assert training_data.spending_entry_id is None
        assert training_data.feedback_provided is False
        assert training_data.feedback_type is None
        assert training_data.corrected_data == {}
        assert training_data.admin_notes is None
        assert training_data.accuracy_score is None
        assert training_data.improvement_suggestions == []
        assert training_data.category_mapping_learned == {}
        assert isinstance(training_data.created_at, datetime)
        assert isinstance(training_data.updated_at, datetime)
        assert training_data.reviewed_at is None

    def test_initialization_with_values(self):
        """Test initialization with specific values."""
        # Arrange
        test_id = AITrainingDataId.generate()
        test_confidence = ConfidenceScore(0.85)
        test_time = datetime.utcnow()

        # Act
        training_data = AITrainingData(
            id=test_id,
            input_text="Buy coffee 150 baht",
            language="th",
            user_id="user123",
            session_id="session456",
            raw_ai_response='{"amount": 150}',
            parsed_ai_data={"amount": 150, "currency": "THB"},
            ai_confidence=test_confidence,
            processing_time_ms=1200,
            model_version="llama3.2:3b",
            status=ProcessingStatus.SUCCESS,
            created_at=test_time,
        )

        # Assert
        assert training_data.id == test_id
        assert training_data.input_text == "Buy coffee 150 baht"
        assert training_data.language == "th"
        assert training_data.user_id == "user123"
        assert training_data.session_id == "session456"
        assert training_data.raw_ai_response == '{"amount": 150}'
        assert training_data.parsed_ai_data == {"amount": 150, "currency": "THB"}
        assert training_data.ai_confidence == test_confidence
        assert training_data.processing_time_ms == 1200
        assert training_data.model_version == "llama3.2:3b"
        assert training_data.status == ProcessingStatus.SUCCESS
        assert training_data.created_at == test_time

    def test_mark_as_failed(self):
        """Test marking training data as failed."""
        # Arrange
        training_data = AITrainingData()
        error_message = "Parsing failed"
        validation_errors = ["Missing amount", "Invalid currency"]

        # Act
        with patch(
            "src.ai_service.domain.entities.ai_training_data.datetime"
        ) as mock_datetime:
            mock_now = datetime(2023, 1, 1, 12, 0, 0)
            mock_datetime.utcnow.return_value = mock_now

            training_data.mark_as_failed(error_message, validation_errors)

        # Assert
        assert training_data.status == ProcessingStatus.FAILED_VALIDATION
        assert training_data.error_message == error_message
        assert training_data.validation_errors == validation_errors
        assert training_data.updated_at == mock_now

    def test_mark_as_failed_without_validation_errors(self):
        """Test marking as failed without validation errors."""
        # Arrange
        training_data = AITrainingData()
        error_message = "General error"

        # Act
        training_data.mark_as_failed(error_message)

        # Assert
        assert training_data.status == ProcessingStatus.FAILED_VALIDATION
        assert training_data.error_message == error_message
        assert training_data.validation_errors == []

    def test_add_feedback(self):
        """Test adding feedback to training data."""
        # Arrange
        training_data = AITrainingData(
            parsed_ai_data={"category": "food", "amount": 100}
        )
        corrected_data = {"category": "dining", "amount": 120}
        admin_notes = "User corrected category"

        # Act
        with patch(
            "src.ai_service.domain.entities.ai_training_data.datetime"
        ) as mock_datetime:
            mock_now = datetime(2023, 1, 1, 12, 0, 0)
            mock_datetime.utcnow.return_value = mock_now

            training_data.add_feedback(
                FeedbackType.USER_CORRECTION, corrected_data, admin_notes
            )

        # Assert
        assert training_data.feedback_provided is True
        assert training_data.feedback_type == FeedbackType.USER_CORRECTION
        assert training_data.corrected_data == corrected_data
        assert training_data.admin_notes == admin_notes
        assert training_data.updated_at == mock_now
        assert training_data.accuracy_score is not None
        assert training_data.category_mapping_learned == {"food": "dining"}

    def test_calculate_accuracy_score_perfect_match(self):
        """Test accuracy calculation when AI data matches corrected data."""
        # Arrange
        training_data = AITrainingData(
            parsed_ai_data={"category": "food", "amount": 100, "currency": "THB"}
        )
        corrected_data = {"category": "food", "amount": 100, "currency": "THB"}

        # Act
        training_data.add_feedback(FeedbackType.USER_CORRECTION, corrected_data)

        # Assert
        assert training_data.accuracy_score == 1.0  # Perfect match

    def test_calculate_accuracy_score_partial_match(self):
        """Test accuracy calculation with partial matches."""
        # Arrange
        training_data = AITrainingData(
            parsed_ai_data={"category": "food", "amount": 100, "currency": "THB"}
        )
        corrected_data = {
            "category": "dining",
            "amount": 100,
        }  # Only category corrected

        # Act
        training_data.add_feedback(FeedbackType.USER_CORRECTION, corrected_data)

        # Assert
        # 2 out of 3 fields correct (amount and currency unchanged, category corrected)
        assert abs(training_data.accuracy_score - (2 / 3)) < 0.01

    def test_calculate_accuracy_score_no_data(self):
        """Test accuracy calculation with no data."""
        # Arrange
        training_data = AITrainingData()

        # Act
        training_data.add_feedback(FeedbackType.USER_CORRECTION, {})

        # Assert
        assert training_data.accuracy_score is None

    def test_extract_category_mappings(self):
        """Test extracting category mappings from feedback."""
        # Arrange
        training_data = AITrainingData(
            parsed_ai_data={"category": "restaurant", "amount": 100}
        )
        corrected_data = {"category": "Food & Dining", "amount": 100}

        # Act
        training_data.add_feedback(FeedbackType.USER_CORRECTION, corrected_data)

        # Assert
        assert training_data.category_mapping_learned == {"restaurant": "Food & Dining"}

    def test_extract_category_mappings_no_change(self):
        """Test category mapping when category doesn't change."""
        # Arrange
        training_data = AITrainingData(
            parsed_ai_data={"category": "food", "amount": 100}
        )
        corrected_data = {"category": "food", "amount": 120}  # Only amount changed

        # Act
        training_data.add_feedback(FeedbackType.USER_CORRECTION, corrected_data)

        # Assert
        assert training_data.category_mapping_learned == {}

    def test_generate_learning_insights(self):
        """Test generating learning insights."""
        # Arrange
        training_data = AITrainingData(
            input_text="Buy coffee 150 baht with credit card",
            language="th",
            status=ProcessingStatus.SUCCESS,
            ai_confidence=ConfidenceScore(0.85),
            accuracy_score=0.9,
            feedback_provided=True,
            feedback_type=FeedbackType.USER_CORRECTION,
            error_message=None,
            validation_errors=[],
            category_mapping_learned={"coffee": "Food & Dining"},
        )

        # Act
        insights = training_data.generate_learning_insights()

        # Assert
        assert insights["input_text"] == training_data.input_text
        assert insights["language"] == "th"
        assert insights["status"] == "success"
        assert insights["ai_confidence"] == 0.85
        assert insights["accuracy_score"] == 0.9
        assert insights["feedback_provided"] is True
        assert insights["feedback_type"] == "user_correction"
        assert insights["category_mapping_learned"] == {"coffee": "Food & Dining"}
        assert "input_patterns" in insights
        assert "common_errors" in insights
        assert "confidence_accuracy_analysis" in insights

    def test_analyze_input_patterns(self):
        """Test input pattern analysis."""
        # Arrange
        training_data = AITrainingData(
            input_text="Buy coffee 150 baht with credit card", language="th"
        )

        # Act
        insights = training_data.generate_learning_insights()
        patterns = insights["input_patterns"]

        # Assert
        assert patterns["text_length"] == len(training_data.input_text)
        assert patterns["language"] == "th"
        assert patterns["contains_numbers"] is True
        assert patterns["contains_currency"] is True
        assert patterns["word_count"] == 7

    def test_analyze_input_patterns_no_numbers_or_currency(self):
        """Test input pattern analysis without numbers or currency."""
        # Arrange
        training_data = AITrainingData(input_text="hello world", language="en")

        # Act
        insights = training_data.generate_learning_insights()
        patterns = insights["input_patterns"]

        # Assert
        assert patterns["contains_numbers"] is False
        assert patterns["contains_currency"] is False
        assert patterns["word_count"] == 2

    def test_identify_common_errors(self):
        """Test identifying common errors."""
        # Arrange
        training_data = AITrainingData(
            error_message="Parsing failed",
            validation_errors=["Missing amount", "Invalid format"],
        )

        # Act
        insights = training_data.generate_learning_insights()
        errors = insights["common_errors"]

        # Assert
        assert "Parsing failed" in errors
        assert "Missing amount" in errors
        assert "Invalid format" in errors

    def test_analyze_confidence_accuracy(self):
        """Test confidence vs accuracy analysis."""
        # Arrange
        training_data = AITrainingData(
            ai_confidence=ConfidenceScore(0.9), accuracy_score=0.7
        )

        # Act
        insights = training_data.generate_learning_insights()
        analysis = insights["confidence_accuracy_analysis"]

        # Assert
        assert analysis["ai_confidence"] == 0.9
        assert analysis["actual_accuracy"] == 0.7
        assert abs(analysis["confidence_gap"] - 0.2) < 0.01

    def test_to_dict_conversion(self):
        """Test converting training data to dictionary."""
        # Arrange
        test_id = AITrainingDataId.generate()
        test_time = datetime(2023, 1, 1, 12, 0, 0)
        training_data = AITrainingData(
            id=test_id,
            input_text="test text",
            language="en",
            ai_confidence=ConfidenceScore(0.8),
            created_at=test_time,
            updated_at=test_time,
        )

        # Act
        data_dict = training_data.to_dict()

        # Assert
        assert data_dict["id"] == str(test_id)
        assert data_dict["input_text"] == "test text"
        assert data_dict["language"] == "en"
        assert data_dict["ai_confidence"] == 0.8
        assert data_dict["created_at"] == test_time.isoformat()
        assert data_dict["updated_at"] == test_time.isoformat()
        assert data_dict["reviewed_at"] is None

    def test_from_dict_conversion(self):
        """Test creating training data from dictionary."""
        # Arrange
        test_id = "test-id-123"
        test_time = "2023-01-01T12:00:00"
        data_dict = {
            "id": test_id,
            "input_text": "test text",
            "language": "th",
            "ai_confidence": 0.75,
            "status": "success",
            "feedback_type": "user_correction",
            "created_at": test_time,
            "updated_at": test_time,
            "reviewed_at": None,
        }

        # Act
        training_data = AITrainingData.from_dict(data_dict)

        # Assert
        assert str(training_data.id) == test_id
        assert training_data.input_text == "test text"
        assert training_data.language == "th"
        assert training_data.ai_confidence.value == 0.75
        assert training_data.status == ProcessingStatus.SUCCESS
        assert training_data.feedback_type == FeedbackType.USER_CORRECTION
        assert training_data.created_at == datetime.fromisoformat(test_time)
        assert training_data.updated_at == datetime.fromisoformat(test_time)
        assert training_data.reviewed_at is None

    def test_from_dict_with_datetime_objects(self):
        """Test from_dict with datetime objects instead of strings."""
        # Arrange
        test_time = datetime(2023, 1, 1, 12, 0, 0)
        data_dict = {
            "id": "test-id",
            "input_text": "test",
            "created_at": test_time,  # datetime object
            "updated_at": test_time,  # datetime object
        }

        # Act
        training_data = AITrainingData.from_dict(data_dict)

        # Assert
        assert training_data.created_at == test_time
        assert training_data.updated_at == test_time

    def test_roundtrip_conversion(self):
        """Test that to_dict and from_dict are inverse operations."""
        # Arrange
        original = AITrainingData(
            input_text="Buy coffee 150 baht",
            language="th",
            user_id="user123",
            parsed_ai_data={"amount": 150},
            ai_confidence=ConfidenceScore(0.85),
            processing_time_ms=1200,
            status=ProcessingStatus.SUCCESS,
            feedback_provided=True,
            feedback_type=FeedbackType.USER_CORRECTION,
            corrected_data={"amount": 160},
            accuracy_score=0.9,
        )

        # Act
        data_dict = original.to_dict()
        reconstructed = AITrainingData.from_dict(data_dict)

        # Assert
        assert str(reconstructed.id) == str(original.id)
        assert reconstructed.input_text == original.input_text
        assert reconstructed.language == original.language
        assert reconstructed.user_id == original.user_id
        assert reconstructed.parsed_ai_data == original.parsed_ai_data
        assert reconstructed.ai_confidence.value == original.ai_confidence.value
        assert reconstructed.processing_time_ms == original.processing_time_ms
        assert reconstructed.status == original.status
        assert reconstructed.feedback_provided == original.feedback_provided
        assert reconstructed.feedback_type == original.feedback_type
        assert reconstructed.corrected_data == original.corrected_data
        assert reconstructed.accuracy_score == original.accuracy_score
